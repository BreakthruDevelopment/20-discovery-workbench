"""One test per access rule in the spec's "Access rules" paragraph, allowed and refused.

The rules, and the test that holds each:

* an `analyst` reaches only engagements it is assigned to -- `test_analyst_reaches_own_*`
* a `sponsor` gets `read_readout` on its own engagement only when `state = final` --
  `test_sponsor_*`
* a `sponsor` gets no source action at all -- `test_sponsor_reaches_no_source_*`
* only a `lead` may finalise -- `test_only_a_lead_*`
* finalising twice is refused by a unique guard -- `test_finalising_twice_*`
* `--live` is `lead`-only -- `test_run_live_*`
"""

from __future__ import annotations

import pytest

from tests.conftest import ACME, NORTHWIND, Fixture
from workbench.core.errors import AccessDenied, AlreadyFinal, CoverageGapsPresent
from workbench.core.principals import (
    Action,
    EngagementState,
    Principal,
    Resource,
    Role,
    assert_can,
    may,
)

# ---- assignment ---------------------------------------------------------------------------


def test_assignment_is_resolved_from_the_store(
    analyst: Principal, other_analyst: Principal
) -> None:
    assert analyst.engagements == frozenset({ACME})
    assert other_analyst.engagements == frozenset({NORTHWIND})


def test_a_role_a_principal_is_not_assigned_as_yields_no_engagements(fixture: Fixture) -> None:
    """Assignment is matched on the role as well as the id: `--role lead` is not a promotion."""
    impostor = fixture.store.load_principal("analyst-rao", Role.LEAD)
    assert impostor.engagements == frozenset()


def test_analyst_reaches_own_engagement(fixture: Fixture, analyst: Principal) -> None:
    assert fixture.store.engagement(analyst, ACME).client == "Acme Industrial"


def test_analyst_is_refused_the_other_engagement(fixture: Fixture, analyst: Principal) -> None:
    with pytest.raises(AccessDenied):
        fixture.store.engagement(analyst, NORTHWIND)


def test_analyst_is_refused_the_other_engagements_sources(
    fixture: Fixture, analyst: Principal
) -> None:
    with pytest.raises(AccessDenied):
        fixture.store.source_documents(analyst, NORTHWIND)


def test_an_unknown_engagement_is_refused_as_out_of_scope(
    fixture: Fixture, analyst: Principal
) -> None:
    """Not `not_found`: an engagement nobody is assigned to is out of scope, and the refusal says
    nothing about whether it exists."""
    with pytest.raises(AccessDenied):
        fixture.store.engagement(analyst, "no-such-engagement")


# ---- the sponsor --------------------------------------------------------------------------


def test_sponsor_is_refused_a_draft_readout(fixture: Fixture, sponsor: Principal) -> None:
    with pytest.raises(AccessDenied) as refusal:
        fixture.store.readout(sponsor, ACME)
    assert refusal.value.category.value == "permission"
    assert refusal.value.retryable is False


def test_sponsor_reads_a_final_readout(
    fixture: Fixture, sponsor: Principal, lead: Principal
) -> None:
    fixture.store.finalise(lead, ACME)
    readout = fixture.store.readout(sponsor, ACME)
    assert readout.state == "final"
    assert readout.finalised_by == "lead-parrott"


def test_sponsor_reaches_no_source_index_even_when_final(
    fixture: Fixture, sponsor: Principal, lead: Principal
) -> None:
    fixture.store.finalise(lead, ACME)
    with pytest.raises(AccessDenied):
        fixture.store.source_documents(sponsor, ACME)


def test_sponsor_reaches_no_source_path_even_when_final(
    fixture: Fixture, sponsor: Principal, lead: Principal, analyst: Principal
) -> None:
    refs = fixture.store.index_sources(analyst, ACME, fixture.acme_library)
    fixture.store.finalise(lead, ACME)
    with pytest.raises(AccessDenied):
        fixture.store.document_path(sponsor, ACME, refs[0].doc_id)


def test_sponsor_cannot_trace_a_claim(
    fixture: Fixture, sponsor: Principal, lead: Principal
) -> None:
    assert not may(
        Principal("sponsor-acme", Role.SPONSOR, frozenset({ACME})),
        Action.TRACE_CLAIM,
        Resource(ACME, EngagementState.FINAL),
    )


