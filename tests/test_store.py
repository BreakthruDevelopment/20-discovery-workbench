"""The store's own rules: the owner filter inside every query, and `verified` set only in code."""

from __future__ import annotations

import sqlite3

import pytest
from agent_container.core.tool import ErrorCategory

from tests.conftest import ACME, ACME_QUOTE, NORTHWIND, Fixture
from workbench.core.errors import AccessDenied, InvalidInput, NotFound
from workbench.core.principals import Principal
from workbench.core.sources import SourceRef
from workbench.core.store import NewClaim, NewQuestion, Store

CLERK = "interviews/ap-clerk.md"


def _index_refs(
    fixture: Fixture, principal: Principal, engagement_id: str
) -> tuple[SourceRef, ...]:
    return fixture.store.index_sources(principal, engagement_id, fixture.library(engagement_id))


def _index(fixture: Fixture, principal: Principal, engagement_id: str) -> dict[str, str]:
    return {ref.path: ref.doc_id for ref in _index_refs(fixture, principal, engagement_id)}


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


# ---- regressions from the first review round --------------------------------------------------


def test_reindexing_after_a_claim_exists_does_not_raise(
    fixture: Fixture, analyst: Principal
) -> None:
    """`claim.doc_id` has a foreign key to `source_document`, so the first version's
    delete-and-reinsert raised a raw `sqlite3.IntegrityError` -- outside `errors.py` entirely --
    the moment a second `wb discover` ran after any claim existed."""
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    fixture.store.record_claims(
        analyst,
        ACME,
        [NewClaim(question_id, "Matching is manual.", index[CLERK], ACME_QUOTE, 0.9)],
        fixture.acme_library,
    )
    assert _index(fixture, analyst, ACME) == index


def test_reindexing_keeps_a_row_a_claim_still_cites(fixture: Fixture, analyst: Principal) -> None:
    """A document that leaves the tree while a claim cites it keeps its row, so `wb trace` can
    still resolve what the claim named; reading it then fails honestly instead."""
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    fixture.store.record_claims(
        analyst,
        ACME,
        [NewClaim(question_id, "Matching is manual.", index[CLERK], ACME_QUOTE, 0.9)],
        fixture.acme_library,
    )
    (fixture.config.engagement_sources_root(ACME) / CLERK).unlink()
    refs = fixture.store.index_sources(analyst, ACME, fixture.acme_library)
    assert CLERK not in {ref.path for ref in refs}
    # Still recorded, because a claim cites it.
    assert fixture.store.document_path(analyst, ACME, index[CLERK]) == CLERK


def test_reindexing_drops_a_row_nothing_cites(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    (fixture.config.engagement_sources_root(ACME) / CLERK).unlink()
    _index(fixture, analyst, ACME)
    with pytest.raises(NotFound):
        fixture.store.document_path(analyst, ACME, index[CLERK])


def test_reindexing_an_emptied_tree_does_not_raise(fixture: Fixture, analyst: Principal) -> None:
    """The empty case: `id NOT IN ()` is a syntax error in SQLite, so it has its own branch."""
    _index(fixture, analyst, ACME)
    root = fixture.config.engagement_sources_root(ACME)
    for path in sorted(root.rglob("*")):
        if path.is_file():
            path.unlink()
    assert fixture.store.index_sources(analyst, ACME, fixture.acme_library) == ()


def test_two_engagements_may_hold_the_same_filename(
    fixture: Fixture, analyst: Principal, other_analyst: Principal
) -> None:
    """`source_document.id` is a database-wide primary key, so an id derived from the path alone
    collided the moment both engagements held a `systems-inventory.csv` -- which the spec's own
    pack filename makes likely."""
    northwind_root = fixture.config.engagement_sources_root(NORTHWIND)
    (northwind_root / "systems-inventory.csv").write_text(
        "system,owner,notes\nAS400,IT,remittance import\n", encoding="utf-8"
    )
    acme = _index(fixture, analyst, ACME)
    northwind = _index(fixture, other_analyst, NORTHWIND)
    assert acme["systems-inventory.csv"] != northwind["systems-inventory.csv"]
    assert len(fixture.store.source_documents(analyst, ACME)) == 2
    assert len(fixture.store.source_documents(other_analyst, NORTHWIND)) == 2


def test_the_wrong_library_cannot_index_an_engagement(fixture: Fixture, analyst: Principal) -> None:
    """The last piece of the owner filter that could have lived in a caller."""
    with pytest.raises(InvalidInput):
        fixture.store.index_sources(analyst, ACME, fixture.northwind_library)
    assert fixture.store.source_documents(analyst, ACME) == ()


def test_the_wrong_library_cannot_verify_a_claim(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [NewClaim(question_id, "t", index[CLERK], ACME_QUOTE, 0.5)],
            fixture.northwind_library,
        )


def test_a_claim_may_not_cite_a_document_its_question_did_not_name(
    fixture: Fixture, analyst: Principal
) -> None:
    """Scoped context passing is a boundary per subagent, not only per engagement: a finding
    citing a document its question never named did not come from what that subagent was shown."""
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [
                NewClaim(
                    question_id,
                    "from a document this question never named",
                    index["systems-inventory.csv"],
                    ACME_QUOTE,
                    0.5,
                )
            ],
            fixture.acme_library,
        )
    assert fixture.store.claims(analyst, ACME) == ()


