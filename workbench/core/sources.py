"""The read-only source library: the only module in this repo that opens a file under `sources/`.

What it guarantees, and why each one is here rather than in a caller:

* **One resolved root.** The root is resolved once, at construction. Every request is joined to it,
  resolved, and refused unless it is still inside it. `Path.resolve()` follows symlinks, so a link
  inside the root aiming out of it resolves outside and is refused by the same check -- which is
  why there is no separate symlink rule to forget. The pack itself contains no symlinks; the escape
  fixture is built at test time (`tests/test_sources.py`).
* **A positive allowlist of extensions.** `.md`, `.txt` and `.csv` are served; everything else is
  refused. Sources are text by the spec -- no OCR, no PDF -- so the allowlist costs nothing, and it
  refuses the pack's generator script and its manifest (`.json`/`.yaml`/`.toml`) without needing to
  know their names. The manifest is the answer key: a model that could read it would be scored
  against its own crib.
* **The manifest refused by name as well.** A `manifest.md` would pass the allowlist, so any file
  whose stem is `manifest`, at any depth, is refused outright. Two independent refusals for the one
  file that must never be served.
* **Byte caps, per file and per run.** A file over the per-file cap is served trimmed, with a stated
  `unread_reason`; a library instance that has served its per-run cap serves no more text, with a
  stated reason. Never a silent trim: a subagent reports `unread[]` from these reasons, and the
  readout turns them into coverage rather than into a confident claim over half a document.
* **`verify_quote`, against the whole file.** Provenance is checked in code, not asked of a model.
  It reads the document in full, independent of both caps, and returns a bool: a quote either is or
  is not in the document. It cannot be used to read text out, because it returns no text.

Nothing here writes, moves, creates or deletes anything. Every file is opened read-only, as bytes.
"""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from workbench.core.errors import (
    InvalidInput,
    SourceOutsideRoot,
    SourceRefused,
    SourceUnreadable,
)

#: Served extensions. A positive allowlist, so a new file type is refused until someone adds it.
ALLOWED_SUFFIXES = frozenset({".md", ".txt", ".csv"})

#: Never served, at any depth, whatever its extension: the pack's manifest is the answer key.
REFUSED_STEMS = frozenset({"manifest"})

#: A quote shorter than this is refused rather than verified. Without a floor, "the" is present
#: verbatim in every document and a model could mark any claim provenanced by quoting a stopword.
MIN_QUOTE_CHARS = 16

#: And an upper bound, so a "quote" cannot be a whole document pasted back at us.
MAX_QUOTE_CHARS = 2_000


@dataclass(frozen=True, slots=True)
class SourceRef:
    """One entry in the source index: what a document is, without its contents.

    This is what the `discovery-plan` task is given -- ids, paths, sizes, and what is unreadable --
    and what `store.index_sources` writes to `source_document`. `unread_reason` is set when the
    file exists but cannot be served as text at all; a trim is reported per read, not here.
    """

    doc_id: str
    path: str
    bytes: int
    sha256: str
    readable: bool
    unread_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SourceText:
    """One document's text as served, and the truth about whether all of it was served."""

    doc_id: str
    path: str
    text: str
    truncated: bool
    unread_reason: str | None = None


