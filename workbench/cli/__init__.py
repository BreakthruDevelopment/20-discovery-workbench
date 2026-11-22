"""Command-line entry point (`wb`). Subcommands arrive in later slices; for now `--version`."""

import argparse
from collections.abc import Sequence

from workbench import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wb", description="Discovery workbench.")
    parser.add_argument("--version", action="version", version=f"wb {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    print(f"wb {__version__}: no command given; see --help")
    return 0
