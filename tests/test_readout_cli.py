"""`wb readout`, `wb trace` and `wb finalise` on the committed pack, at zero cost.

The discovery recording is 20.4's: five questions, one throttled subagent, one fabricated quote.
This file is what that recording becomes once it is read back. Coverage is the failed question,
not the coverage the readout fixture invents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.conftest_pack import ACME, CYCLE, FABRICATED, INJECTION, MATCHING, NO_DUPES, PACK_ROOT
from workbench.cli import main
from workbench.core.config import Config
from workbench.core.principals import Role
from workbench.core.store import Store


def _configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    database = tmp_path / "wb.sqlite3"
    monkeypatch.setenv("WB_DATABASE", str(database))
    monkeypatch.setenv("WB_SOURCES_ROOT", str(PACK_ROOT))
    return database


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(args)
    return code, capsys.readouterr().out


def _who(principal: str, role: str) -> list[str]:
    return ["--principal", principal, "--role", role]


def _discover(capsys: pytest.CaptureFixture[str]) -> None:
    code, out = _run(["discover", ACME, *_who("analyst-rao", "analyst")], capsys)
    assert code == 0, out


def _rows(value: object) -> list[dict[str, Any]]:
    assert isinstance(value, list)
    rows: list[dict[str, Any]] = []
    for item in value:
        assert isinstance(item, dict)
        rows.append({str(key): item[key] for key in item})
    return rows


def _open(database: Path) -> tuple[Config, Store]:
    return Config(database_path=database, sources_root=PACK_ROOT), Store.open(
        Config(database_path=database, sources_root=PACK_ROOT)
    )


# ---- the readout ----------------------------------------------------------------------------


def test_readout_renders_coverage_first_and_keeps_the_contradiction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Statement 5.6 on the committed recording.

    Coverage is the throttled question, printed before anything else. Exception handling has no
    verified claim, so its level is unknown. The duplicate-payment disagreement is both quotes.
    The fixture's level 5, its average, and its claim of a finished run do not survive.
    """
    database = _configure(tmp_path, monkeypatch)
    _discover(capsys)
    code, out = _run(["readout", ACME, *_who("analyst-rao", "analyst")], capsys)
    assert code == 0, out

    assert out.index("\ncoverage:") < out.index("\nconflicts:") < out.index("\nmaturity:")
    assert out.index("\nmaturity:") < out.index("\noutcomes:") < out.index("\nroi:")
    assert out.index("\nroi:") < out.index("\nroadmap:")
    assert "client: Acme Industrial" in out
    assert "readout: draft" in out
    assert "do something with AI" not in out
    assert "coverage: 5 question(s), 4 answered, 1 failed" in out
    gap_lines = [line for line in out.splitlines() if line.startswith("  GAP ")]
    assert len(gap_lines) == 1
    assert "What happens to an invoice that fails the match" in gap_lines[0]
    assert "conflicts: 1" in out
    assert NO_DUPES in out
    assert "HLP-4901" in out
    assert "invoice matching: level 2" in out
    assert "exception handling: level unknown" in out
    assert "level 5" not in out
    assert "effectively stopped" not in out
    assert "On balance" not in out
    assert "uniformly high" not in out
    assert FABRICATED not in out
    assert INJECTION not in out
    assert "roi: none" not in out
    assert "Stop the undocumented mailbox copy" in out

    config, store = _open(database)
    del config
    with store:
        analyst = store.load_principal("analyst-rao", Role.ANALYST)
        verified = store.claims(analyst, ACME, verified_only=True)
        by_quote = {claim.quote: claim for claim in verified}
        readout = store.readout(analyst, ACME)
        maturity = _rows(readout.maturity)
        matching = next(item for item in maturity if item["dimension"] == "invoice matching")
        exception = next(item for item in maturity if item["dimension"] == "exception handling")
        cycle = next(item for item in maturity if item["dimension"] == "cycle time")
        assert matching["level"] == 2
        assert matching["claim_ids"] == [by_quote[MATCHING].id]
        assert matching["claim_ids"] != ["C1"]
        assert exception["level"] == "unknown"
        assert exception["claim_ids"] == []
        assert cycle["level"] == 3
        assert cycle["claim_ids"] == [by_quote[CYCLE].id]
        gaps = store.failed_run_question_ids(analyst, ACME)
        coverage = readout.coverage
        assert isinstance(coverage, dict)
        assert coverage["questions_total"] == 5
        assert coverage["answered"] == 4
        assert coverage["failed"] == 1
        recorded_gaps = coverage["gaps"]
        assert recorded_gaps == [
            {
                "question_id": gaps[0],
                "reason": (
                    "subagent run failed: transient, retryable=true: "
                    "What happens to an invoice that fails the match, and who picks it up?"
                ),
            }
        ]
        outcomes = _rows(readout.outcomes)
        conflicts = [item for item in outcomes if item.get("conflict") is True]
        assert len(conflicts) == 1
        stored_quotes = {quote["quote"] for quote in conflicts[0]["quotes"]}
        assert NO_DUPES in stored_quotes
        assert any("HLP-4901" in str(quote) for quote in stored_quotes)
        assert "effectively stopped" not in json.dumps(outcomes)
        roi = readout.roi
        assert isinstance(roi, dict)
        assert roi["basis_claim_ids"] == [by_quote[MATCHING].id, by_quote[CYCLE].id]
        injection = next(claim for claim in store.claims(analyst, ACME) if claim.quote == INJECTION)
        blob = json.dumps(
            {"maturity": readout.maturity, "outcomes": readout.outcomes, "roi": readout.roi}
        )
        assert injection.id not in blob
        assert INJECTION not in blob


