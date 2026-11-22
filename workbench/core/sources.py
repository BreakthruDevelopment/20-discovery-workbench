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

**No failure leaves this module untyped.** Every entry point answers with a `WorkbenchError`,
which is what carries an `error_category` and keeps a caller's batch alive. Two exception families
have to be caught for that, not one: `OSError` for the ordinary filesystem failures, and
`RuntimeError` for a **symlink loop** -- `Path.resolve(strict=False)` deliberately converts ELOOP
into `RuntimeError("Symlink loop from <absolute path>")` rather than an `OSError`, so catching
`OSError` alone leaves exactly the hole it was meant to close, absolute path in the message and
all. This repo pins Python >=3.12,<3.13, where that is the shipped behaviour.
"""

from __future__ import annotations

import hashlib
import os
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from workbench.core.config import Config
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


def _servable_name(path: Path) -> bool:
    """Whether a filename is one this library serves at all: the stem and extension rules."""
    return path.stem.lower() not in REFUSED_STEMS and path.suffix.lower() in ALLOWED_SUFFIXES


def _normalise_newlines(text: str) -> str:
    """CRLF and CR to LF. A line-ending difference is an encoding detail, not a text difference."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


#: How much of the path digest goes in a document id. 8 hex characters over a per-engagement
#: namespace; the readable slug beside it is what makes a fixture reviewable.
_DIGEST_CHARS = 8


