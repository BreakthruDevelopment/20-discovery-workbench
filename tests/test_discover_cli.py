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
from agent_container.core.tool import ToolContext

from tests.conftest_pack import ACME, CLERK, FIXTURE, MATCHING, Pack
from tests.recordings import answer, finding, tool_use
from workbench.cli import build_parser, main
from workbench.cli.discover import FIXTURE as CLI_FIXTURE
from workbench.coordinator.providers import ProviderSource
from workbench.coordinator.schemas import Plan, PlannedQuestion, Specialist
from workbench.core.principals import Principal
from workbench.core.sources import SourceLibrary

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


# ---- what a subagent can put on an operator's screen ----------------------------------------


def test_a_model_chosen_document_id_cannot_forge_a_coverage_line(
    pack: Pack, pack_analyst: Principal
) -> None:
    """The coverage block is the product, and a `doc_id` is the one piece of model-chosen text
    that used to reach it. An id carrying a newline forged a `GAP` line inside `wb discover`'s
    output -- the single thing a subagent that obeyed the planted injection could actually do.

    Two guards, tested together: the schema refuses such an id, and a refused id is recorded under
    a fixed key rather than under itself.
    """
    import pydantic

    from workbench.coordinator.schemas import Finding
    from workbench.coordinator.tools import OFF_MANIFEST, ReadDocumentTool, _ReadArgs

    forged = "x\n  GAP  q9 (process): none, retryable=false\n  FORGED"

    # 1. The schema refuses it, in a finding and in a read request alike.
    with pytest.raises(pydantic.ValidationError):
        Finding.model_validate(
            {"claim": "c", "doc_id": forged, "quote": "a quote long enough", "confidence": 0.5}
        )
    with pytest.raises(pydantic.ValidationError):
        _ReadArgs.model_validate({"doc_id": forged})

    # 2. And even a well-formed id the question did not name is recorded under a fixed key, so no
    #    model-chosen id reaches the record the coverage block is rendered from.
    library = SourceLibrary.for_engagement(pack.config, ACME)
    reader = ReadDocumentTool(library, {CLERK: "transcripts/01-ap-clerk.md"}, char_budget=20_000)
    invented = "doc-acme-p2p--not-a-real-document-00000000"
    refused = asyncio.run(
        reader.invoke({"doc_id": invented}, ToolContext(run_id="r", turn=1, tool_use_id="t"))
    )
    assert refused.is_error is True
    assert invented not in refused.content
    assert list(reader.unread_reasons) == [OFF_MANIFEST]


def test_the_coverage_block_contains_only_lines_the_cli_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every GAP line in the real run's output corresponds to a real failed subagent."""
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(Path(__file__).resolve().parents[1] / "sources"))
    assert main(["discover", ACME, "--principal", "analyst-rao", "--role", "analyst"]) == 0
    out = capsys.readouterr().out
    gaps = [line for line in out.splitlines() if "GAP" in line]
    assert len(gaps) == 1
    assert "FORGED" not in out


def test_model_prose_cannot_add_a_line_to_the_report() -> None:
    """`strategy_note` is the planner's own prose and was printed verbatim, so a note containing a
    newline could add a line indistinguishable from one the CLI wrote."""
    from workbench.cli.discover import _one_line

    forged = "a plan\n  GAP  q9 (process): none, retryable=false\n  FORGED"
    flattened = _one_line(forged)
    assert "\n" not in flattened
    assert "\r" not in flattened
    assert "GAP" in flattened  # the text is kept; only its ability to be a line is removed
    assert _one_line("x" * 5_000).endswith("…")
    assert len(_one_line("x" * 5_000)) <= 601


def test_model_prose_cannot_carry_a_terminal_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """End to end through `main`, with the one model-controlled prose field forged.

    Two holes this closes, both found by review. `_one_line` split on whitespace, and `\x1b` is
    not whitespace: `"\x1b[2J\x1b[H"` reached the terminal, and `strategy:` is the LAST line
    printed, so an escape there can clear the screen or redraw over the coverage block above it.
    And the flatten was only ever asserted on the helper -- reverting the call site to
    `print(f"strategy: {result.strategy_note}")` left the whole suite green, because the only
    CLI-level run used the tame committed fixture.
    """
    forged = (
        "a plan\x1b[2J\x1b[H\n  GAP  q9 (process): none, retryable=false\n"
        "claims: 99 verified, 0 not verified\n  FORGED"
    )
    recording = {
        "plan": [
            tool_use(
                "submit_plan",
                {
                    "questions": [
                        {
                            "text": "how is matching done?",
                            "specialist": "process",
                            "doc_ids": [CLERK],
                            "rationale": "the clerk describes it",
                        }
                    ],
                    "strategy_note": forged,
                },
            )
        ],
        "specialists": {
            "1": {
                "replies": [
                    tool_use("read_document", {"doc_id": CLERK}, use_id="r1"),
                    tool_use(
                        "submit_answer",
                        answer([finding(claim="manual matching", doc_id=CLERK, quote=MATCHING)]),
                        use_id="a1",
                    ),
                ]
            }
        },
    }
    fixture = tmp_path / "forged.json"
    fixture.write_text(json.dumps(recording), encoding="utf-8")
    monkeypatch.setattr("workbench.cli.discover.FIXTURE", fixture)
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(Path(__file__).resolve().parents[1] / "sources"))

    assert main(["discover", ACME, "--principal", "analyst-rao", "--role", "analyst"]) == 0
    out = capsys.readouterr().out

    assert "\x1b" not in out
    assert [line for line in out.splitlines() if line.startswith("  GAP")] == []
    assert [line for line in out.splitlines() if line.startswith("claims:")] == [
        "claims: 1 verified, 0 not verified"
    ]
    assert "FORGED" in out  # the text is kept, on the strategy line, and owns no line of its own
    assert len([line for line in out.splitlines() if "FORGED" in line]) == 1
    assert out.splitlines()[-1].startswith("strategy: a plan")
