"""`wb discover <engagement>`: plan, fan out, record. Thin on purpose.

20.6 owns the shape of this package, so this module adds one subcommand and nothing else: it
parses arguments, builds a principal through the store, picks a provider source, runs the
coordinator and prints what happened. Every decision that matters -- who may act, what a subagent
may read, whether a quote checks out -- is made in `workbench/core/` and `workbench/coordinator/`,
not here.

Replay is the default and needs no network. `--live` is `lead`-only, and the check is
`assert_can(RUN_LIVE)` against the engagement, not a flag this module interprets.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from agent_container.core.budget import Budget

from workbench.coordinator.coordinator import DiscoveryCoordinator, DiscoveryRun
from workbench.coordinator.providers import LiveSource, ProviderSource, ReplaySource
from workbench.core.config import Config
from workbench.core.errors import WorkbenchError
from workbench.core.principals import EngagementState, Principal, Role
from workbench.core.store import Store

#: The committed recording. Beside this package's code, so the wheel carries it.
FIXTURE = (
    Path(__file__).resolve().parent.parent / "coordinator" / "fixtures" / "acme-discovery.json"
)

#: One discovery run's whole allowance. Each subagent takes a `Budget.child()` of it, so the run as
#: a whole stops at these numbers however many subagents the plan asks for.
RUN_MAX_TURNS = 60
RUN_MAX_TOKENS = 400_000
RUN_MAX_SECONDS = 600.0


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("engagement", help="the engagement id, for example acme-p2p")
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
        help="call Bedrock instead of the committed recording (lead only)",
    )


def run(args: argparse.Namespace) -> int:
    config = Config.from_env()
    try:
        with Store.open(config) as store:
            store.build()
            principal = store.load_principal(args.principal, Role(args.role))
            source = _source(store, principal, args.engagement, live=bool(args.live))
            result = asyncio.run(
                DiscoveryCoordinator(store, config, source).discover(
                    principal,
                    args.engagement,
                    budget=Budget(
                        max_turns=RUN_MAX_TURNS,
                        max_tokens=RUN_MAX_TOKENS,
                        max_seconds=RUN_MAX_SECONDS,
                    ),
                )
            )
    except WorkbenchError as exc:
        # The category, the code and the retry flag -- never a stack trace, and never a value the
        # caller passed in.
        print(f"{exc.code}: {exc.detail or 'refused'}")
        print(f"category={exc.category.value} retryable={str(exc.retryable).lower()}")
        return 1
    _report(result)
    return 0


def _source(
    store: Store, principal: Principal, engagement_id: str, *, live: bool
) -> ProviderSource:
    if not live:
        return ReplaySource.from_file(FIXTURE)
    # `--live` is an action, checked like any other. Reading the engagement first means the check
    # sees its real state and that the principal is assigned to it.
    # Read the engagement first so the check sees its real state and that this principal is
    # assigned to it; `LiveSource` itself calls `assert_can(RUN_LIVE)`, so forgetting that line
    # here could not open the live path.
    engagement = store.engagement(principal, engagement_id)
    return LiveSource(
        Config.from_env(), principal, engagement.id, EngagementState(engagement.state)
    )


def _one_line(value: str, *, limit: int = 600) -> str:
    """Model text, flattened to one line and capped, before it is printed.

    `strategy_note` is the planner's own prose and it was printed verbatim: a note containing a
    newline could add a line to this output, and a line that looks like `  GAP  q9 (process): …`
    is indistinguishable from one this function wrote. The same reasoning as the `doc_id` pattern,
    applied at the other end -- constrain the id where it enters, flatten the prose where it
    leaves. Every line-breaking character goes, not just `\n`: `\r` alone moves a terminal's
    cursor to the start of the line and overwrites what is already there.

    And every other non-printable with it, which splitting on whitespace does not reach: `\x1b`
    is not whitespace, so `"\x1b[2J\x1b[H"` survived the flatten -- and `strategy:` is the last
    line printed, so an escape sequence there can clear the screen or redraw over the coverage
    block it was printed below. `DOC_ID_PATTERN` already refuses exactly these characters in an
    id; this is the same rule at the other end, which is where it should have been from the
    start: the two halves of one guard cannot disagree about what is dangerous.
    """
    flattened = " ".join(value.split())
    visible = "".join(char for char in flattened if char.isprintable())
    return visible if len(visible) <= limit else visible[:limit] + "…"


def _report(result: DiscoveryRun) -> None:
    """Coverage first, then the findings. A gap is never further down the page than a claim."""
    failed = result.failed
    print(f"engagement: {result.engagement_id}")
    print(
        f"coverage: {len(result.questions)} question(s), "
        f"{len(result.questions) - len(failed)} answered, {len(failed)} failed"
    )
    for outcome in failed:
        category = outcome.error_category.value if outcome.error_category else "unknown"
        print(
            f"  GAP  q{outcome.seq} ({outcome.specialist}): {category}, "
            f"retryable={str(outcome.is_retryable).lower()}"
        )
    for dropped in result.dropped:
        print(f"  DROPPED question: {dropped.reason}")
    print(
        f"claims: {len(result.verified_claims)} verified, "
        f"{len(result.unverified_claims)} not verified"
    )
    for outcome in result.outcomes:
        if outcome.state != "ok":
            continue
        note = " insufficient_evidence" if outcome.insufficient_evidence else ""
        print(
            f"  q{outcome.seq} ({outcome.specialist}): {outcome.findings_recorded} recorded "
            f"of {outcome.findings_offered} offered, {outcome.turns} turn(s){note}"
        )
        for doc_id, reason in sorted(outcome.unread.items()):
            print(f"      unread {doc_id}: {reason}")
    print(f"strategy: {_one_line(result.strategy_note)}")
