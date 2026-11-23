"""`scripts/smoke.sh` runs the replay demo, and `--url` checks the HTTP surface."""

from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
from pathlib import Path

from workbench.cli import http as http_mod

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "smoke.sh"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    venv_bin = ROOT / ".venv" / "bin"
    env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")
    return env


def _tail(text: str, lines: int = 40) -> str:
    return "\n".join(text.splitlines()[-lines:])


def test_smoke_script_replays_twice_and_ignores_its_configured_database() -> None:
    # S603: the smoke script is a shell program. Running it is the test.
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(SMOKE)],
        check=False,
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, _tail(result.stdout) + "\n" + _tail(result.stderr)


def test_smoke_url_checks_health_and_the_map() -> None:
    bound = http_mod.bind("127.0.0.1", 0)
    thread = threading.Thread(target=bound.serve_forever, daemon=True)
    thread.start()
    address = bound.server_address
    host, port = str(address[0]), int(address[1])
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.02)
    else:
        bound.shutdown()
        bound.server_close()
        raise AssertionError("the server did not accept a connection")
    try:
        # S603: the smoke script is a shell program. Running it is the test.
        result = subprocess.run(  # noqa: S603
            ["/bin/bash", str(SMOKE), "--url", f"http://{host}:{port}"],
            check=False,
            cwd=ROOT,
            env=_env(),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, _tail(result.stdout) + "\n" + _tail(result.stderr)
    finally:
        bound.shutdown()
        bound.server_close()
        thread.join(timeout=5)
