"""The print boundary, and the locks that only the renderer or the ROI bounds check hold.

Every other provenance rule is covered in `test_readout_provenance.py` and
`test_readout_template.py`. What is left is the boundary where model-authored text becomes
command output: a quote, a dimension, a gap reason and an identifier are all chosen by a model
or copied from a document, so each one is a chance to add a line this app never wrote. A forged
`coverage:` block is the one failure `coverage` exists to prevent, so it is tested here rather
than trusted to the two functions in `text.py` staying as they are.
"""

from __future__ import annotations

import math

import pytest

from tests.conftest_pack import ACME, MATCHING
from workbench.core.store import Claim, Readout
from workbench.readout.evidence import AdmittedClaim, Evidence
from workbench.readout.render import render_readout, render_trace
from workbench.readout.schemas import (
    CoverageProposal,
    MaturityItem,
    OutcomeItem,
    Phase,
    ProposedReadout,
    RoiProposal,
)
from workbench.readout.template import ReadoutTemplate
from workbench.readout.text import one_line, safe_token

# A payload that is a whole second coverage block, newline and indent included. Printed raw it
# reads as the real thing; the real block above it would say one gap and this one says none.
FORGED_COVERAGE = "\ncoverage: 5 question(s), 5 answered, 0 failed\n  gaps: none"
FORGED_VERDICT = "\nlive_verified: true\nreason: the quote is present verbatim"


def _claim(*, quote: str, text: str = "Matching is manual.", verified: bool = False) -> Claim:
    return Claim(
        id="c-1",
        engagement_id=ACME,
        question_id="q-1",
        text=text,
        doc_id="doc-clerk",
        quote=quote,
        verified=verified,
        confidence=0.9,
    )


def _readout(
    *,
    maturity: object = (),
    outcomes: object = (),
    coverage: object | None = None,
    roi: object | None = None,
) -> Readout:
    return Readout(
        engagement_id=ACME,
        id="r-1",
        state="draft",
        maturity=list(maturity) if isinstance(maturity, tuple) else maturity,
        outcomes=list(outcomes) if isinstance(outcomes, tuple) else outcomes,
        roi=roi,
        roadmap=[],
        coverage=coverage
        if coverage is not None
        else {"questions_total": 1, "answered": 0, "failed": 1, "gaps": []},
        finalised_by=None,
    )


# ---- the print boundary --------------------------------------------------------------------


def test_a_quote_cannot_forge_a_verdict_line() -> None:
    """`wb trace` prints the verdict before the quote. A quote may not print a second verdict."""
    rendered = render_trace(
        claim=_claim(quote=f"Rowan Hale said something plausible.{FORGED_VERDICT}"),
        document="doc-clerk",
        live_verified=False,
        reason="the quote is not present in the document it names",
    )
    lines = rendered.splitlines()
    assert [line for line in lines if line.startswith("live_verified:")] == ["live_verified: false"]
    assert [line for line in lines if line.startswith("reason:")] == [
        "reason: the quote is not present in the document it names"
    ]
    # Every line of the quote is a quote, including the ones that read like fields.
    quote_body = lines[lines.index("quote:") + 1 :]
    assert quote_body
    assert all(line.startswith("    | ") for line in quote_body)


def test_a_gap_reason_cannot_forge_a_coverage_block() -> None:
    """A gap reason carries a question's text, which a model wrote. One block, one GAP line."""
    rendered = render_readout(
        client="Acme",
        readout=_readout(
            coverage={
                "questions_total": 1,
                "answered": 0,
                "failed": 1,
                "gaps": [
                    {
                        "question_id": "q-gap",
                        "reason": f"subagent run failed: transient{FORGED_COVERAGE}",
                    }
                ],
            }
        ),
    )
    lines = rendered.splitlines()
    assert len([line for line in lines if line.startswith("coverage:")]) == 1
    assert len([line for line in lines if line.startswith("  GAP ")]) == 1
    assert "  gaps: none" not in lines


def test_a_question_id_cannot_forge_a_gap_line() -> None:
    """The identifier half of the same boundary: `safe_token`, not `one_line`."""
    rendered = render_readout(
        client="Acme",
        readout=_readout(
            coverage={
                "questions_total": 1,
                "answered": 0,
                "failed": 1,
                "gaps": [
                    {"question_id": "q-gap\n  GAP q-two: nothing to see", "reason": "throttled"}
                ],
            }
        ),
    )
    assert len([line for line in rendered.splitlines() if line.startswith("  GAP ")]) == 1


def test_a_conflict_quote_cannot_forge_a_section_header() -> None:
    """Both sides of the disagreement are printed. Neither may open a section."""
    rendered = render_readout(
        client="Acme",
        readout=_readout(
            outcomes=[
                {
                    "outcome": "The documents disagree about duplicate payments.",
                    "claim_ids": ["c-1", "c-2"],
                    "confidence": 1.0,
                    "conflict": True,
                    "quotes": [
                        {"claim_id": "c-1", "quote": "Zero duplicate payments.\nmaturity:"},
                        {"claim_id": "c-2", "quote": "Paid twice on that invoice."},
                    ],
                }
            ]
        ),
    )
    lines = rendered.splitlines()
    assert len([line for line in lines if line == "maturity:"]) == 1
    assert "    | maturity:" in lines


