"""`wb sources list`: the source index, with sizes and what is unreadable.

Thin on purpose, same as the other commands. Who may list is decided by the store
(`LIST_SOURCES`), and what is unreadable is decided by the source library. This
module parses arguments and prints the index.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from workbench.core.config import Config
from workbench.core.errors import WorkbenchError
from workbench.core.principals import Role
from workbench.core.sources import SourceLibrary, SourceRef
from workbench.core.store import Store
from workbench.readout.text import one_line, safe_token


def add_list(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("engagement", help="the engagement id, for example acme-p2p")
    parser.add_argument("--principal", required=True, help="the acting principal's id")
    parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in Role],
        help="the acting principal's role",
    )


def run(args: argparse.Namespace) -> int:
    config = Config.from_env()
    try:
        with Store.open(config) as store:
            store.build()
            principal = store.load_principal(args.principal, Role(args.role))
            library = SourceLibrary.for_engagement(config, args.engagement)
            refs = store.index_sources(principal, args.engagement, library)
    except WorkbenchError as exc:
        return _fail(exc)
    print(render_sources(args.engagement, refs), end="")
    return 0


def render_sources(engagement_id: str, refs: Sequence[SourceRef]) -> str:
    """The index as text. Paths and reasons are flattened so they cannot add a line."""
    lines = [
        f"engagement: {safe_token(engagement_id, limit=128)}",
        f"documents: {len(refs)}",
    ]
    for ref in refs:
        line = (
            f"{one_line(ref.path, limit=300)} bytes={ref.bytes} "
            f"readable={str(ref.readable).lower()}"
        )
        if not ref.readable:
            line += f" reason={one_line(ref.unread_reason or 'unreadable', limit=200)}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _fail(exc: WorkbenchError) -> int:
    print(f"{exc.code}: {one_line(exc.detail, limit=400) or 'refused'}")
    print(f"category={exc.category.value} retryable={str(exc.retryable).lower()}")
    return 1