# ---- trace ----------------------------------------------------------------------------------


def test_trace_shows_an_unverified_quote_and_the_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database = _configure(tmp_path, monkeypatch)
    _discover(capsys)
    _config, store = _open(database)
    with store:
        analyst = store.load_principal("analyst-rao", Role.ANALYST)
        fabricated = next(
            claim for claim in store.claims(analyst, ACME) if claim.quote == FABRICATED
        )
        claim_id = fabricated.id
    code, out = _run(["trace", claim_id, *_who("analyst-rao", "analyst")], capsys)
    assert code == 0, out
    assert "recorded_verified: false" in out
    assert "live_verified: false" in out
    assert "the quote is not present verbatim in the document it names" in out
    assert out.index("recorded_verified:") < out.index("quote:")
    assert out.index("live_verified:") < out.index("quote:")
    assert FABRICATED in out
    document = next(line for line in out.splitlines() if line.startswith("document:"))
    assert not document.split("document:", 1)[1].strip().startswith("/")


def test_trace_and_a_draft_readout_refuse_the_people_who_must_not_see_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A sponsor has no trace and no draft. Another engagement's analyst has neither quote."""
    database = _configure(tmp_path, monkeypatch)
    _discover(capsys)
    _config, store = _open(database)
    with store:
        analyst = store.load_principal("analyst-rao", Role.ANALYST)
        claim_id = next(
            claim.id for claim in store.claims(analyst, ACME) if claim.quote == FABRICATED
        )

    code, sponsor_readout = _run(["readout", ACME, *_who("sponsor-acme", "sponsor")], capsys)
    assert code == 1
    assert "access_denied" in sponsor_readout
    assert "category=permission" in sponsor_readout
    assert "retryable=false" in sponsor_readout
    assert "Acme Industrial" not in sponsor_readout
    assert "procure-to-pay" not in sponsor_readout
    assert "coverage:" not in sponsor_readout
    assert FABRICATED not in sponsor_readout
    assert NO_DUPES not in sponsor_readout

    code, sponsor_trace = _run(["trace", claim_id, *_who("sponsor-acme", "sponsor")], capsys)
    assert code == 1
    assert "access_denied" in sponsor_trace
    assert "category=permission" in sponsor_trace
    assert FABRICATED not in sponsor_trace
    assert "recorded_verified" not in sponsor_trace

    code, foreign = _run(["trace", claim_id, *_who("analyst-shaw", "analyst")], capsys)
    assert code == 1
    assert "access_denied" in foreign
    assert "category=permission" in foreign
    assert "retryable=false" in foreign
    assert FABRICATED not in foreign
    assert claim_id not in foreign


def test_trace_of_an_unknown_claim_echoes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(tmp_path, monkeypatch)
    marker = "claim-marker-not-a-real-id"
    code, out = _run(["trace", marker, *_who("analyst-rao", "analyst")], capsys)
    assert code == 1
    assert "not_found" in out
    assert "category=business" in out
    assert marker not in out


