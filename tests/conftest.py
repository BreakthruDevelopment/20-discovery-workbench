"""Fixtures: a built store on a temporary database, and a small source tree per engagement.

Nothing here touches a configured database or the committed `sources/` tree: every test gets its
own `tmp_path`, which is also what the demo and the smoke script will do in 20.6.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import count
from pathlib import Path

import pytest

from workbench.core.config import Config
from workbench.core.principals import Principal, Role
from workbench.core.sources import SourceLibrary
from workbench.core.store import Store

ACME = "acme-p2p"
NORTHWIND = "northwind-ar"

#: A planted sentence long enough to pass the minimum-quote floor, used across the quote tests.
ACME_QUOTE = "Three-way matching is done by hand on every invoice over ten thousand dollars."
NORTHWIND_QUOTE = "Remittance advice arrives as a PDF attachment and is retyped by the AR clerk."


@dataclass(frozen=True, slots=True)
class Fixture:
    """Everything a test needs: the store, the config, and a library per engagement."""

    store: Store
    config: Config
    acme_library: SourceLibrary
    northwind_library: SourceLibrary

    def library(self, engagement_id: str) -> SourceLibrary:
        return self.acme_library if engagement_id == ACME else self.northwind_library


def _write_tree(root: Path) -> None:
    """Two engagements' worth of evidence, plus the one file that must never be served."""
    acme = root / ACME
    (acme / "interviews").mkdir(parents=True)
    (acme / "interviews" / "ap-clerk.md").write_text(
        "# AP clerk\n\n"
        f"{ACME_QUOTE}\n\n"
        "There is no exception queue, so a mismatch sits in a shared mailbox.\n",
        encoding="utf-8",
    )
    (acme / "systems-inventory.csv").write_text(
        "system,owner,notes\nWebLogic,IT,undocumented integration to the supplier portal\n",
        encoding="utf-8",
    )
    # The answer key. Never served: refused by its stem and, being JSON, by the extension
    # allowlist as well.
    (acme / "manifest.json").write_text(
        '{"planted_facts": ["manual three-way matching"]}\n', encoding="utf-8"
    )
    # The generator script, refused by the extension allowlist.
    (acme / "generate.py").write_text("# builds the pack\n", encoding="utf-8")

    northwind = root / NORTHWIND
    northwind.mkdir(parents=True)
    (northwind / "ar-notes.md").write_text(f"# AR notes\n\n{NORTHWIND_QUOTE}\n", encoding="utf-8")


@pytest.fixture
def fixture(tmp_path: Path) -> Iterator[Fixture]:
    sources_root = tmp_path / "sources"
    _write_tree(sources_root)
    config = Config(
        database_path=tmp_path / "workbench.sqlite3",
        sources_root=sources_root,
        max_source_file_bytes=4_096,
        max_source_run_bytes=16_384,
    )
    ids = count(1)
    with Store.open(
        config,
        now=lambda: datetime(2026, 11, 21, 12, 0, tzinfo=UTC),
        new_id=lambda: f"id-{next(ids):04d}",
    ) as store:
        store.build()
        yield Fixture(
            store=store,
            config=config,
            acme_library=SourceLibrary(
                config.engagement_sources_root(ACME),
                max_file_bytes=config.max_source_file_bytes,
                max_run_bytes=config.max_source_run_bytes,
            ),
            northwind_library=SourceLibrary(
                config.engagement_sources_root(NORTHWIND),
                max_file_bytes=config.max_source_file_bytes,
                max_run_bytes=config.max_source_run_bytes,
            ),
        )


@pytest.fixture
def analyst(fixture: Fixture) -> Principal:
    return fixture.store.load_principal("analyst-rao", Role.ANALYST)


@pytest.fixture
def lead(fixture: Fixture) -> Principal:
    return fixture.store.load_principal("lead-parrott", Role.LEAD)


@pytest.fixture
def sponsor(fixture: Fixture) -> Principal:
    return fixture.store.load_principal("sponsor-acme", Role.SPONSOR)


@pytest.fixture
def other_analyst(fixture: Fixture) -> Principal:
    """Assigned to the OTHER engagement. The owner filter's counter-example."""
    return fixture.store.load_principal("analyst-shaw", Role.ANALYST)
