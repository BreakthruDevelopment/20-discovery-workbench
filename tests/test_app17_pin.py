"""App 17 is pinned by git tag, and the pinned library must actually resolve and import."""

import json
import tomllib
from importlib.metadata import distribution
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
PIN_TAG = "v0.1.1"
PIN_COMMIT = "8b3d030fadc5599077d04078945b6f8d036c5731"


def test_pyproject_pins_app17_by_tag_not_branch_or_commit() -> None:
    source = tomllib.loads(PYPROJECT.read_text())["tool"]["uv"]["sources"]["agent-container"]
    assert source["git"] == "https://github.com/BreakthruDevelopment/17-agent-container"
    assert source["tag"] == PIN_TAG
    assert "branch" not in source
    assert "rev" not in source


def test_installed_app17_is_the_tagged_commit() -> None:
    direct_url = distribution("agent-container").read_text("direct_url.json")
    assert direct_url is not None
    vcs = json.loads(direct_url)["vcs_info"]
    assert vcs["commit_id"] == PIN_COMMIT


def test_app17_contracts_this_repo_builds_on_import() -> None:
    from agent_container.core.budget import Budget
    from agent_container.core.gate import PermissionGate
    from agent_container.core.provider import ModelProvider
    from agent_container.core.tool import Tool

    for symbol in (Budget, PermissionGate, ModelProvider, Tool):
        assert symbol.__module__.startswith("agent_container.core.")
