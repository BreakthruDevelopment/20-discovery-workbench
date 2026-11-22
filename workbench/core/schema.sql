-- The engagement store. Built by `store.py`, which is the only module that opens this database.
--
-- Wave 1 owns this file: it creates EVERY table in the spec's data model, so no later slice needs a
-- schema change. `STRICT` on every table (SQLite 3.37+) makes a column's declared type an actual
-- constraint rather than a suggestion, and the CHECK constraints below carry the closed sets --
-- role, state, specialist, error category -- so a bad value is refused by the database even if some
-- future caller reaches it without going through the typed accessors.
--
-- `engagement_id` is the owner column. Every read in `store.py` filters on it; the schema backs
-- that up with foreign keys so a row cannot point at an engagement that does not exist.

CREATE TABLE IF NOT EXISTS engagement (
    id                TEXT PRIMARY KEY,
    client            TEXT NOT NULL,
    brief             TEXT NOT NULL,
    sponsor_principal TEXT NOT NULL,
    state             TEXT NOT NULL CHECK (state IN ('open', 'final'))
) STRICT;

-- Analyst and lead assignment. The spec states the rule ("an `analyst` reaches only engagements it
-- is assigned to") but its data-model table has no home for it, so wave 1 adds this one rather than
-- leaving a stated access rule unrepresentable -- and adds it now, so no later slice needs a schema
-- change for it either. A sponsor is NOT listed here: `engagement.sponsor_principal` is the single
-- home for that link, and the CHECK below makes storing a sponsor twice impossible rather than
-- merely discouraged.
CREATE TABLE IF NOT EXISTS engagement_principal (
    engagement_id TEXT NOT NULL REFERENCES engagement (id),
    principal_id  TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('analyst', 'lead')),
    PRIMARY KEY (engagement_id, principal_id)
) STRICT;