def test_sponsor_is_refused_another_engagements_final_readout(
    fixture: Fixture, lead: Principal
) -> None:
    other_sponsor = fixture.store.load_principal("sponsor-northwind", Role.SPONSOR)
    fixture.store.finalise(lead, ACME)
    with pytest.raises(AccessDenied):
        fixture.store.readout(other_sponsor, ACME)


# ---- finalise -----------------------------------------------------------------------------


def test_only_a_lead_may_finalise(fixture: Fixture, analyst: Principal) -> None:
    with pytest.raises(AccessDenied):
        fixture.store.finalise(analyst, ACME)


def test_a_lead_may_finalise(fixture: Fixture, lead: Principal) -> None:
    assert fixture.store.finalise(lead, ACME).state == "final"


def test_finalising_twice_is_refused_by_the_unique_guard(fixture: Fixture, lead: Principal) -> None:
    fixture.store.finalise(lead, ACME)
    with pytest.raises(AlreadyFinal):
        fixture.store.finalise(lead, ACME)


def test_finalising_records_whether_gaps_were_accepted(fixture: Fixture, lead: Principal) -> None:
    fixture.store.finalise(lead, ACME)
    assert fixture.store.finalisation_accepted_gaps(lead, ACME) is False


def test_a_final_readout_is_not_rewritten(fixture: Fixture, lead: Principal) -> None:
    fixture.store.finalise(lead, ACME)
    with pytest.raises(AlreadyFinal):
        fixture.store.save_readout(
            lead, ACME, maturity=[], outcomes=[], roadmap=[], coverage={"gaps": []}
        )


def test_finalise_is_refused_while_a_subagent_run_failed(
    fixture: Fixture, lead: Principal, analyst: Principal
) -> None:
    from agent_container.core.tool import ErrorCategory

    from workbench.core.store import NewQuestion

    refs = fixture.store.index_sources(analyst, ACME, fixture.acme_library)
    (question,) = fixture.store.record_questions(
        analyst,
        ACME,
        [NewQuestion("How is matching done?", "process", [refs[0].doc_id], "the planted fact")],
    )
    fixture.store.record_subagent_run(
        analyst,
        ACME,
        question_id=question.id,
        state="failed",
        turns=1,
        tokens=120,
        error_category=ErrorCategory.TRANSIENT,
        is_retryable=True,
    )
    with pytest.raises(CoverageGapsPresent):
        fixture.store.finalise(lead, ACME)
    readout = fixture.store.finalise(lead, ACME, accept_gaps=True)
    assert readout.state == "final"
    assert fixture.store.finalisation_accepted_gaps(lead, ACME) is True


# ---- --live -------------------------------------------------------------------------------


def test_run_live_is_lead_only() -> None:
    scope = Resource(ACME, EngagementState.OPEN)
    assert may(Principal("lead-parrott", Role.LEAD, frozenset({ACME})), Action.RUN_LIVE, scope)
    assert not may(
        Principal("analyst-rao", Role.ANALYST, frozenset({ACME})), Action.RUN_LIVE, scope
    )
    assert not may(
        Principal("sponsor-acme", Role.SPONSOR, frozenset({ACME})), Action.RUN_LIVE, scope
    )


# ---- the pure layer -----------------------------------------------------------------------


@pytest.mark.parametrize("action", list(Action))
def test_an_unassigned_principal_is_refused_every_action(action: Action) -> None:
    """Scope is checked before role, so nothing is reachable outside an assignment."""
    stranger = Principal("stranger", Role.LEAD, frozenset())
    with pytest.raises(AccessDenied):
        assert_can(stranger, action, Resource(ACME, EngagementState.FINAL))


@pytest.mark.parametrize("action", list(Action))
def test_a_lead_reaches_every_action_on_its_own_engagement(action: Action) -> None:
    lead = Principal("lead-parrott", Role.LEAD, frozenset({ACME}))
    assert_can(lead, action, Resource(ACME, EngagementState.FINAL))


def test_scope_is_checked_before_role() -> None:
    """A sponsor outside the engagement is refused for scope, not for its role or the state: the
    message must be the scope one, because the role refusal would confirm the engagement exists."""
    sponsor = Principal("sponsor-acme", Role.SPONSOR, frozenset({ACME}))
    with pytest.raises(AccessDenied) as refusal:
        assert_can(sponsor, Action.READ_READOUT, Resource(NORTHWIND, EngagementState.FINAL))
    assert "not assigned" in str(refusal.value)
