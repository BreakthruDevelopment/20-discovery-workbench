"""Run `readout-synthesis` and store the locked readout.

Replay is the default: the committed fixture in `fixtures/acme-readout.json`. A caller that
wants Bedrock passes a provider it has already authorised; this module does not construct one,
so it cannot promote itself onto the network.

The model's answer is parsed by the schema tool, then passed through `ReadoutTemplate`. What is
saved is the locked result. A run that ends without a submission saves nothing: the draft stays
as it was, which is a stated failure rather than an empty readout that looks finished.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_container.core.budget import Budget
from agent_container.core.errors import AgentContainerError, ReplayFormatError
from agent_container.core.provider import ModelProvider
from agent_container.core.replay import ReplayProvider, parse_replies
from agent_container.core.tool import ErrorCategory

from workbench.core.config import Config
from workbench.core.errors import InvalidInput, ProviderFailed, WorkbenchError
from workbench.core.principals import Principal
from workbench.core.store import Readout, Store

from .agent import SubmitReadoutTool, SynthesisAgent
from .evidence import collect_evidence
from .schemas import ProposedReadout
from .template import ReadoutTemplate

#: Beside this package, so the wheel carries it with the code.
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "acme-readout.json"

#: One submission, plus room for a single validation retry. The committed fixture uses the first.
_MAX_TURNS = 4
_MAX_TOKENS = 40_000
_MAX_SECONDS = 120.0


class SynthesisRefused(WorkbenchError):
    """The model finished without submitting a readout. Nothing was saved."""

    code = "synthesis_refused"
    category = ErrorCategory.BUSINESS
    retryable = False


def replay_provider() -> ModelProvider:
    """The committed readout recording. Zero cost, no network."""
    try:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidInput("the committed readout recording could not be read") from exc
    if not isinstance(payload, dict):
        raise InvalidInput("the committed readout recording could not be read")
    try:
        replies = parse_replies(payload)
    except ReplayFormatError as exc:
        raise InvalidInput("the committed readout recording could not be read") from exc
    return ReplayProvider(replies)


async def synthesise(
    store: Store,
    config: Config,
    principal: Principal,
    engagement_id: str,
    provider: ModelProvider,
) -> Readout:
    """Re-verify, call the model, lock the sections, and replace the draft readout."""
    evidence = collect_evidence(store, config, principal, engagement_id)
    if not evidence.message.strip():
        raise InvalidInput("the synthesis input is empty")
    proposal = await _propose(provider, evidence.message)
    assembled = ReadoutTemplate().assemble(evidence, proposal)
    return store.save_readout(
        principal,
        engagement_id,
        maturity=list(assembled.maturity),
        outcomes=list(assembled.outcomes),
        roadmap=list(assembled.roadmap),
        coverage=assembled.coverage,
        roi=assembled.roi,
    )


async def _propose(provider: ModelProvider, message: str) -> ProposedReadout:
    submit = SubmitReadoutTool()
    agent = SynthesisAgent(provider, submit)
    try:
        result = await agent.run(
            message,
            Budget(max_turns=_MAX_TURNS, max_tokens=_MAX_TOKENS, max_seconds=_MAX_SECONDS),
        )
    except AgentContainerError as exc:
        raise ProviderFailed("the synthesis model call failed") from exc
    if submit.proposal is None:
        raise SynthesisRefused(f"synthesis ended as {result.end_reason.value} without a readout")
    return submit.proposal
