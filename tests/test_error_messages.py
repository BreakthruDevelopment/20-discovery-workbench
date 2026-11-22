"""Every refusal's message is built from fixed codes and schema-derived names, never from input.

This is the project's own scar tissue: an error message built from parsed input leaks that input,
and it took five review rounds and six distinct routes to close in app 17. The test is written as a
sweep rather than as one assertion per call site, so a new accessor that echoes its argument is
caught without anyone remembering to add a case: every refusal below is fed a marker value in the
place a caller's value goes, and the marker must not appear in the message.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tests.conftest import ACME, ACME_QUOTE, Fixture
from workbench.core.errors import (
    AccessDenied,
    AlreadyFinal,
    CoverageGapsPresent,
    InvalidInput,
    NotFound,
    ProviderFailed,
    SourceOutsideRoot,
    SourceRefused,
    SourceUnreadable,
    StoreCorrupt,
    Throttled,
    WorkbenchError,
    classify,
)
from workbench.core.principals import (
    Action,
    EngagementState,
    Principal,
    Resource,
    Role,
    assert_can,
)
from workbench.core.sources import SourceLibrary
from workbench.core.store import NewClaim, NewQuestion

#: Distinctive enough that a substring match cannot be a coincidence.
MARKER = "zzmarkerzz-leaked-value"


def _refusals(fixture: Fixture, analyst: Principal) -> list[tuple[str, Callable[[], object]]]:
    """One callable per refusal that takes caller-supplied input, each poisoned with MARKER."""
    store = fixture.store
    library = fixture.acme_library
    refs = store.index_sources(analyst, ACME, library)
    doc_id = refs[0].doc_id
    (question,) = store.record_questions(
        analyst, ACME, [NewQuestion("How is matching done?", "process", [doc_id], "planted")]
    )
    return [
        ("engagement out of scope", lambda: store.engagement(analyst, MARKER)),
        ("source index out of scope", lambda: store.source_documents(analyst, MARKER)),
        ("unknown document id", lambda: store.document_path(analyst, ACME, MARKER)),
        ("unknown claim id", lambda: store.claim(analyst, MARKER)),
        (
            "bad specialist",
            lambda: store.record_questions(
                analyst, ACME, [NewQuestion("q", MARKER, [doc_id], "r")]
            ),
        ),
        (
            "document outside the engagement",
            lambda: store.record_questions(
                analyst, ACME, [NewQuestion("q", "process", [MARKER], "r")]
            ),
        ),
        (
            "question outside the engagement",
            lambda: store.record_subagent_run(
                analyst, ACME, question_id=MARKER, state="ok", turns=1, tokens=1
            ),
        ),
        (
            "bad run state",
            lambda: store.record_subagent_run(
                analyst, ACME, question_id=question.id, state=MARKER, turns=1, tokens=1
            ),
        ),
        (
            "claim document outside the engagement",
            lambda: store.record_claims(
                analyst,
                ACME,
                [NewClaim(question.id, "text", MARKER, ACME_QUOTE, 0.5)],
                library,
            ),
        ),
        ("path outside the root", lambda: library.read(f"../{MARKER}/notes.md")),
        ("absolute path", lambda: library.read(f"/{MARKER}")),
        ("refused extension", lambda: library.read(f"{MARKER}.json")),
        ("refused manifest", lambda: library.read("manifest.json")),
        ("missing document", lambda: library.read(f"{MARKER}.md")),
        ("padded path", lambda: library.read(f" {MARKER}.md")),
        ("short quote", lambda: library.verify_quote(refs[0].path, MARKER[:4])),
        ("overlong quote", lambda: library.verify_quote(refs[0].path, MARKER * 500)),
        ("empty principal id", lambda: store.load_principal("   ", Role.ANALYST)),
    ]


#: Members of `Store` and `SourceLibrary` that take no caller-supplied value to leak, so there is
#: nothing for the sweep to poison. Everything else must appear in `_COVERED` below.
_NOTHING_TO_LEAK = {
    "Store.open",
    "Store.close",
    "Store.create_schema",
    "Store.seed",
    "Store.build",
    "Store.engagement_ids",
    "Store.engagement_summary",
    "Store.questions",
    "Store.subagent_runs",
    "Store.claims",
    "Store.readout",
    "Store.save_readout",
    "Store.failed_run_question_ids",
    "Store.finalise",
    "Store.finalisation_accepted_gaps",
    "Store.index_sources",
    "SourceLibrary.list_documents",
    # Derives a root and a label from a config; the only refusal is the constructor's blank-label
    # check, which names no caller value.
    "SourceLibrary.for_engagement",
}

#: Which member each sweep case exercises. The sweep is hand-written -- a generic fuzzer cannot
#: know what a valid call looks like -- but `test_every_member_that_takes_input_is_swept` makes the
#: COVERAGE automatic: a new public member is either listed here, or declared as having nothing to
#: leak, or the suite fails. That is the part the first version of this file only claimed.
_COVERED = {
    "engagement out of scope": "Store.engagement",
    "source index out of scope": "Store.source_documents",
    "unknown document id": "Store.document_path",
    "unknown claim id": "Store.claim",
    "bad specialist": "Store.record_questions",
    "document outside the engagement": "Store.record_questions",
    "question outside the engagement": "Store.record_subagent_run",
    "bad run state": "Store.record_subagent_run",
    "claim document outside the engagement": "Store.record_claims",
    "path outside the root": "SourceLibrary.read",
    "absolute path": "SourceLibrary.read",
    "refused extension": "SourceLibrary.read",
    "refused manifest": "SourceLibrary.read",
    "missing document": "SourceLibrary.read",
    "padded path": "SourceLibrary.read",
    "short quote": "SourceLibrary.verify_quote",
    "overlong quote": "SourceLibrary.verify_quote",
    "empty principal id": "Store.load_principal",
}


def test_no_refusal_echoes_its_input(fixture: Fixture, analyst: Principal) -> None:
    cases = _refusals(fixture, analyst)
    for label, call in cases:
        with pytest.raises(WorkbenchError) as refusal:
            call()
        message = str(refusal.value)
        assert MARKER not in message, f"{label} leaked its input: {message}"
    assert {label for label, _ in cases} == set(_COVERED)


def test_every_member_that_takes_input_is_swept() -> None:
    """The guard that makes the sweep's coverage automatic.

    Shares `_public_callables` with the sponsor sweep so both see classmethods: built on
    `inspect.isfunction`, both missed a deliberately leaky classmethod without a failure.
    """
    from tests.test_sponsor_surface import _public_callables
    from workbench.core.sources import SourceLibrary as Library
    from workbench.core.store import Store

    members = {
        f"{owner.__name__}.{name}"
        for owner in (Store, Library)
        for name in _public_callables(owner)
    }
    uncovered = members - set(_COVERED.values()) - _NOTHING_TO_LEAK
    assert not uncovered, (
        "these public members are not covered by the message sweep: "
        f"{sorted(uncovered)}. Add a case to _refusals/_COVERED, or list it in "
        "_NOTHING_TO_LEAK with the reason it has no caller value to echo."
    )


def test_an_access_refusal_names_no_engagement(analyst: Principal) -> None:
    with pytest.raises(WorkbenchError) as refusal:
        assert_can(analyst, Action.READ_READOUT, Resource(MARKER, EngagementState.FINAL))
    assert MARKER not in str(refusal.value)


def test_a_role_refusal_names_the_closed_sets_only(fixture: Fixture, analyst: Principal) -> None:
    with pytest.raises(WorkbenchError) as refusal:
        fixture.store.finalise(analyst, ACME)
    message = str(refusal.value)
    assert Role.ANALYST.value in message
    assert Action.FINALISE_READOUT.value in message
    assert ACME not in message


# ---- the category mapping ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("error", "category", "retryable"),
    [
        (AccessDenied(), "permission", False),
        (NotFound(), "business", False),
        (InvalidInput(), "validation", False),
        (SourceOutsideRoot(), "permission", False),
        (SourceRefused(), "permission", False),
        (SourceUnreadable(), "business", False),
        (AlreadyFinal(), "business", False),
        (CoverageGapsPresent(), "business", False),
        (StoreCorrupt(), "internal", False),
        (Throttled(), "transient", True),
        (ProviderFailed(), "internal", False),
    ],
)
def test_each_error_maps_to_an_app_17_category(
    error: WorkbenchError, category: str, retryable: bool
) -> None:
    assert error.category.value == category
    assert error.retryable is retryable
    result = error.as_tool_result()
    assert result.is_error is True
    assert result.error_category is not None
    assert result.error_category.value == category
    assert result.is_retryable is retryable


def test_an_unclassified_failure_is_internal_and_not_retried() -> None:
    """A failure nobody classified is not one to try again."""
    category, retryable = classify(RuntimeError("something broke"))
    assert category.value == "internal"
    assert retryable is False


def test_a_timeout_is_transient_and_retryable() -> None:
    category, retryable = classify(TimeoutError())
    assert category.value == "transient"
    assert retryable is True


def test_a_workbench_error_answers_for_itself(tmp_path: Path) -> None:
    library = SourceLibrary(tmp_path, engagement_id=ACME, max_file_bytes=10, max_run_bytes=10)
    try:
        library.read("../escape.md")
    except WorkbenchError as exc:
        assert classify(exc) == (exc.category, exc.retryable)
    else:  # pragma: no cover - the read above always refuses
        pytest.fail("the escape was not refused")
