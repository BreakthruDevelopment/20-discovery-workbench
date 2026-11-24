"""What the built image does by default, asserted against the Dockerfile.

The deployed container is `wb serve`. Six slices of this app were built, reviewed and
merged while the image's command was `--version`, which prints one line and exits, so
nothing deployable existed and no test or workflow step said so (issue #24).

`ci.yml`'s `Container image` job proves the real thing: it builds the image, runs it with
no arguments and curls both routes. These assertions are the cheap half -- they run in
`pytest`, need no Docker, and fail on the one-line edit that would put the image back to
printing a version.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from workbench.cli.http import _DEFAULT_PORT

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def _directive(name: str) -> str:
    """The last `name` instruction in the Dockerfile, as written."""
    found: list[str] = []
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{name} "):
            found.append(stripped[len(name) + 1 :].strip())
    assert found, f"the Dockerfile has no {name} instruction"
    return found[-1]


def _exec_form(name: str) -> list[str]:
    """A JSON exec-form instruction as its argument list.

    Exec form and not shell form on purpose: shell form wraps the process in `/bin/sh -c`,
    which does not forward SIGTERM, so the platform's stop signal would be swallowed and
    every deploy would wait out the kill timeout.
    """
    raw = _directive(name)
    assert raw.startswith("["), f"{name} must be exec form, so signals reach the process"
    parsed = json.loads(raw)
    assert isinstance(parsed, list) and all(isinstance(item, str) for item in parsed)
    return parsed


def test_the_image_entry_point_is_the_cli() -> None:
    assert _exec_form("ENTRYPOINT") == ["wb"]


def test_the_image_serves_by_default_rather_than_printing_a_version() -> None:
    """The regression that made the app undeployable. `--version` here is the bug."""
    assert _exec_form("CMD") == ["serve"]


def test_the_build_validates_the_lock() -> None:
    """`--frozen` installs from the lock without checking it matches pyproject.toml."""
    body = DOCKERFILE.read_text(encoding="utf-8")
    sync = [
        line for line in body.splitlines() if "uv sync" in line and not line.strip().startswith("#")
    ]
    assert sync, "the build stage no longer runs uv sync"
    for line in sync:
        words = shlex.split(line.removeprefix("RUN "))
        assert "--locked" in words, "uv sync must validate the lock"
        assert "--frozen" not in words, "--frozen does not validate the lock; --locked does"


def test_the_image_documents_the_default_port() -> None:
    """EXPOSE documents the default. The served port comes from PORT at runtime.

    Compared to `_DEFAULT_PORT` so the documented default and the code default
    cannot drift. The image does not pin the runtime port: `PORT` is read when
    the container starts, which is why CI also curls a `PORT=9123` run.
    """
    assert _directive("EXPOSE") == str(_DEFAULT_PORT)
