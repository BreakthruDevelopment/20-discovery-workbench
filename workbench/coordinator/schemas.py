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

#: What a document id may contain. Derived ids are `doc-<engagement>--<slug>-<digest>`, so this is
#: generous -- and it is here because a `doc_id` is **model-chosen text** that reaches an operator's
#: terminal. Unconstrained, a subagent could name a document
#: `"x\n  GAP  q9 (process): none, retryable=false"` and forge a line inside `wb discover`'s
#: coverage block, which is the product. A pattern with no newline in it is the fix; keeping the id
#: out of the record where it is not ours is the other half (see `tools.py`).
DOC_ID_PATTERN = r"\A[A-Za-z0-9._-]{1,256}\z"

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


class Answer(_Strict):
    """The `specialist-answer` reply from one subagent."""

    findings: list[Finding] = Field(default_factory=list, max_length=MAX_FINDINGS)
    #: The subagent's own statement that its documents did not answer the question. Recorded and
    #: carried into coverage: "I could not tell" is an answer this app wants to keep.
    insufficient_evidence: bool = False
    #: Documents it could not read in full, with the reason -- which comes from the source
    #: library's stated `unread_reason`, not from the model's imagination.
    unread: list[DocId] = Field(default_factory=list, max_length=32)
