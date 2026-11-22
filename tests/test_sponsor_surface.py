"""A `sponsor` reaches the finalised readout and **nothing else**, proved by exhaustion.

Why this file exists. The first version of 20.2 put `claims()`, `questions()`, `subagent_runs()`
and `engagement()` behind `READ_READOUT`, which a sponsor holds once the engagement is final. The
`TRACE_CLAIM` refusal beside them was therefore decorative: `store.claims(sponsor, ...)` returned
every claim with its verbatim quote, unverified ones included. 123 tests were green, because the
sponsor tests asserted `may(...) is False` on one action instead of calling the accessors.

So this file does not test a list of actions. It calls **every public accessor on `Store`** as a
sponsor against a finalised engagement and asserts each one either succeeds (and is on the short
allowed list) or raises `AccessDenied`. A new accessor is covered the moment it exists: it either
appears in `_ALLOWED_FOR_SPONSOR` by someone's decision, or the sweep fails.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest
from agent_container.core.tool import ErrorCategory

from tests.conftest import ACME, ACME_QUOTE, Fixture
from workbench.core.errors import AccessDenied
from workbench.core.principals import Action, Principal
from workbench.core.store import NewClaim, NewQuestion, Store

#: The only accessors a sponsor may reach, and the reason each is allowed.
_SPONSOR_MAY = {
    # The finalised readout itself: the sponsor's one entitlement.
    "readout",
    # `(id, client, state)` only, for a readout header. No brief, no sponsor_principal.
    "engagement_summary",
    # Reads the principal's own assignment and returns no engagement data at all.
    "engagement_ids",
}

#: Lifecycle, not data access: these take no principal, so there is nothing to authorise. Listed
#: by name so that a new *accessor* can never land here by accident -- it would have to be added
#: here on purpose, and the sweep's message says so.
_NOT_ACCESSORS = {"open", "close", "create_schema", "seed", "build", "load_principal"}


def _public_accessors() -> list[str]:
    """Every public `Store` method that takes an acting principal."""
    return sorted(
        name
        for name, member in inspect.getmembers(Store, callable)
        if not name.startswith("_") and inspect.isfunction(member) and name not in _NOT_ACCESSORS
    )


def _sponsor_call(fixture: Fixture, sponsor: Principal, name: str, context: dict[str, Any]) -> None:
    """Call one accessor as the sponsor, with arguments that would work for an analyst."""
    store = fixture.store
    calls: dict[str, Any] = {
        "engagement": lambda: store.engagement(sponsor, ACME),
        "engagement_summary": lambda: store.engagement_summary(sponsor, ACME),
        "engagement_ids": lambda: store.engagement_ids(sponsor),
        "index_sources": lambda: store.index_sources(sponsor, ACME, fixture.acme_library),
        "source_documents": lambda: store.source_documents(sponsor, ACME),
        "document_path": lambda: store.document_path(sponsor, ACME, context["doc_id"]),
        "record_questions": lambda: store.record_questions(
            sponsor, ACME, [NewQuestion("q", "process", [context["doc_id"]], "r")]
        ),
        "questions": lambda: store.questions(sponsor, ACME),
        "record_subagent_run": lambda: store.record_subagent_run(
            sponsor, ACME, question_id=context["question_id"], state="ok", turns=1, tokens=1
        ),
        "subagent_runs": lambda: store.subagent_runs(sponsor, ACME),
        "record_claims": lambda: store.record_claims(
            sponsor,
            ACME,
            [NewClaim(context["question_id"], "t", context["doc_id"], ACME_QUOTE, 0.5)],
            fixture.acme_library,
        ),
        "claims": lambda: store.claims(sponsor, ACME),
        "claim": lambda: store.claim(sponsor, context["claim_id"]),
        "readout": lambda: store.readout(sponsor, ACME),
        "save_readout": lambda: store.save_readout(
            sponsor, ACME, maturity=[], outcomes=[], roadmap=[], coverage={}
        ),
        "failed_run_question_ids": lambda: store.failed_run_question_ids(sponsor, ACME),
        "finalise": lambda: store.finalise(sponsor, ACME),
        "finalisation_accepted_gaps": lambda: store.finalisation_accepted_gaps(sponsor, ACME),
    }
    calls[name]()


@pytest.fixture
def finalised(fixture: Fixture, analyst: Principal, lead: Principal) -> dict[str, Any]:
    """A finalised engagement with one question, one run and one claim already recorded."""
    refs = fixture.store.index_sources(analyst, ACME, fixture.acme_library)
    doc_id = refs[0].doc_id
    (question,) = fixture.store.record_questions(
        analyst, ACME, [NewQuestion("How is matching done?", "process", [doc_id], "planted")]
    )
    fixture.store.record_subagent_run(
        analyst, ACME, question_id=question.id, state="ok", turns=2, tokens=300
    )
    (claim,) = fixture.store.record_claims(
        analyst,
        ACME,
        [NewClaim(question.id, "Matching is manual.", doc_id, ACME_QUOTE, 0.9)],
        fixture.acme_library,
    )
    fixture.store.finalise(lead, ACME)
    return {"doc_id": doc_id, "question_id": question.id, "claim_id": claim.id}


def test_every_store_accessor_is_covered_by_this_sweep(
    fixture: Fixture, sponsor: Principal, finalised: dict[str, Any]
) -> None:
    """The guard that makes the sweep automatic rather than a list someone has to remember."""
    accessors = _public_accessors()
    assert "claims" in accessors, "the sweep must see the accessor that was the original defect"
    for name in accessors:
        try:
            _sponsor_call(fixture, sponsor, name, finalised)
        except KeyError:
            pytest.fail(
                f"Store.{name} takes a principal but has no case in "
                "tests/test_sponsor_surface.py; add one, and add it to _SPONSOR_MAY only if a "
                "sponsor really may call it."
            )
        except AccessDenied:
            continue
        else:
            assert name in _SPONSOR_MAY, (
                f"Store.{name} succeeded for a sponsor and is not in _SPONSOR_MAY"
            )


@pytest.mark.parametrize("name", _public_accessors())
def test_a_sponsor_is_refused_every_accessor_but_its_readout(
    fixture: Fixture, sponsor: Principal, finalised: dict[str, Any], name: str
) -> None:
    if name in _SPONSOR_MAY:
        _sponsor_call(fixture, sponsor, name, finalised)
        return
    with pytest.raises(AccessDenied) as refusal:
        _sponsor_call(fixture, sponsor, name, finalised)
    assert refusal.value.category.value == "permission"
    assert refusal.value.retryable is False


def test_a_sponsor_reads_no_claim_and_no_quote_in_bulk(
    fixture: Fixture, sponsor: Principal, finalised: dict[str, Any]
) -> None:
    """The original defect, stated as its own test so the regression is named."""
    with pytest.raises(AccessDenied):
        fixture.store.claims(sponsor, ACME)
    with pytest.raises(AccessDenied):
        fixture.store.claims(sponsor, ACME, verified_only=True)


def test_a_sponsor_reads_no_brief(
    fixture: Fixture, sponsor: Principal, finalised: dict[str, Any]
) -> None:
    with pytest.raises(AccessDenied):
        fixture.store.engagement(sponsor, ACME)
    engagement_id, client, state = fixture.store.engagement_summary(sponsor, ACME)
    assert (engagement_id, client, state.value) == (ACME, "Acme Industrial", "final")


def test_a_sponsor_reads_the_finalised_readout(
    fixture: Fixture, sponsor: Principal, finalised: dict[str, Any]
) -> None:
    assert fixture.store.readout(sponsor, ACME).state == "final"


def test_read_readout_and_read_discovery_are_distinct_actions() -> None:
    """If these ever collapse, the sweep above becomes decorative again. Asserted as a property of
    the whole enum rather than a comparison of the two: `mypy --strict` rightly rejects comparing
    two distinct literals, which is itself the static half of this guarantee."""
    values = {action.value for action in Action}
    assert len(values) == len(list(Action))
    assert {Action.READ_READOUT.value, Action.READ_DISCOVERY.value} <= values


def test_an_unverified_claim_is_not_reachable_by_a_sponsor_either(
    fixture: Fixture, analyst: Principal, lead: Principal, sponsor: Principal
) -> None:
    refs = fixture.store.index_sources(analyst, ACME, fixture.acme_library)
    (question,) = fixture.store.record_questions(
        analyst, ACME, [NewQuestion("q", "process", [refs[0].doc_id], "r")]
    )
    fixture.store.record_subagent_run(
        analyst,
        ACME,
        question_id=question.id,
        state="failed",
        turns=1,
        tokens=1,
        error_category=ErrorCategory.TRANSIENT,
        is_retryable=True,
    )
    (claim,) = fixture.store.record_claims(
        analyst,
        ACME,
        [NewClaim(question.id, "invented", refs[0].doc_id, "A sentence nobody ever wrote.", 0.9)],
        fixture.acme_library,
    )
    assert claim.verified is False
    fixture.store.finalise(lead, ACME, accept_gaps=True)
    with pytest.raises(AccessDenied):
        fixture.store.claims(sponsor, ACME)
