"""The Template Method readout.

`assemble` is the skeleton: maturity, then outcomes, then the ROI model, then the roadmap, then
coverage. A subclass may override those five steps. It may not override `assemble` or the locks
the skeleton applies after each step; a class that tries is refused when it is defined.

The locks are the provenance rules, and they are why the steps are not trusted with the result:

* a maturity level is an integer 1-5 only when at least one cited claim was verified and shown;
  otherwise the level is the literal `unknown`
* an outcome whose cited claims do not resolve is dropped
* an outcome or a level that cites one side of a disagreement and not the other loses those
  claims, so one side cannot stand in for both
* an outcome that cites both sides is dropped, and the skeleton adds one conflict that carries
  both quotes verbatim
* an ROI figure with no remaining basis claims, a non-finite bound, or a basis that touches a
  disagreement is stored as null
* coverage is recomputed from the recorded runs; whatever the step returned is discarded
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, final

from .conflicts import find_conflicts
from .evidence import Evidence, coverage_document
from .schemas import (
    MAX_DIMENSION_CHARS,
    MAX_OUTCOME_CHARS,
    MAX_PHASE_CHARS,
    MaturityItem,
    OutcomeItem,
    Phase,
    ProposedReadout,
    RoiProposal,
)
from .text import one_line, safe_token

_CONFLICT_TEXT = (
    "These claims disagree. Both quotes are kept and neither is averaged into the other."
)


@dataclass(frozen=True, slots=True)
class AssembledReadout:
    """The readout sections, ready for `store.save_readout`."""

    maturity: tuple[dict[str, object], ...]
    outcomes: tuple[dict[str, object], ...]
    roi: dict[str, object] | None
    roadmap: tuple[dict[str, object], ...]
    coverage: dict[str, object]


class _SkeletonMeta(type):
    """Refuse a subclass that replaces the skeleton or the locks inside it.

    The check looks at the class body, not at a method a caller might patch later. Overriding
    `assemble` is how a readout would quietly reorder the sections or skip a lock; the type
    error is raised at definition so that readout is never constructed.
    """

    _LOCKED = frozenset(
        {
            "assemble",
            "_lock_maturity",
            "_lock_outcomes",
            "_lock_roi",
            "_lock_roadmap",
            "_lock_coverage",
            "_attach_conflicts",
        }
    )

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ) -> _SkeletonMeta:
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        if any(getattr(base, "_readout_skeleton", False) for base in bases):
            locked = sorted(item for item in namespace if item in mcls._LOCKED)
            if locked:
                raise TypeError(
                    f"{name} overrides the readout skeleton ({', '.join(locked)}); "
                    "override maturity, outcomes, roi_model, roadmap or coverage instead"
                )
        return cls


class ReadoutTemplate(metaclass=_SkeletonMeta):
    """The fixed skeleton. Subclasses override the section steps and nothing else."""

    _readout_skeleton = True

    @final
    def assemble(self, evidence: Evidence, proposal: ProposedReadout) -> AssembledReadout:
        """Run the five steps in order, locking each result before the next step sees it."""
        maturity = self._lock_maturity(self.maturity(evidence, proposal), evidence)
        outcomes = self._lock_outcomes(self.outcomes(evidence, proposal), evidence)
        roi = self._lock_roi(self.roi_model(evidence, proposal), evidence)
        roadmap = self._lock_roadmap(self.roadmap(evidence, proposal))
        coverage = self._lock_coverage(self.coverage(evidence, proposal), evidence)
        return AssembledReadout(
            maturity=tuple(maturity),
            outcomes=tuple(outcomes),
            roi=roi,
            roadmap=tuple(roadmap),
            coverage=coverage,
        )

    # -- steps a subclass may override -------------------------------------------------------

    def maturity(self, evidence: Evidence, proposal: ProposedReadout) -> tuple[MaturityItem, ...]:
        """The maturity step. The lock, not this method, decides which levels survive."""
        del evidence
        return tuple(proposal.maturity)

    def outcomes(self, evidence: Evidence, proposal: ProposedReadout) -> tuple[OutcomeItem, ...]:
        """The outcomes step. An item with no basis is dropped by the lock."""
        del evidence
        return tuple(proposal.outcomes)

    def roi_model(self, evidence: Evidence, proposal: ProposedReadout) -> RoiProposal | None:
        """The ROI model.

        The track's first named cut is this function. Return None, and the readout stores null
        in the nullable `roi` column. That is the whole cut: one function, no schema change.
        The lock still drops a figure this function returns when it has no basis claims.
        """
        del evidence
        return proposal.roi

    def roadmap(self, evidence: Evidence, proposal: ProposedReadout) -> tuple[Phase, ...]:
        """The roadmap step."""
        del evidence
        return tuple(proposal.roadmap)

    def coverage(self, evidence: Evidence, proposal: ProposedReadout) -> dict[str, object]:
        """The coverage step. The lock discards this return and records the runs."""
        del proposal
        return coverage_document(evidence.questions)

    # -- locks: part of the skeleton ---------------------------------------------------------

    def _lock_maturity(
        self, items: Sequence[MaturityItem], evidence: Evidence
    ) -> list[dict[str, object]]:
        pairs = _pair_sets(evidence)
        locked: list[dict[str, object]] = []
        for item in items:
            dimension = one_line(item.dimension, limit=MAX_DIMENSION_CHARS)
            if not dimension:
                continue
            claim_ids = _without_partial_pairs(_resolve(evidence, item.claim_ids), pairs)
            level: int | str = item.level if claim_ids else "unknown"
            if not isinstance(level, int):
                level = "unknown"
            locked.append({"dimension": dimension, "level": level, "claim_ids": claim_ids})
        return locked

    def _lock_outcomes(
        self, items: Sequence[OutcomeItem], evidence: Evidence
    ) -> list[dict[str, object]]:
        pairs = _pair_sets(evidence)
        locked: list[dict[str, object]] = []
        for item in items:
            claim_ids = _without_partial_pairs(_resolve(evidence, item.claim_ids), pairs)
            if not claim_ids or _cites_whole_pair(claim_ids, pairs):
                # No basis, or both sides of a disagreement: the model's sentence is not kept.
                # A whole pair is restated by `_attach_conflicts`, with the quotes, not this text.
                continue
            text = one_line(item.outcome, limit=MAX_OUTCOME_CHARS)
            if not text:
                continue
            locked.append(
                {
                    "outcome": text,
                    "claim_ids": claim_ids,
                    "confidence": float(item.confidence),
                }
            )
        return self._attach_conflicts(locked, evidence)

    def _attach_conflicts(
        self, outcomes: list[dict[str, object]], evidence: Evidence
    ) -> list[dict[str, object]]:
        """Append one conflict per disagreement, quotes copied from the claims."""
        attached = list(outcomes)
        for left, right in find_conflicts(tuple(item.claim for item in evidence.admitted)):
            attached.append(
                {
                    "outcome": _CONFLICT_TEXT,
                    "claim_ids": [left.id, right.id],
                    "confidence": 1.0,
                    "conflict": True,
                    "quotes": [
                        {"claim_id": left.id, "quote": left.quote},
                        {"claim_id": right.id, "quote": right.quote},
                    ],
                }
            )
        return attached

    def _lock_roi(self, roi: RoiProposal | None, evidence: Evidence) -> dict[str, object] | None:
        if roi is None:
            return None
        if not math.isfinite(roi.low) or not math.isfinite(roi.high) or roi.low > roi.high:
            return None
        pairs = _pair_sets(evidence)
        basis = _resolve(evidence, roi.basis_claim_ids)
        if not basis:
            return None
        # A figure grounded on a contradicted claim would be the average the conflict exists to
        # stop. Either side is enough to drop it; the claims remain in the conflict itself.
        contradicted = {claim_id for pair in pairs for claim_id in pair}
        if any(claim_id in contradicted for claim_id in basis):
            return None
        driver = one_line(roi.driver, limit=500)
        assumption = one_line(roi.assumption, limit=1_000)
        if not driver or not assumption:
            return None
        return {
            "driver": driver,
            "basis_claim_ids": basis,
            "low": float(roi.low),
            "high": float(roi.high),
            "assumption": assumption,
        }

    def _lock_roadmap(self, phases: Sequence[Phase]) -> list[dict[str, object]]:
        locked: list[dict[str, object]] = []
        for phase in phases:
            name = one_line(phase.phase, limit=MAX_PHASE_CHARS)
            if not name:
                continue
            depends = [
                cleaned
                for item in phase.depends_on
                if (cleaned := one_line(item, limit=MAX_PHASE_CHARS))
            ]
            locked.append({"phase": name, "weeks": int(phase.weeks), "depends_on": depends[:8]})
        return locked

    def _lock_coverage(self, _proposed: dict[str, object], evidence: Evidence) -> dict[str, object]:
        """Coverage is mandatory and is the recorded runs, not the step's return value."""
        document = coverage_document(evidence.questions)
        gaps: list[dict[str, str]] = []
        raw_gaps = document["gaps"]
        if isinstance(raw_gaps, list):
            for gap in raw_gaps:
                if not isinstance(gap, dict):
                    continue
                question_id = gap.get("question_id")
                reason = gap.get("reason")
                if not isinstance(question_id, str) or not isinstance(reason, str):
                    continue
                safe_id = safe_token(question_id)
                if not safe_id:
                    continue
                gaps.append({"question_id": safe_id, "reason": one_line(reason, limit=400)})
        omitted = document["gaps_omitted"]
        return {
            "questions_total": document["questions_total"],
            "answered": document["answered"],
            "failed": document["failed"],
            "gaps": gaps,
            "gaps_omitted": omitted if isinstance(omitted, int) and omitted > 0 else 0,
        }


def _resolve(evidence: Evidence, tokens: Sequence[str]) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        claim_id = evidence.resolve(token)
        if claim_id is None or claim_id in seen:
            continue
        seen.add(claim_id)
        resolved.append(claim_id)
        if len(resolved) == 8:
            break
    return resolved


def _pair_sets(evidence: Evidence) -> tuple[frozenset[str], ...]:
    return tuple(
        frozenset({left.id, right.id})
        for left, right in find_conflicts(tuple(item.claim for item in evidence.admitted))
    )


def _without_partial_pairs(claim_ids: list[str], pairs: Sequence[frozenset[str]]) -> list[str]:
    """Drop claims that are one side of a disagreement and not both."""
    present = set(claim_ids)
    blocked: set[str] = set()
    for pair in pairs:
        overlap = present & pair
        if overlap and overlap != pair:
            blocked |= overlap
    return [claim_id for claim_id in claim_ids if claim_id not in blocked]


def _cites_whole_pair(claim_ids: Sequence[str], pairs: Sequence[frozenset[str]]) -> bool:
    present = set(claim_ids)
    return any(pair <= present for pair in pairs)
