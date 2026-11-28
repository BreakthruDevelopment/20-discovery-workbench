"""Render a stored readout, coverage first.

The skeleton assembles maturity, outcomes, ROI, roadmap and then coverage. What a person reads
is the other way up: coverage is printed before any section that could look like a finished
answer, and a conflict -- both quotes, not a blend -- is printed before maturity. Every line of
model or document text is flattened or prefixed, so it cannot add a line this module did not
write or redraw the block above it.

`wb trace` is the other renderer. It prints the verification result before the quote, and the
quote with every line prefixed.
"""

from __future__ import annotations

from workbench.core.errors import InvalidInput
from workbench.core.store import Claim, Readout

from .text import one_line, safe_token


def render_readout(*, client: str, readout: Readout) -> str:
    """The readout as text. The first section after the header is coverage."""
    lines = [
        f"engagement: {safe_token(readout.engagement_id, limit=128)}",
        f"client: {one_line(client, limit=200)}",
        f"readout: {safe_token(readout.state, limit=16)}",
        *_coverage_lines(readout.coverage),
        *_conflict_lines(readout.outcomes),
        *_maturity_lines(readout.maturity),
        *_outcome_lines(readout.outcomes),
        *_roi_lines(readout.roi),
        *_roadmap_lines(readout.roadmap),
    ]
    return "\n".join(lines) + "\n"


def render_trace(
    *,
    claim: Claim,
    document: str | None,
    live_verified: bool,
    reason: str,
) -> str:
    """One claim for `wb trace`: the verdict, then the document, then the quote."""
    lines = [
        f"claim: {safe_token(claim.id, limit=64)}",
        f"recorded_verified: {str(claim.verified).lower()}",
        f"live_verified: {str(live_verified).lower()}",
        f"reason: {one_line(reason, limit=300)}",
        f"document: {one_line(document or '', limit=300)}",
        f"text: {one_line(claim.text, limit=600)}",
        "quote:",
        *_quote_lines(claim.quote),
    ]
    return "\n".join(lines) + "\n"


def _coverage_lines(coverage: object) -> list[str]:
    section = _mapping(coverage, "readout.coverage")
    total = _count(section.get("questions_total"))
    answered = _count(section.get("answered"))
    failed = _count(section.get("failed"))
    lines = [f"coverage: {total} question(s), {answered} answered, {failed} failed"]
    gaps = section.get("gaps")
    if not isinstance(gaps, list):
        raise InvalidInput("readout.coverage is not the recorded shape")
    if not gaps:
        lines.append("  gaps: none")
    for gap in gaps:
        if not isinstance(gap, dict):
            raise InvalidInput("readout.coverage is not the recorded shape")
        question_id = gap.get("question_id")
        reason = gap.get("reason")
        lines.append(
            f"  GAP {safe_token(question_id if isinstance(question_id, str) else '', limit=64)}: "
            f"{one_line(reason if isinstance(reason, str) else '', limit=400)}"
        )
    omitted = _count(section.get("gaps_omitted"))
    if omitted:
        lines.append(f"  {omitted} further gap(s) not listed here")
    return lines


def _conflict_lines(outcomes: object) -> list[str]:
    items = _conflict_items(outcomes)
    if not items:
        return ["conflicts: 0"]
    lines = [f"conflicts: {len(items)}"]
    for item in items:
        lines.append(f"  {one_line(_text(item.get('outcome')), limit=400)}")
        quotes = item.get("quotes")
        if not isinstance(quotes, list):
            continue
        for quote in quotes:
            if not isinstance(quote, dict):
                continue
            lines.extend(_quote_lines(_text(quote.get("quote"))))
    return lines


def _maturity_lines(maturity: object) -> list[str]:
    lines = ["maturity:"]
    items = _list(maturity, "readout.maturity")
    if not items:
        lines.append("  none")
        return lines
    for item in items:
        if not isinstance(item, dict):
            raise InvalidInput("readout.maturity is not the recorded shape")
        level = _level(item.get("level"))
        lines.append(f"  - {one_line(_text(item.get('dimension')), limit=200)}: level {level}")
        lines.append(f"    claims: {_id_list(item.get('claim_ids'))}")
    return lines


def _outcome_lines(outcomes: object) -> list[str]:
    lines = ["outcomes:"]
    items = [
        item
        for item in _list(outcomes, "readout.outcomes")
        if isinstance(item, dict) and item.get("conflict") is not True
    ]
    if not items:
        lines.append("  none")
        return lines
    for item in items:
        lines.append(f"  - {one_line(_text(item.get('outcome')), limit=400)}")
        lines.append(f"    claims: {_id_list(item.get('claim_ids'))}")
    return lines


def _roi_lines(roi: object) -> list[str]:
    if roi is None:
        return ["roi: none"]
    section = _mapping(roi, "readout.roi")
    low = section.get("low")
    high = section.get("high")
    lines = [
        "roi:",
        f"  driver: {one_line(_text(section.get('driver')), limit=300)}",
        f"  range: {_bound(low)} to {_bound(high)}",
        f"  assumption: {one_line(_text(section.get('assumption')), limit=400)}",
        f"  basis: {_id_list(section.get('basis_claim_ids'))}",
    ]
    return lines


def _roadmap_lines(roadmap: object) -> list[str]:
    lines = ["roadmap:"]
    items = _list(roadmap, "readout.roadmap")
    if not items:
        lines.append("  none")
        return lines
    for item in items:
        if not isinstance(item, dict):
            raise InvalidInput("readout.roadmap is not the recorded shape")
        weeks = item.get("weeks")
        week_text = str(weeks) if isinstance(weeks, int) and not isinstance(weeks, bool) else "?"
        phase = one_line(_text(item.get("phase")), limit=200)
        lines.append(f"  - {phase}: {safe_token(week_text, limit=8)} weeks")
    return lines


def _conflict_items(outcomes: object) -> list[dict[str, object]]:
    if not isinstance(outcomes, list):
        raise InvalidInput("readout.outcomes is not the recorded shape")
    items: list[dict[str, object]] = []
    for item in outcomes:
        if isinstance(item, dict) and item.get("conflict") is True:
            items.append(item)
    return items


def _quote_lines(quote: str) -> list[str]:
    """The quote, one prefixed line per source line, controls removed.

    The prefix is what makes a quote that contains the words `GAP` or `verified: true` still a
    quote. The characters of the quote are otherwise unchanged.
    """
    raw_lines = quote.splitlines() or [""]
    rendered: list[str] = []
    for line in raw_lines:
        visible = "".join(char for char in line if char.isprintable() or char == "\t")
        rendered.append(f"    | {visible}")
    return rendered


def _list(value: object, field: str) -> list[object]:
    if isinstance(value, list):
        return value
    raise InvalidInput(f"{field} is not the recorded shape")


def _mapping(value: object, field: str) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    raise InvalidInput(f"{field} is not the recorded shape")


def _count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value if value >= 0 else 0


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _level(value: object) -> str:
    """A rendered level is `1`-`5` or `unknown`. Prose never gets a second chance here."""
    if isinstance(value, bool):
        return "unknown"
    if isinstance(value, int) and 1 <= value <= 5:
        return str(value)
    if isinstance(value, str) and value.strip().lower() == "unknown":
        return "unknown"
    return "unknown"


def _bound(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return "?"
    return f"{value:g}"


def _id_list(value: object) -> str:
    if not isinstance(value, list):
        return "none"
    tokens = [safe_token(item, limit=64) for item in value if isinstance(item, str)]
    tokens = [token for token in tokens if token]
    return " ".join(tokens) if tokens else "none"
