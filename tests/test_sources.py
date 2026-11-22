"""One test per source-library rule, including the manifest refusal and a symlink out of the root.

The symlink fixture is built here, at test time: the committed pack contains no symlinks (spec,
20.3), so the escape case has no fixture to inherit and must be constructed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import ACME, ACME_QUOTE, Fixture
from workbench.core.errors import (
    InvalidInput,
    SourceOutsideRoot,
    SourceRefused,
    SourceUnreadable,
)
from workbench.core.sources import MIN_QUOTE_CHARS, SourceLibrary

CLERK = "interviews/ap-clerk.md"


def _library(
    root: Path, *, engagement_id: str = ACME, file_cap: int = 4_096, run_cap: int = 16_384
) -> SourceLibrary:
    return SourceLibrary(
        root, engagement_id=engagement_id, max_file_bytes=file_cap, max_run_bytes=run_cap
    )


# ---- the index ----------------------------------------------------------------------------


def test_the_index_lists_only_text_documents(fixture: Fixture) -> None:
    paths = [ref.path for ref in fixture.acme_library.list_documents()]
    assert paths == ["interviews/ap-clerk.md", "systems-inventory.csv"]


def test_the_index_is_sorted_and_deterministic(fixture: Fixture) -> None:
    first = fixture.acme_library.list_documents()
    second = _library(fixture.config.engagement_sources_root(ACME)).list_documents()
    assert first == second
    assert [ref.path for ref in first] == sorted(ref.path for ref in first)


def test_the_index_carries_sizes_and_digests(fixture: Fixture) -> None:
    (clerk,) = [r for r in fixture.acme_library.list_documents() if r.path == CLERK]
    body = (fixture.config.engagement_sources_root(ACME) / CLERK).read_bytes()
    assert clerk.bytes == len(body)
    assert len(clerk.sha256) == 64
    assert clerk.readable is True


def test_a_missing_tree_is_an_empty_library(tmp_path: Path) -> None:
    """The second seeded engagement has no committed pack; an empty index is the honest answer."""
    assert _library(tmp_path / "absent").list_documents() == []


def test_an_undecodable_file_is_listed_as_unreadable(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "broken.txt").write_bytes(b"\xff\xfe not utf-8")
    (ref,) = _library(root).list_documents()
    assert ref.readable is False
    assert ref.unread_reason is not None


# ---- the manifest and the extension allowlist ---------------------------------------------


def test_the_manifest_is_refused(fixture: Fixture) -> None:
    with pytest.raises(SourceRefused):
        fixture.acme_library.read("manifest.json")


def test_the_manifest_is_absent_from_the_index(fixture: Fixture) -> None:
    assert all("manifest" not in ref.path for ref in fixture.acme_library.list_documents())


def test_a_manifest_with_a_served_extension_is_still_refused(tmp_path: Path) -> None:
    """The stem refusal is the second of two independent guards: `.md` passes the allowlist."""
    root = tmp_path / "pack"
    root.mkdir()
    (root / "manifest.md").write_text("the answer key\n", encoding="utf-8")
    library = _library(root)
    with pytest.raises(SourceRefused):
        library.read("manifest.md")
    assert library.list_documents() == []


def test_the_generator_script_is_refused(fixture: Fixture) -> None:
    with pytest.raises(SourceRefused):
        fixture.acme_library.read("generate.py")


# ---- the root -----------------------------------------------------------------------------


def test_a_parent_traversal_is_refused(fixture: Fixture) -> None:
    with pytest.raises(SourceOutsideRoot):
        fixture.acme_library.read("../northwind-ar/ar-notes.md")


def test_an_absolute_path_is_refused(fixture: Fixture) -> None:
    with pytest.raises(SourceOutsideRoot):
        fixture.acme_library.read("/etc/hostname")


def test_a_symlink_out_of_the_root_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("a document that is not this engagement's evidence\n", encoding="utf-8")
    root = tmp_path / "pack"
    root.mkdir()
    (root / "escape.md").symlink_to(outside)
    with pytest.raises(SourceOutsideRoot):
        _library(root).read("escape.md")


def test_a_symlink_out_of_the_root_is_absent_from_the_index(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("not this engagement's evidence\n", encoding="utf-8")
    root = tmp_path / "pack"
    root.mkdir()
    (root / "escape.md").symlink_to(outside)
    (root / "real.md").write_text("evidence\n", encoding="utf-8")
    assert [ref.path for ref in _library(root).list_documents()] == ["real.md"]


def test_a_symlink_inside_the_root_is_served(tmp_path: Path) -> None:
    """The check is on where a path lands, not on whether a link was involved."""
    root = tmp_path / "pack"
    root.mkdir()
    (root / "real.md").write_text("evidence inside the root\n", encoding="utf-8")
    (root / "alias.md").symlink_to(root / "real.md")
    assert _library(root).read("alias.md").text == "evidence inside the root\n"


def test_an_empty_or_padded_path_is_refused(fixture: Fixture) -> None:
    for candidate in ("", " ", f" {CLERK}", f"{CLERK} "):
        with pytest.raises(InvalidInput):
            fixture.acme_library.read(candidate)


def test_a_nul_byte_in_a_path_is_refused(fixture: Fixture) -> None:
    with pytest.raises(InvalidInput):
        fixture.acme_library.read("interviews/ap\x00-clerk.md")


def test_a_missing_document_inside_the_root_is_unreadable(fixture: Fixture) -> None:
    with pytest.raises(SourceUnreadable):
        fixture.acme_library.read("interviews/absent.md")


def test_a_directory_is_refused(fixture: Fixture) -> None:
    with pytest.raises(SourceRefused):
        fixture.acme_library.read("interviews")


# ---- the byte caps ------------------------------------------------------------------------


def test_a_whole_document_is_served_untrimmed(fixture: Fixture) -> None:
    served = fixture.acme_library.read(CLERK)
    assert served.truncated is False
    assert served.unread_reason is None
    assert ACME_QUOTE in served.text


def test_the_per_file_cap_trims_and_states_why(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "long.md").write_text("x" * 500, encoding="utf-8")
    served = _library(root, file_cap=100).read("long.md")
    assert len(served.text) == 100
    assert served.truncated is True
    assert served.unread_reason is not None
    assert "per-file" in served.unread_reason


def test_the_per_run_cap_trims_and_states_why(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "a.md").write_text("a" * 100, encoding="utf-8")
    (root / "b.md").write_text("b" * 100, encoding="utf-8")
    library = _library(root, file_cap=1_000, run_cap=150)
    assert library.read("a.md").truncated is False
    second = library.read("b.md")
    assert len(second.text) == 50
    assert second.truncated is True
    assert second.unread_reason is not None
    assert "per-run" in second.unread_reason


def test_an_exhausted_per_run_cap_serves_nothing_and_says_so(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "a.md").write_text("a" * 100, encoding="utf-8")
    (root / "b.md").write_text("b" * 100, encoding="utf-8")
    library = _library(root, file_cap=1_000, run_cap=100)
    library.read("a.md")
    third = library.read("b.md")
    assert third.text == ""
    assert third.truncated is True
    assert third.unread_reason is not None


def test_a_trim_inside_a_multibyte_character_does_not_fail(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "accents.md").write_text("éééééé", encoding="utf-8")
    served = _library(root, file_cap=5).read("accents.md")
    assert served.text == "éé"
    assert served.truncated is True


def test_a_nonpositive_cap_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidInput):
        SourceLibrary(tmp_path, engagement_id=ACME, max_file_bytes=0, max_run_bytes=10)


def test_a_library_is_rooted_at_one_named_engagement(tmp_path: Path) -> None:
    with pytest.raises(InvalidInput):
        SourceLibrary(tmp_path, engagement_id="  ", max_file_bytes=10, max_run_bytes=10)


# ---- verify_quote -------------------------------------------------------------------------


def test_a_verbatim_quote_verifies(fixture: Fixture) -> None:
    assert fixture.acme_library.verify_quote(CLERK, ACME_QUOTE) is True


def test_a_fabricated_quote_does_not_verify(fixture: Fixture) -> None:
    assert (
        fixture.acme_library.verify_quote(
            CLERK, "Matching is fully automated and has been since 2019."
        )
        is False
    )


def test_a_reworded_quote_does_not_verify(fixture: Fixture) -> None:
    """Whitespace is not collapsed and case is not folded: rewording is not quoting."""
    assert fixture.acme_library.verify_quote(CLERK, ACME_QUOTE.replace(" ", "  ")) is False
    assert fixture.acme_library.verify_quote(CLERK, ACME_QUOTE.upper()) is False


def test_a_quote_shorter_than_the_floor_is_refused(fixture: Fixture) -> None:
    with pytest.raises(InvalidInput):
        fixture.acme_library.verify_quote(CLERK, "the")
    assert MIN_QUOTE_CHARS > 3


def test_an_overlong_quote_is_refused(fixture: Fixture) -> None:
    with pytest.raises(InvalidInput):
        fixture.acme_library.verify_quote(CLERK, "x" * 5_000)


def test_verify_quote_ignores_the_byte_caps(tmp_path: Path) -> None:
    """A quote is checked against the document, not against what a subagent was shown."""
    root = tmp_path / "pack"
    root.mkdir()
    tail = "The exception queue was decommissioned in March and never replaced."
    (root / "long.md").write_text(("x" * 500) + "\n" + tail + "\n", encoding="utf-8")
    library = _library(root, file_cap=50, run_cap=50)
    assert library.read("long.md").truncated is True
    assert library.verify_quote("long.md", tail) is True


def test_verify_quote_refuses_a_path_outside_the_root(fixture: Fixture) -> None:
    with pytest.raises(SourceOutsideRoot):
        fixture.acme_library.verify_quote("../northwind-ar/ar-notes.md", ACME_QUOTE)


def test_verify_quote_refuses_the_manifest(fixture: Fixture) -> None:
    with pytest.raises(SourceRefused):
        fixture.acme_library.verify_quote("manifest.json", "planted_facts manual three-way")


def test_crlf_line_endings_do_not_defeat_a_quote(tmp_path: Path) -> None:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "dos.md").write_bytes(b"A sentence split\r\nover two lines of evidence.\r\n")
    assert _library(root).verify_quote("dos.md", "A sentence split\nover two lines") is True


# ---- regressions from the first review round ------------------------------------------------


def test_a_document_id_carries_its_engagement(fixture: Fixture) -> None:
    from workbench.core.sources import document_id

    assert document_id("acme-p2p", "a.md") != document_id("northwind-ar", "a.md")


def test_a_document_id_is_injective_over_separators() -> None:
    """Collapsing `/` and `.` into `-` made `a/b.md` and `a--b.md` the same id."""
    from workbench.core.sources import document_id

    paths = ["a/b.md", "a--b.md", "x.y.md", "x-y.md", "a/b/c.md", "a--b--c.md"]
    ids = [document_id(ACME, path) for path in paths]
    assert len(set(ids)) == len(paths)


def test_a_symlink_named_like_a_document_cannot_surface_the_manifest(tmp_path: Path) -> None:
    """`_entries` screened the link's own name, `_resolve` the resolved one: a link named
    `notes.md` pointing at `manifest.json` was listed with the manifest's real size and digest."""
    root = tmp_path / "pack"
    root.mkdir()
    (root / "manifest.json").write_text('{"planted_facts": ["the answer key"]}\n', encoding="utf-8")
    (root / "notes.md").symlink_to(root / "manifest.json")
    library = _library(root)
    assert library.list_documents() == []
    with pytest.raises(SourceRefused):
        library.read("notes.md")


def test_a_symlinked_directory_component_out_of_the_root_is_refused(tmp_path: Path) -> None:
    """The variant people get wrong: the escape is a directory, not the file."""
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "notes.md").write_text("another engagement's evidence entirely\n", encoding="utf-8")
    root = tmp_path / "pack"
    root.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    library = _library(root)
    with pytest.raises(SourceOutsideRoot):
        library.read("linked/notes.md")
    assert library.list_documents() == []
