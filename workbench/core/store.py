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

#: Stamped into `PRAGMA user_version` by `schema.sql` and checked by `Store.open`, so a database
#: from a different schema becomes one stated refusal instead of a column-by-column
#: `sqlite3.OperationalError` with no error category. Bump it with any change to `schema.sql`.
SCHEMA_VERSION = 1

#: Readout states. `draft` until a lead finalises.
READOUT_DRAFT = "draft"
READOUT_FINAL = "final"

#: Free-text caps, enforced at the boundary. Not decoration: a question's text and a claim's text
#: both flow into 20.5's synthesis prompt, which has a 12,000-character input cap of its own, so an
#: unbounded field here is a prompt that silently loses its tail -- or an input that crowds the
#: real evidence out. NUL is rejected outright: SQLite stores it, Postgres cannot, and app 20's
#: sibling repos learned that one as a 500.
MAX_TEXT_CHARS = 2_000
MAX_RATIONALE_CHARS = 1_000

#: Cap per readout JSON section, on the serialised text. `save_readout` is the one boundary whose
#: input is a structure rather than a string, and a boundary without a bound is not one: a
#: 500,000-character `maturity` was accepted, and these sections are what `wb readout` renders.
MAX_SECTION_CHARS = 20_000


def _json_section(value: object, *, field: str) -> str:
    """One readout section, serialised, NUL-free and length-capped, or `InvalidInput`."""
    try:
        encoded = json.dumps(value)
    except (TypeError, ValueError) as exc:
        # A `datetime` or a `Decimal` in a readout section is the near miss 20.5 will make. A raw
        # `TypeError` out of the store has no error category and no field name in it.
        raise InvalidInput(f"{field} is not JSON-serialisable") from exc
    # `json.dumps` escapes a NUL to the six characters `\u0000`, so the raw check alone never
    # fires; both forms are rejected, since a caller may also hand over pre-escaped text.
    if "\x00" in encoded or "\\u0000" in encoded:
        raise InvalidInput(f"{field} contains no NUL byte")
    if len(encoded) > MAX_SECTION_CHARS:
        raise InvalidInput(f"{field} is at most {MAX_SECTION_CHARS} characters when serialised")
    return encoded


