"""Command-line entry point (`wb`)."""

import argparse
from collections.abc import Sequence

from workbench import __version__
from workbench.cli import demo, discover, http, readout, sources


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
    sources_parser = sub.add_parser(
        "sources",
        help="the engagement's source index",
        description="List an engagement's source index, with sizes and what is unreadable.",
    )
    sources_sub = sources_parser.add_subparsers(dest="sources_command", required=True)
    sources.add_list(
        sources_sub.add_parser(
            "list",
            help="list sources with sizes and what is unreadable",
        )
    )
    demo.add_arguments(
        sub.add_parser(
            "demo",
            help="tell the discovery story on recorded replies",
            description=(
                "List sources, run discovery, render the readout, trace an unverified claim "
                "and finalise, on recorded replies. --live calls Bedrock and is lead only. "
                "The database is a fresh temporary directory, never the configured path."
            ),
        )
    )
    http.add_arguments(
        sub.add_parser(
            "serve",
            help="serve GET /healthz and GET /",
            description=(
                "Serve the version and a replay round-trip at /healthz, and the static "
                "exam-coverage map at /."
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
    if args.command == "sources":
        return sources.run(args)
    if args.command == "demo":
        return demo.run(args)
    if args.command == "serve":
        return http.run(args)
    print(f"wb {__version__}: no command given; see --help")
    return 0
