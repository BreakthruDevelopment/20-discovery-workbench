"""Command-line entry point (`wb`). Subcommands are added by the slice that owns each one."""

import argparse
from collections.abc import Sequence

from workbench import __version__
from workbench.cli import discover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wb", description="Discovery workbench.")
    parser.add_argument("--version", action="version", version=f"wb {__version__}")
    # `required=False` so a bare `wb` still prints the help line `tests/test_cli.py` pins, which is
    # what the installed-CLI smoke step in CI checks.
    sub = parser.add_subparsers(dest="command")
    discover.add_arguments(
        sub.add_parser(
            "discover",
            help="plan scoped questions, run the subagents, and record what they found",
            description=(
                "Plan scoped questions from the engagement's brief and source index, delegate "
                "them to concurrent subagents, and record every question, claim and subagent run."
            ),
        )
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "discover":
        return discover.run(args)
    print(f"wb {__version__}: no command given; see --help")
    return 0
