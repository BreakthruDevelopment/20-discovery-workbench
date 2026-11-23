"""The readout skeleton, and the provenance rules it applies in code.

A subclass may replace a section step. It may not replace the order of those steps, or the locks
that decide which levels, outcomes and figures survive. The model's coverage is discarded. A
contradiction is kept as both quotes.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from agent_container.core.loop import MAX_USER_MESSAGE_CHARS
from agent_container.core.tool import Effect

from tests.conftest_pack import (
    ACME,
    CYCLE,
    FABRICATED,
    INJECTION,
    MATCHING,
    NO_DUPES,
)
from tests.conftest_pack import (
    FIXTURE as DISCOVERY_FIXTURE,
)
from workbench.coordinator.prompts import DATA_NOT_INSTRUCTIONS
from workbench.core.config import SYNTHESIS_INPUT_CAP
from workbench.core.store import Claim
from workbench.readout.agent import SubmitReadoutTool, SynthesisAgent
from workbench.readout.conflicts import find_conflicts
from workbench.readout.evidence import AdmittedClaim, Evidence, QuestionView, build_message
from workbench.readout.prompts import SYNTHESIS_SYSTEM
from workbench.readout.schemas import (
    CoverageProposal,
    MaturityItem,
    OutcomeItem,
    Phase,
    ProposedReadout,
    RoiProposal,
)
from workbench.readout.synthesis import FIXTURE, replay_provider
from workbench.readout.template import AssembledReadout, ReadoutTemplate, _SkeletonMeta

_LEFT = "id-dupes"
_RIGHT = "id-ticket"
_CLEAN = "id-match"


def _claim(
    claim_id: str,
    doc_id: str,
    text: str,
    quote: str,
    *,
    verified: bool = True,
) -> Claim:
    return Claim(
        id=claim_id,
        engagement_id=ACME,
        question_id="q-1",
        text=text,
        doc_id=doc_id,
        quote=quote,
        verified=verified,
        confidence=0.9,
    )


def _pair() -> tuple[Claim, Claim, Claim]:
    """The planted disagreement, plus one claim that does not take a side."""
    left = _claim(
        _LEFT,
        "doc-procurement",
        "The procurement lead asserts there have been no duplicate payments lately.",
        "We have had zero duplicate payments in the period under review here.",
    )
    right = _claim(
        _RIGHT,
        "doc-ticket",
        "The ticket extract records a duplicate payment to a supplier.",
        "Duplicate payment to Lowlamp Paper was paid twice on that invoice.",
    )
    clean = _claim(
        _CLEAN,
        "doc-clerk",
        "Three-way matching is performed manually by the clerk.",
        MATCHING,
    )
    return left, right, clean


def _evidence(
    claims: tuple[Claim, ...] | list[Claim],
    *,
    shown: frozenset[str] | None = None,
    questions: tuple[QuestionView, ...] = (),
) -> Evidence:
    admitted = tuple(
        AdmittedClaim(label=f"C{index}", claim=claim) for index, claim in enumerate(claims, start=1)
    )
    labels = frozenset(item.label for item in admitted) if shown is None else shown
    return Evidence(
        admitted=admitted,
        shown_labels=labels,
        questions=questions,
        message="evidence",
        omitted_claims=0,
    )


def _coverage(*, answered: int = 5, failed: int = 0) -> CoverageProposal:
    return CoverageProposal(questions_total=5, answered=answered, failed=failed, gaps=[])


def _proposal_for(left: Claim, right: Claim, clean: Claim) -> ProposedReadout:
    del left, right, clean
    return ProposedReadout(
        maturity=[
            MaturityItem(dimension="invoice matching", level=2, claim_ids=["C3"]),
            MaturityItem(dimension="exception handling", level=5, claim_ids=[]),
            MaturityItem(dimension="duplicate payments", level="high", claim_ids=["C1"]),
            MaturityItem(dimension="one side only", level=4, claim_ids=["C1"]),
        ],
        outcomes=[
            OutcomeItem(
                outcome="Three-way matching is done by hand.",
                claim_ids=["C3"],
                confidence=0.95,
            ),
            OutcomeItem(
                outcome="Duplicate payments have effectively stopped.",
                claim_ids=["C1"],
                confidence=0.4,
            ),
            OutcomeItem(
                outcome="On balance, duplicate payments are rare.",
                claim_ids=["C1", "C2"],
                confidence=0.5,
            ),
            OutcomeItem(
                outcome="Maturity is uniformly high.",
                claim_ids=[],
                confidence=0.2,
            ),
        ],
        roi=RoiProposal(
            driver="the duplicate-payment assertion",
            basis_claim_ids=["C1"],
            low=1,
            high=4,
            assumption="This figure rests on a claim the other document contradicts.",
        ),
        roadmap=[Phase(phase="Replace manual matching", weeks=8, depends_on=[])],
        coverage=_coverage(),
    )


def _questions() -> tuple[QuestionView, ...]:
    return (
        QuestionView(question_id="q-ok", seq=1, text="How is matching done?", state="ok"),
        QuestionView(
            question_id="q-gap",
            seq=2,
            text="What happens to an invoice that fails the match?",
            state="failed",
            error_category="transient",
            is_retryable=True,
        ),
        QuestionView(question_id="q-missing", seq=3, text="Who owns the queue?", state=None),
    )


# ---- the skeleton --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method",
    [
        "assemble",
        "_lock_maturity",
        "_lock_outcomes",
        "_lock_roi",
        "_lock_roadmap",
        "_lock_coverage",
        "_attach_conflicts",
    ],
)
def test_a_subclass_cannot_replace_the_skeleton(method: str) -> None:
    """The refusal is at definition. A readout that reorders the sections is never constructed."""
    with pytest.raises(TypeError, match="skeleton"):
        _SkeletonMeta("Broken", (ReadoutTemplate,), {method: lambda *_args, **_kwargs: None})


def test_every_skeleton_method_is_in_the_locked_set() -> None:
    """`_LOCKED` is hand-maintained, so a new `_lock_*` step would be silently overridable.

    The parametrized test above only proves the seven names currently listed are refused. This
    one closes the gap the other way round: the skeleton's own entry point plus every `_lock_*`
    and `_attach_*` method defined on `ReadoutTemplate` must appear in `_LOCKED`.
    """
    # No `callable()` filter: in 3.12 `callable(classmethod(f))` and `callable(property(f))` are
    # both False, so a descriptor-shaped lock left out of `_LOCKED` would be invisible to it. The
    # whole MRO, not just `vars(ReadoutTemplate)`, so a lock added on a future base is seen too.
    defined = {
        name
        for klass in ReadoutTemplate.__mro__
        if klass is not object
        for name in vars(klass)
        if name.startswith(("_lock_", "_attach_"))
    }
    defined.add("assemble")
    assert defined <= _SkeletonMeta._LOCKED, sorted(defined - _SkeletonMeta._LOCKED)
    # And nothing is listed that does not exist, which would read as cover it does not give.
    assert defined >= _SkeletonMeta._LOCKED, sorted(_SkeletonMeta._LOCKED - defined)


def test_the_steps_run_in_skeleton_order() -> None:
    seen: list[str] = []

    class _Recording(ReadoutTemplate):
        def maturity(
            self, evidence: Evidence, proposal: ProposedReadout
        ) -> tuple[MaturityItem, ...]:
            seen.append("maturity")
            return super().maturity(evidence, proposal)

        def outcomes(
            self, evidence: Evidence, proposal: ProposedReadout
        ) -> tuple[OutcomeItem, ...]:
            seen.append("outcomes")
            return super().outcomes(evidence, proposal)

        def roi_model(self, evidence: Evidence, proposal: ProposedReadout) -> RoiProposal | None:
            seen.append("roi_model")
            return super().roi_model(evidence, proposal)

        def roadmap(self, evidence: Evidence, proposal: ProposedReadout) -> tuple[Phase, ...]:
            seen.append("roadmap")
            return super().roadmap(evidence, proposal)

        def coverage(self, evidence: Evidence, proposal: ProposedReadout) -> dict[str, object]:
            seen.append("coverage")
            return super().coverage(evidence, proposal)

    left, right, clean = _pair()
    _Recording().assemble(_evidence((left, right, clean)), _proposal_for(left, right, clean))
    assert seen == ["maturity", "outcomes", "roi_model", "roadmap", "coverage"]


def test_returning_none_from_the_roi_model_is_the_cut() -> None:
    """Dropping the ROI model is one function. The column stays null. Nothing else is dropped."""

    class _Cut(ReadoutTemplate):
        def roi_model(self, evidence: Evidence, proposal: ProposedReadout) -> RoiProposal | None:
            del evidence, proposal
            return None

    clean = _claim(_CLEAN, "doc-clerk", "Matching is manual.", MATCHING)
    evidence = _evidence((clean,))
    proposal = ProposedReadout(
        maturity=[MaturityItem(dimension="invoice matching", level=2, claim_ids=["C1"])],
        outcomes=[
            OutcomeItem(
                outcome="Three-way matching is done by hand.",
                claim_ids=["C1"],
                confidence=0.9,
            )
        ],
        roi=RoiProposal(
            driver="manual matching",
            basis_claim_ids=["C1"],
            low=1,
            high=3,
            assumption="A range only where a verified claim names the driver.",
        ),
        roadmap=[Phase(phase="Replace manual matching", weeks=8, depends_on=[])],
        coverage=_coverage(),
    )
    cut = _Cut().assemble(evidence, proposal)
    kept = ReadoutTemplate().assemble(evidence, proposal)
    assert cut.roi is None
    assert cut.maturity == kept.maturity
    assert cut.outcomes == kept.outcomes
    assert cut.roadmap == kept.roadmap
    assert isinstance(kept.roi, dict)
    assert kept.roi["basis_claim_ids"] == [_CLEAN]
    assert kept.roi["low"] == 1.0
    assert kept.roi["high"] == 3.0


def test_a_lying_coverage_step_is_discarded() -> None:
    """Whatever the step returns, coverage is the recorded runs."""

    class _Liar(ReadoutTemplate):
        def coverage(self, evidence: Evidence, proposal: ProposedReadout) -> dict[str, object]:
            del evidence, proposal
            return {"questions_total": 99, "answered": 99, "failed": 0, "gaps": []}

    evidence = _evidence((), questions=_questions())
    proposal = ProposedReadout(coverage=_coverage(answered=5, failed=0))
    coverage = _Liar().assemble(evidence, proposal).coverage
    assert coverage["questions_total"] == 3
    assert coverage["answered"] == 1
    assert coverage["failed"] == 1
    gaps = coverage["gaps"]
    assert isinstance(gaps, list)
    assert [gap["question_id"] for gap in gaps] == ["q-gap", "q-missing"]
    assert "fails the match" in gaps[0]["reason"]
    assert gaps[1]["reason"].startswith("no subagent run was recorded")


# ---- provenance locks -----------------------------------------------------------------------


def test_levels_without_a_verified_claim_are_unknown_and_prose_never_stands_in() -> None:
    left, right, clean = _pair()
    assembled = ReadoutTemplate().assemble(
        _evidence((left, right, clean)), _proposal_for(left, right, clean)
    )
    by_dimension = {str(item["dimension"]): item for item in assembled.maturity}
    assert by_dimension["invoice matching"]["level"] == 2
    assert by_dimension["invoice matching"]["claim_ids"] == [_CLEAN]
    assert by_dimension["exception handling"]["level"] == "unknown"
    assert by_dimension["exception handling"]["claim_ids"] == []
    # "high" parsed as unknown, and it stays unknown even though a claim was named.
    assert by_dimension["duplicate payments"]["level"] == "unknown"
    assert "high" not in json.dumps(assembled.maturity)
    # One side of the disagreement is not a basis for a level.
    assert by_dimension["one side only"]["level"] == "unknown"
    assert by_dimension["one side only"]["claim_ids"] == []


def test_an_outcome_or_roi_without_a_basis_is_dropped() -> None:
    clean = _claim(_CLEAN, "doc-clerk", "Matching is manual.", MATCHING)
    proposal = ProposedReadout(
        outcomes=[OutcomeItem(outcome="Maturity is uniformly high.", claim_ids=[], confidence=0.2)],
        roi=RoiProposal(
            driver="unspecified savings",
            basis_claim_ids=[],
            low=1,
            high=2,
            assumption="No claim was named, so this is not a figure.",
        ),
        coverage=_coverage(),
    )
    assembled = ReadoutTemplate().assemble(_evidence((clean,)), proposal)
    assert assembled.outcomes == ()
    assert assembled.roi is None


def test_a_contradiction_keeps_both_quotes_and_drops_the_average() -> None:
    left, right, clean = _pair()
    evidence = _evidence((left, right, clean))
    assembled = ReadoutTemplate().assemble(evidence, _proposal_for(left, right, clean))
    texts = [str(item["outcome"]) for item in assembled.outcomes]
    assert "Duplicate payments have effectively stopped." not in texts
    assert "On balance, duplicate payments are rare." not in texts
    assert "Maturity is uniformly high." not in texts
    assert "Three-way matching is done by hand." in texts
    conflicts = [item for item in assembled.outcomes if item.get("conflict") is True]
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict["claim_ids"] == [_LEFT, _RIGHT]
    quotes = conflict["quotes"]
    assert isinstance(quotes, list)
    assert quotes == [
        {"claim_id": _LEFT, "quote": left.quote},
        {"claim_id": _RIGHT, "quote": right.quote},
    ]
    assert assembled.roi is None


def test_a_claim_the_cap_omitted_cannot_be_cited_and_the_conflict_is_still_kept() -> None:
    """The model may cite only labels the message listed. The code still holds both quotes."""
    left, right, clean = _pair()
    evidence = _evidence((left, right, clean), shown=frozenset({"C3"}))
    assert evidence.resolve("C3") == _CLEAN
    assert evidence.resolve(_CLEAN) == _CLEAN
    assert evidence.resolve("C1") is None
    assert evidence.resolve(_LEFT) is None
    assembled = ReadoutTemplate().assemble(evidence, _proposal_for(left, right, clean))
    conflicts = [item for item in assembled.outcomes if item.get("conflict") is True]
    assert len(conflicts) == 1
    assert conflicts[0]["quotes"] == [
        {"claim_id": _LEFT, "quote": left.quote},
        {"claim_id": _RIGHT, "quote": right.quote},
    ]
    kept = [str(item["outcome"]) for item in assembled.outcomes if item.get("conflict") is not True]
    assert kept == ["Three-way matching is done by hand."]


def test_an_roi_grounded_on_a_contradicted_claim_is_dropped() -> None:
    left, right, clean = _pair()
    proposal = ProposedReadout(
        roi=RoiProposal(
            driver="manual matching and the contradicted assertion",
            basis_claim_ids=["C3", "C1"],
            low=1,
            high=3,
            assumption="One of these claims is the disagreement, so the figure goes.",
        ),
        coverage=_coverage(),
    )
    assembled = ReadoutTemplate().assemble(_evidence((left, right, clean)), proposal)
    assert assembled.roi is None


# ---- the planted pack, without a store -------------------------------------------------------


def _recorded_findings() -> list[tuple[str, str, str]]:
    payload: Any = json.loads(DISCOVERY_FIXTURE.read_text(encoding="utf-8"))
    findings: list[tuple[str, str, str]] = []
    for entry in payload["specialists"].values():
        if entry.get("error"):
            continue
        for reply in entry["replies"]:
            for use in reply["tool_uses"]:
                if use["name"] != "submit_answer":
                    continue
                for finding in use["input"]["findings"]:
                    findings.append(
                        (str(finding["claim"]), str(finding["doc_id"]), str(finding["quote"]))
                    )
    return findings


def test_the_planted_contradiction_is_the_only_conflict() -> None:
    """Harbour's 'no supplier' is a negation, and so is the laptop line. Neither is this pair.

    The pair is the procurement assertion and the ticket, different documents, one of them
    negated, sharing a content bigram that is not just 'last twelve months'.
    """
    claims = [
        _claim(
            f"id-{index:04d}",
            doc_id,
            text,
            quote,
            verified=quote != FABRICATED,
        )
        for index, (text, doc_id, quote) in enumerate(_recorded_findings(), start=1)
    ]
    pairs = find_conflicts(claims)
    assert len(pairs) == 1
    quotes = {pairs[0][0].quote, pairs[0][1].quote}
    assert NO_DUPES in quotes
    assert any("HLP-4901" in quote for quote in quotes)
    assert INJECTION not in quotes
    assert CYCLE not in quotes
    assert MATCHING not in quotes


def test_an_unverified_claim_is_not_a_side_of_a_conflict() -> None:
    left, right, _clean = _pair()
    hidden = Claim(
        id="id-hidden",
        engagement_id=ACME,
        question_id="q-1",
        text=left.text,
        doc_id="doc-other",
        quote=left.quote,
        verified=False,
        confidence=0.9,
    )
    assert find_conflicts((hidden, right)) == ()


# ---- the prompt and the cap -----------------------------------------------------------------


def test_the_system_prompt_carries_the_standing_line_and_the_claim_rule() -> None:
    assert DATA_NOT_INSTRUCTIONS in SYNTHESIS_SYSTEM
    assert "name a claim id" in SYNTHESIS_SYSTEM
    assert "Name what is missing rather than filling it in." in SYNTHESIS_SYSTEM
    submit = SubmitReadoutTool()
    agent = SynthesisAgent(replay_provider(), submit)
    assert list(agent._tools) == ["submit_readout"]
    assert submit.effect is Effect.READ


def test_prose_and_booleans_do_not_become_levels() -> None:
    assert MaturityItem(dimension="cycle time", level="mature", claim_ids=["C1"]).level == "unknown"
    assert MaturityItem(dimension="cycle time", level=True, claim_ids=["C1"]).level == "unknown"
    assert MaturityItem(dimension="cycle time", level=9, claim_ids=["C1"]).level == "unknown"
    assert MaturityItem(dimension="cycle time", level="3", claim_ids=["C1"]).level == 3
    with pytest.raises(ValueError, match="confidence"):
        OutcomeItem(outcome="A finding.", claim_ids=["C1"], confidence=True)


def test_claims_past_the_cap_are_a_stated_prefix() -> None:
    """The synthesis cap and app 17's wall: the message uses the smaller one, and says so."""
    questions = (QuestionView(question_id="q1", seq=1, text="How is matching done?", state="ok"),)
    admitted = tuple(
        AdmittedClaim(
            label=f"C{index}",
            claim=_claim(f"id-{index}", f"doc-{index}", "alpha " * 200, "beta " * 200),
        )
        for index in range(1, 12)
    )
    cap = min(SYNTHESIS_INPUT_CAP, MAX_USER_MESSAGE_CHARS)
    message, shown, omitted = build_message(questions, admitted, cap=cap)
    assert cap == MAX_USER_MESSAGE_CHARS
    assert len(message) <= cap
    assert omitted > 0
    assert f"[CLAIMS TRUNCATED: {omitted} further verified claim(s)" in message
    labels = [f"C{index}" for index in range(1, 12)]
    assert [label for label in labels if label in shown] == labels[: len(shown)]
    assert labels[len(shown)] not in message