# ---- finalise -------------------------------------------------------------------------------


def test_finalise_refuses_the_gap_unless_it_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gap the readout names is the gap finalise refuses. Accepting it is recorded."""
    database = _configure(tmp_path, monkeypatch)
    _discover(capsys)
    code, refused = _run(["finalise", ACME, *_who("lead-parrott", "lead")], capsys)
    assert code == 1
    assert "coverage_gaps_present" in refused
    assert "category=business" in refused
    assert "retryable=false" in refused

    code, accepted = _run(
        ["finalise", ACME, *_who("lead-parrott", "lead"), "--accept-gaps"], capsys
    )
    assert code == 0, accepted
    assert "state: final" in accepted
    assert "finalised_by: lead-parrott" in accepted
    assert "accept_gaps: true" in accepted

    code, again = _run(["finalise", ACME, *_who("lead-parrott", "lead"), "--accept-gaps"], capsys)
    assert code == 1
    assert "already_final" in again
    assert "category=business" in again
    assert "retryable=false" in again

    config = Config(database_path=database, sources_root=PACK_ROOT)
    with Store.open(config) as store:
        lead = store.load_principal("lead-parrott", Role.LEAD)
        assert store.finalisation_accepted_gaps(lead, ACME) is True


def test_a_final_readout_is_rendered_for_the_sponsor_without_calling_the_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database = _configure(tmp_path, monkeypatch)
    _discover(capsys)
    code, _out = _run(["readout", ACME, *_who("analyst-rao", "analyst")], capsys)
    assert code == 0
    code, _accepted = _run(
        ["finalise", ACME, *_who("lead-parrott", "lead"), "--accept-gaps"], capsys
    )
    assert code == 0

    def _boom(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("a final readout must be rendered as stored")

    monkeypatch.setattr("workbench.cli.readout.synthesise", _boom)
    monkeypatch.setattr("workbench.cli.readout.LiveSource", _boom)
    # A lead's `--live` on a final readout and a sponsor's plain read both get the stored
    # readout. The model is never called for either: `synthesise` and `LiveSource` are trapped.
    code, lead_out = _run(["readout", ACME, *_who("lead-parrott", "lead"), "--live"], capsys)
    assert code == 0, lead_out
    assert "readout: final" in lead_out
    code, out = _run(["readout", ACME, *_who("sponsor-acme", "sponsor")], capsys)
    assert code == 0, out
    assert out == lead_out
    assert "client: Acme Industrial" in out
    assert "readout: final" in out
    assert "coverage: 5 question(s), 4 answered, 1 failed" in out
    assert NO_DUPES in out
    assert "HLP-4901" in out
    assert "do something with AI" not in out
    # The database the test opened above is the one the command used.
    assert database.is_file()


def test_an_analyst_cannot_finalise_or_synthesise_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(tmp_path, monkeypatch)
    code, finalise = _run(["finalise", ACME, *_who("analyst-rao", "analyst")], capsys)
    assert code == 1
    assert "access_denied" in finalise
    assert "category=permission" in finalise
    assert "retryable=false" in finalise
    assert "coverage:" not in finalise

    code, live = _run(["readout", ACME, *_who("analyst-rao", "analyst"), "--live"], capsys)
    assert code == 1
    assert "access_denied" in live
    assert "category=permission" in live
    assert "retryable=false" in live
    assert "run_live" in live
    assert "coverage:" not in live
    assert "Acme Industrial" not in live
    assert "invoice matching" not in live


def test_a_sponsor_is_refused_live_on_a_final_readout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _configure(tmp_path, monkeypatch)
    _discover(capsys)
    code, _out = _run(["readout", ACME, *_who("analyst-rao", "analyst")], capsys)
    assert code == 0
    code, _accepted = _run(
        ["finalise", ACME, *_who("lead-parrott", "lead"), "--accept-gaps"], capsys
    )
    assert code == 0

    code, live = _run(["readout", ACME, *_who("sponsor-acme", "sponsor"), "--live"], capsys)
    assert code == 1
    assert "access_denied" in live
    assert "category=permission" in live
    assert "retryable=false" in live
    assert "run_live" in live
    assert "readout:" not in live
    assert "Acme Industrial" not in live
