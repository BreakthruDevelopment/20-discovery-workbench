"""The store's own rules: the owner filter inside every query, and `verified` set only in code."""

from __future__ import annotations

import sqlite3

import pytest
from agent_container.core.tool import ErrorCategory

from tests.conftest import ACME, ACME_QUOTE, NORTHWIND, Fixture
from workbench.core.errors import AccessDenied, InvalidInput, NotFound
from workbench.core.principals import Principal
from workbench.core.store import NewClaim, NewQuestion

CLERK = "interviews/ap-clerk.md"


def _index(fixture: Fixture, principal: Principal, engagement_id: str) -> dict[str, str]:
    refs = fixture.store.index_sources(principal, engagement_id, fixture.library(engagement_id))
    return {ref.path: ref.doc_id for ref in refs}


def _one_question(fixture: Fixture, analyst: Principal, doc_id: str) -> str:
    (question,) = fixture.store.record_questions(
        analyst,
        ACME,
        [NewQuestion("How is three-way matching done?", "process", [doc_id], "planted fact 1")],
    )
    return question.id


# ---- the schema and the seed --------------------------------------------------------------


def test_the_seed_is_idempotent_and_deterministic(fixture: Fixture, analyst: Principal) -> None:
    fixture.store.seed()
    fixture.store.seed()
    assert fixture.store.engagement(analyst, ACME).brief.startswith("We spend too much")


def test_the_seed_holds_two_engagements_with_disjoint_principals(
    analyst: Principal, other_analyst: Principal
) -> None:
    assert analyst.engagements.isdisjoint(other_analyst.engagements)


def test_every_table_in_the_data_model_exists(fixture: Fixture) -> None:
    """Wave 1 creates every table, so no later slice needs a schema change."""
    expected = {
        "engagement",
        "engagement_principal",
        "source_document",
        "question",
        "subagent_run",
        "claim",
        "readout",
        "finalisation",
    }
    rows = fixture.store._connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    assert expected <= {str(row["name"]) for row in rows}


def test_the_schema_refuses_a_specialist_outside_the_closed_set(fixture: Fixture) -> None:
    """Belt as well as braces: the accessor validates, and the database refuses too."""
    with pytest.raises(sqlite3.IntegrityError):
        fixture.store._connection.execute(
            "INSERT INTO question (id, engagement_id, seq, text, specialist, doc_ids, rationale) "
            "VALUES ('q', 'acme-p2p', 1, 't', 'vibes', '[]', 'r')"
        )


def test_the_schema_refuses_an_ok_run_that_claims_an_error(fixture: Fixture) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        fixture.store._connection.execute(
            "INSERT INTO subagent_run "
            "(id, question_id, state, error_category, is_retryable, turns, tokens) "
            "VALUES ('r', 'q', 'ok', 'transient', 1, 1, 1)"
        )


# ---- the source index -----------------------------------------------------------------------


