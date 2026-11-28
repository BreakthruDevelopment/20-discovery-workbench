"""The synthesis input is bounded in both its unbounded quantities, and says what it left out.

`question` is append-only across `wb discover` runs, so an engagement that has been discovered
repeatedly accumulates questions. Each question adds a run state to the message and a gap to the
recomputed coverage. Neither may grow without bound, and run states may not crowd claims out of
the message.
"""

from __future__ import annotations

from agent_container.core.loop import MAX_USER_MESSAGE_CHARS

from workbench.core.config import SYNTHESIS_INPUT_CAP
from workbench.core.store import Claim
from workbench.readout.evidence import (
    AdmittedClaim,
    Evidence,
    QuestionView,
    build_message,
    coverage_document,
)
from workbench.readout.render import _coverage_lines
from workbench.readout.schemas import MAX_GAPS
from workbench.readout.template import ReadoutTemplate

CAP = min(SYNTHESIS_INPUT_CAP, MAX_USER_MESSAGE_CHARS)


def _question(seq: int, state: str | None = "ok", *, claims: int = 1) -> QuestionView:
    return QuestionView(
        question_id=f"q{seq}",
        seq=seq,
        text=f"question {seq} " + "word " * 80,
        state=state,
        verified_claims=claims,
        error_category="throttled" if state == "failed" else None,
        is_retryable=state == "failed",
    )


def _admitted(count: int) -> tuple[AdmittedClaim, ...]:
    return tuple(
        AdmittedClaim(
            label=f"C{index}",
            claim=Claim(
                id=f"id-{index}",
                engagement_id="acme",
                question_id="q1",
                text=f"claim {index}",
                doc_id="doc",
                quote="a quote",
                verified=True,
                confidence=0.9,
            ),
        )
        for index in range(1, count + 1)
    )


def test_many_questions_do_not_crowd_the_claims_out_and_the_message_says_so() -> None:
    questions = tuple(_question(seq) for seq in range(1, 61))
    message, shown, omitted = build_message(questions, _admitted(5), cap=CAP)
    assert len(message) <= CAP
    # The claims are listed, not squeezed out by sixty run states.
    assert shown == frozenset({"C1", "C2", "C3", "C4", "C5"})
    assert omitted == 0
    assert "id=C1 " in message
    # The states that were left out are named, with a count, and not described as succeeded.
    left_out = 60 - message.count("- seq=")
    assert left_out > 0
    assert f"[RUN STATES TRUNCATED: {left_out} further question(s)" in message
    assert "not a statement that they succeeded" in message


def test_a_failed_run_is_kept_when_states_overflow_their_share() -> None:
    questions = [*(_question(seq) for seq in range(1, 61)), _question(61, "failed")]
    message, _shown, _omitted = build_message(questions, _admitted(2), cap=CAP)
    assert "seq=61 state=failed error=throttled retryable=true" in message
    assert "seq=60 state=ok" not in message


def test_states_that_fit_are_all_listed_with_no_truncation_line() -> None:
    questions = tuple(_question(seq) for seq in range(1, 6))
    message, _shown, _omitted = build_message(questions, _admitted(2), cap=CAP)
    assert message.count("- seq=") == 5
    assert "RUN STATES TRUNCATED" not in message


def test_the_recomputed_gap_list_is_capped_and_the_overflow_is_counted() -> None:
    questions = tuple(_question(seq, None, claims=0) for seq in range(1, 101))
    document = coverage_document(questions)
    gaps = document["gaps"]
    assert isinstance(gaps, list)
    assert len(gaps) == MAX_GAPS
    assert document["gaps_omitted"] == 100 - MAX_GAPS


def test_a_failed_run_outranks_the_other_kinds_when_the_gap_list_is_full() -> None:
    questions = [
        *(_question(seq, "ok", claims=0) for seq in range(1, 41)),
        _question(41, "failed", claims=0),
    ]
    document = coverage_document(questions)
    gaps = document["gaps"]
    assert isinstance(gaps, list)
    assert gaps[0]["question_id"] == "q41"
    assert document["gaps_omitted"] == 41 - MAX_GAPS


def test_the_lock_and_the_render_carry_the_overflow() -> None:
    questions = tuple(_question(seq, None, claims=0) for seq in range(1, 51))
    evidence = Evidence(
        admitted=(),
        shown_labels=frozenset(),
        questions=questions,
        message="evidence",
        omitted_claims=0,
    )
    locked = ReadoutTemplate()._lock_coverage({}, evidence)
    gaps = locked["gaps"]
    assert isinstance(gaps, list)
    assert len(gaps) == MAX_GAPS
    assert locked["gaps_omitted"] == 50 - MAX_GAPS
    lines = _coverage_lines(locked)
    assert f"  {50 - MAX_GAPS} further gap(s) not listed here" in lines
    assert sum(1 for line in lines if line.startswith("  GAP ")) == MAX_GAPS


def test_a_list_within_the_cap_says_nothing_was_left_out() -> None:
    document = coverage_document((_question(1, None, claims=0),))
    assert document["gaps_omitted"] == 0
    assert not any("further gap" in line for line in _coverage_lines(document))
