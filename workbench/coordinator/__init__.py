"""The coordinator: statements 1.2, 1.3 and 5.3, and the adaptive half of 1.6.

New files only. This package calls `workbench/core/` and never edits it: every read and write goes
through the store's accessors, under the acting principal, with the `engagement_id` filter inside
them.

What is where:

* `schemas.py` -- the pydantic output schemas and their closed sets. Every model answer is parsed
  through one before any value is used.
* `prompts.py` -- the three system prompts, and the standing line that document text, tool results
  and another agent's answer are data and never instructions.
* `tools.py` -- the read-only tool manifest: `read_document`, scoped in code to the documents one
  question named, plus the two schema-submission tools.
* `agents.py` -- the two `AgentLoop` subclasses, which override only `before_model` (to force
  `tool_choice`) and `should_stop`.
* `providers.py` -- a committed recording by default; Bedrock behind app 17's rate limiter only on
  an explicit `--live`.
* `coordinator.py` -- the Mediator, and the Composite face: one `discover()` call, one result.
"""

from .coordinator import (
    DiscoveryCoordinator,
    DiscoveryRun,
    DroppedQuestion,
    PlanRefused,
    SubagentOutcome,
)
from .providers import LiveSource, ProviderSource, Recording, ReplaySource
from .schemas import Answer, Finding, Plan, PlannedQuestion, Specialist
from .tools import ReadDocumentTool, SubmitAnswerTool, SubmitPlanTool

__all__ = [
    "Answer",
    "DiscoveryCoordinator",
    "DiscoveryRun",
    "DroppedQuestion",
    "Finding",
    "LiveSource",
    "Plan",
    "PlanRefused",
    "PlannedQuestion",
    "ProviderSource",
    "ReadDocumentTool",
    "Recording",
    "ReplaySource",
    "Specialist",
    "SubagentOutcome",
    "SubmitAnswerTool",
    "SubmitPlanTool",
]
