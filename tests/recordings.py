"""Build an ad-hoc `ProviderSource` in a test, without committing a fixture for every case.

The committed recording in `workbench/coordinator/fixtures/` is the demo and the happy path. An
eval usually needs one thing changed -- a plan that names another engagement's document, a subagent
that answers with a fabricated quote, a planner that never submits -- and a committed fixture per
case would be eight more files nobody reads. These helpers build the same reply shape in memory.
"""

from __future__ import annotations

from typing import Any

from workbench.coordinator.providers import Recording, ReplaySource


def tool_use(name: str, payload: dict[str, Any], *, use_id: str = "u1") -> dict[str, Any]:
    """One recorded reply: a `tool_use` stop reason carrying one call."""
    return {
        "stop_reason": "tool_use",
        "text": "",
        "tool_uses": [{"id": use_id, "name": name, "input": payload}],
        "usage": {"input_tokens": 500, "output_tokens": 120},
    }


def end_turn(text: str = "done") -> dict[str, Any]:
    """A reply that ends the turn without calling anything. How a model fails to answer."""
    return {
        "stop_reason": "end_turn",
        "text": text,
        "tool_uses": [],
        "usage": {"input_tokens": 500, "output_tokens": 20},
    }


def recording_source(
    *,
    plan_payload: dict[str, Any] | None,
    plan_replies: int = 1,
    specialists: dict[str, dict[str, Any]] | None = None,
) -> ReplaySource:
    """A source whose planner submits `plan_payload` (or never submits, if it is `None`).

    `plan_replies` is how many attempts the recording can serve: the coordinator replans once, so
    a case that must reach the refusal needs two.
    """
    reply = tool_use("submit_plan", plan_payload) if plan_payload is not None else end_turn()
    return ReplaySource(
        Recording.model_validate(
            {
                "plan": [reply] * plan_replies,
                "specialists": specialists or {},
            }
        )
    )


def answering_specialist(reads: list[str], answer: dict[str, Any]) -> dict[str, Any]:
    """One subagent that reads `reads` in order and then submits `answer`."""
    return {
        "replies": [
            *(
                tool_use("read_document", {"doc_id": doc_id}, use_id=f"r{n}")
                for n, doc_id in enumerate(reads, start=1)
            ),
            tool_use("submit_answer", answer, use_id="a1"),
        ]
    }


def finding(
    *, claim: str, doc_id: str, quote: str, confidence: float = 0.9, uncertainty: str = ""
) -> dict[str, Any]:
    return {
        "claim": claim,
        "doc_id": doc_id,
        "quote": quote,
        "confidence": confidence,
        "uncertainty": uncertainty,
    }


def answer(findings: list[dict[str, Any]], *, insufficient: bool = False) -> dict[str, Any]:
    return {"findings": findings, "insufficient_evidence": insufficient, "unread": []}