def document_id(engagement_id: str, relative_path: str) -> str:
    """The stable id for a document at `relative_path` in `engagement_id`.

    Derived rather than assigned, so the index is deterministic: re-indexing the same tree produces
    the same ids and a recorded fixture keeps naming the same documents.

    Two things it must not do, both learned the hard way. It must not be **shared between
    engagements**: `source_document.id` is a database-wide primary key, and two engagements that
    both hold a `systems-inventory.csv` -- which the seed's two engagements plausibly would --
    would collide on the second one's index. And it must not be **lossy**: collapsing `/` and `.`
    into `-` made `a/b.md` and `a--b.md` the same id. So the engagement is part of the id and a
    digest of the exact relative path is appended, which restores injectivity; the readable slug is
    kept only because a reviewer has to be able to recognise a fixture.
    """
    slug = relative_path.replace("/", "--").replace(".", "-")
    digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:_DIGEST_CHARS]
    return f"doc-{engagement_id}--{slug}-{digest}"


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
        engagement_id: str,
        max_file_bytes: int,
        max_run_bytes: int,
    ) -> None:
        if max_file_bytes <= 0 or max_run_bytes <= 0:
            raise InvalidInput("source byte caps must be positive")
        if not engagement_id.strip():
            raise InvalidInput("a source library is rooted at one named engagement")
        self._engagement_id = engagement_id
        self._max_file_bytes = max_file_bytes
        self._max_run_bytes = max_run_bytes
        self._bytes_served = 0
        # `strict=False` (the default): a missing tree is an empty library, not a crash. The
        # second engagement in the seed has no committed pack, and an empty index is the honest
        # answer for it. `RuntimeError` as well as `OSError`: see the module docstring on ELOOP.
        try:
            self._root = root.resolve()
        except (OSError, RuntimeError) as exc:
            raise SourceUnreadable("the engagement's source root could not be resolved") from exc

    @property
    def root(self) -> Path:
        return self._root

    @classmethod
    def for_engagement(cls, config: Config, engagement_id: str) -> SourceLibrary:
        """The sanctioned constructor: root and label both derived from one config.

        Built by hand, the two can disagree -- `SourceLibrary(northwind_root,
        engagement_id="acme-p2p")` satisfied the store's label check and then verified a quote
        against the other engagement's file. `store.index_sources` and `store.record_claims` now
        check the resolved root as well as the label, and this is how a caller gets one that
        passes.
        """
        return cls(
            config.engagement_sources_root(engagement_id),
            engagement_id=engagement_id,
            max_file_bytes=config.max_source_file_bytes,
            max_run_bytes=config.max_source_run_bytes,
        )

    @property
    def engagement_id(self) -> str:
        """Which engagement's evidence this library serves.

        Carried so `store.index_sources` and `store.record_claims` can refuse a library rooted at
        a different engagement than the one they were asked about: that is the last piece of the
        owner filter that would otherwise live in a caller.
        """
        return self._engagement_id

    @property
    def bytes_served(self) -> int:
        return self._bytes_served

    @property
    def run_bytes_remaining(self) -> int:
        return max(0, self._max_run_bytes - self._bytes_served)

    def _resolve(self, relative_path: str) -> tuple[Path, str]:
        """`(absolute path, the requested relative path)`, or a refusal.

        The one gate on the filesystem, and the only place a caller's path becomes a real one.

        It returns **both** because they can differ and each is needed for a different job. The
        resolved path is the security answer: `..` is gone, symlinks are followed, and a path that
        lands outside the root is refused. The requested path, merely normalised, is the *index*
        answer: `source_document` is keyed on the path as listed, so for an in-root
        `alias.md -> notes.md` a read of `alias.md` must report `alias.md`'s document id. Reporting
        the target's id instead made `read()` and `list_documents()` disagree, and a claim built
        from a subagent's own read was then refused by `record_claims`' per-question check.
        """
        if not relative_path or relative_path.strip() != relative_path:
            raise InvalidInput("a document path is required and carries no surrounding whitespace")
        if "\x00" in relative_path:
            raise InvalidInput("a document path contains no NUL byte")
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise SourceOutsideRoot("a document path is relative to the engagement's source root")
        try:
            resolved = (self._root / candidate).resolve()
        except (OSError, RuntimeError) as exc:
            # A symlink loop arrives here as `RuntimeError`, carrying the absolute path in its
            # message; everything else as `OSError`. Both become one refusal that names neither.
            raise SourceUnreadable(
                "a document path under the source root could not be resolved"
            ) from exc
        # `is_relative_to` on the resolved pair is the whole check: `..` segments are gone and any
        # symlink has been followed, so a link out of the tree lands outside the root here. The
        # root itself satisfies it and is then refused by the suffix check below, as a directory.
        if not resolved.is_relative_to(self._root):
            raise SourceOutsideRoot("a document path resolves outside the engagement's source root")
        # Lexical normalisation only, for the index key. `resolve()` above is the security answer;
        # this cannot be, because it does not follow links -- which is exactly why it is the right
        # key for a path that WAS a link.
        requested = PurePosixPath(os.path.normpath(candidate.as_posix())).as_posix()
        if requested == ".." or requested.startswith("../"):
            raise SourceOutsideRoot("a document path resolves outside the engagement's source root")
        # Both names are screened: the one asked for and the one it lands on. Either alone leaves a
        # hole -- `notes.md -> manifest.json` passes the first, and a served name is no excuse for
        # a refused target.
        for name in (PurePosixPath(requested), resolved):
            if Path(name).stem.lower() in REFUSED_STEMS:
                raise SourceRefused("the source library does not serve the pack manifest")
            if Path(name).suffix.lower() not in ALLOWED_SUFFIXES:
                raise SourceRefused("the source library serves only text documents")
        return resolved, requested

    def _entries(self) -> Iterator[Path]:
        """Every servable file under the root, sorted, with refused paths already dropped."""
        try:
            if not self._root.is_dir():
                return
            candidates = sorted(self._root.rglob("*"))
        except (OSError, RuntimeError):
            # The root itself is unreadable. An empty index, not a traceback.
            return
        for path in candidates:
            try:
                if not path.is_file():
                    continue
            except (OSError, RuntimeError):
                continue
            if not _servable_name(path):
                continue
            try:
                resolved = path.resolve()
            except (OSError, RuntimeError):
                continue
            if not resolved.is_relative_to(self._root):
                # A symlink inside the tree pointing out of it. Left out of the index entirely:
                # it is not this engagement's evidence, so it is not listed as unreadable either.
                continue
            # The resolved name is screened as well as the link's own. `notes.md -> manifest.json`
            # passes the name check and lands on the answer key; `_resolve` would refuse it on a
            # read, but it would already have been listed with the manifest's real size and
            # digest, which is a leak from the one file that must never be served.
            if not _servable_name(resolved):
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
            readable = True
            reason: str | None = None
            try:
                raw = path.read_bytes()
            except OSError:
                # A file inside the root the process cannot read: mode 000, a dangling link, a
                # device, a race with something rewriting the tree. Listed as unreadable rather
                # than escaping as a raw `OSError` -- which is what `wb sources list` and
                # `wb discover` would have died on, at step one, as a traceback. The reason names
                # no path and no errno string: both carry the absolute filesystem path.
                refs.append(
                    SourceRef(
                        doc_id=document_id(self._engagement_id, relative),
                        path=relative,
                        bytes=0,
                        sha256="",
                        readable=False,
                        unread_reason="the file could not be read from disk",
                    )
                )
                continue
            digest = hashlib.sha256(raw).hexdigest()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                readable = False
                reason = "not valid UTF-8 text"
            refs.append(
                SourceRef(
                    doc_id=document_id(self._engagement_id, relative),
                    path=relative,
                    bytes=len(raw),
                    sha256=digest,
                    readable=readable,
                    unread_reason=reason,
                )
            )
        return refs

    def _read_bytes(self, relative_path: str) -> tuple[str, bytes]:
        """`(the requested relative path, its bytes)`, or a `SourceUnreadable`.

        Every `OSError` is mapped here. A raw one escaping this module reaches the CLI as a
        traceback, carries the absolute filesystem path in its message -- which `errors.py` states
        and tests that refusals never do -- and sails past `_quote_checks_out` in `store.py`, which
        catches `WorkbenchError`, so one unreadable document would roll back a whole batch of
        claims instead of leaving that one `verified: false`.
        """
        resolved, requested = self._resolve(relative_path)
        try:
            if not resolved.is_file():
                raise SourceUnreadable("no such document in the engagement's source root")
            return requested, resolved.read_bytes()
        except (OSError, RuntimeError) as exc:
            raise SourceUnreadable("a document under the source root could not be read") from exc

    def read(self, relative_path: str) -> SourceText:
        """Serve one document as text, trimmed to the caps, with the trim stated.

        The per-run cap is spent by what is actually served, so a trimmed read spends only the
        bytes it handed back.
        """
        relative, raw = self._read_bytes(relative_path)
        doc_id = document_id(self._engagement_id, relative)
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
        and not about what some subagent was shown.

        It returns a bool and no text. That is **not** the same as leaking nothing: a caller that
        can ask many questions can walk a string out of a capped document one character at a time,
        and measured, 318 queries recovered 36 characters from beyond a 40-byte cap. The control
        that matters is therefore not this return type but who may call it -- `store.record_claims`
        is the only caller, it runs under `assert_can`, and it accepts a quote only against a
        document the claim's own question named. A model never calls this directly, and it has no
        tool that does.

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
