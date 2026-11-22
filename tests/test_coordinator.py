"""The coordinator's own rules: scoped context, the plan screen, and recording.

The spec's named evals are in `tests/test_discovery_evals.py`; this file holds the mechanics each
of them rests on.
"""

from __future__ import annotations

import asyncio

import pytest
from agent_container.core.budget import Budget
from agent_container.core.loop import MAX_USER_MESSAGE_CHARS
from agent_container.core.messages import ModelRequest, ModelResponse
from agent_container.core.provider import ModelProvider
from agent_container.core.tool import ToolContext

from tests.conftest_pack import (
    ACME,
    CLERK,
    FIXTURE,
    MATCHING,
    POLICY,
    RECEIVING,
    Pack,
)
from tests.recordings import answer, answering_specialist, finding, recording_source
from workbench.coordinator.coordinator import (
    DiscoveryCoordinator,
    DiscoveryRun,
    PlanRefused,
)
from workbench.coordinator.providers import ReplaySource
from workbench.coordinator.schemas import MAX_QUESTIONS, Answer, Plan, PlannedQuestion, Specialist
from workbench.coordinator.tools import ReadDocumentTool
from workbench.core.principals import Principal
from workbench.core.sources import SourceLibrary


def _run(pack: Pack, principal: Principal, engagement_id: str = ACME) -> DiscoveryRun:
    source = ReplaySource.from_file(FIXTURE)
    return asyncio.run(
        pack.coordinator(source).discover(principal, engagement_id, budget=_budget())
    )


def _budget() -> Budget:
    return Budget(max_turns=60, max_tokens=400_000, max_seconds=600.0)


def _ctx() -> ToolContext:
    return ToolContext(run_id="r", turn=1, tool_use_id="t")


# ---- the run as a whole --------------------------------------------------------------------


def test_the_recorded_run_is_the_shape_the_spec_describes(
    pack: Pack, pack_analyst: Principal
) -> None:
    """Five subagents, one throttled, one fabricated quote, the injection reported as content."""
    result = _run(pack, pack_analyst)
    assert len(result.questions) == 5
    assert len(result.failed) == 1
    assert len(result.verified_claims) == 7
    assert len(result.unverified_claims) == 1
    assert result.replanned is False


def test_the_run_is_recorded_in_plan_order(pack: Pack, pack_analyst: Principal) -> None:
    """A recorded demo that is not deterministic is not a demo."""
    first = _run(pack, pack_analyst)
    assert [q.text for q in first.questions] == [
        q.text for q in pack.store.questions(pack_analyst, ACME)
    ]
    assert [(o.seq, o.state) for o in first.outcomes] == [
        (1, "ok"),
        (2, "ok"),
        (3, "ok"),
        (4, "ok"),
        (5, "failed"),
    ]


def test_a_second_run_against_the_same_database_replays_the_same_way(
    pack: Pack, pack_analyst: Principal
) -> None:
    """The recording is keyed by plan position, not by `question.seq`.

    `record_questions` continues the engagement's numbering, so the second run's questions are
    seq 6-10. Keyed by `seq`, every one of them would miss the recording and fail, turning a
    recorded five-subagent demo into five provider failures on its second invocation -- and
    `wb demo` run twice is the first thing anyone does.
    """
    first = _run(pack, pack_analyst)
    second = _run(pack, pack_analyst)

    assert [o.state for o in second.outcomes] == [o.state for o in first.outcomes]
    assert [o.seq for o in second.outcomes] == [6, 7, 8, 9, 10]
    assert [o.specialist for o in second.outcomes] == [o.specialist for o in first.outcomes]
    assert [o.findings_recorded for o in second.outcomes] == [
        o.findings_recorded for o in first.outcomes
    ]
    runs = pack.store.subagent_runs(pack_analyst, ACME)
    assert sorted(run.state for run in runs) == ["failed"] * 2 + ["ok"] * 8


def test_a_dropped_question_leaves_the_survivor_answered(
    pack: Pack, pack_analyst: Principal
) -> None:
    """Position is counted over the questions that survived the screen, and so is `seq`.

    `record_questions` numbers only the kept questions, so the two agree here -- this test
    pins that agreement rather than distinguishing the two keys (the second-run test above is
    what does that), and would catch a screen that recorded a dropped question or a position
    counted over the unscreened plan.
    """
    source = recording_source(
        plan_payload={
            "questions": [
                {
                    "text": "a question about the other engagement",
                    "specialist": "process",
                    "doc_ids": ["doc-northwind-ar--ar-notes-md-deadbeef"],
                    "rationale": "because",
                },
                {
                    "text": "how is matching done?",
                    "specialist": "process",
                    "doc_ids": [CLERK],
                    "rationale": "because",
                },
            ],
            "strategy_note": "a note",
        },
        specialists={
            "1": answering_specialist(
                [CLERK],
                answer([finding(claim="matching is manual", doc_id=CLERK, quote=MATCHING)]),
            ),
        },
    )
    result = asyncio.run(pack.coordinator(source).discover(pack_analyst, ACME, budget=_budget()))
    assert len(result.dropped) == 1
    assert [o.state for o in result.outcomes] == ["ok"]
    assert result.outcomes[0].findings_recorded == 1


