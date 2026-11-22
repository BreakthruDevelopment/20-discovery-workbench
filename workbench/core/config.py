"""Configuration: the database path, the source root, the Bedrock identifiers and the input caps.

Every value is read once, here, from the environment, and passed down as a `Config`. Nothing in the
repo reads `os.environ` anywhere else, so what a run depends on is readable in one place -- and the
Bedrock profile id in particular is never a literal at a call site, which is what the spec asks.

The profile id has **no default.** The project records the model (Claude Sonnet 4.6), the region
(us-east-2) and that the Global Anthropic inference profile is the route, but the profile's own
identifier is not written down anywhere in `ai-dev-os`, and inventing a plausible one would be a
value that looks configured and fails at the first live call. `live_model_reference()` raises
`InvalidInput` naming the variable instead, and the replay path -- which is every test, every demo
and CI -- never asks for it.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from workbench.core.errors import InvalidInput

#: Recorded in `ai-dev-os/specs/day-0-aws-demo-track.md`: the second AWS account, us-east-2.
DEFAULT_REGION = "us-east-2"

#: Input caps, in characters, one per AI task (spec, "AI feature"). Enforced where the prompt is
#: built, in 20.4 and 20.5; held here so all three are visible together.
PLAN_INPUT_CAP = 8_000
ANSWER_INPUT_CAP = 20_000
SYNTHESIS_INPUT_CAP = 12_000

#: At most six questions in a plan (spec, `discovery-plan` output schema).
MAX_QUESTIONS = 6

#: Source byte caps. Per file, and per run across every file a single library instance serves, so a
#: fan-out cannot read the whole pack into one context by asking for it a file at a time.
MAX_SOURCE_FILE_BYTES = 120_000
MAX_SOURCE_RUN_BYTES = 400_000


@dataclass(frozen=True, slots=True)
class Config:
    """Everything a run needs from its environment."""

    database_path: Path
    sources_root: Path
    region: str = DEFAULT_REGION
    bedrock_profile_id: str | None = None
    max_source_file_bytes: int = MAX_SOURCE_FILE_BYTES
    max_source_run_bytes: int = MAX_SOURCE_RUN_BYTES
    plan_input_cap: int = PLAN_INPUT_CAP
    answer_input_cap: int = ANSWER_INPUT_CAP
    synthesis_input_cap: int = SYNTHESIS_INPUT_CAP
    max_questions: int = MAX_QUESTIONS

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, *, base: Path | None = None) -> Config:
        """Build a config from `WB_*` variables, defaulting relative to `base` (default: cwd)."""
        values = os.environ if env is None else env
        root = Path.cwd() if base is None else base
        profile = values.get("WB_BEDROCK_PROFILE_ID", "").strip()
        return cls(
            database_path=Path(values.get("WB_DATABASE", str(root / "workbench.sqlite3"))),
            sources_root=Path(values.get("WB_SOURCES_ROOT", str(root / "sources"))),
            region=values.get("WB_REGION", DEFAULT_REGION).strip() or DEFAULT_REGION,
            bedrock_profile_id=profile or None,
        )

    def engagement_sources_root(self, engagement_id: str) -> Path:
        """Where one engagement's evidence lives: `<sources_root>/<engagement id>`.

        The engagement id is a store-held identifier, not a free-text argument -- `store.py`
        resolves it through `load_principal` and the `engagement` row before anything reaches this
        -- and `SourceLibrary` resolves and re-checks the root it is given either way.
        """
        return self.sources_root / engagement_id

    def live_model_reference(self) -> str:
        """The model identifier for a `--live` run, or `InvalidInput` if it is not configured."""
        if self.bedrock_profile_id is None:
            raise InvalidInput("WB_BEDROCK_PROFILE_ID is required for a live run")
        return self.bedrock_profile_id
