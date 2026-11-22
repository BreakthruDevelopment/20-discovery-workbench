"""Where a model reply comes from: a committed recording by default, Bedrock only on `--live`.

Each subagent gets **its own** provider object, because each is its own `AgentLoop` and a
`ReplayProvider` hands out its replies in order -- one shared between five concurrent subagents
would interleave them nondeterministically, which is the opposite of a recorded demo.

On the live path the opposite is true: every loop shares **one** `RateLimitedProvider`, because the
thing being limited is the rate at which this process calls Bedrock. A limiter per subagent would
cap each one and limit nothing. That shared limiter is why a five-way fan-out cannot trip
throttling (app 17 slice 17.3).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from agent_container.core.limiter import RateLimitedProvider
from agent_container.core.messages import ModelRequest, ModelResponse
from agent_container.core.provider import ModelProvider
from agent_container.core.replay import ReplayProvider, parse_replies
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from workbench.core.config import Config
from workbench.core.errors import InvalidInput, ProviderFailed, Throttled
from workbench.core.principals import Action, EngagementState, Principal, Resource, assert_can

#: At most this many model calls in flight at once on the live path. Four is app 17's own default
#: and is below the fan-out the plan can ask for, which is the point.
MAX_CONCURRENT_MODEL_CALLS = 4


class ProviderSource(Protocol):
    """Where the coordinator gets a provider for the plan, and one per subagent."""

    def plan_provider(self) -> ModelProvider: ...
    def specialist_provider(self, position: int) -> ModelProvider: ...


class _FailingProvider(ModelProvider):
    """A provider that fails on its first call. How a recorded run records a failed subagent.

    The failure has to come from the provider, not from a flag the coordinator reads, or the
    recorded demo would be proving that the coordinator can print the word "failed" rather than
    that a real provider error becomes a `subagent_run` row and a named coverage gap.
    """

    def __init__(self, code: str) -> None:
        self._code = code

    async def converse(self, request: ModelRequest) -> ModelResponse:
        if self._code == "throttled":
            raise Throttled("the model provider asked us to slow down")
        raise ProviderFailed("the model provider failed")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _SpecialistRecording(_Strict):
    """One subagent's recorded replies, or the error it is recorded as failing with."""

    replies: list[dict[str, object]] = Field(default_factory=list)
    error: str | None = None

    def provider(self) -> ModelProvider:
        if self.error is not None:
            return _FailingProvider(self.error)
        return ReplayProvider(parse_replies({"replies": self.replies}))


class Recording(_Strict):
    """The committed fixture: the plan's replies, and one entry per subagent by plan position.

    Keyed by **position in the plan** -- "1" is the first question of whatever plan is being run --
    never by `question.seq`, which continues an engagement's existing numbering and so differs on
    a second run of the same engagement.
    """

    plan: list[dict[str, object]] = Field(min_length=1)
    specialists: dict[str, _SpecialistRecording] = Field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Recording:
        import json

        try:
            return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, ValidationError) as exc:
            # Named by file role, never by content: a fixture is a file on disk, but a parse error
            # message that quoted it would put recorded model text into a refusal.
            raise InvalidInput("the committed discovery recording could not be read") from exc


class ReplaySource:
    """A `ProviderSource` over a committed recording. The default for every test and the demo."""

    def __init__(self, recording: Recording) -> None:
        self._recording = recording

    @classmethod
    def from_file(cls, path: Path) -> ReplaySource:
        return cls(Recording.load(path))

    @property
    def recorded_specialists(self) -> Mapping[str, _SpecialistRecording]:
        return dict(self._recording.specialists)

    def plan_provider(self) -> ModelProvider:
        return ReplayProvider(parse_replies({"replies": self._recording.plan}))

    def specialist_provider(self, position: int) -> ModelProvider:
        recorded = self._recording.specialists.get(str(position))
        if recorded is None:
            # A plan with more questions than the recording covers. A stated failure per subagent,
            # which the run then reports as a coverage gap -- not an exception that loses the run.
            return _FailingProvider("provider_failed")
        return recorded.provider()


class LiveSource:
    """Bedrock behind app 17's rate limiter. Reached only by an explicit, `lead`-only `--live`.

    **The `lead`-only check is here, not in the caller.** This repo's `AGENTS.md` puts access
    checks inside the layer that holds the capability, and the capability a `LiveSource` holds is
    "this run may spend money at Bedrock". A check in `wb discover` would be one copy per entry
    point, and 20.6 adds a second (`wb demo --live`) -- so constructing one of these without the
    right principal must be what fails, rather than forgetting a line at a call site.
    """

    def __init__(
        self, config: Config, principal: Principal, engagement_id: str, state: EngagementState
    ) -> None:
        from agent_container.core.bedrock import BedrockProvider

        assert_can(principal, Action.RUN_LIVE, Resource(engagement_id, state))
        model = config.live_model_reference()
        self._shared = RateLimitedProvider(
            BedrockProvider(model_id=model, region_name=config.region),
            max_concurrent=MAX_CONCURRENT_MODEL_CALLS,
        )

    def plan_provider(self) -> ModelProvider:
        return self._shared

    def specialist_provider(self, position: int) -> ModelProvider:
        # Deliberately the same object for every subagent: see the module docstring.
        return self._shared