def test_a_header_that_does_not_fit_is_truncated_out_loud() -> None:
    message, shown, omitted = build_message(
        (QuestionView(question_id="q1", seq=1, text="x " * 100, state="failed"),),
        (
            AdmittedClaim(
                label="C1",
                claim=_claim("id-1", "doc-1", "a claim that must not appear", MATCHING),
            ),
        ),
        cap=80,
    )
    assert len(message) <= 80
    assert "TRUNCATED" in message
    assert shown == frozenset()
    assert omitted == 1
    assert "a claim that must not appear" not in message
    assert MATCHING not in message


def test_the_committed_readout_recording_lies_where_the_locks_have_to_notice() -> None:
    """The fixture is the case the code exists for: a level with no claim, a finished coverage, an
    average of the contradiction. If it stops lying, these tests stop proving the locks."""
    payload: Any = json.loads(FIXTURE.read_text(encoding="utf-8"))
    submitted = payload["replies"][0]["tool_uses"][0]["input"]
    exception = next(
        item for item in submitted["maturity"] if item["dimension"] == "exception handling"
    )
    assert exception["level"] == 5
    assert exception["claim_ids"] == []
    outcomes = [item["outcome"] for item in submitted["outcomes"]]
    assert "Duplicate payments have effectively stopped." in outcomes
    assert "On balance, duplicate payments are rare." in outcomes
    assert "Maturity is uniformly high." in outcomes
    assert submitted["coverage"] == {
        "questions_total": 5,
        "answered": 5,
        "failed": 0,
        "gaps": [],
    }
    repo = DISCOVERY_FIXTURE.parents[3]
    assert FIXTURE.relative_to(repo).parts[0] == "workbench"


def test_assemble_returns_the_locked_sections() -> None:
    """A smoke of the return type the store is handed: tuples, and a null ROI when dropped."""
    left, right, clean = _pair()
    assembled = ReadoutTemplate().assemble(
        _evidence((left, right, clean)), _proposal_for(left, right, clean)
    )
    assert isinstance(assembled, AssembledReadout)
    assert assembled.roi is None
    assert assembled.roadmap[0]["phase"] == "Replace manual matching"