def test_the_index_is_scoped_to_one_engagement(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    _index(fixture, analyst, ACME)
    _index(fixture, other_analyst, NORTHWIND)
    acme_paths = {ref.path for ref in fixture.store.source_documents(analyst, ACME)}
    northwind_paths = {ref.path for ref in fixture.store.source_documents(other_analyst, NORTHWIND)}
    assert acme_paths == {CLERK, "systems-inventory.csv"}
    assert northwind_paths == {"ar-notes.md"}


def test_reindexing_an_unchanged_tree_writes_the_same_rows(
    fixture: Fixture, analyst: Principal
) -> None:
    first = _index(fixture, analyst, ACME)
    assert _index(fixture, analyst, ACME) == first


def test_a_document_id_from_another_engagement_is_not_found(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    """The re-check every model-returned `doc_id` goes through: the query filters on the owner."""
    _index(fixture, analyst, ACME)
    northwind = _index(fixture, other_analyst, NORTHWIND)
    with pytest.raises(NotFound):
        fixture.store.document_path(analyst, ACME, northwind["ar-notes.md"])


def test_a_document_path_resolves_for_its_own_engagement(
    fixture: Fixture, analyst: Principal
) -> None:
    index = _index(fixture, analyst, ACME)
    assert fixture.store.document_path(analyst, ACME, index[CLERK]) == CLERK


# ---- questions ------------------------------------------------------------------------------


def test_a_question_naming_another_engagements_document_is_refused(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    _index(fixture, analyst, ACME)
    northwind = _index(fixture, other_analyst, NORTHWIND)
    with pytest.raises(InvalidInput):
        fixture.store.record_questions(
            analyst,
            ACME,
            [
                NewQuestion(
                    "What does the other client do?",
                    "process",
                    [northwind["ar-notes.md"]],
                    "out of scope",
                )
            ],
        )
    assert fixture.store.questions(analyst, ACME) == ()


def test_questions_are_numbered_in_plan_order(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    recorded = fixture.store.record_questions(
        analyst,
        ACME,
        [
            NewQuestion("first", "process", [index[CLERK]], "r1"),
            NewQuestion("second", "systems", [index["systems-inventory.csv"]], "r2"),
        ],
    )
    assert [question.seq for question in recorded] == [1, 2]
    assert [question.seq for question in fixture.store.questions(analyst, ACME)] == [1, 2]


def test_a_question_with_no_document_is_refused(fixture: Fixture, analyst: Principal) -> None:
    _index(fixture, analyst, ACME)
    with pytest.raises(InvalidInput):
        fixture.store.record_questions(analyst, ACME, [NewQuestion("vague", "process", [], "none")])


def test_a_specialist_outside_the_closed_set_is_refused(
    fixture: Fixture, analyst: Principal
) -> None:
    index = _index(fixture, analyst, ACME)
    with pytest.raises(InvalidInput):
        fixture.store.record_questions(
            analyst, ACME, [NewQuestion("q", "vibes", [index[CLERK]], "r")]
        )


# ---- subagent runs --------------------------------------------------------------------------


def test_a_failed_run_is_recorded_with_its_category_and_retry_flag(
    fixture: Fixture, analyst: Principal
) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    run = fixture.store.record_subagent_run(
        analyst,
        ACME,
        question_id=question_id,
        state="failed",
        turns=2,
        tokens=900,
        error_category=ErrorCategory.TRANSIENT,
        is_retryable=True,
    )
    assert run.state == "failed"
    assert run.error_category == "transient"
    assert run.is_retryable is True
    assert fixture.store.failed_run_question_ids(analyst, ACME) == (question_id,)


def test_a_retried_question_is_no_longer_a_gap(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    fixture.store.record_subagent_run(
        analyst,
        ACME,
        question_id=question_id,
        state="failed",
        turns=1,
        tokens=10,
        error_category=ErrorCategory.TRANSIENT,
        is_retryable=True,
    )
    fixture.store.record_subagent_run(
        analyst, ACME, question_id=question_id, state="ok", turns=3, tokens=400
    )
    assert fixture.store.failed_run_question_ids(analyst, ACME) == ()


def test_a_failed_run_with_no_category_is_refused(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_subagent_run(
            analyst, ACME, question_id=question_id, state="failed", turns=1, tokens=1
        )


def test_a_run_cannot_be_attached_to_another_engagements_question(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    northwind = _index(fixture, other_analyst, NORTHWIND)
    (their_question,) = fixture.store.record_questions(
        other_analyst,
        NORTHWIND,
        [NewQuestion("their question", "data", [northwind["ar-notes.md"]], "theirs")],
    )
    _index(fixture, analyst, ACME)
    with pytest.raises(InvalidInput):
        fixture.store.record_subagent_run(
            analyst, ACME, question_id=their_question.id, state="ok", turns=1, tokens=1
        )


# ---- claims and provenance ------------------------------------------------------------------


def test_a_verbatim_quote_is_recorded_verified(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    (claim,) = fixture.store.record_claims(
        analyst,
        ACME,
        [NewClaim(question_id, "Matching is manual.", index[CLERK], ACME_QUOTE, 0.9)],
        fixture.acme_library,
    )
    assert claim.verified is True
    assert fixture.store.claims(analyst, ACME, verified_only=True) == (claim,)


def test_a_fabricated_quote_is_recorded_unverified_and_excluded(
    fixture: Fixture, analyst: Principal
) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    (claim,) = fixture.store.record_claims(
        analyst,
        ACME,
        [
            NewClaim(
                question_id,
                "Matching is automated.",
                index[CLERK],
                "Matching has been automated since 2019 across every supplier.",
                0.8,
            )
        ],
        fixture.acme_library,
    )
    assert claim.verified is False
    assert fixture.store.claims(analyst, ACME, verified_only=True) == ()
    # Still traceable, with its quote, so `wb trace` can show why it was excluded.
    assert fixture.store.claim(analyst, claim.id).verified is False


def test_a_claim_cannot_assert_its_own_verification(fixture: Fixture, analyst: Principal) -> None:
    """`NewClaim` carries no `verified` field at all: the store computes it from the document."""
    assert "verified" not in NewClaim.__dataclass_fields__


def test_a_claim_naming_another_engagements_document_is_refused(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    index = _index(fixture, analyst, ACME)
    northwind = _index(fixture, other_analyst, NORTHWIND)
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [NewClaim(question_id, "theirs", northwind["ar-notes.md"], ACME_QUOTE, 0.5)],
            fixture.acme_library,
        )
    assert fixture.store.claims(analyst, ACME) == ()


def test_confidence_outside_zero_to_one_is_refused(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [NewClaim(question_id, "claim", index[CLERK], ACME_QUOTE, 1.5)],
            fixture.acme_library,
        )


def test_tracing_another_engagements_claim_is_refused(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    from tests.conftest import NORTHWIND_QUOTE

    northwind = _index(fixture, other_analyst, NORTHWIND)
    (their_question,) = fixture.store.record_questions(
        other_analyst,
        NORTHWIND,
        [NewQuestion("their question", "data", [northwind["ar-notes.md"]], "theirs")],
    )
    (their_claim,) = fixture.store.record_claims(
        other_analyst,
        NORTHWIND,
        [
            NewClaim(
                their_question.id,
                "Remittance is retyped.",
                northwind["ar-notes.md"],
                NORTHWIND_QUOTE,
                0.7,
            )
        ],
        fixture.northwind_library,
    )
    assert their_claim.verified is True
    with pytest.raises(AccessDenied):
        fixture.store.claim(analyst, their_claim.id)


def test_tracing_a_claim_that_exists_nowhere_is_not_found(
    fixture: Fixture, analyst: Principal
) -> None:
    with pytest.raises(NotFound):
        fixture.store.claim(analyst, "id-does-not-exist")


# ---- the readout ----------------------------------------------------------------------------


def test_a_draft_readout_is_seeded_with_zeroed_coverage(
    fixture: Fixture, analyst: Principal
) -> None:
    readout = fixture.store.readout(analyst, ACME)
    assert readout.state == "draft"
    assert readout.coverage == {"questions_total": 0, "answered": 0, "failed": 0, "gaps": []}
    assert readout.roi is None


def test_a_saved_readout_round_trips_and_roi_may_stay_null(
    fixture: Fixture, analyst: Principal
) -> None:
    """The ROI cut is a null in a nullable column, not a migration."""
    saved = fixture.store.save_readout(
        analyst,
        ACME,
        maturity=[{"dimension": "process", "level": "unknown", "claim_ids": []}],
        outcomes=[],
        roadmap=[{"phase": "discover", "weeks": 2, "depends_on": []}],
        coverage={"questions_total": 1, "answered": 0, "failed": 1, "gaps": [{"reason": "x"}]},
    )
    assert saved.roi is None
    assert fixture.store.readout(analyst, ACME).maturity == saved.maturity
