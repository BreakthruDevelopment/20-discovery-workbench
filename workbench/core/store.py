"""The engagement store: the only module in this repo that opens the database.

Two rules are kept here rather than asked of callers, because a rule a caller can forget is not a
rule:

1. **The `engagement_id` filter is inside every query.** No accessor takes a raw WHERE clause and
   none returns a cursor. A caller names an engagement; the SQL always filters on it.
2. **`assert_can` runs before any row is read or written**, on every accessor, with the engagement's
   own state. The order matters: scope first, then role, then the row -- so a cross-engagement read
   is refused before it touches data, and a refusal carries no row in it.

`load_principal` resolves assignment once, from `engagement_principal` for an analyst or a lead and
from `engagement.sponsor_principal` for a sponsor, into the `Principal` that `assert_can` then reads
without a database. Nothing else resolves assignment, so there is one answer to "which engagements
is this principal in".

Rows come back as frozen dataclasses, never as `sqlite3.Row`, so a caller cannot reach a column the
accessor did not mean to give it and nothing downstream depends on column order.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self

from agent_container.core.tool import ErrorCategory

from workbench.core.config import Config
from workbench.core.errors import (
    AlreadyFinal,
    CoverageGapsPresent,
    InvalidInput,
    NotFound,
    StoreCorrupt,
    WorkbenchError,
)
from workbench.core.principals import (
    Action,
    EngagementState,
    Principal,
    Resource,
    Role,
    assert_can,
)
from workbench.core.sources import SourceLibrary, SourceRef

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_SEED_PATH = Path(__file__).with_name("seed.sql")

#: The closed set of specialists a question may name (spec, `discovery-plan` output schema).
SPECIALISTS = frozenset({"process", "systems", "data", "change"})

#: Readout states. `draft` until a lead finalises.
READOUT_DRAFT = "draft"
READOUT_FINAL = "final"


@dataclass(frozen=True, slots=True)
class Engagement:
    id: str
    client: str
    brief: str
    sponsor_principal: str
    state: EngagementState


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    engagement_id: str
    seq: int
    text: str
    specialist: str
    doc_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class SubagentRun:
    id: str
    question_id: str
    state: str
    error_category: str | None
    is_retryable: bool
    turns: int
    tokens: int


@dataclass(frozen=True, slots=True)
class Claim:
    id: str
    engagement_id: str
    question_id: str
    text: str
    doc_id: str
    quote: str
    verified: bool
    confidence: float


@dataclass(frozen=True, slots=True)
class Readout:
    engagement_id: str
    id: str
    state: str
    maturity: object
    outcomes: object
    roi: object | None
    roadmap: object
    coverage: object
    finalised_by: str | None


@dataclass(frozen=True, slots=True)
class NewQuestion:
    """One planned question, as the coordinator hands it over. `seq` is assigned by the store."""

    text: str
    specialist: str
    doc_ids: Sequence[str]
    rationale: str


@dataclass(frozen=True, slots=True)
class NewClaim:
    """One finding, as a subagent's answer hands it over.

    `verified` is **not** here: the store sets it from `SourceLibrary.verify_quote`, so no caller
    and no model can assert that a quote checks out.
    """

    question_id: str
    text: str
    doc_id: str
    quote: str
    confidence: float


class Store:
    """An open engagement database. Use as a context manager, one per command run."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._connection = connection
        self._now = now
        self._new_id = new_id

    # ---- opening and building -------------------------------------------------------------

    @classmethod
    def open(
        cls,
        config: Config,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> Self:
        """Open (and create, if absent) the database at the configured path.

        `isolation_level=None` turns off the driver's implicit transaction handling so the explicit
        `BEGIN IMMEDIATE` in `_transaction` is the only transaction, which is what makes the
        finalise guard a real one rather than two statements that happen to be adjacent.
        """
        path = config.database_path
        if path.parent != Path():
            path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        return cls(connection, now=now, new_id=new_id)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def create_schema(self) -> None:
        """Apply `schema.sql`. Idempotent: every statement is `IF NOT EXISTS`."""
        self._connection.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))

    def seed(self) -> None:
        """Apply `seed.sql`. Deterministic and idempotent (`INSERT OR IGNORE`)."""
        self._connection.executescript(_SEED_PATH.read_text(encoding="utf-8"))

    def build(self) -> None:
        """Schema then seed: how a fresh database is made, in the demo, the tests and the smoke."""
        self.create_schema()
        self.seed()

    class _Transaction:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection

        def __enter__(self) -> sqlite3.Connection:
            self._connection.execute("BEGIN IMMEDIATE")
            return self._connection

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            if exc_type is None:
                self._connection.execute("COMMIT")
            else:
                self._connection.execute("ROLLBACK")

    def _transaction(self) -> Store._Transaction:
        return Store._Transaction(self._connection)

    # ---- principals -----------------------------------------------------------------------

    def load_principal(self, principal_id: str, role: Role) -> Principal:
        """Resolve one principal's engagement assignment. The only place assignment is read.

        A sponsor's engagements come from `engagement.sponsor_principal`; an analyst's or a lead's
        from `engagement_principal`, matched on the role as well as the id, so a principal assigned
        as an analyst cannot act as a lead by passing a different `--role`.
        """
        if not principal_id.strip():
            raise InvalidInput("a principal id is required")
        if role is Role.SPONSOR:
            rows = self._connection.execute(
                "SELECT id FROM engagement WHERE sponsor_principal = ?", (principal_id,)
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT engagement_id AS id FROM engagement_principal "
                "WHERE principal_id = ? AND role = ?",
                (principal_id, role.value),
            ).fetchall()
        return Principal(
            id=principal_id, role=role, engagements=frozenset(str(row["id"]) for row in rows)
        )

    # ---- engagements ----------------------------------------------------------------------

    def _engagement_row(self, engagement_id: str) -> Engagement:
        """The engagement, with no access check. Private: every public accessor checks first."""
        row = self._connection.execute(
            "SELECT id, client, brief, sponsor_principal, state FROM engagement WHERE id = ?",
            (engagement_id,),
        ).fetchone()
        if row is None:
            # Unreachable through a public accessor: `assert_can` has already refused any
            # engagement outside the principal's assignment, and assignment is read from this same
            # table. A row that vanished between the two is a corrupt store, not a missing one.
            raise StoreCorrupt("an assigned engagement is absent from the engagement table")
        return Engagement(
            id=str(row["id"]),
            client=str(row["client"]),
            brief=str(row["brief"]),
            sponsor_principal=str(row["sponsor_principal"]),
            state=EngagementState(str(row["state"])),
        )

    def _authorise(self, principal: Principal, action: Action, engagement_id: str) -> Engagement:
        """Scope, then role, then the row. Returns the engagement so callers need no second read.

        `assert_can` is called with the engagement id alone first -- through a `Resource` whose
        state is read only after the scope check passes -- so a principal outside the engagement is
        refused without a query.
        """
        if engagement_id not in principal.engagements:
            assert_can(principal, action, Resource(engagement_id, EngagementState.OPEN))
            raise StoreCorrupt("the scope check passed for an unassigned engagement")
        engagement = self._engagement_row(engagement_id)
        assert_can(principal, action, Resource(engagement.id, engagement.state))
        return engagement

    def engagement(self, principal: Principal, engagement_id: str) -> Engagement:
        """One engagement, for a principal that may read its readout."""
        return self._authorise(principal, Action.READ_READOUT, engagement_id)

    def engagement_ids(self, principal: Principal) -> tuple[str, ...]:
        """The engagements this principal is assigned to, sorted. No row data."""
        return tuple(sorted(principal.engagements))

    # ---- the source index -----------------------------------------------------------------

    def index_sources(
        self, principal: Principal, engagement_id: str, library: SourceLibrary
    ) -> tuple[SourceRef, ...]:
        """Rebuild `source_document` for one engagement from its source library.

        The index is derived, never authored: ids and digests come from the tree, so re-indexing an
        unchanged tree writes the same rows. Rows for documents that have disappeared are deleted,
        which is why this runs in one transaction -- a half-updated index would let a stale
        `doc_id` be followed.
        """
        self._authorise(principal, Action.LIST_SOURCES, engagement_id)
        refs = tuple(library.list_documents())
        with self._transaction() as connection:
            connection.execute(
                "DELETE FROM source_document WHERE engagement_id = ?", (engagement_id,)
            )
            connection.executemany(
                "INSERT INTO source_document (id, engagement_id, path, sha256, bytes) "
                "VALUES (?, ?, ?, ?, ?)",
                [(ref.doc_id, engagement_id, ref.path, ref.sha256, ref.bytes) for ref in refs],
            )
        return refs

    def source_documents(self, principal: Principal, engagement_id: str) -> tuple[SourceRef, ...]:
        """The recorded source index for one engagement, sorted by path."""
        self._authorise(principal, Action.LIST_SOURCES, engagement_id)
        rows = self._connection.execute(
            "SELECT id, path, sha256, bytes FROM source_document "
            "WHERE engagement_id = ? ORDER BY path",
            (engagement_id,),
        ).fetchall()
        return tuple(
            SourceRef(
                doc_id=str(row["id"]),
                path=str(row["path"]),
                bytes=int(row["bytes"]),
                sha256=str(row["sha256"]),
                readable=True,
            )
            for row in rows
        )

    def document_path(self, principal: Principal, engagement_id: str, doc_id: str) -> str:
        """The relative path of one document of this engagement, or `NotFound`.

        This is the re-check the spec asks for: every `doc_id` a model returns goes through here
        before it is followed, and a `doc_id` belonging to another engagement is simply absent,
        because the query filters on `engagement_id`.
        """
        self._authorise(principal, Action.READ_SOURCE, engagement_id)
        row = self._connection.execute(
            "SELECT path FROM source_document WHERE engagement_id = ? AND id = ?",
            (engagement_id, doc_id),
        ).fetchone()
        if row is None:
            raise NotFound("no such document in this engagement's source index")
        return str(row["path"])

    # ---- questions ------------------------------------------------------------------------

    def record_questions(
        self, principal: Principal, engagement_id: str, questions: Iterable[NewQuestion]
    ) -> tuple[Question, ...]:
        """Append a plan's questions. `seq` continues this engagement's existing numbering.

        Every `doc_ids` entry is checked against this engagement's `source_document` rows inside
        the transaction, so a question naming another engagement's document is refused here --
        before any subagent runs -- rather than trusted and dropped later.
        """
        self._authorise(principal, Action.RUN_DISCOVERY, engagement_id)
        planned = list(questions)
        for question in planned:
            if question.specialist not in SPECIALISTS:
                raise InvalidInput("specialist is outside the closed set")
            if not question.doc_ids:
                raise InvalidInput("a question names at least one document")
            if not question.text.strip() or not question.rationale.strip():
                raise InvalidInput("a question carries text and a rationale")

        recorded: list[Question] = []
        with self._transaction() as connection:
            known = {
                str(row["id"])
                for row in connection.execute(
                    "SELECT id FROM source_document WHERE engagement_id = ?", (engagement_id,)
                ).fetchall()
            }
            next_seq = 1 + int(
                connection.execute(
                    "SELECT COALESCE(MAX(seq), 0) FROM question WHERE engagement_id = ?",
                    (engagement_id,),
                ).fetchone()[0]
            )
            for offset, question in enumerate(planned):
                if not set(question.doc_ids) <= known:
                    raise InvalidInput("a question names a document outside this engagement")
                question_id = self._new_id()
                seq = next_seq + offset
                doc_ids = tuple(question.doc_ids)
                connection.execute(
                    "INSERT INTO question "
                    "(id, engagement_id, seq, text, specialist, doc_ids, rationale) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        question_id,
                        engagement_id,
                        seq,
                        question.text,
                        question.specialist,
                        json.dumps(list(doc_ids)),
                        question.rationale,
                    ),
                )
                recorded.append(
                    Question(
                        id=question_id,
                        engagement_id=engagement_id,
                        seq=seq,
                        text=question.text,
                        specialist=question.specialist,
                        doc_ids=doc_ids,
                        rationale=question.rationale,
                    )
                )
        return tuple(recorded)

    def questions(self, principal: Principal, engagement_id: str) -> tuple[Question, ...]:
        """This engagement's questions, in plan order."""
        self._authorise(principal, Action.READ_READOUT, engagement_id)
        rows = self._connection.execute(
            "SELECT id, engagement_id, seq, text, specialist, doc_ids, rationale "
            "FROM question WHERE engagement_id = ? ORDER BY seq",
            (engagement_id,),
        ).fetchall()
        return tuple(
            Question(
                id=str(row["id"]),
                engagement_id=str(row["engagement_id"]),
                seq=int(row["seq"]),
                text=str(row["text"]),
                specialist=str(row["specialist"]),
                doc_ids=tuple(_json_string_list(str(row["doc_ids"]))),
                rationale=str(row["rationale"]),
            )
            for row in rows
        )

    # ---- subagent runs --------------------------------------------------------------------

    def record_subagent_run(
        self,
        principal: Principal,
        engagement_id: str,
        *,
        question_id: str,
        state: str,
        turns: int,
        tokens: int,
        error_category: ErrorCategory | None = None,
        is_retryable: bool = False,
    ) -> SubagentRun:
        """Record what one subagent did, including that it failed.

        A failure is a row, not an exception that unwinds the run: statement 5.3 is the record
        existing. `question_id` is checked against this engagement, so a run cannot be attached to
        another engagement's question.
        """
        self._authorise(principal, Action.RUN_DISCOVERY, engagement_id)
        if state not in {"ok", "failed"}:
            raise InvalidInput("a subagent run state is either ok or failed")
        if state == "failed" and error_category is None:
            raise InvalidInput("a failed subagent run carries an error category")
        if state == "ok" and (error_category is not None or is_retryable):
            raise InvalidInput("only a failed subagent run carries an error category or a retry")
        run_id = self._new_id()
        with self._transaction() as connection:
            self._assert_question_in_engagement(connection, engagement_id, question_id)
            connection.execute(
                "INSERT INTO subagent_run "
                "(id, question_id, state, error_category, is_retryable, turns, tokens) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    question_id,
                    state,
                    None if error_category is None else error_category.value,
                    1 if is_retryable else 0,
                    turns,
                    tokens,
                ),
            )
        return SubagentRun(
            id=run_id,
            question_id=question_id,
            state=state,
            error_category=None if error_category is None else error_category.value,
            is_retryable=is_retryable,
            turns=turns,
            tokens=tokens,
        )

    def subagent_runs(self, principal: Principal, engagement_id: str) -> tuple[SubagentRun, ...]:
        """Every subagent run of this engagement, joined through `question` for the owner filter."""
        self._authorise(principal, Action.READ_READOUT, engagement_id)
        rows = self._connection.execute(
            "SELECT r.id, r.question_id, r.state, r.error_category, r.is_retryable, "
            "r.turns, r.tokens FROM subagent_run AS r "
            "JOIN question AS q ON q.id = r.question_id "
            "WHERE q.engagement_id = ? ORDER BY q.seq, r.rowid",
            (engagement_id,),
        ).fetchall()
        return tuple(
            SubagentRun(
                id=str(row["id"]),
                question_id=str(row["question_id"]),
                state=str(row["state"]),
                error_category=(
                    None if row["error_category"] is None else str(row["error_category"])
                ),
                is_retryable=bool(row["is_retryable"]),
                turns=int(row["turns"]),
                tokens=int(row["tokens"]),
            )
            for row in rows
        )

    # ---- claims ---------------------------------------------------------------------------

    def record_claims(
        self,
        principal: Principal,
        engagement_id: str,
        claims: Iterable[NewClaim],
        library: SourceLibrary,
    ) -> tuple[Claim, ...]:
        """Record findings, verifying every quote in code before the row is written.

        `verified` is computed here, from `SourceLibrary.verify_quote` against the document the
        claim itself names, resolved through this engagement's `source_document` index. A claim
        quoting text that is not in its document is still recorded -- `wb trace` must be able to
        show it, and 20.5 excludes it from synthesis -- but it is recorded as `verified: false`,
        and nothing a caller or a model passes in can change that.
        """
        self._authorise(principal, Action.RUN_DISCOVERY, engagement_id)
        incoming = list(claims)
        recorded: list[Claim] = []
        with self._transaction() as connection:
            paths = {
                str(row["id"]): str(row["path"])
                for row in connection.execute(
                    "SELECT id, path FROM source_document WHERE engagement_id = ?",
                    (engagement_id,),
                ).fetchall()
            }
            for claim in incoming:
                if not 0.0 <= claim.confidence <= 1.0:
                    raise InvalidInput("confidence is between 0 and 1")
                if not claim.text.strip():
                    raise InvalidInput("a claim carries text")
                self._assert_question_in_engagement(connection, engagement_id, claim.question_id)
                path = paths.get(claim.doc_id)
                if path is None:
                    raise InvalidInput("a claim names a document outside this engagement")
                verified = _quote_checks_out(library, path, claim.quote)
                claim_id = self._new_id()
                connection.execute(
                    "INSERT INTO claim "
                    "(id, engagement_id, question_id, text, doc_id, quote, verified, confidence) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        claim_id,
                        engagement_id,
                        claim.question_id,
                        claim.text,
                        claim.doc_id,
                        claim.quote,
                        1 if verified else 0,
                        claim.confidence,
                    ),
                )
                recorded.append(
                    Claim(
                        id=claim_id,
                        engagement_id=engagement_id,
                        question_id=claim.question_id,
                        text=claim.text,
                        doc_id=claim.doc_id,
                        quote=claim.quote,
                        verified=verified,
                        confidence=claim.confidence,
                    )
                )
        return tuple(recorded)

    def claims(
        self, principal: Principal, engagement_id: str, *, verified_only: bool = False
    ) -> tuple[Claim, ...]:
        """This engagement's claims. `verified_only` is what synthesis reads."""
        self._authorise(principal, Action.READ_READOUT, engagement_id)
        if verified_only:
            rows = self._connection.execute(
                "SELECT id, engagement_id, question_id, text, doc_id, quote, verified, confidence "
                "FROM claim WHERE engagement_id = ? AND verified = 1 ORDER BY rowid",
                (engagement_id,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT id, engagement_id, question_id, text, doc_id, quote, verified, confidence "
                "FROM claim WHERE engagement_id = ? ORDER BY rowid",
                (engagement_id,),
            ).fetchall()
        return tuple(_claim_from_row(row) for row in rows)

    def claim(self, principal: Principal, claim_id: str) -> Claim:
        """One claim by id, for `wb trace`.

        The owning engagement is resolved first and then authorised, so a claim id belonging to an
        engagement this principal is not in is refused with `access_denied` and no row data. A
        claim id that exists nowhere is `not_found`.
        """
        row = self._connection.execute(
            "SELECT engagement_id FROM claim WHERE id = ?", (claim_id,)
        ).fetchone()
        if row is None:
            raise NotFound("no such claim")
        engagement_id = str(row["engagement_id"])
        self._authorise(principal, Action.TRACE_CLAIM, engagement_id)
        full = self._connection.execute(
            "SELECT id, engagement_id, question_id, text, doc_id, quote, verified, confidence "
            "FROM claim WHERE engagement_id = ? AND id = ?",
            (engagement_id, claim_id),
        ).fetchone()
        if full is None:
            raise NotFound("no such claim")
        return _claim_from_row(full)

    # ---- the readout ----------------------------------------------------------------------

    def readout(self, principal: Principal, engagement_id: str) -> Readout:
        """This engagement's readout. The sponsor's only reachable row, and only once final."""
        self._authorise(principal, Action.READ_READOUT, engagement_id)
        row = self._connection.execute(
            "SELECT engagement_id, id, state, maturity_json, outcomes_json, roi_json, "
            "roadmap_json, coverage_json, finalised_by FROM readout WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()
        if row is None:
            raise NotFound("this engagement has no readout")
        return Readout(
            engagement_id=str(row["engagement_id"]),
            id=str(row["id"]),
            state=str(row["state"]),
            maturity=json.loads(str(row["maturity_json"])),
            outcomes=json.loads(str(row["outcomes_json"])),
            roi=None if row["roi_json"] is None else json.loads(str(row["roi_json"])),
            roadmap=json.loads(str(row["roadmap_json"])),
            coverage=json.loads(str(row["coverage_json"])),
            finalised_by=None if row["finalised_by"] is None else str(row["finalised_by"]),
        )

    def save_readout(
        self,
        principal: Principal,
        engagement_id: str,
        *,
        maturity: object,
        outcomes: object,
        roadmap: object,
        coverage: object,
        roi: object | None = None,
    ) -> Readout:
        """Replace the draft readout's content. Refused once the readout is final.

        `roi` defaults to `None`, which is the shape the track's first named cut takes: dropping the
        ROI model leaves a null in a nullable column and costs no migration.
        """
        self._authorise(principal, Action.RUN_DISCOVERY, engagement_id)
        with self._transaction() as connection:
            state = connection.execute(
                "SELECT state FROM readout WHERE engagement_id = ?", (engagement_id,)
            ).fetchone()
            if state is None:
                raise NotFound("this engagement has no readout")
            if str(state["state"]) == READOUT_FINAL:
                raise AlreadyFinal("a finalised readout is not rewritten")
            connection.execute(
                "UPDATE readout SET maturity_json = ?, outcomes_json = ?, roi_json = ?, "
                "roadmap_json = ?, coverage_json = ? WHERE engagement_id = ?",
                (
                    json.dumps(maturity),
                    json.dumps(outcomes),
                    None if roi is None else json.dumps(roi),
                    json.dumps(roadmap),
                    json.dumps(coverage),
                    engagement_id,
                ),
            )
        return self.readout(principal, engagement_id)

    def failed_run_question_ids(self, principal: Principal, engagement_id: str) -> tuple[str, ...]:
        """The questions whose latest subagent run failed: the readout's named coverage gaps.

        Latest, not any: a question retried successfully is answered. The latest run per question
        is the highest `rowid`, which is insertion order.
        """
        self._authorise(principal, Action.READ_READOUT, engagement_id)
        rows = self._connection.execute(
            "SELECT q.id AS question_id, ("
            "  SELECT r.state FROM subagent_run AS r "
            "  WHERE r.question_id = q.id ORDER BY r.rowid DESC LIMIT 1"
            ") AS latest_state "
            "FROM question AS q WHERE q.engagement_id = ? ORDER BY q.seq",
            (engagement_id,),
        ).fetchall()
        return tuple(
            str(row["question_id"]) for row in rows if str(row["latest_state"]) == "failed"
        )

    def finalise(
        self, principal: Principal, engagement_id: str, *, accept_gaps: bool = False
    ) -> Readout:
        """Mark the readout final. `lead` only, once, and not over gaps unless they are accepted.

        Three refusals, each in its proper place:

        * **Role.** `assert_can` refuses anyone but a `lead`.
        * **Gaps.** A question whose latest run failed is a coverage gap; finalising over one needs
          `accept_gaps`, and the fact that it was given is recorded in `finalisation`.
        * **Twice.** `finalisation.engagement_id` is the primary key, so a second finalise is
          refused by the database. The `IntegrityError` is mapped to `AlreadyFinal` here; no caller
          checks "is it already final" and then acts, which is the check that races.
        """
        self._authorise(principal, Action.FINALISE_READOUT, engagement_id)
        gaps = self.failed_run_question_ids(principal, engagement_id)
        if gaps and not accept_gaps:
            raise CoverageGapsPresent(
                f"{len(gaps)} question(s) have a failed subagent run; "
                "finalising over them requires accept_gaps"
            )
        stamp = self._now().isoformat()
        try:
            with self._transaction() as connection:
                connection.execute(
                    "INSERT INTO finalisation "
                    "(engagement_id, finalised_by, accept_gaps, finalised_at) "
                    "VALUES (?, ?, ?, ?)",
                    (engagement_id, principal.id, 1 if accept_gaps else 0, stamp),
                )
                connection.execute(
                    "UPDATE readout SET state = ?, finalised_by = ? WHERE engagement_id = ?",
                    (READOUT_FINAL, principal.id, engagement_id),
                )
                connection.execute(
                    "UPDATE engagement SET state = ? WHERE id = ?",
                    (EngagementState.FINAL.value, engagement_id),
                )
        except sqlite3.IntegrityError as exc:
            raise AlreadyFinal("this engagement's readout is already final") from exc
        return self.readout(principal, engagement_id)

    def finalisation_accepted_gaps(self, principal: Principal, engagement_id: str) -> bool:
        """Whether this engagement was finalised with `--accept-gaps`. `NotFound` if it is open."""
        self._authorise(principal, Action.READ_READOUT, engagement_id)
        row = self._connection.execute(
            "SELECT accept_gaps FROM finalisation WHERE engagement_id = ?", (engagement_id,)
        ).fetchone()
        if row is None:
            raise NotFound("this engagement has not been finalised")
        return bool(row["accept_gaps"])

    # ---- helpers --------------------------------------------------------------------------

    @staticmethod
    def _assert_question_in_engagement(
        connection: sqlite3.Connection, engagement_id: str, question_id: str
    ) -> None:
        row = connection.execute(
            "SELECT 1 FROM question WHERE engagement_id = ? AND id = ?",
            (engagement_id, question_id),
        ).fetchone()
        if row is None:
            raise InvalidInput("a question id outside this engagement")


def _claim_from_row(row: sqlite3.Row) -> Claim:
    return Claim(
        id=str(row["id"]),
        engagement_id=str(row["engagement_id"]),
        question_id=str(row["question_id"]),
        text=str(row["text"]),
        doc_id=str(row["doc_id"]),
        quote=str(row["quote"]),
        verified=bool(row["verified"]),
        confidence=float(row["confidence"]),
    )


def _json_string_list(raw: str) -> list[str]:
    """Decode a stored JSON array of strings, or report a corrupt store."""
    value = json.loads(raw)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise StoreCorrupt("a stored doc_ids column is not a JSON array of strings")
    return [str(item) for item in value]


def _quote_checks_out(library: SourceLibrary, path: str, quote: str) -> bool:
    """`verify_quote`, with its refusals folded into `False`.

    A quote too short, too long or naming an unreadable document is not verified; it is also not an
    exception that abandons the whole discovery run, because one bad finding among eight must not
    cost the other seven. The claim lands `verified: false` and `wb trace` shows it.
    """
    try:
        return library.verify_quote(path, quote)
    except WorkbenchError:
        return False
