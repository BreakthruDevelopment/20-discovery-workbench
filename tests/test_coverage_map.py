"""The committed coverage map matches the script, and each cited line is still there."""

from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "coverage_map.py"
MAP = ROOT / "workbench" / "cli" / "exam_coverage.txt"

#: Independent of the generator's table, so a `--check` that always succeeds still fails here
#: when a cited line no longer holds the statement.
EXPECTED = {
    "1.2": ("workbench/coordinator/coordinator.py", "class DiscoveryCoordinator:"),
    "1.3": ("workbench/coordinator/agents.py", "class SpecialistAgent(AgentLoop):"),
    "5.3": ("workbench/coordinator/coordinator.py", "def _record_failure("),
    "5.6": (
        "workbench/readout/template.py",
        'level: int | str = item.level if claim_ids else "unknown"',
    ),
}


def _script_main() -> Callable[[list[str]], int]:
    namespace = runpy.run_path(str(SCRIPT), run_name="coverage_map_under_test")
    main = namespace["main"]
    if not callable(main):
        raise AssertionError("the coverage script does not define main")
    return cast(Callable[[list[str]], int], main)


def test_pytest_runs_the_coverage_script_and_the_map_is_current() -> None:
    assert _script_main()(["--check"]) == 0


def test_the_script_rejects_an_unknown_argument() -> None:
    assert _script_main()(["--write-somewhere-else"]) == 2


def test_each_cited_line_still_holds_its_statement() -> None:
    rows = [
        line.split("\t")
        for line in MAP.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert [row[0] for row in rows] == ["1.2", "1.3", "5.3", "5.6"]
    seen: set[str] = set()
    for statement_id, _subject, slice_id, reference in rows:
        path_text, line_text = reference.rsplit(":", 1)
        expected_path, needle = EXPECTED[statement_id]
        assert path_text == expected_path
        assert slice_id in {"20.4", "20.5"}
        line = (ROOT / path_text).read_text(encoding="utf-8").splitlines()[int(line_text) - 1]
        assert needle in line
        seen.add(statement_id)
    assert seen == set(EXPECTED)
