"""`wb discover`, and the two properties the fan-out claims that a stub can silently fake.

The concurrency test is written against this project's own lesson that a "concurrent" test can pass
because its stub never yields: it uses an `asyncio.Barrier` sized to the number of subagents, so it
can only pass if they are genuinely in flight together, and a sequential coordinator deadlocks and
fails on the timeout rather than passing.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from agent_container.core.budget import Budget
from agent_container.core.messages import ModelRequest, ModelResponse
from agent_container.core.provider import ModelProvider
from agent_container.core.replay import ReplayProvider, parse_replies

from tests.conftest_pack import ACME, CLERK, FIXTURE, MATCHING, Pack
from tests.recordings import answer, finding, tool_use
from workbench.cli import build_parser, main
from workbench.cli.discover import FIXTURE as CLI_FIXTURE
from workbench.coordinator.providers import ProviderSource
from workbench.coordinator.schemas import Plan, PlannedQuestion, Specialist
from workbench.core.principals import Principal

SUBAGENTS = 3


def _plan_of(count: int) -> dict[str, object]:
    return Plan(
        questions=[
            PlannedQuestion(
                text=f"Question {n}: how is matching done?",
                specialist=Specialist.PROCESS,
                doc_ids=[CLERK],
                rationale="the clerk describes it",
            )
            for n in range(1, count + 1)
        ],
        strategy_note="one question per subagent",
    ).model_dump(mode="json")


class _BarrierProvider(ModelProvider):
    """Answers only once every sibling has also been called. Sequential execution deadlocks."""

    def __init__(self, barrier: asyncio.Barrier, reply: ModelResponse) -> None:
        self._barrier = barrier
        self._reply = reply
        self._arrived = False

    async def converse(self, request: ModelRequest) -> ModelResponse:
        if not self._arrived:
            self._arrived = True
            await self._barrier.wait()
        return self._reply


class _BarrierSource:
    """A `ProviderSource` whose subagents must all be in flight before any of them can answer."""

    def __init__(self, barrier: asyncio.Barrier) -> None:
        self._barrier = barrier
        self._plan = parse_replies({"replies": [tool_use("submit_plan", _plan_of(SUBAGENTS))]})
        self._answer = parse_replies(
            {
                "replies": [
                    tool_use(
                        "submit_answer",
                        answer([finding(claim="Manual.", doc_id=CLERK, quote=MATCHING)]),
                    )
                ]
            }
        )

    def plan_provider(self) -> ModelProvider:
        return ReplayProvider(self._plan)

    def specialist_provider(self, seq: int) -> ModelProvider:
        return _BarrierProvider(self._barrier, self._answer[0])


def test_the_subagents_really_run_concurrently(pack: Pack, pack_analyst: Principal) -> None:
    source: ProviderSource = _BarrierSource(asyncio.Barrier(SUBAGENTS))

    async def go() -> int:
        result = await pack.coordinator(source).discover(
            pack_analyst,
            ACME,
            budget=Budget(max_turns=60, max_tokens=400_000, max_seconds=600.0),
        )
        return len(result.outcomes)

    async def guarded() -> int:
        return await asyncio.wait_for(go(), timeout=10)

    assert asyncio.run(guarded()) == SUBAGENTS


def test_a_sequential_fan_out_would_fail_this_test(pack: Pack, pack_analyst: Principal) -> None:
    """Proof the barrier is load-bearing: one subagent short of the barrier's size never answers,
    which is exactly what a sequential coordinator would look like."""
    source: ProviderSource = _BarrierSource(asyncio.Barrier(SUBAGENTS + 1))

    async def guarded() -> None:
        await asyncio.wait_for(
            pack.coordinator(source).discover(
                pack_analyst,
                ACME,
                budget=Budget(max_turns=60, max_tokens=400_000, max_seconds=600.0),
            ),
            timeout=2,
        )

    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(guarded())


# ---- the command ---------------------------------------------------------------------------


def test_discover_runs_on_the_committed_recording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The whole command at zero cost, against the committed pack and the committed recording."""
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(Path(__file__).resolve().parents[1] / "sources"))
    code = main(["discover", ACME, "--principal", "analyst-rao", "--role", "analyst"])
    out = capsys.readouterr().out
    assert code == 0
    assert "coverage: 5 question(s), 4 answered, 1 failed" in out
    # Coverage is printed before any claim: a gap is never further down the page than a finding.
    assert out.index("coverage:") < out.index("claims:")
    assert "GAP" in out
    assert "claims: 7 verified, 1 not verified" in out


def test_discover_refuses_a_principal_outside_the_engagement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(Path(__file__).resolve().parents[1] / "sources"))
    code = main(["discover", ACME, "--principal", "analyst-shaw", "--role", "analyst"])
    out = capsys.readouterr().out
    assert code == 1
    assert "access_denied" in out
    assert "category=permission" in out
    assert "retryable=false" in out


def test_discover_refuses_a_sponsor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(Path(__file__).resolve().parents[1] / "sources"))
    code = main(["discover", ACME, "--principal", "sponsor-acme", "--role", "sponsor"])
    assert code == 1
    assert "access_denied" in capsys.readouterr().out


def test_an_unknown_role_is_refused_by_the_parser() -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["discover", ACME, "--principal", "x", "--role", "wizard"])
    assert exit_info.value.code == 2


def test_a_bare_wb_still_prints_the_version_line(capsys: pytest.CaptureFixture[str]) -> None:
    """20.1's smoke step checks this, and adding a subcommand must not break it."""
    assert main([]) == 0
    assert "no command given" in capsys.readouterr().out


# ---- the committed recording ships -----------------------------------------------------------


def test_the_cli_and_the_tests_use_the_same_committed_recording() -> None:
    assert CLI_FIXTURE == FIXTURE
    assert FIXTURE.is_file()


def test_the_recording_is_inside_the_package(tmp_path: Path) -> None:
    """It sits under `workbench/`, so the wheel carries it: a demo that needs no network must not
    need the source checkout either."""
    relative = FIXTURE.relative_to(Path(__file__).resolve().parents[1])
    assert relative.parts[0] == "workbench"
    assert json.loads(FIXTURE.read_text(encoding="utf-8"))["specialists"]
