"""`wb demo` tells the recorded story and leaves a configured database alone."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tests.conftest_pack import PACK_ROOT
from workbench.cli import main
from workbench.coordinator.coordinator import DiscoveryCoordinator
from workbench.core.config import Config
from workbench.core.store import Store


def _fingerprint(path: Path) -> list[tuple[str, bytes]]:
    return [(item.name, item.read_bytes()) for item in sorted(path.parent.glob(path.name + "*"))]


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_the_demo_tells_the_story_twice_and_leaves_the_configured_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configured = tmp_path / "configured.sqlite3"
    with Store.open(Config(database_path=configured, sources_root=PACK_ROOT)) as store:
        store.build()
    before = _fingerprint(configured)
    created: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def spy(suffix: str | None = None, prefix: str | None = None, dir: str | None = None) -> str:
        path = real_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        created.append(path)
        return path

    monkeypatch.setattr(tempfile, "mkdtemp", spy)
    monkeypatch.setenv("WB_DATABASE", str(configured))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))
    monkeypatch.chdir(tmp_path)

    args = ["demo", "--principal", "lead-parrott", "--role", "lead"]
    code, first, err = _run(args, capsys)
    assert code == 0, err
    code, second, err = _run(args, capsys)
    assert code == 0, err
    assert first == second
    assert _fingerprint(configured) == before
    assert not (tmp_path / "workbench.sqlite3").exists()
    assert created
    assert all(not Path(path).exists() for path in created)
    assert str(configured) not in first
    assert "wb-demo-" not in first

    assert "demo: replay" in first
    assert "documents: 8" in first
    assert "coverage: 5 question(s), 4 answered, 1 failed" in first
    assert "GAP  q" in first
    assert "claims: 7 verified, 1 not verified" in first
    assert "conflicts: 1" in first
    assert "exception handling: level unknown" in first
    assert "invoice matching: level 2" in first
    assert "recorded_verified: false" in first
    assert "coverage_gaps_present:" in first
    assert "state: final" in first
    assert "accept_gaps: true" in first
    assert "HLP-4901" in first
    assert first.index("sources:") < first.index("discover:") < first.index("readout:")
    assert first.index("readout:") < first.index("trace:") < first.index("finalise:")
    assert first.index("coverage_gaps_present:") < first.index("state: final")


def test_an_analyst_cannot_finish_the_story_by_finalising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configured = tmp_path / "configured.sqlite3"
    configured.write_bytes(b"sentinel-not-a-database\n")
    before = configured.read_bytes()
    monkeypatch.setenv("WB_DATABASE", str(configured))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))
    code, out, err = _run(["demo", "--principal", "analyst-rao", "--role", "analyst"], capsys)
    assert code == 1, err
    assert "access_denied" in out
    assert "category=permission" in out
    assert "retryable=false" in out
    assert "finalise_readout" in out
    assert "state: final" not in out
    assert "accept_gaps: true" not in out
    assert configured.read_bytes() == before
    assert not Path(str(configured) + "-wal").exists()


def test_live_is_refused_before_discovery_for_an_analyst(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    configured = tmp_path / "configured.sqlite3"
    configured.write_bytes(b"sentinel-not-a-database\n")
    before = configured.read_bytes()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WB_DATABASE", raising=False)
    monkeypatch.setenv("WB_DATABASE", str(configured))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))

    async def boom(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("discovery must not start")

    monkeypatch.setattr(DiscoveryCoordinator, "discover", boom)
    code, out, err = _run(
        ["demo", "--principal", "analyst-rao", "--role", "analyst", "--live"], capsys
    )
    assert code == 1, err
    assert "access_denied" in out
    assert "run_live" in out
    assert "category=permission" in out
    assert "retryable=false" in out
    assert "demo:" not in out
    assert "coverage:" not in out
    assert configured.read_bytes() == before
    assert not (tmp_path / "workbench.sqlite3").exists()


def test_a_sponsor_is_refused_and_the_configured_database_stays_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WB_DATABASE", raising=False)
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))
    code, out, err = _run(["demo", "--principal", "sponsor-acme", "--role", "sponsor"], capsys)
    assert code == 1, err
    assert "access_denied" in out
    assert "category=permission" in out
    assert "documents:" not in out
    assert "coverage:" not in out
    assert not (tmp_path / "workbench.sqlite3").exists()
