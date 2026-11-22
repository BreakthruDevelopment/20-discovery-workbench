"""Config is read once, from the environment, and never invents a Bedrock identifier."""

from __future__ import annotations

from pathlib import Path

import pytest

from workbench.core.config import DEFAULT_REGION, Config
from workbench.core.errors import InvalidInput


def test_defaults_are_relative_to_the_given_base(tmp_path: Path) -> None:
    config = Config.from_env({}, base=tmp_path)
    assert config.database_path == tmp_path / "workbench.sqlite3"
    assert config.sources_root == tmp_path / "sources"
    assert config.region == DEFAULT_REGION


def test_the_environment_overrides_each_value(tmp_path: Path) -> None:
    config = Config.from_env(
        {
            "WB_DATABASE": str(tmp_path / "other.sqlite3"),
            "WB_SOURCES_ROOT": str(tmp_path / "evidence"),
            "WB_REGION": "us-west-2",
            "WB_BEDROCK_PROFILE_ID": "a-profile-id",
        },
        base=tmp_path,
    )
    assert config.database_path == tmp_path / "other.sqlite3"
    assert config.sources_root == tmp_path / "evidence"
    assert config.region == "us-west-2"
    assert config.live_model_reference() == "a-profile-id"


def test_a_live_run_without_a_profile_id_is_refused_by_name(tmp_path: Path) -> None:
    """The project does not record the profile id anywhere, so config asks for it rather than
    guessing one that would look configured and fail at the first live call."""
    config = Config.from_env({}, base=tmp_path)
    assert config.bedrock_profile_id is None
    with pytest.raises(InvalidInput) as refusal:
        config.live_model_reference()
    assert "WB_BEDROCK_PROFILE_ID" in str(refusal.value)


def test_a_blank_profile_id_is_treated_as_unset(tmp_path: Path) -> None:
    config = Config.from_env({"WB_BEDROCK_PROFILE_ID": "   "}, base=tmp_path)
    assert config.bedrock_profile_id is None


def test_the_engagement_source_root_is_under_the_sources_root(tmp_path: Path) -> None:
    config = Config.from_env({}, base=tmp_path)
    assert config.engagement_sources_root("acme-p2p") == tmp_path / "sources" / "acme-p2p"


def test_the_input_caps_match_the_spec(tmp_path: Path) -> None:
    config = Config.from_env({}, base=tmp_path)
    assert (config.plan_input_cap, config.answer_input_cap, config.synthesis_input_cap) == (
        8_000,
        20_000,
        12_000,
    )
    assert config.max_questions == 6