def test_free_text_is_length_capped(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    with pytest.raises(InvalidInput):
        fixture.store.record_questions(
            analyst, ACME, [NewQuestion("q" * 5_000, "process", [index[CLERK]], "r")]
        )
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [NewClaim(question_id, "c" * 5_000, index[CLERK], ACME_QUOTE, 0.5)],
            fixture.acme_library,
        )


def test_a_nul_byte_in_free_text_is_refused(fixture: Fixture, analyst: Principal) -> None:
    """SQLite stores a NUL; Postgres cannot, and these fields feed 20.5's synthesis prompt."""
    index = _index(fixture, analyst, ACME)
    with pytest.raises(InvalidInput):
        fixture.store.record_questions(
            analyst, ACME, [NewQuestion("q\x00uestion", "process", [index[CLERK]], "r")]
        )
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [NewClaim(question_id, "cl\x00aim", index[CLERK], ACME_QUOTE, 0.5)],
            fixture.acme_library,
        )


def test_free_text_is_trimmed(fixture: Fixture, analyst: Principal) -> None:
    index = _index(fixture, analyst, ACME)
    (question,) = fixture.store.record_questions(
        analyst, ACME, [NewQuestion("  padded  ", "process", [index[CLERK]], "  why  ")]
    )
    assert (question.text, question.rationale) == ("padded", "why")


def test_the_recorded_index_reports_what_is_unreadable(
    fixture: Fixture, analyst: Principal
) -> None:
    """`source_documents` returned `readable=True` for every row, so `wb sources list` -- "the
    source index, with sizes and what is unreadable" -- would have called an undecodable document
    fine, and 20.6 would have had nothing to reveal it."""
    (fixture.config.engagement_sources_root(ACME) / "broken.txt").write_bytes(b"\xff\xfe nope")
    live = {ref.path: ref for ref in _index_refs(fixture, analyst, ACME)}
    assert live["broken.txt"].readable is False
    recorded = {ref.path: ref for ref in fixture.store.source_documents(analyst, ACME)}
    assert recorded["broken.txt"].readable is False
    assert recorded["broken.txt"].unread_reason == live["broken.txt"].unread_reason
    assert recorded[CLERK].readable is True
    assert recorded[CLERK].unread_reason is None


def test_a_readout_section_is_length_capped(fixture: Fixture, analyst: Principal) -> None:
    """`save_readout` was the one boundary with no bound at all."""
    with pytest.raises(InvalidInput):
        fixture.store.save_readout(
            analyst,
            ACME,
            maturity=["x" * 500_000],
            outcomes=[],
            roadmap=[],
            coverage={"gaps": []},
        )


def test_a_nul_byte_in_a_readout_section_is_refused(fixture: Fixture, analyst: Principal) -> None:
    with pytest.raises(InvalidInput):
        fixture.store.save_readout(
            analyst,
            ACME,
            maturity=[],
            outcomes=[],
            roadmap=[],
            coverage={"gaps": [{"reason": "pro\x00blem"}]},
        )


def test_a_library_whose_label_and_root_disagree_is_refused(
    fixture: Fixture, analyst: Principal
) -> None:
    """Checking the label alone let a library rooted at the other engagement's tree through, and
    it then verified a quote against that engagement's file."""
    from tests.conftest import NORTHWIND_QUOTE
    from workbench.core.sources import SourceLibrary

    mislabelled = SourceLibrary(
        fixture.config.engagement_sources_root(NORTHWIND),
        engagement_id=ACME,
        max_file_bytes=fixture.config.max_source_file_bytes,
        max_run_bytes=fixture.config.max_source_run_bytes,
    )
    assert mislabelled.verify_quote("ar-notes.md", NORTHWIND_QUOTE) is True
    with pytest.raises(InvalidInput):
        fixture.store.index_sources(analyst, ACME, mislabelled)
    index = _index(fixture, analyst, ACME)
    question_id = _one_question(fixture, analyst, index[CLERK])
    with pytest.raises(InvalidInput):
        fixture.store.record_claims(
            analyst,
            ACME,
            [NewClaim(question_id, "theirs", index[CLERK], NORTHWIND_QUOTE, 0.9)],
            mislabelled,
        )


def test_an_unserialisable_readout_section_is_refused(fixture: Fixture, analyst: Principal) -> None:
    """A `datetime` or a `Decimal` is the near miss 20.5 will make; a raw `TypeError` out of the
    store carries no error category and no field name."""
    from datetime import date

    with pytest.raises(InvalidInput) as refusal:
        fixture.store.save_readout(
            analyst,
            ACME,
            maturity=[],
            outcomes=[],
            roadmap=[{"phase": "discover", "starts": date(2026, 11, 21)}],
            coverage={"gaps": []},
        )
    assert "readout.roadmap" in str(refusal.value)


def test_a_database_from_another_schema_version_is_refused(fixture: Fixture) -> None:
    """Otherwise a stale scratch database fails one column at a time as
    `sqlite3.OperationalError`, outside `errors.py` and with no category."""
    from dataclasses import replace

    from workbench.core.errors import StoreCorrupt

    other = fixture.config.database_path.with_name("other.sqlite3")
    with Store.open(replace(fixture.config, database_path=other)) as store:
        store.build()
        store._connection.execute("PRAGMA user_version = 99")
    with pytest.raises(StoreCorrupt):
        Store.open(replace(fixture.config, database_path=other))


def test_the_schema_stamp_matches_the_constant(fixture: Fixture) -> None:
    from workbench.core.store import SCHEMA_VERSION

    stamped = fixture.store._connection.execute("PRAGMA user_version").fetchone()[0]
    assert int(stamped) == SCHEMA_VERSION
