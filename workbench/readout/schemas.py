"""The pydantic output schema for `readout-synthesis`.

This track's zod, same as the coordinator's. The model is forced to call `submit_readout`, and
nothing downstream reads a raw reply. Fields are bounded. What the schema deliberately allows,
because the rule is enforced in code afterwards rather than by refusing the whole answer:

* a maturity `level` that is prose parses as `unknown` -- prose never stands in for a level
* an outcome may name no claim ids -- the skeleton then drops it
* an ROI may name no basis claims -- the skeleton then stores null
* `coverage` is required, so the model cannot omit it, and the skeleton then replaces it with the
  coverage computed from the recorded runs

A schema can only say a claim id is a short string. Whether that id was actually given to the
model is checked against the evidence, not here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_DIMENSIONS = 8
MAX_OUTCOMES = 8
MAX_PHASES = 8
MAX_BASIS = 8
MAX_GAPS = 32
MAX_DIMENSION_CHARS = 200
MAX_OUTCOME_CHARS = 2_000
MAX_DRIVER_CHARS = 500
MAX_ASSUMPTION_CHARS = 1_000
MAX_PHASE_CHARS = 200
MAX_REASON_CHARS = 500
MAX_ID_CHARS = 64

#: Levels the model may mean. Anything else -- "high", "mature", "level 5" as a sentence -- is
#: `unknown` at the boundary, so a later step never has to wonder whether prose slipped through.
_NUMERIC_LEVELS = {"1", "2", "3", "4", "5"}


def _clean(value: str, field: str) -> str:
    """Trim, and refuse blank or NUL-bearing text. The message names the field, not the value."""
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{field} is blank")
    if "\x00" in trimmed:
        raise ValueError(f"{field} contains a NUL byte")
    return trimmed


def _ids(value: list[str]) -> list[str]:
    """Keep short, printable, single-line tokens. Drop the rest rather than echoing them."""
    kept: list[str] = []
    for item in value:
        token = item.strip()
        if not token or len(token) > MAX_ID_CHARS:
            continue
        if any(not char.isprintable() or char.isspace() for char in token):
            continue
        kept.append(token)
    return kept


class _Strict(BaseModel):
    """Forbid unknown fields. A model answer is validated, not massaged into shape."""

    model_config = ConfigDict(extra="forbid", strict=False, frozen=True)


class MaturityItem(_Strict):
    """One maturity dimension. A level with no claim behind it does not survive the skeleton."""

    dimension: str = Field(min_length=1, max_length=MAX_DIMENSION_CHARS)
    level: int | str
    claim_ids: list[str] = Field(default_factory=list, max_length=MAX_BASIS)

    @field_validator("dimension")
    @classmethod
    def _dimension(cls, value: str) -> str:
        return _clean(value, "dimension")

    @field_validator("level", mode="before")
    @classmethod
    def _level(cls, value: object) -> int | str:
        """1-5, or the literal `unknown`. Prose and booleans become `unknown`."""
        if isinstance(value, bool):
            return "unknown"
        if isinstance(value, int):
            return value if 1 <= value <= 5 else "unknown"
        if isinstance(value, str):
            text = value.strip().lower()
            if text == "unknown":
                return "unknown"
            if text in _NUMERIC_LEVELS:
                return int(text)
        return "unknown"

    @field_validator("claim_ids")
    @classmethod
    def _claim_ids(cls, value: list[str]) -> list[str]:
        return _ids(value)


class OutcomeItem(_Strict):
    """One outcome. Empty `claim_ids` is legal here and dropped by the skeleton."""

    outcome: str = Field(min_length=1, max_length=MAX_OUTCOME_CHARS)
    claim_ids: list[str] = Field(default_factory=list, max_length=MAX_BASIS)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("outcome")
    @classmethod
    def _outcome(cls, value: str) -> str:
        return _clean(value, "outcome")

    @field_validator("claim_ids")
    @classmethod
    def _claim_ids(cls, value: list[str]) -> list[str]:
        return _ids(value)

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value: object) -> object:
        # `bool` is an `int`, and lax mode would otherwise turn `True` into `1.0`.
        if isinstance(value, bool):
            raise ValueError("confidence is a number between 0 and 1")
        return value


class RoiProposal(_Strict):
    """The model's ROI figure. Without basis claims the skeleton stores null, not this object."""

    driver: str = Field(min_length=1, max_length=MAX_DRIVER_CHARS)
    basis_claim_ids: list[str] = Field(default_factory=list, max_length=MAX_BASIS)
    low: float
    high: float
    assumption: str = Field(min_length=1, max_length=MAX_ASSUMPTION_CHARS)

    @field_validator("driver")
    @classmethod
    def _driver(cls, value: str) -> str:
        return _clean(value, "driver")

    @field_validator("assumption")
    @classmethod
    def _assumption(cls, value: str) -> str:
        return _clean(value, "assumption")

    @field_validator("basis_claim_ids")
    @classmethod
    def _basis(cls, value: list[str]) -> list[str]:
        return _ids(value)

    @field_validator("low", "high", mode="before")
    @classmethod
    def _bound(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("an ROI bound is a number")
        return value


class Phase(_Strict):
    """One roadmap phase. `depends_on` names other phases, not claims."""

    phase: str = Field(min_length=1, max_length=MAX_PHASE_CHARS)
    weeks: int = Field(ge=1, le=520)
    depends_on: list[str] = Field(default_factory=list, max_length=MAX_BASIS)

    @field_validator("phase")
    @classmethod
    def _phase(cls, value: str) -> str:
        return _clean(value, "phase")

    @field_validator("depends_on")
    @classmethod
    def _depends(cls, value: list[str]) -> list[str]:
        kept: list[str] = []
        for item in value:
            text = _clean(item, "depends_on") if item.strip() else ""
            if text and len(text) <= MAX_PHASE_CHARS and "\x00" not in text:
                kept.append(text)
        return kept

    @field_validator("weeks", mode="before")
    @classmethod
    def _weeks(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("weeks is a number of weeks")
        return value


class GapProposal(_Strict):
    """A gap as the model describes it. The skeleton does not keep it: coverage is recomputed."""

    question_id: str = Field(min_length=1, max_length=MAX_ID_CHARS)
    reason: str = Field(min_length=1, max_length=MAX_REASON_CHARS)

    @field_validator("question_id", "reason")
    @classmethod
    def _text(cls, value: str) -> str:
        return _clean(value, "coverage")


class CoverageProposal(_Strict):
    """Required on every submission, and replaced in code by the recorded run states."""

    questions_total: int = Field(ge=0, le=100)
    answered: int = Field(ge=0, le=100)
    failed: int = Field(ge=0, le=100)
    gaps: list[GapProposal] = Field(default_factory=list, max_length=MAX_GAPS)


class ProposedReadout(_Strict):
    """The `readout-synthesis` answer, before provenance rules run."""

    maturity: list[MaturityItem] = Field(default_factory=list, max_length=MAX_DIMENSIONS)
    outcomes: list[OutcomeItem] = Field(default_factory=list, max_length=MAX_OUTCOMES)
    roi: RoiProposal | None = None
    roadmap: list[Phase] = Field(default_factory=list, max_length=MAX_PHASES)
    coverage: CoverageProposal
