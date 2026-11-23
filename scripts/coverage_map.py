"""Write or check the static exam-coverage map.

pytest runs this script (`--check`) so a moved line fails the suite instead of
leaving `GET /` publishing a stale file and line. With no arguments it rewrites
`workbench/cli/exam_coverage.txt`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from workbench.cli.coverage import map_path, render

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        text = render(ROOT)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    destination = map_path()
    if args == ["--check"]:
        try:
            current = destination.read_text(encoding="utf-8")
        except OSError:
            print("exam coverage map is missing; run scripts/coverage_map.py", file=sys.stderr)
            return 1
        if current != text:
            print("exam coverage map is stale; run scripts/coverage_map.py", file=sys.stderr)
            return 1
        return 0
    if args == []:
        destination.write_text(text, encoding="utf-8")
        return 0
    print("usage: scripts/coverage_map.py [--check]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
