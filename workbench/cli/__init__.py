"""Command-line entry point (`wb`). Subcommands are added by the slice that owns each one."""

import argparse
from collections.abc import Sequence

from workbench import __version__
from workbench.cli import discover, readout


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
    readout.add_readout(
        sub.add_parser(
            "readout",
            help="synthesise and render the readout, coverage gaps first",
            description=(
                "Synthesise a draft readout from verified claims and render it with coverage "
                "first. A final readout is rendered as stored."
            ),
        )
    )
    readout.add_trace(
        sub.add_parser(
            "trace",
            help="show one claim, its quote and whether that quote checks out",
            description=(
                "Show one claim, the document it cites, the verbatim quote, and the result of "
                "checking that quote against the document."
            ),
        )
    )
    readout.add_finalise(
        sub.add_parser(
            "finalise",
            help="mark the readout final (lead only)",
            description=(
                "Mark the readout final. Refuses while a subagent run failed unless "
                "--accept-gaps is given, which is recorded."
            ),
        )
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "discover":
        return discover.run(args)
    if args.command == "readout":
        return readout.run_readout(args)
    if args.command == "trace":
        return readout.run_trace(args)
    if args.command == "finalise":
        return readout.run_finalise(args)
    print(f"wb {__version__}: no command given; see --help")
    return 0