def _text(value: str, *, field: str, limit: int) -> str:
    """A free-text field, trimmed, length-capped and NUL-free, or `InvalidInput`.

    The message names the FIELD, never the value: `field` is a schema-derived name supplied by the
    accessor, so a refusal cannot hand a caller's own text back to it.
    """
    trimmed = value.strip()
    if not trimmed:
        raise InvalidInput(f"{field} is required")
    if "\x00" in trimmed:
        raise InvalidInput(f"{field} contains no NUL byte")
    if len(trimmed) > limit:
        raise InvalidInput(f"{field} is at most {limit} characters")
    return trimmed


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
        config: Config,
        *,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._connection = connection
        self._config = config
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
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version not in (0, SCHEMA_VERSION):
            # 0 is "no schema applied yet", which `create_schema` then stamps. Any other value is
            # a database built by a different version of `schema.sql`, and continuing would mean
            # queries failing one column at a time as `sqlite3.OperationalError` -- outside
            # `errors.py`, with no category. This repo ships no migration tool, so the answer is a
            # stated refusal; the demo and the smoke build in a fresh `mkdtemp()` anyway.
            connection.close()
            raise StoreCorrupt("this database was built by a different schema version")
        return cls(connection, config, now=now, new_id=new_id)

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
        """One engagement, including its brief. `READ_DISCOVERY`, so no sponsor reaches it."""
        return self._authorise(principal, Action.READ_DISCOVERY, engagement_id)

    def engagement_summary(
        self, principal: Principal, engagement_id: str
    ) -> tuple[str, str, EngagementState]:
        """`(id, client, state)` and nothing else: what a readout header needs.

        The narrow surface a `sponsor` may have. It deliberately omits `brief` and
        `sponsor_principal`, so rendering a finalised readout for a sponsor never needs
        `engagement()` and therefore never needs `READ_DISCOVERY`.
        """
        engagement = self._authorise(principal, Action.READ_READOUT, engagement_id)
        return engagement.id, engagement.client, engagement.state

    def engagement_ids(self, principal: Principal) -> tuple[str, ...]:
        """The engagements this principal is assigned to, sorted. No row data."""
        return tuple(sorted(principal.engagements))

    # ---- the source index -----------------------------------------------------------------

    def index_sources(
        self, principal: Principal, engagement_id: str, library: SourceLibrary
    ) -> tuple[SourceRef, ...]:
        """Rebuild `source_document` for one engagement from its source library.

        The index is derived, never authored: ids and digests come from the tree, so re-indexing an
        unchanged tree writes the same rows.

        **Upsert, not delete-and-reinsert.** `claim.doc_id` has a foreign key to this table and
        SQLite enforces it immediately, so clearing the engagement's rows first raised a raw
        `sqlite3.IntegrityError` -- outside `errors.py`, so with no `error_category` and no way for
        a caller to react -- the moment a second `wb discover` ran after any claim existed. Which
        is an ordinary sequence, not an edge case.

        A row whose document has disappeared from the tree is deleted **only if no claim cites
        it**. One that is cited stays, because `wb trace` has to resolve the document a claim
        names; reading it then fails as `source_unreadable`, which is the honest answer. Note the
        limit of that: the row records what the document is *now*, because the upsert overwrites
        `sha256` for a document that changed in place -- so it is a record of what a claim pointed
        at only for a document that left the tree. 20.5 re-verifies every quote before synthesis,
        which is where a changed document is actually caught. All in one transaction, so a
        half-updated index can never be followed.
        """
        self._authorise(principal, Action.LIST_SOURCES, engagement_id)
        # The last piece of the owner filter that could otherwise sit in a caller: with the wrong
        # library, this would write another engagement's documents into this index and
        # `document_path` would hand them straight back.
        self._assert_library(library, engagement_id)
        refs = tuple(library.list_documents())
        try:
            with self._transaction() as connection:
                connection.executemany(
                    "INSERT INTO source_document "
                    "(id, engagement_id, path, sha256, bytes, readable, unread_reason) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET path = excluded.path, "
                    "sha256 = excluded.sha256, bytes = excluded.bytes, "
                    "readable = excluded.readable, unread_reason = excluded.unread_reason",
                    [
                        (
                            ref.doc_id,
                            engagement_id,
                            ref.path,
                            ref.sha256,
                            ref.bytes,
                            1 if ref.readable else 0,
                            ref.unread_reason,
                        )
                        for ref in refs
                    ],
                )
                current = {ref.doc_id for ref in refs}
                recorded = {
                    str(row["id"])
                    for row in connection.execute(
                        "SELECT id FROM source_document WHERE engagement_id = ?",
                        (engagement_id,),
                    ).fetchall()
                }
                # One fully parameterised statement per stale id, rather than a generated
                # `IN (...)` list: no SQL text is ever built from data, there is no `IN ()`
                # empty-list special case, and an index is dozens of files. The
                # `NOT IN (SELECT doc_id ...)` is what keeps a row a claim still cites.
                for doc_id in sorted(recorded - current):
                    connection.execute(
                        "DELETE FROM source_document WHERE engagement_id = ? AND id = ? "
                        "AND id NOT IN (SELECT doc_id FROM claim WHERE engagement_id = ?)",
                        (engagement_id, doc_id, engagement_id),
                    )
        except sqlite3.IntegrityError as exc:
            # The one integrity route left here: a row kept because a claim cites it, whose `path`
            # now collides with an incoming row under `UNIQUE (engagement_id, path)`. Reachable
            # only across a change to the id format with a claim already recorded -- a scratch
            # database from an older build -- but mapped rather than left raw, because every other
            # failure in this module carries an `error_category` and this one would not.
            raise StoreCorrupt(
                "the recorded source index cannot be reconciled with this engagement's tree"
            ) from exc
        except sqlite3.OperationalError as exc:
            # A database whose `source_document` predates this schema: `create_schema` is
            # `IF NOT EXISTS`, so it adds no column to an existing table. `Store.open`'s version
            # check catches this for anything stamped; this catches a database stamped 0 by a
            # build that had no stamp.
            raise StoreCorrupt("the recorded source index does not match this schema") from exc
        return refs

    def source_documents(self, principal: Principal, engagement_id: str) -> tuple[SourceRef, ...]:
        """The recorded source index for one engagement, sorted by path.

        Readability comes from the stored columns, not from an assumption. The first version
        returned `readable=True` and no reason for every row, so `wb sources list` -- whose job
        the spec states as "the source index, with sizes **and what is unreadable**" -- would have
        reported an undecodable document as fine, with nothing in 20.6 to reveal it.
        """
        self._authorise(principal, Action.LIST_SOURCES, engagement_id)
        rows = self._connection.execute(
            "SELECT id, path, sha256, bytes, readable, unread_reason FROM source_document "
            "WHERE engagement_id = ? ORDER BY path",
            (engagement_id,),
        ).fetchall()
        return tuple(
            SourceRef(
                doc_id=str(row["id"]),
                path=str(row["path"]),
                bytes=int(row["bytes"]),
                sha256=str(row["sha256"]),
                readable=bool(row["readable"]),
                unread_reason=(None if row["unread_reason"] is None else str(row["unread_reason"])),
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
        checked: list[NewQuestion] = []
        for question in planned:
            if question.specialist not in SPECIALISTS:
                raise InvalidInput("specialist is outside the closed set")
            if not question.doc_ids:
                raise InvalidInput("a question names at least one document")
            checked.append(
                NewQuestion(
                    text=_text(question.text, field="question.text", limit=MAX_TEXT_CHARS),
                    specialist=question.specialist,
                    doc_ids=tuple(question.doc_ids),
                    rationale=_text(
                        question.rationale,
                        field="question.rationale",
                        limit=MAX_RATIONALE_CHARS,
                    ),
                )
            )
        planned = checked

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
        """This engagement's questions, in plan order. `READ_DISCOVERY`: not a sponsor's to see."""
        self._authorise(principal, Action.READ_DISCOVERY, engagement_id)
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
        self._authorise(principal, Action.READ_DISCOVERY, engagement_id)
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

        **A claim may only cite a document its own question named.** Scoped context passing is the
        boundary: a subagent is handed its question's documents and nothing else, so a finding
        citing a document that question never named did not come from what the subagent was shown.
        Checking only "is it in this engagement" would let one subagent's answer reach across to
        another's evidence, which is the same leak as crossing engagements, one level down.

        `claim.text` and `claim.quote` are each capped at `MAX_TEXT_CHARS`, so one claim can be
        twice that. Deliberate -- a quote must be able to be long enough to be worth verifying --
        and it means the caps bound a claim at 4,000 characters, not 2,000; 20.5's own synthesis
        cap is what bounds how many claims reach a prompt.
        """
        self._authorise(principal, Action.RUN_DISCOVERY, engagement_id)
        self._assert_library(library, engagement_id)
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
                text = _text(claim.text, field="claim.text", limit=MAX_TEXT_CHARS)
                quote = _text(claim.quote, field="claim.quote", limit=MAX_TEXT_CHARS)
                self._assert_question_in_engagement(connection, engagement_id, claim.question_id)
                if claim.doc_id not in self._question_doc_ids(connection, claim.question_id):
                    raise InvalidInput("a claim cites a document its question did not name")
                path = paths.get(claim.doc_id)
                if path is None:
                    raise InvalidInput("a claim names a document outside this engagement")
                verified = _quote_checks_out(library, path, quote)
                claim_id = self._new_id()
                connection.execute(
                    "INSERT INTO claim "
                    "(id, engagement_id, question_id, text, doc_id, quote, verified, confidence) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        claim_id,
                        engagement_id,
                        claim.question_id,
                        text,
                        claim.doc_id,
                        quote,
                        1 if verified else 0,
                        claim.confidence,
                    ),
                )
                recorded.append(
                    Claim(
                        id=claim_id,
                        engagement_id=engagement_id,
                        question_id=claim.question_id,
                        text=text,
                        doc_id=claim.doc_id,
                        quote=quote,
                        verified=verified,
                        confidence=claim.confidence,
                    )
                )
        return tuple(recorded)

    def claims(
        self, principal: Principal, engagement_id: str, *, verified_only: bool = False
    ) -> tuple[Claim, ...]:
        """This engagement's claims, with their verbatim quotes. `verified_only` is what synthesis
        reads.

        `READ_DISCOVERY`, not `READ_READOUT`. A claim and its quote are the evidence behind the
        readout, not the readout: a sponsor that could call this would hold, in bulk, exactly what
        the `TRACE_CLAIM` refusal beside it exists to withhold -- and would get the *unverified*
        claims too, which are the ones the product exists to keep out of a readout.
        """
        self._authorise(principal, Action.READ_DISCOVERY, engagement_id)
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
                    _json_section(maturity, field="readout.maturity"),
                    _json_section(outcomes, field="readout.outcomes"),
                    None if roi is None else _json_section(roi, field="readout.roi"),
                    _json_section(roadmap, field="readout.roadmap"),
                    _json_section(coverage, field="readout.coverage"),
                    engagement_id,
                ),
            )
        return self.readout(principal, engagement_id)

    def failed_run_question_ids(self, principal: Principal, engagement_id: str) -> tuple[str, ...]:
        """The questions whose latest subagent run failed: the readout's named coverage gaps.

        Latest, not any: a question retried successfully is answered. The latest run per question
        is the highest `rowid`, which is insertion order.
        """
        self._authorise(principal, Action.READ_DISCOVERY, engagement_id)
        return _failed_question_ids(self._connection, engagement_id)

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

        The gap check runs **inside** the write transaction, after `BEGIN IMMEDIATE`. Outside it,
        a subagent run that failed between the check and the insert produced a `final` readout with
        an unaccepted gap in it -- the one state `--accept-gaps` exists to make impossible.
        """
        self._authorise(principal, Action.FINALISE_READOUT, engagement_id)
        stamp = self._now().isoformat()
        try:
            with self._transaction() as connection:
                gaps = _failed_question_ids(connection, engagement_id)
                if gaps and not accept_gaps:
                    raise CoverageGapsPresent(
                        f"{len(gaps)} question(s) have a failed subagent run; "
                        "finalising over them requires accept_gaps"
                    )
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
        self._authorise(principal, Action.READ_DISCOVERY, engagement_id)
        row = self._connection.execute(
            "SELECT accept_gaps FROM finalisation WHERE engagement_id = ?", (engagement_id,)
        ).fetchone()
        if row is None:
            raise NotFound("this engagement has not been finalised")
        return bool(row["accept_gaps"])

    # ---- helpers --------------------------------------------------------------------------

    def _assert_library(self, library: SourceLibrary, engagement_id: str) -> None:
        """Refuse a library that is not this engagement's, by label **and** by resolved root.

        The label alone was not enough: `SourceLibrary(northwind_root,
        engagement_id="acme-p2p")` satisfied it and then verified a quote against the other
        engagement's file. The root is the fact; the label is a claim about it.
        """
        if library.engagement_id != engagement_id:
            raise InvalidInput("the source library is rooted at a different engagement")
        expected = self._config.engagement_sources_root(engagement_id)
        try:
            resolved = expected.resolve()
        except (OSError, RuntimeError) as exc:
            raise StoreCorrupt("the configured source root could not be resolved") from exc
        if library.root != resolved:
            raise InvalidInput("the source library is rooted outside this engagement's source root")

    @staticmethod
    def _question_doc_ids(connection: sqlite3.Connection, question_id: str) -> frozenset[str]:
        """The documents one question named, as recorded in its own row."""
        row = connection.execute(
            "SELECT doc_ids FROM question WHERE id = ?", (question_id,)
        ).fetchone()
        if row is None:
            raise InvalidInput("a question id outside this engagement")
        return frozenset(_json_string_list(str(row["doc_ids"])))

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


def _failed_question_ids(connection: sqlite3.Connection, engagement_id: str) -> tuple[str, ...]:
    """The questions whose LATEST subagent run failed. Takes a connection so `finalise` can run it
    inside its own transaction and `failed_run_question_ids` can run it outside one."""
    rows = connection.execute(
        "SELECT q.id AS question_id, ("
        "  SELECT r.state FROM subagent_run AS r "
        "  WHERE r.question_id = q.id ORDER BY r.rowid DESC LIMIT 1"
        ") AS latest_state "
        "FROM question AS q WHERE q.engagement_id = ? ORDER BY q.seq",
        (engagement_id,),
    ).fetchall()
    return tuple(str(row["question_id"]) for row in rows if str(row["latest_state"]) == "failed")


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