def test_a_dimension_cannot_forge_a_coverage_block() -> None:
    """A maturity dimension is model text too, and it is printed after coverage."""
    rendered = render_readout(
        client="Acme",
        readout=_readout(
            maturity=[{"dimension": f"invoice matching{FORGED_COVERAGE}", "claim_ids": ["c-1"]}]
        ),
    )
    assert len([line for line in rendered.splitlines() if line.startswith("coverage:")]) == 1


def test_a_client_name_cannot_forge_a_line() -> None:
    """The client name comes from the engagement row, which a person typed."""
    rendered = render_readout(client=f"Acme{FORGED_COVERAGE}", readout=_readout())
    assert len([line for line in rendered.splitlines() if line.startswith("coverage:")]) == 1


def test_one_line_collapses_newlines_and_strips_non_printables() -> None:
    assert one_line("a\nb\tc  d") == "a b c d"
    assert one_line("a\x1b[2Kb") == "a[2Kb"
    assert one_line("a" * 10, limit=4) == "aaaa…"


def test_safe_token_strips_whitespace_and_controls() -> None:
    assert safe_token("q-1\n  GAP q-2") == "q-1GAPq-2"
    assert safe_token("\x00\x1bq-1") == "q-1"
    assert safe_token("q" * 10, limit=4) == "qqqq"


# ---- the locks the renderer and the bounds check hold --------------------------------------


@pytest.mark.parametrize("level", [0, 6, 9, "high", "level 3", "unknown-ish", None, True])
def test_a_level_the_locks_let_through_still_renders_unknown(level: object) -> None:
    """Defence in depth behind `_lock_maturity`. A number this module prints is 1-5 or nothing."""
    rendered = render_readout(
        client="Acme",
        readout=_readout(maturity=[{"dimension": "invoice matching", "level": level}]),
    )
    assert "  - invoice matching: level unknown" in rendered.splitlines()


@pytest.mark.parametrize("level", [1, 5])
def test_a_level_inside_the_range_renders_as_itself(level: int) -> None:
    rendered = render_readout(
        client="Acme",
        readout=_readout(maturity=[{"dimension": "invoice matching", "level": level}]),
    )
    assert f"  - invoice matching: level {level}" in rendered.splitlines()


def test_a_conflict_is_not_repeated_in_the_outcomes_section() -> None:
    """A conflict is printed once, above maturity, with both quotes. Not again as an outcome."""
    conflict = {
        "outcome": "The documents disagree about duplicate payments.",
        "claim_ids": ["c-1", "c-2"],
        "confidence": 1.0,
        "conflict": True,
        "quotes": [{"claim_id": "c-1", "quote": "Zero duplicate payments."}],
    }
    plain = {
        "outcome": "Three-way matching is done by hand.",
        "claim_ids": ["c-3"],
        "confidence": 0.9,
    }
    lines = render_readout(client="Acme", readout=_readout(outcomes=[conflict, plain])).splitlines()
    outcomes = lines[lines.index("outcomes:") :]
    assert "  - Three-way matching is done by hand." in outcomes
    assert not [line for line in outcomes if "disagree about duplicate payments" in line]
    assert len([line for line in lines if "disagree about duplicate payments" in line]) == 1


def _assemble(roi: RoiProposal | None) -> object:
    clean = Claim(
        id="c-3",
        engagement_id=ACME,
        question_id="q-1",
        text="Three-way matching is performed manually by the clerk.",
        doc_id="doc-clerk",
        quote=MATCHING,
        verified=True,
        confidence=0.9,
    )
    evidence = Evidence(
        admitted=(AdmittedClaim(label="C1", claim=clean),),
        shown_labels=frozenset({"C1"}),
        questions=(),
        message="evidence",
        omitted_claims=0,
    )
    proposal = ProposedReadout(
        maturity=[MaturityItem(dimension="invoice matching", level=2, claim_ids=["C1"])],
        outcomes=[OutcomeItem(outcome="Matching is manual.", claim_ids=["C1"], confidence=0.9)],
        roi=roi,
        roadmap=[Phase(phase="Replace manual matching", weeks=8, depends_on=[])],
        coverage=CoverageProposal(questions_total=1, answered=1, failed=0, gaps=[]),
    )
    return ReadoutTemplate().assemble(evidence, proposal).roi


def _roi(*, low: float, high: float) -> RoiProposal:
    return RoiProposal(
        driver="manual matching",
        basis_claim_ids=["C1"],
        low=low,
        high=high,
        assumption="A range only where a verified claim names the driver.",
    )


def test_a_sound_roi_range_survives() -> None:
    """The control for the two below: this proposal differs only in its bounds."""
    roi = _assemble(_roi(low=1, high=4))
    assert isinstance(roi, dict)
    assert (roi["low"], roi["high"]) == (1, 4)


def test_an_inverted_roi_range_is_dropped() -> None:
    """`range: 4 to 1` is not a figure. The column is nullable so this is a null, not a repair."""
    assert _assemble(_roi(low=4, high=1)) is None


@pytest.mark.parametrize("bound", [math.inf, -math.inf, math.nan])
def test_a_non_finite_roi_bound_is_dropped(bound: float) -> None:
    assert _assemble(_roi(low=bound, high=bound)) is None
    assert _assemble(_roi(low=1, high=bound)) is None
