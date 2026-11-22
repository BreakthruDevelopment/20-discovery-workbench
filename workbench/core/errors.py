"""Workbench errors, each mapping to an app-17 `ErrorCategory` and an `is_retryable` flag.

Why the mapping lives here. App 17's `ToolResult` carries `error_category` and `is_retryable` so a
model can tell a retry from a dead end, and 20.4's error propagation records the same two values on
a `subagent_run` row. Both need one table of truth for "what kind of failure is this", and both sit
outside `workbench/core/`, so the table is here and they read it.

**Messages carry no caller input.** Every message is built from this module's fixed `code` plus, at
most, a `detail` string the raising code wrote itself -- never an engagement id, a path, a quote, a
document id or any other value that came in from a CLI argument, a file or a model. An error is one
of the easiest ways to hand a value back to whoever supplied it, and a cross-engagement id echoed in
a refusal tells the caller the id was real. `tests/test_error_messages.py` asserts this for every
store and source-library refusal by feeding each one a marker value and asserting the marker is
absent from the message. `detail` exists for schema-derived names (a field name, a column name, a
closed-set value) and fixed phrases; nothing else belongs in it.
"""

from __future__ import annotations

import asyncio
from typing import ClassVar

from agent_container.core.tool import ErrorCategory, ToolResult


class WorkbenchError(Exception):
    """Base class. Subclasses set `code`, `category` and `retryable` as class attributes."""

    code: ClassVar[str] = "workbench_error"
    category: ClassVar[ErrorCategory] = ErrorCategory.INTERNAL
    retryable: ClassVar[bool] = False

    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(f"{self.code}: {detail}" if detail else self.code)

    def as_tool_result(self) -> ToolResult:
        """This error as a tool result, so a subagent sees a category rather than a traceback."""
        return ToolResult.error(self.category, str(self), retryable=self.retryable)


class AccessDenied(WorkbenchError):
    """The acting principal may not do this. Never retryable, and never for this caller."""

    code = "access_denied"
    category = ErrorCategory.PERMISSION
    retryable = False


class NotFound(WorkbenchError):
    """A row that must exist does not. A rule said no, so nothing is gained by retrying.

    Reached only after the access check has passed, so it never answers "does this exist" for a
    principal that may not see it: `store.py` resolves the owning engagement and calls `assert_can`
    before it reports a missing row.
    """

    code = "not_found"
    category = ErrorCategory.BUSINESS
    retryable = False


class AlreadyFinal(WorkbenchError):
    """A readout was finalised twice. Raised from the unique guard, not from a caller's check."""

    code = "already_final"
    category = ErrorCategory.BUSINESS
    retryable = False


class CoverageGapsPresent(WorkbenchError):
    """`finalise` was called while a subagent run is `failed` and `--accept-gaps` was not given."""

    code = "coverage_gaps_present"
    category = ErrorCategory.BUSINESS
    retryable = False


class InvalidInput(WorkbenchError):
    """A value failed validation at the boundary. The caller can fix it and call again."""

    code = "invalid_input"
    category = ErrorCategory.VALIDATION
    retryable = False


class SourceOutsideRoot(WorkbenchError):
    """A requested path resolved outside the source root, or through a symlink that leaves it."""

    code = "source_outside_root"
    category = ErrorCategory.PERMISSION
    retryable = False


class SourceRefused(WorkbenchError):
    """A path inside the root that the library does not serve: the manifest, or a non-text file.

    `permission`, not `business`: the refusal is about what this library is allowed to hand out,
    and the answer will not change on a retry or with different arguments.
    """

    code = "source_refused"
    category = ErrorCategory.PERMISSION
    retryable = False


class SourceUnreadable(WorkbenchError):
    """A file under the root exists but cannot be served as text: undecodable, or not a file."""

    code = "source_unreadable"
    category = ErrorCategory.BUSINESS
    retryable = False


class StoreCorrupt(WorkbenchError):
    """The database is missing its schema, or a row broke an invariant the schema cannot express."""

    code = "store_corrupt"
    category = ErrorCategory.INTERNAL
    retryable = False


class Throttled(WorkbenchError):
    """A provider asked us to slow down. The one category that is retryable by default."""

    code = "throttled"
    category = ErrorCategory.TRANSIENT
    retryable = True


class ProviderFailed(WorkbenchError):
    """A model provider failed for a reason that is not throttling and not our input."""

    code = "provider_failed"
    category = ErrorCategory.INTERNAL
    retryable = False


def classify(exc: BaseException) -> tuple[ErrorCategory, bool]:
    """The `(error_category, is_retryable)` pair to record for `exc`.

    20.4 calls this when a subagent fails, so a `subagent_run` row carries the same two values a
    `ToolResult` would. A `WorkbenchError` answers for itself. Anything else is `internal` and not
    retryable: a failure nobody classified is not one to try again, and guessing `transient` from an
    exception type is how a dead end becomes a retry loop.

    `TimeoutError` and `asyncio.CancelledError` are the two exceptions to that, and only because
    both mean "this did not finish", not "this cannot work". `CancelledError` derives from
    `BaseException`, which is why the parameter is typed that way: a coordinator that caught only
    `Exception` would let a cancelled subagent escape unrecorded.
    """
    if isinstance(exc, WorkbenchError):
        return exc.category, exc.retryable
    if isinstance(exc, TimeoutError):
        return ErrorCategory.TRANSIENT, True
    if isinstance(exc, asyncio.CancelledError):
        return ErrorCategory.TRANSIENT, False
    return ErrorCategory.INTERNAL, False