-- An index over `sources/<engagement id>/`, built by `store.index_sources` from the source library.
-- Contents are never stored: a document is read through `sources.py` every time, so there is one
-- copy of the evidence and `verify_quote` cannot be fooled by a stale one.
CREATE TABLE IF NOT EXISTS source_document (
    id            TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagement (id),
    path          TEXT NOT NULL,
    sha256        TEXT NOT NULL,
    bytes         INTEGER NOT NULL CHECK (bytes >= 0),
    -- Readability is PERSISTED, not re-derived. `wb sources list` is "the source index, with sizes
    -- and what is unreadable", and it is a read command: it must not open every file again to find
    -- out, and it must not quietly report everything readable because the column was missing. An
    -- unreadable document always carries its reason and never the other way round, so the two
    -- columns cannot drift apart. A file that could not be read at all has no digest, which is the
    -- only case an empty sha256 is allowed.
    readable      INTEGER NOT NULL CHECK (readable IN (0, 1)),
    unread_reason TEXT,
    CHECK ((readable = 0) = (unread_reason IS NOT NULL)),
    CHECK (readable = 0 OR length(sha256) = 64)
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS source_document_engagement_path
    ON source_document (engagement_id, path);

-- The coordinator's plan, append-only. `doc_ids` is a JSON array of `source_document.id`; every id
-- in it is re-checked against `source_document` in code before it is followed, because JSON cannot
-- carry a foreign key.
CREATE TABLE IF NOT EXISTS question (
    id            TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagement (id),
    seq           INTEGER NOT NULL CHECK (seq >= 1),
    text          TEXT NOT NULL,
    specialist    TEXT NOT NULL CHECK (specialist IN ('process', 'systems', 'data', 'change')),
    doc_ids       TEXT NOT NULL CHECK (json_valid(doc_ids) AND json_type(doc_ids) = 'array'),
    rationale     TEXT NOT NULL
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS question_engagement_seq ON question (engagement_id, seq);

-- One row per subagent attempt. A `failed` row is what statement 5.3 is built on: it is the record
-- that something did not happen, and the readout turns it into a named coverage gap.
CREATE TABLE IF NOT EXISTS subagent_run (
    id             TEXT PRIMARY KEY,
    question_id    TEXT NOT NULL REFERENCES question (id),
    state          TEXT NOT NULL CHECK (state IN ('ok', 'failed')),
    -- The closed set is app 17's `ErrorCategory`, spelled out so the database refuses a value the
    -- recording code never meant to write.
    error_category TEXT CHECK (
        error_category IS NULL
        OR error_category IN ('transient', 'validation', 'permission', 'business', 'internal')
    ),
    is_retryable   INTEGER NOT NULL DEFAULT 0 CHECK (is_retryable IN (0, 1)),
    turns          INTEGER NOT NULL CHECK (turns >= 0),
    tokens         INTEGER NOT NULL CHECK (tokens >= 0),
    -- A failure must say why; a success must not claim a category or a retry.
    CHECK (
        (state = 'failed' AND error_category IS NOT NULL)
        OR (state = 'ok' AND error_category IS NULL AND is_retryable = 0)
    )
) STRICT;

CREATE INDEX IF NOT EXISTS subagent_run_question ON subagent_run (question_id);

-- A claim and its provenance. `verified` is set in code by the quote check in `sources.py`, never
-- by a model: `store.record_claims` takes the verified flag from `verify_quote` and nothing else
-- can set it.
CREATE TABLE IF NOT EXISTS claim (
    id            TEXT PRIMARY KEY,
    engagement_id TEXT NOT NULL REFERENCES engagement (id),
    question_id   TEXT NOT NULL REFERENCES question (id),
    text          TEXT NOT NULL,
    doc_id        TEXT NOT NULL REFERENCES source_document (id),
    quote         TEXT NOT NULL,
    verified      INTEGER NOT NULL CHECK (verified IN (0, 1)),
    confidence    REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0)
) STRICT;

CREATE INDEX IF NOT EXISTS claim_engagement ON claim (engagement_id);
CREATE INDEX IF NOT EXISTS claim_question ON claim (question_id);

-- One readout per engagement, hence `engagement_id` as the primary key. `roi_json` is nullable so
-- that dropping the ROI model -- the track's first named cut -- is a null, not a migration.
CREATE TABLE IF NOT EXISTS readout (
    engagement_id TEXT PRIMARY KEY REFERENCES engagement (id),
    id            TEXT NOT NULL UNIQUE,
    state         TEXT NOT NULL CHECK (state IN ('draft', 'final')),
    maturity_json TEXT NOT NULL CHECK (json_valid(maturity_json)),
    outcomes_json TEXT NOT NULL CHECK (json_valid(outcomes_json)),
    roi_json      TEXT CHECK (roi_json IS NULL OR json_valid(roi_json)),
    roadmap_json  TEXT NOT NULL CHECK (json_valid(roadmap_json)),
    coverage_json TEXT NOT NULL CHECK (json_valid(coverage_json)),
    finalised_by  TEXT,
    CHECK ((state = 'final') = (finalised_by IS NOT NULL))
) STRICT;

-- The finalise guard. `engagement_id` is the primary key, so a second finalise is refused by the
-- database with an integrity error that `store.finalise` maps to `AlreadyFinal` -- the refusal is
-- in the schema, not in a caller's `if`. It also records `accept_gaps`, which the spec requires be
-- recorded when a lead finalises over a known coverage gap.
CREATE TABLE IF NOT EXISTS finalisation (
    engagement_id TEXT PRIMARY KEY REFERENCES engagement (id),
    finalised_by  TEXT NOT NULL,
    accept_gaps   INTEGER NOT NULL CHECK (accept_gaps IN (0, 1)),
    finalised_at  TEXT NOT NULL
) STRICT;

-- Stamped so `Store.open` can refuse a database built by a different version of this file, rather
-- than failing one column at a time as `sqlite3.OperationalError` with no error category. Bump it
-- here and in `store.SCHEMA_VERSION` together, with any change above.
PRAGMA user_version = 1;
