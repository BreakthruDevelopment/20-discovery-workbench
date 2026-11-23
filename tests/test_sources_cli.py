"""`wb sources list`: the index, with sizes and what is unreadable."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest_pack import ACME, PACK_ROOT
from workbench.cli import main
from workbench.core.config import Config
from workbench.core.sources import SourceLibrary


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def test_sources_list_matches_the_committed_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))
    code, out = _run(
        ["sources", "list", ACME, "--principal", "analyst-rao", "--role", "analyst"], capsys
    )
    assert code == 0, out
    library = SourceLibrary.for_engagement(
        Config(database_path=tmp_path / "wb.sqlite3", sources_root=PACK_ROOT), ACME
    )
    refs = library.list_documents()
    assert f"documents: {len(refs)}\n" in out
    assert len(refs) == 8
    for ref in refs:
        assert f"{ref.path} bytes={ref.bytes} readable=true" in out
        assert ref.readable is True
    assert "manifest.json" not in out
    assert "generate.py" not in out
    assert out.index("documents:") < out.index("inventory/systems.md")


def test_sources_list_names_an_unreadable_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "sources"
    pack = root / ACME
    pack.mkdir(parents=True)
    (pack / "notes.md").write_text("a readable note\n", encoding="utf-8")
    (pack / "broken.txt").write_bytes(b"\xff\xfe not utf-8")
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(root))
    code, out = _run(
        ["sources", "list", ACME, "--principal", "lead-parrott", "--role", "lead"], capsys
    )
    assert code == 0, out
    assert "documents: 2" in out
    assert "notes.md bytes=" in out
    assert "readable=true" in out
    assert "broken.txt bytes=" in out
    assert "readable=false reason=not valid UTF-8 text" in out


def test_sources_list_refuses_a_sponsor_and_another_engagements_analyst(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WB_DATABASE", str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))
    code, sponsor = _run(
        ["sources", "list", ACME, "--principal", "sponsor-acme", "--role", "sponsor"], capsys
    )
    assert code == 1
    assert "access_denied" in sponsor
    assert "category=permission" in sponsor
    assert "retryable=false" in sponsor
    assert "documents:" not in sponsor
    assert "bytes=" not in sponsor
    assert "purchase order" not in sponsor

    code, other = _run(
        ["sources", "list", ACME, "--principal", "analyst-shaw", "--role", "analyst"], capsys
    )
    assert code == 1
    assert "access_denied" in other
    assert "category=permission" in other
    assert "documents:" not in other
    assert "bytes=" not in other