def _normalise_newlines(text: str) -> str:
    """CRLF and CR to LF. A line-ending difference is an encoding detail, not a text difference."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def document_id(relative_path: str) -> str:
    """The stable id for a document at `relative_path` within one engagement.

    Derived from the path rather than assigned, so the index is deterministic: re-indexing the same
    tree produces the same ids, and a recorded fixture keeps naming the same documents.
    """
    slug = relative_path.replace("/", "--").replace(".", "-")
    return f"doc-{slug}"


class SourceLibrary:
    """A read-only view of one engagement's evidence tree.

    One instance per run. The per-run byte cap is instance state, so the ceiling is over everything
    this run has read -- across subagents, since they share the library -- and a fan-out cannot
    gather the whole pack by asking for it a file at a time.
    """

    def __init__(
        self,
        root: Path,
        *,
        max_file_bytes: int,
        max_run_bytes: int,
    ) -> None:
        if max_file_bytes <= 0 or max_run_bytes <= 0:
            raise InvalidInput("source byte caps must be positive")
        self._max_file_bytes = max_file_bytes
        self._max_run_bytes = max_run_bytes
        self._bytes_served = 0
        # `strict=False`: a missing tree is an empty library, not a crash. The second engagement in
        # the seed has no committed pack, and an empty index is the honest answer for it.
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    @property
    def bytes_served(self) -> int:
        return self._bytes_served

    @property
    def run_bytes_remaining(self) -> int:
        return max(0, self._max_run_bytes - self._bytes_served)

    def _resolve(self, relative_path: str) -> Path:
        """The absolute path for `relative_path`, or a refusal. The one gate on the filesystem."""
        if not relative_path or relative_path.strip() != relative_path:
            raise InvalidInput("a document path is required and carries no surrounding whitespace")
        if "\x00" in relative_path:
            raise InvalidInput("a document path contains no NUL byte")
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise SourceOutsideRoot("a document path is relative to the engagement's source root")
        resolved = (self._root / candidate).resolve()
        # `is_relative_to` on the resolved pair is the whole check: `..` segments are gone and any
        # symlink has been followed, so a link out of the tree lands outside the root here. The
        # root itself satisfies it and is then refused by the suffix check below, as a directory.
        if not resolved.is_relative_to(self._root):
            raise SourceOutsideRoot("a document path resolves outside the engagement's source root")
        if resolved.stem.lower() in REFUSED_STEMS:
            raise SourceRefused("the source library does not serve the pack manifest")
        if resolved.suffix.lower() not in ALLOWED_SUFFIXES:
            raise SourceRefused("the source library serves only text documents")
        return resolved

    def _entries(self) -> Iterator[Path]:
        """Every servable file under the root, sorted, with refused paths already dropped."""
        if not self._root.is_dir():
            return
        for path in sorted(self._root.rglob("*")):
            if not path.is_file():
                continue
            if path.stem.lower() in REFUSED_STEMS:
                continue
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(self._root):
                # A symlink inside the tree pointing out of it. Left out of the index entirely:
                # it is not this engagement's evidence, so it is not listed as unreadable either.
                continue
            yield path

    def list_documents(self) -> list[SourceRef]:
        """The source index: every servable document, with its size, digest and readability.

        Sorted by path, so the index -- and therefore the plan prompt built from it and the
        `source_document` rows written from it -- is deterministic.
        """
        refs: list[SourceRef] = []
        for path in self._entries():
            relative = path.relative_to(self._root).as_posix()
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            readable = True
            reason: str | None = None
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                readable = False
                reason = "not valid UTF-8 text"
            refs.append(
                SourceRef(
                    doc_id=document_id(relative),
                    path=relative,
                    bytes=len(raw),
                    sha256=digest,
                    readable=readable,
                    unread_reason=reason,
                )
            )
        return refs

    def _read_bytes(self, relative_path: str) -> tuple[Path, bytes]:
        resolved = self._resolve(relative_path)
        if not resolved.is_file():
            raise SourceUnreadable("no such document in the engagement's source root")
        return resolved, resolved.read_bytes()

    def read(self, relative_path: str) -> SourceText:
        """Serve one document as text, trimmed to the caps, with the trim stated.

        The per-run cap is spent by what is actually served, so a trimmed read spends only the
        bytes it handed back.
        """
        resolved, raw = self._read_bytes(relative_path)
        relative = resolved.relative_to(self._root).as_posix()
        doc_id = document_id(relative)
        total = len(raw)

        if self.run_bytes_remaining == 0:
            return SourceText(
                doc_id=doc_id,
                path=relative,
                text="",
                truncated=True,
                unread_reason=(
                    f"the per-run source cap of {self._max_run_bytes} bytes was already reached; "
                    "none of this document was read"
                ),
            )

        allowance = min(self._max_file_bytes, self.run_bytes_remaining)
        served = raw[:allowance]
        reasons: list[str] = []
        if total > allowance:
            binding = (
                "the per-file cap"
                if allowance == self._max_file_bytes
                else "what was left of the per-run cap"
            )
            reasons.append(
                f"trimmed to the first {allowance} of {total} bytes by {binding} "
                f"(per-file {self._max_file_bytes} bytes, per-run {self._max_run_bytes} bytes)"
            )

        # `errors="ignore"` only at the trim boundary would hide a genuinely undecodable file, so
        # decode strictly and report that separately; a cut multi-byte character at the boundary is
        # dropped by `_decode_prefix`, which is a trim, not a decode failure.
        try:
            text = _decode_prefix(served, truncated=total > allowance)
        except UnicodeDecodeError as exc:
            raise SourceUnreadable("a document under the source root is not valid UTF-8") from exc

        self._bytes_served += len(served)
        return SourceText(
            doc_id=doc_id,
            path=relative,
            text=_normalise_newlines(text),
            truncated=total > allowance,
            unread_reason="; ".join(reasons) or None,
        )

    def verify_quote(self, relative_path: str, quote: str) -> bool:
        """Whether `quote` appears verbatim in the document at `relative_path`.

        Reads the document in full, past both byte caps, because the question is about the document
        and not about what some subagent was shown. It returns a bool and no text, so it is not a
        way to read a capped document out a substring at a time -- an attacker already holds the
        candidate string.

        Verbatim, with exactly two concessions, both of which are encoding rather than wording:
        line endings are normalised to LF, and both sides are NFC-normalised so a decomposed
        accent matches its composed form. Whitespace is **not** collapsed and case is **not**
        folded: a model that rewrapped or retyped a sentence did not quote it, and a provenance
        check that forgives rewording is not one.
        """
        if len(quote) < MIN_QUOTE_CHARS:
            raise InvalidInput(f"a quote is at least {MIN_QUOTE_CHARS} characters")
        if len(quote) > MAX_QUOTE_CHARS:
            raise InvalidInput(f"a quote is at most {MAX_QUOTE_CHARS} characters")
        _, raw = self._read_bytes(relative_path)
        try:
            document = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceUnreadable("a document under the source root is not valid UTF-8") from exc
        haystack = unicodedata.normalize("NFC", _normalise_newlines(document))
        needle = unicodedata.normalize("NFC", _normalise_newlines(quote))
        return needle in haystack


def _decode_prefix(served: bytes, *, truncated: bool) -> str:
    """Decode `served` as UTF-8, dropping at most a partial character at a trim boundary."""
    if not truncated:
        return served.decode("utf-8")
    # A cap can land inside a multi-byte character. Walk back at most three bytes -- the longest
    # UTF-8 continuation tail -- and no further, so a genuinely undecodable file still raises.
    for cut in range(4):
        head = served if cut == 0 else served[:-cut]
        try:
            return head.decode("utf-8")
        except UnicodeDecodeError:
            continue
    return served.decode("utf-8")
