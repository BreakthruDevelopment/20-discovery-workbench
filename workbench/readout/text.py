"""Flatten text before it is shown to a person or placed in a prompt.

A claim, a quote and a question are model-chosen or document text. Printed raw, a newline in one
of them becomes an extra line of command output, and an escape sequence can redraw the coverage
block above it. The same rule `wb discover` applies to a strategy note, in the one place both the
prompt and the readout can share it.
"""

from __future__ import annotations


def one_line(value: str, *, limit: int = 600) -> str:
    """One visible line, capped. Non-printable characters are removed, not escaped into view."""
    flattened = " ".join(value.split())
    visible = "".join(char for char in flattened if char.isprintable())
    if len(visible) <= limit:
        return visible
    return visible[:limit] + "…"


def safe_token(value: str, *, limit: int = 64) -> str:
    """An identifier safe to print: no whitespace, no controls, capped.

    A question id or a claim id that carried a newline would forge a line the way a `doc_id` once
    forged a `GAP` line. Identifiers this app creates are already tame; this is the print boundary
    refusing to trust that.
    """
    cleaned = "".join(char for char in value if char.isprintable() and not char.isspace())
    return cleaned[:limit]