def test_every_question_and_run_is_recorded(pack: Pack, pack_analyst: Principal) -> None:
    result = _run(pack, pack_analyst)
    assert len(pack.store.questions(pack_analyst, ACME)) == 5
    runs = pack.store.subagent_runs(pack_analyst, ACME)
    assert len(runs) == 5
    assert sorted(run.state for run in runs) == ["failed", "ok", "ok", "ok", "ok"]
    assert len(pack.store.claims(pack_analyst, ACME)) == len(result.claims)


def test_the_plan_message_carries_the_index_and_never_a_document(
    pack: Pack, pack_analyst: Principal
) -> None:
    """The planner is given ids, paths and sizes -- never contents (spec, `discovery-plan`)."""
    library = SourceLibrary.for_engagement(pack.config, ACME)
    index = pack.store.index_sources(pack_analyst, ACME, library)
    coordinator = DiscoveryCoordinator(pack.store, pack.config, ReplaySource.from_file(FIXTURE))
    brief = pack.store.engagement(pack_analyst, ACME).brief
    message = coordinator._plan_message(brief, index)
    assert brief in message
    for ref in index:
        assert ref.doc_id in message
        assert ref.path in message
    # No document's text, checked against the real first line of a real transcript.
    first_line = library.read("transcripts/01-ap-clerk.md").text.splitlines()[2]
    assert first_line not in message


def test_the_plan_message_fits_both_caps(pack: Pack, pack_analyst: Principal) -> None:
    """`config.plan_input_cap` is 8,000 and so is app 17's own user-message cap: a message over
    either one is an `InputTooLarge` from the pinned tag, not a trimmed prompt."""
    library = SourceLibrary.for_engagement(pack.config, ACME)
    index = pack.store.index_sources(pack_analyst, ACME, library)
    coordinator = DiscoveryCoordinator(pack.store, pack.config, ReplaySource.from_file(FIXTURE))
    message = coordinator._plan_message("a brief", index)
    assert len(message) <= min(pack.config.plan_input_cap, MAX_USER_MESSAGE_CHARS)


def test_a_long_index_is_truncated_with_the_drop_stated(
    pack: Pack, pack_analyst: Principal
) -> None:
    from workbench.core.sources import SourceRef

    coordinator = DiscoveryCoordinator(pack.store, pack.config, ReplaySource.from_file(FIXTURE))
    index = tuple(
        SourceRef(
            doc_id=f"doc-acme-p2p--filler-{n:04d}",
            path=f"filler/{n:04d}.md",
            bytes=10,
            sha256="0" * 64,
            readable=True,
        )
        for n in range(400)
    )
    message = coordinator._plan_message("a brief", index)
    assert len(message) <= pack.config.plan_input_cap
    assert "INDEX TRUNCATED" in message


# ---- the plan screen -----------------------------------------------------------------------


def _plan(*questions: PlannedQuestion) -> Plan:
    return Plan(questions=list(questions), strategy_note="a note")


def _question(*doc_ids: str, text: str = "a question") -> PlannedQuestion:
    return PlannedQuestion(
        text=text, specialist=Specialist.PROCESS, doc_ids=list(doc_ids), rationale="because"
    )


def test_a_question_naming_an_unknown_document_is_dropped(
    pack: Pack, pack_analyst: Principal
) -> None:
    library = SourceLibrary.for_engagement(pack.config, ACME)
    index = pack.store.index_sources(pack_analyst, ACME, library)
    coordinator = DiscoveryCoordinator(pack.store, pack.config, ReplaySource.from_file(FIXTURE))
    kept, dropped = coordinator._screen(
        _plan(_question(CLERK), _question("doc-northwind-ar--ar-notes-md-deadbeef")), index
    )
    assert len(kept) == 1
    assert len(dropped) == 1
    assert "not in this engagement's source index" in dropped[0].reason


