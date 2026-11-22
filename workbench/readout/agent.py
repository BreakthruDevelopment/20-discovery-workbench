"""The synthesis loop: one forced call to `submit_readout`.

Same two hooks as the planner, and nothing else. `before_model` forces the schema tool.
`should_stop` ends the run once that tool has been called, so a forced `tool_choice` cannot
spend the budget submitting the same readout again. The loop itself is app 17's, and it ends
on the stop reason.
"""

from __future__ import annotations

from dataclasses import replace

from agent_container.core.loop import AgentLoop, RunState
from agent_container.core.messages import ModelRequest, ToolChoice
from agent_container.core.provider import ModelProvider
from agent_container.core.tool import Effect, ErrorCategory, Tool, ToolContext, ToolResult

from .prompts import SYNTHESIS_SYSTEM
from .schemas import ProposedReadout


class SubmitReadoutTool(Tool[ProposedReadout]):
    """The readout schema as the tool the model is forced to call."""

    name = "submit_readout"
    description = (
        "Submit the discovery readout. Call this exactly once. Every claim id must be one you "
        "were given. Use level unknown, drop an outcome, or send roi null rather than inventing "
        "support you do not have. coverage is required."
    )
    effect = Effect.READ
    input_model = ProposedReadout

    def __init__(self) -> None:
        self.proposal: ProposedReadout | None = None

    async def run(self, args: ProposedReadout, ctx: ToolContext) -> ToolResult:
        del ctx
        if self.proposal is not None:
            return ToolResult.error(
                ErrorCategory.BUSINESS, "the readout has already been submitted for this run"
            )
        self.proposal = args
        return ToolResult.ok("Readout received. Nothing further is needed.")


class SynthesisAgent(AgentLoop):
    """One forced `submit_readout`. The evidence is the user message, already capped."""

    def __init__(self, provider: ModelProvider, submit: SubmitReadoutTool) -> None:
        super().__init__(provider, [submit], system_prompt=SYNTHESIS_SYSTEM)
        self._submit = submit

    async def before_model(self, state: RunState, request: ModelRequest) -> ModelRequest:
        del state
        return replace(request, tool_choice=ToolChoice(mode="tool", name=self._submit.name))

    async def should_stop(self, state: RunState) -> str | None:
        del state
        if self._submit.proposal is not None:
            return "the readout has been submitted"
        return None
