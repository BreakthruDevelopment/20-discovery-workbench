"""Quotes are checked again before synthesis, and a changed document is caught there.

The store's `verified` flag is what `record_claims` wrote. This package does not rewrite it. A
claim that no longer matches its document is left out of the message, and `wb trace` is where it
stays visible, with the reason.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

from agent_container.core.budget import Budget
from agent_container.core.loop import MAX_USER_MESSAGE_CHARS

from tests.conftest import ACME_QUOTE, Fixture
from tests.conftest_pack import (
    ACME,
    CYCLE,
    FABRICATED,
    FIXTURE,
    INJECTION,
    MATCHING,
    NO_DUPES,
    Pack,
)
from workbench.cli.readout import _inspect
from workbench.coordinator.providers import ReplaySource
from workbench.core.config import SYNTHESIS_INPUT_CAP
from workbench.core.principals import Principal
from workbench.core.store import NewClaim, NewQuestion
from workbench.readout.evidence import collect_evidence
from workbench.readout.render import render_trace

_CLERK = "interviews/ap-clerk.md"


def _discover(pack: Pack, principal: Principal) -> None:
    asyncio.run(
        pack.coordinator(ReplaySource.from_file(FIXTURE)).discover(
            principal,
            ACME,
            budget=Budget(max_turns=60, max_tokens=400_000, max_seconds=600.0),
        )
    )


def _record_clerk_claim(fixture: Fixture, analyst: Principal) -> str:
    refs = fixture.store.index_sources(analyst, ACME, fixture.acme_library)
    doc_id = next(ref.doc_id for ref in refs if ref.path == _CLERK)
    (question,) = fixture.store.record_questions(
        analyst,
        ACME,
        [NewQuestion("How is matching done?", "process", [doc_id], "the clerk says so")],
    )
    (claim,) = fixture.store.record_claims(
        analyst,
        ACME,
        [NewClaim(question.id, "Matching is manual.", doc_id, ACME_QUOTE, 0.9)],
        fixture.acme_library,
    )
    assert claim.verified is True
    return claim.id


def test_a_changed_document_is_excluded_and_the_stored_flag_stays(
    fixture: Fixture, analyst: Principal
) -> None:
    """Re-verify is the check. There is no store call that would flip `verified` back to false."""
    claim_id = _record_clerk_claim(fixture, analyst)
    path = fixture.config.sources_root / ACME / _CLERK
    path.write_text(
        "# AP clerk\n\nThe sentence that was here has been replaced with other words.\n",
        encoding="utf-8",
    )
    evidence = collect_evidence(fixture.store, fixture.config, analyst, ACME)
    assert claim_id not in {item.claim.id for item in evidence.admitted}
    assert ACME_QUOTE not in evidence.message
    stored = fixture.store.claim(analyst, claim_id)
    assert stored.verified is True

    document, live, reason = _inspect(fixture.store, fixture.config, analyst, stored)
    assert live is False
    assert reason == "the quote is not present verbatim in the document it names"
    rendered = render_trace(claim=stored, document=document, live_verified=live, reason=reason)
    assert "recorded_verified: true" in rendered
    assert "recorded_verified: false" not in rendered
    assert rendered.index("live_verified: false") < rendered.index("quote:")
    assert ACME_QUOTE in rendered
    assert document == _CLERK


def test_a_cap_below_the_wall_drops_claims_and_says_so(
    fixture: Fixture, analyst: Principal
) -> None:
    _record_clerk_claim(fixture, analyst)
    config = replace(fixture.config, synthesis_input_cap=80)
    evidence = collect_evidence(fixture.store, config, analyst, ACME)
    assert len(evidence.message) <= min(80, MAX_USER_MESSAGE_CHARS)
    assert "TRUNCATED" in evidence.message
    assert evidence.shown_labels == frozenset()
    assert evidence.resolve("C1") is None
    assert ACME_QUOTE not in evidence.message
    # Admitted, because the quote still checks out, and unshown, because it did not fit.
    assert len(evidence.admitted) == 1
    assert evidence.omitted_claims == 1


def test_the_committed_run_labels_claims_in_store_order(
    pack: Pack, pack_analyst: Principal
) -> None:
    """The readout fixture cites C1..C7. Those labels are this order, or the mapping is wrong."""
    _discover(pack, pack_analyst)
    evidence = collect_evidence(pack.store, pack.config, pack_analyst, ACME)
    by_label = {item.label: item.claim for item in evidence.admitted}
    assert by_label["C1"].quote == MATCHING
    assert by_label["C2"].quote == CYCLE
    assert by_label["C3"].quote == NO_DUPES
    assert "HLP-4901" in by_label["C4"].quote
    assert "not in the inventory" in by_label["C5"].quote
    assert by_label["C6"].quote == INJECTION
    assert "Harbour" in by_label["C7"].quote
    assert FABRICATED not in {item.claim.quote for item in evidence.admitted}
    assert FABRICATED not in evidence.message
    assert INJECTION in evidence.message
    assert len(evidence.message) <= min(pack.config.synthesis_input_cap, MAX_USER_MESSAGE_CHARS)
    assert evidence.omitted_claims == 0
    assert "TRUNCATED" not in evidence.message


def test_synthesis_uses_the_smaller_of_the_two_caps() -> None:
    assert min(SYNTHESIS_INPUT_CAP, MAX_USER_MESSAGE_CHARS) == MAX_USER_MESSAGE_CHARS