def test_a_dropped_question_takes_its_whole_document_list_with_it(
    pack: Pack, pack_analyst: Principal
) -> None:
    """Not just the offending id: a question built around another engagement's document is not a
    question about this engagement, and keeping the rest would change what was asked."""
    library = SourceLibrary.for_engagement(pack.config, ACME)
    index = pack.store.index_sources(pack_analyst, ACME, library)
    coordinator = DiscoveryCoordinator(pack.store, pack.config, ReplaySource.from_file(FIXTURE))
    kept, dropped = coordinator._screen(
        _plan(_question(CLERK, "doc-elsewhere--x-md-00000000")), index
    )
    assert kept == []
    assert len(dropped) == 1


def test_a_drop_reason_names_no_document_id(pack: Pack, pack_analyst: Principal) -> None:
    """An id the model invented is model output; a reason built from it would carry it onward."""
    library = SourceLibrary.for_engagement(pack.config, ACME)
    index = pack.store.index_sources(pack_analyst, ACME, library)
    coordinator = DiscoveryCoordinator(pack.store, pack.config, ReplaySource.from_file(FIXTURE))
    marker = "doc-zzmarkerzz--leaked-00000000"
    _, dropped = coordinator._screen(_plan(_question(marker)), index)
    assert marker not in dropped[0].reason


def test_a_plan_with_no_surviving_question_is_a_stated_refusal(
    pack: Pack, pack_analyst: Principal
) -> None:
    """End to end, not by calling `_screen`: a recorded plan whose only question names another
    engagement's document must reach `PlanRefused` rather than an empty run reported as a
    success. The planner is retried once first, which is why the recording holds two replies."""
    plan = _plan(_question("doc-northwind-ar--ar-notes-md-deadbeef")).model_dump(mode="json")
    source = recording_source(plan_payload=plan, plan_replies=2)
    with pytest.raises(PlanRefused):
        asyncio.run(pack.coordinator(source).discover(pack_analyst, ACME, budget=_budget()))
    assert pack.store.questions(pack_analyst, ACME) == ()
    assert pack.store.subagent_runs(pack_analyst, ACME) == ()


def test_a_planner_that_never_submits_is_replanned_once_then_refused(
    pack: Pack, pack_analyst: Principal
) -> None:
    source = recording_source(plan_payload=None, plan_replies=2)
    with pytest.raises(PlanRefused):
        asyncio.run(pack.coordinator(source).discover(pack_analyst, ACME, budget=_budget()))


def test_the_schema_refuses_more_than_six_questions() -> None:
    """More than six is a rejected plan, in the schema, before any code sees it."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _plan(*[_question(CLERK, text=f"q{n}") for n in range(MAX_QUESTIONS + 1)])


def test_the_schema_refuses_a_specialist_outside_the_closed_set() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PlannedQuestion.model_validate(
            {"text": "q", "specialist": "vibes", "doc_ids": [CLERK], "rationale": "r"}
        )


def test_the_schema_refuses_a_question_naming_no_document() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _question()


def test_the_schema_refuses_an_unknown_field() -> None:
    """`extra='forbid'`: a field nobody decided about is a rejected answer, not an ignored one."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Answer.model_validate({"findings": [], "insufficient_evidence": False, "mood": "upbeat"})


# ---- scoped context ------------------------------------------------------------------------


def test_a_subagent_cannot_read_a_document_its_question_did_not_name(pack: Pack) -> None:
    """The access boundary, enforced per subagent in code and not by a prompt instruction."""
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(library, {CLERK: "transcripts/01-ap-clerk.md"}, char_budget=20_000)
    refused = asyncio.run(reader.invoke({"doc_id": RECEIVING}, _ctx()))
    assert refused.is_error is True
    assert refused.error_category is not None
    assert refused.error_category.value == "permission"
    assert refused.is_retryable is False
    assert RECEIVING not in refused.content


def test_a_subagent_reads_a_document_its_question_names(pack: Pack) -> None:
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(library, {CLERK: "transcripts/01-ap-clerk.md"}, char_budget=20_000)
    served = asyncio.run(reader.invoke({"doc_id": CLERK}, _ctx()))
    assert served.is_error is False
    assert "Rowan Hale" in served.content


def test_the_reading_budget_is_shared_across_the_question_s_documents(pack: Pack) -> None:
    """A flat allowance let the first document take all of it, and the second was reported
    entirely unread -- a question answered from one of its two documents."""
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(
        library,
        {CLERK: "transcripts/01-ap-clerk.md", POLICY: "memos/ap-operating-policy.md"},
        char_budget=20_000,
    )
    asyncio.run(reader.invoke({"doc_id": CLERK}, _ctx()))
    second = asyncio.run(reader.invoke({"doc_id": POLICY}, _ctx()))
    assert second.is_error is False
    assert POLICY not in reader.unread_reasons
    assert reader.documents_served[POLICY] > 0


