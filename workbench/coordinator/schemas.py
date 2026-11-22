"""The pydantic output schemas for the two coordinator tasks, and their closed sets.

This track's zod. Every model answer is parsed through one of these **before any value is used**,
and nothing downstream reads a raw model reply. The schemas are `extra="forbid"` so a field nobody
decided about is a rejected answer rather than a silently ignored one, and every list and string is
bounded, because an unbounded field in a model answer is an unbounded prompt in the next task.

What the schema deliberately does **not** do: it does not decide whether a `doc_id` is real, and it
does not decide whether a `quote` is in its document. Both are checked in code against the store --
`store.document_path` for a `doc_id`, `SourceLibrary.verify_quote` for a quote -- because a schema
can only say that a field is a string of the right shape, and the whole product here is the
difference between well-shaped and true.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: At most six questions in a plan (spec, `discovery-plan`). More than six is a rejected plan.
MAX_QUESTIONS = 6

#: At most eight findings from one subagent (spec, `specialist-answer`).
MAX_FINDINGS = 8

#: Field bounds. They match `workbench.core.store`'s own column caps, so an answer that parses here
#: cannot be refused by the store for length alone -- one boundary, not two that disagree.
MAX_QUESTION_CHARS = 2_000
MAX_RATIONALE_CHARS = 1_000
MAX_CLAIM_CHARS = 2_000
MAX_QUOTE_CHARS = 2_000
MAX_NOTE_CHARS = 2_000

#: What a document id may contain, as a **deny-list**: anything but a control character, DEL, a
#: C1 character, or a Unicode line or paragraph separator.
#:
#: Why a pattern at all: a `doc_id` is model-chosen text that reaches an operator's terminal
#: through `wb discover`'s coverage block, and an id carrying a newline forged a `GAP` line there.
#: So the thing that must be impossible is a **line break**, not an unusual character.
#:
#: Why not an allow-list: the first version of this was `[A-Za-z0-9._-]`, and it rejected ids this
#: repo's own `document_id()` produces. That function replaces only `/` and `.`, so every other
#: character of a filename survives into the id, and nothing constrains a filename beyond its
#: extension. `AP policy.md`, `memos/résumé.md`, `Q3 spend (draft).csv` and `interview—clerk.md`
#: all yield ids the allow-list refused -- and the failure was ugly: the document indexes fine,
#: appears in the index the planner is shown, the planner copies the id back correctly, and the
#: plan is then rejected, replanned once and refused, blaming the model for reading the index
#: right. The committed pack has only tame filenames, which is exactly why no test caught it.
#:
#: `\A` and `\z`, not `^` and `$`: pydantic-core compiles this with Rust's `regex`, where `$`
#: would also match before a trailing newline. (That engine is also why `\u{...}` is spelled
#: this way, and why Python's own `re` cannot compile this string -- a test pins both facts.)
DOC_ID_PATTERN = r"\A[^\x00-\x1f\x7f-\x9f\u{2028}\u{2029}]{1,256}\z"

#: A document id as a field type. `Annotated` on the ITEM, because `pattern=` on a `list[str]`
#: field is applied to the list and raises `TypeError` out of `model_validate` -- which escapes
#: app 17's `Tool.invoke`, since that catches `ValidationError` only, so the whole loop dies
#: instead of handing the model a validation result it could fix.
DocId = Annotated[str, Field(min_length=1, max_length=256, pattern=DOC_ID_PATTERN)]


def _clean_text(value: str, field: str) -> str:
    """Trim, and refuse blank or NUL-bearing text.

    `min_length=1` passes `"   "`, which then reached `store.record_claims` and raised
    `InvalidInput` from inside the recording loop -- aborting a run whose questions were already
    persisted and leaving them with no `subagent_run` row at all. A model answer is validated here,
    at the boundary, so the store's own refusal stays the backstop it should be.
    """
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{field} is blank")
    if "\x00" in trimmed:
        raise ValueError(f"{field} contains a NUL byte")
    return trimmed


class Specialist(StrEnum):
    """The closed set a planned question may name. A value outside it is a rejected plan."""

    PROCESS = "process"
    SYSTEMS = "systems"
    DATA = "data"
    CHANGE = "change"


class _Strict(BaseModel):
    """Forbid unknown fields and refuse to coerce. A model answer is validated, not massaged."""

    model_config = ConfigDict(extra="forbid", strict=False, frozen=True)


class PlannedQuestion(_Strict):
    """One question the coordinator intends to delegate."""

    text: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    specialist: Specialist
    #: At least one document, because a question naming none is a question no subagent can answer
    #: from evidence -- which is the only kind this app asks.
    doc_ids: list[DocId] = Field(min_length=1, max_length=32)
    rationale: str = Field(min_length=1, max_length=MAX_RATIONALE_CHARS)

    @field_validator("text", "rationale")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        return _clean_text(value, "a planned question's text")


class Plan(_Strict):
    """The `discovery-plan` answer: the questions, and why this shape for this engagement."""

    questions: list[PlannedQuestion] = Field(min_length=1, max_length=MAX_QUESTIONS)
    strategy_note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class Finding(_Strict):
    """One thing a subagent says it found, with the quote that is supposed to support it."""

    claim: str = Field(min_length=1, max_length=MAX_CLAIM_CHARS)
    doc_id: DocId
    quote: str = Field(min_length=1, max_length=MAX_QUOTE_CHARS)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: str = Field(default="", max_length=MAX_NOTE_CHARS)

    @field_validator("claim", "quote")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        return _clean_text(value, "a finding's text")

    @field_validator("uncertainty")
    @classmethod
    def _no_nul(cls, value: str) -> str:
        """`uncertainty` may be empty -- it is optional -- but it may not carry a NUL.

        Nothing persists or prints it today. It is the one `Finding` string outside `_clean_text`,
        and a slice that starts storing it should not have to discover that.
        """
        if "\x00" in value:
            raise ValueError("uncertainty contains a NUL byte")
        return value.strip()


class Answer(_Strict):
    """The `specialist-answer` reply from one subagent."""

    findings: list[Finding] = Field(default_factory=list, max_length=MAX_FINDINGS)
    #: The subagent's own statement that its documents did not answer the question. Recorded and
    #: carried into coverage: "I could not tell" is an answer this app wants to keep.
    insufficient_evidence: bool = False
    #: Documents it could not read in full, with the reason -- which comes from the source
    #: library's stated `unread_reason`, not from the model's imagination.
    unread: list[DocId] = Field(default_factory=list, max_length=32)
