"""`wb demo`: the whole discovery story on a database this command creates.

The database lives in a fresh `mkdtemp()` directory and is removed with that
directory when the command finishes. The configured database path is ignored.
It is a parameter of the store, so honouring it could aim this command at
someone's own database, and deleting a file there would delete that database.
Nothing is removed except the directory this command created.

Replay is the default and needs no network. `--live` constructs a `LiveSource`,
which is what refuses anyone but a lead, before any of the story is printed.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from itertools import count
from pathlib import Path

from agent_container.core.budget import Budget
from agent_container.core.provider import ModelProvider

from workbench.cli.discover import (
    FIXTURE,
    RUN_MAX_SECONDS,
    RUN_MAX_TOKENS,
    RUN_MAX_TURNS,
    _report,
)
from workbench.cli.readout import _inspect
from workbench.cli.sources import render_sources
from workbench.coordinator.coordinator import DiscoveryCoordinator
from workbench.coordinator.providers import LiveSource, ProviderSource, ReplaySource
from workbench.core.config import Config
from workbench.core.errors import CoverageGapsPresent, WorkbenchError
from workbench.core.principals import Principal, Role
from workbench.core.sources import SourceLibrary
from workbench.core.store import Readout, Store
from workbench.readout.render import render_readout, render_trace
from workbench.readout.synthesis import replay_provider, synthesise
from workbench.readout.text import one_line, safe_token

#: The committed pack's engagement. The demo tells that story and no other.
ENGAGEMENT = "acme-p2p"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--principal", required=True, help="the acting principal's id")
    parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in Role],
        help="the acting principal's role",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="call Bedrock instead of the committed recordings (lead only)",
    )


def run(args: argparse.Namespace) -> int:
    # `mkdtemp` is the whole isolation: the directory name is not derived from
    # the configured path, and the `finally` removes only this directory.
    directory = tempfile.mkdtemp(prefix="wb-demo-")
    try:
        configured = Config.from_env()
        config = replace(configured, database_path=Path(directory) / "workbench.sqlite3")
        with _open(config) as store:
            store.build()
            try:
                return asyncio.run(_story(store, config, args))
            except WorkbenchError as exc:
                return _fail(exc)
    except WorkbenchError as exc:
        return _fail(exc)
    finally:
        shutil.rmtree(directory)


async def _story(store: Store, config: Config, args: argparse.Namespace) -> int:
    principal = store.load_principal(args.principal, Role(args.role))
    live = bool(args.live)
    # The live check is first, and it prints nothing. An analyst `--live` is a
    # refusal, not a story that spends money part way through.
    source, synthesis_provider = _providers(store, config, principal, live=live)

    library = SourceLibrary.for_engagement(config, ENGAGEMENT)
    refs = store.index_sources(principal, ENGAGEMENT, library)
    print(f"demo: {'live' if live else 'replay'}")
    print(f"principal: {safe_token(principal.id, limit=128)}")
    print(f"role: {principal.role.value}")
    print("sources:")
    print(render_sources(ENGAGEMENT, refs), end="")

    result = await DiscoveryCoordinator(store, config, source).discover(
        principal,
        ENGAGEMENT,
        budget=Budget(
            max_turns=RUN_MAX_TURNS,
            max_tokens=RUN_MAX_TOKENS,
            max_seconds=RUN_MAX_SECONDS,
        ),
    )
    print("discover:")
    _report(result)

    rendered = await synthesise(store, config, principal, ENGAGEMENT, synthesis_provider)
    _engagement_id, client, _state = store.engagement_summary(principal, ENGAGEMENT)
    print("readout:")
    print(render_readout(client=client, readout=rendered), end="")

    print("trace:")
    if not result.unverified_claims:
        print("trace: none")
    else:
        for claim in result.unverified_claims:
            document, verified, reason = _inspect(store, config, principal, claim)
            print(
                render_trace(claim=claim, document=document, live_verified=verified, reason=reason),
                end="",
            )

    print("finalise:")
    try:
        readout = store.finalise(principal, ENGAGEMENT, accept_gaps=False)
    except CoverageGapsPresent as exc:
        # Expected on the committed recording: one subagent was throttled. The
        # refusal is part of the story. Accepting the gap is the next line, and
        # it is recorded.
        _print_error(exc)
        readout = store.finalise(principal, ENGAGEMENT, accept_gaps=True)
    accepted = store.finalisation_accepted_gaps(principal, ENGAGEMENT)
    _print_final(readout, accepted)
    return 0


def _providers(
    store: Store, config: Config, principal: Principal, *, live: bool
) -> tuple[ProviderSource, ModelProvider]:
    if not live:
        return ReplaySource.from_file(FIXTURE), replay_provider()
    engagement = store.engagement(principal, ENGAGEMENT)
    source = LiveSource(config, principal, engagement.id, engagement.state)
    return source, source.plan_provider()


def _open(config: Config) -> Store:
    """A store whose ids and clock do not change between runs.

    Back-to-back demos print claim ids. A random id would make the second run
    differ, which is the failure the smoke comparison exists to catch.
    """
    ids = count(1)

    def new_id() -> str:
        return f"id-{next(ids):04d}"

    return Store.open(
        config,
        now=lambda: datetime(2026, 11, 21, 12, 0, tzinfo=UTC),
        new_id=new_id,
    )


def _print_final(readout: Readout, accepted: bool) -> None:
    print(f"engagement: {safe_token(readout.engagement_id, limit=128)}")
    print(f"state: {safe_token(readout.state, limit=16)}")
    print(f"finalised_by: {safe_token(readout.finalised_by or '', limit=128)}")
    print(f"accept_gaps: {str(accepted).lower()}")


def _print_error(exc: WorkbenchError) -> None:
    print(f"{exc.code}: {one_line(exc.detail, limit=400) or 'refused'}")
    print(f"category={exc.category.value} retryable={str(exc.retryable).lower()}")


def _fail(exc: WorkbenchError) -> int:
    _print_error(exc)
    return 1
