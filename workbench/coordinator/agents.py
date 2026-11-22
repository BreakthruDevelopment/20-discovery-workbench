"""The two `AgentLoop` subclasses: the planner, and one specialist subagent.

Both do the same two things and nothing else, through the only hooks app 17 lets a subclass
override:

* `before_model` sets `tool_choice`, which is how the output schema becomes a tool the model
  **must** call rather than one it may ignore (statement 2.3). The planner forces `submit_plan` by
  name. A specialist forces `any`, not a name, because it has to be able to read before it answers.
* `should_stop` ends the run the moment the schema tool has been called. Without it the forced
  `tool_choice` would make the next turn submit again, and the loop would spend its whole budget
  arguing with itself over an answer it already has.

Everything else -- the turn loop, the stop-reason branch, the fence, the budget -- is the pinned
tag's, untouched. `ModelRequest` is frozen, so `before_model` returns a `replace()` of it.
"""

from __future__ import annotations

from dataclasses import replace

from agent_container.core.loop import AgentLoop, RunState
from agent_container.core.messages import ModelRequest, ToolChoice
from agent_container.core.provider import ModelProvider

from .prompts import PLAN_SYSTEM, answer_system
from .tools import ReadDocumentTool, SubmitAnswerTool, SubmitPlanTool


class PlanAgent(AgentLoop):
    """The coordinator's own loop: one forced call to `submit_plan`, from the index alone."""

    def __init__(self, provider: ModelProvider, submit: SubmitPlanTool) -> None:
        super().__init__(provider, [submit], system_prompt=PLAN_SYSTEM)
        self._submit = submit

    async def before_model(self, state: RunState, request: ModelRequest) -> ModelRequest:
        return replace(request, tool_choice=ToolChoice(mode="tool", name=self._submit.name))

    async def should_stop(self, state: RunState) -> str | None:
        if self._submit.plan is not None:
            return "the plan has been submitted"
        return None


class SpecialistAgent(AgentLoop):
    """One subagent: its own loop, its own read-only tool manifest, its own question.

    Its manifest is exactly two tools -- `read_document`, scoped in code to the documents its
    question named, and `submit_answer`. It is given no brief, no other question and no other
    subagent's answer, because the only thing it is ever told is the user message the coordinator
    builds for it. That is what makes the context passing one-way: not a prompt asking it to stay
    in its lane, but a loop with nothing else in reach.
    """

    def __init__(
        self,
        provider: ModelProvider,
        *,
        specialist: str,
        reader: ReadDocumentTool,
        submit: SubmitAnswerTool,
    ) -> None:
        super().__init__(
            provider,
            [reader, submit],
            system_prompt=answer_system(specialist),
        )
        self._submit = submit

    async def before_model(self, state: RunState, request: ModelRequest) -> ModelRequest:
        # `any`, not `tool`: it must call *a* tool every turn, so it cannot end its turn with prose
        # instead of an answer -- but it must be free to choose `read_document` first.
        return replace(request, tool_choice=ToolChoice(mode="any"))

    async def should_stop(self, state: RunState) -> str | None:
        if self._submit.answer is not None:
            return "the answer has been submitted"
        return None
