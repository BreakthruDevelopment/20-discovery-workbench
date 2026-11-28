"""`wb readout`, `wb trace` and `wb finalise`.

Thin on purpose, same as `wb discover`: arguments, a principal, a provider, then the package
that owns the decision. Who may act, whether a quote checks out, and whether a gap may be
closed are decided in `workbench/core/` and `workbench/readout/`, not here.

`wb readout` synthesises a draft and then renders it, coverage first. A final readout is
rendered as stored. A sponsor never synthesises: the store's `read_readout` check is what
admits them, and only once the engagement is final. `--live` builds a `LiveSource`, whose
constructor is what refuses anyone but a lead, before any provider is asked to speak.

`wb trace` prints one claim, its document, its quote and the live verification result.
`wb finalise` is the lead-only close. A failed subagent run refuses it unless `--accept-gaps`
is given, and the store records that the flag was given.
"""

from __future__ import annotations

import argparse
import asyncio

from agent_container.core.provider import ModelProvider

from workbench.coordinator.providers import LiveSource, require_live
from workbench.core.config import Config
from workbench.core.errors import WorkbenchError
from workbench.core.principals import Principal, Role
from workbench.core.sources import SourceLibrary
from workbench.core.store import READOUT_FINAL, Claim, Store
from workbench.readout.render import render_readout, render_trace
from workbench.readout.synthesis import replay_provider, synthesise


def add_readout(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("engagement", help="the engagement id, for example acme-p2p")
    _principal_arguments(parser)
    parser.add_argument(
        "--live",
        action="store_true",
        help="call Bedrock for synthesis instead of the committed recording (lead only)",
    )
    parser.set_defaults(command="readout")


def add_trace(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("claim", help="the claim id to trace")
    _principal_arguments(parser)
    parser.set_defaults(command="trace")


def add_finalise(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("engagement", help="the engagement id, for example acme-p2p")
    _principal_arguments(parser)
    parser.add_argument(
        "--accept-gaps",
        action="store_true",
        help="finalise even though a subagent run failed; the acceptance is recorded",
    )
    parser.set_defaults(command="finalise")


def run_readout(args: argparse.Namespace) -> int:
    config = Config.from_env()
    try:
        with Store.open(config) as store:
            store.build()
            principal = store.load_principal(args.principal, Role(args.role))
            current = store.readout(principal, args.engagement)
            if args.live:
                # Judged before the stored-final return, so the lead-only refusal is a check and
                # not an accident of statement order. Same rule `LiveSource` applies; a final
                # readout builds no `LiveSource` and calls no model.
                # `engagement_summary`, not `engagement`: a sponsor may have the summary but not
                # `READ_DISCOVERY`, and the refusal must come from `run_live`, not from that.
                engagement_id, _client, state = store.engagement_summary(principal, args.engagement)
                require_live(principal, engagement_id, state)
            if current.state == READOUT_FINAL:
                rendered = current
            else:
                provider = _provider(
                    store, config, principal, args.engagement, live=bool(args.live)
                )
                rendered = asyncio.run(
                    synthesise(store, config, principal, args.engagement, provider)
                )
            _engagement_id, client, _state = store.engagement_summary(principal, args.engagement)
    except WorkbenchError as exc:
        return _fail(exc)
    print(render_readout(client=client, readout=rendered), end="")
    return 0


def run_trace(args: argparse.Namespace) -> int:
    config = Config.from_env()
    try:
        with Store.open(config) as store:
            store.build()
            principal = store.load_principal(args.principal, Role(args.role))
            claim = store.claim(principal, args.claim)
            document, live, reason = _inspect(store, config, principal, claim)
    except WorkbenchError as exc:
        return _fail(exc)
    print(
        render_trace(claim=claim, document=document, live_verified=live, reason=reason),
        end="",
    )
    return 0


def run_finalise(args: argparse.Namespace) -> int:
    config = Config.from_env()
    try:
        with Store.open(config) as store:
            store.build()
            principal = store.load_principal(args.principal, Role(args.role))
            readout = store.finalise(principal, args.engagement, accept_gaps=bool(args.accept_gaps))
            accepted = store.finalisation_accepted_gaps(principal, args.engagement)
    except WorkbenchError as exc:
        return _fail(exc)
    print(f"engagement: {readout.engagement_id}")
    print(f"state: {readout.state}")
    print(f"finalised_by: {readout.finalised_by or ''}")
    print(f"accept_gaps: {str(accepted).lower()}")
    return 0


def _principal_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--principal", required=True, help="the acting principal's id")
    parser.add_argument(
        "--role",
        required=True,
        choices=[role.value for role in Role],
        help="the acting principal's role",
    )


def _provider(
    store: Store,
    config: Config,
    principal: Principal,
    engagement_id: str,
    *,
    live: bool,
) -> ModelProvider:
    if not live:
        return replay_provider()
    # `LiveSource` checks `RUN_LIVE` in its constructor. Reading the engagement first gives
    # that check the engagement's real state. An analyst --live fails here, before boto3 loads.
    engagement = store.engagement(principal, engagement_id)
    return LiveSource(config, principal, engagement.id, engagement.state).plan_provider()


def _inspect(
    store: Store,
    config: Config,
    principal: Principal,
    claim: Claim,
) -> tuple[str | None, bool, str]:
    """The document path, the live quote check, and a reason that carries no quote text."""
    try:
        path = store.document_path(principal, claim.engagement_id, claim.doc_id)
    except WorkbenchError as exc:
        return None, False, exc.detail or exc.code
    library = SourceLibrary.for_engagement(config, claim.engagement_id)
    try:
        live = library.verify_quote(path, claim.quote)
    except WorkbenchError as exc:
        return path, False, exc.detail or exc.code
    if live:
        return path, True, "the quote is present verbatim in the document it names"
    return path, False, "the quote is not present verbatim in the document it names"


def _fail(exc: WorkbenchError) -> int:
    # The category, the code and the retry flag. Never a stack trace, and never a value the
    # caller passed in: `WorkbenchError` messages are built that way.
    print(f"{exc.code}: {exc.detail or 'refused'}")
    print(f"category={exc.category.value} retryable={str(exc.retryable).lower()}")
    return 1