def test_a_single_document_question_gets_the_whole_allowance(pack: Pack) -> None:
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(library, {CLERK: "transcripts/01-ap-clerk.md"}, char_budget=20_000)
    asyncio.run(reader.invoke({"doc_id": CLERK}, _ctx()))
    assert reader.documents_served[CLERK] == 20_000


def test_a_trim_is_always_stated(pack: Pack) -> None:
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(library, {CLERK: "transcripts/01-ap-clerk.md"}, char_budget=500)
    served = asyncio.run(reader.invoke({"doc_id": CLERK}, _ctx()))
    assert "NOT COMPLETE" in served.content
    assert CLERK in reader.unread_reasons


def test_re_reading_spends_no_budget(pack: Pack) -> None:
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(library, {POLICY: "memos/ap-operating-policy.md"}, char_budget=20_000)
    asyncio.run(reader.invoke({"doc_id": POLICY}, _ctx()))
    spent = reader.chars_served
    asyncio.run(reader.invoke({"doc_id": POLICY}, _ctx()))
    assert reader.chars_served == spent


def test_the_subagent_message_carries_no_brief_and_no_sibling(
    pack: Pack, pack_analyst: Principal
) -> None:
    """One-way context passing, asserted on the only thing a subagent is ever told."""
    from workbench.coordinator.coordinator import _specialist_message

    result = _run(pack, pack_analyst)
    brief = pack.store.engagement(pack_analyst, ACME).brief
    messages = [_specialist_message(question) for question in result.questions]
    for message, question in zip(messages, result.questions, strict=True):
        assert question.text in message
        assert brief not in message
        for other in result.questions:
            if other.id != question.id:
                assert other.text not in message
        assert len(message) <= MAX_USER_MESSAGE_CHARS


def test_each_subagent_gets_its_own_child_budget(pack: Pack, pack_analyst: Principal) -> None:
    """Every turn and token a subagent spends is also recorded against the run's budget, so the
    run as a whole stops at the parent's limits (app 17 slice 17.4)."""
    budget = _budget()
    source = ReplaySource.from_file(FIXTURE)
    result = asyncio.run(pack.coordinator(source).discover(pack_analyst, ACME, budget=budget))
    assert budget.turns_used > 0
    assert budget.tokens_used > 0
    # The parent saw everything the children spent.
    assert budget.tokens_used >= result.tokens_used


# ---- cancellation --------------------------------------------------------------------------


class _HangingProvider(ModelProvider):
    """A subagent provider that never answers. It signals that it was reached, then waits."""

    def __init__(self, started: asyncio.Event) -> None:
        self._started = started

    async def converse(self, request: ModelRequest) -> ModelResponse:
        self._started.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


class _HangingSource:
    """The committed plan, then subagents that hang. A `ProviderSource`, structurally."""

    def __init__(self, plan: ReplaySource, started: asyncio.Event) -> None:
        self._plan = plan
        self._started = started

    def plan_provider(self) -> ModelProvider:
        return self._plan.plan_provider()

    def specialist_provider(self, position: int) -> ModelProvider:
        return _HangingProvider(self._started)


def test_a_cancelled_run_still_records_every_subagent(pack: Pack, pack_analyst: Principal) -> None:
    """Cancelling the run leaves no persisted question without a `subagent_run` row.

    `asyncio.gather(..., return_exceptions=True)` re-raises `CancelledError` when the gather
    itself is cancelled, however carefully each child catches its own. Without the handler the
    recording loop is skipped entirely and five questions sit in the database with no runs --
    a readout built from those rows would count five answered questions and name no gap, which
    is exactly the silent disappearance 5.3 forbids.
    """
    started = asyncio.Event()
    source = _HangingSource(ReplaySource.from_file(FIXTURE), started)

    async def main() -> None:
        task = asyncio.create_task(
            pack.coordinator(source).discover(pack_analyst, ACME, budget=_budget())
        )
        await asyncio.wait_for(started.wait(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(main())

    questions = pack.store.questions(pack_analyst, ACME)
    runs = pack.store.subagent_runs(pack_analyst, ACME)
    assert len(questions) == 5
    assert len(runs) == len(questions)
    assert {run.state for run in runs} == {"failed"}
    assert {run.error_category for run in runs} == {"transient"}
    assert all(run.is_retryable for run in runs)
    assert set(pack.store.failed_run_question_ids(pack_analyst, ACME)) == {
        question.id for question in questions
    }
