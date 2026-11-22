"""Foundation package: the engagement store, the access rules and the source library (20.2).

Wave 1 owns this path. A later slice adds files here only if a security-sensitive `claude` slice
names it. No pre-push guard enforces that here: see AGENTS.md.

What is where:

* `principals.py` -- the three principals, the closed `Action` set and `assert_can`. Pure: no I/O.
* `store.py` -- the only module that opens the database. Every accessor takes the acting principal,
  calls `assert_can`, and filters on `engagement_id` in its own SQL.
* `sources.py` -- the only module that opens a file under `sources/`. Read-only, rooted, capped,
  and the home of `verify_quote`.
* `errors.py` -- the one mapping from a workbench failure to app 17's `error_category` and
  `is_retryable`.
* `config.py` -- every environment-derived value, read once.
* `schema.sql` / `seed.sql` -- every table in the data model, and a deterministic two-engagement
  seed.
"""

from workbench.core.config import Config
from workbench.core.errors import (
    AccessDenied,
    AlreadyFinal,
    CoverageGapsPresent,
    InvalidInput,
    NotFound,
    ProviderFailed,
    SourceOutsideRoot,
    SourceRefused,
    SourceUnreadable,
    StoreCorrupt,
    Throttled,
    WorkbenchError,
    classify,
)
from workbench.core.principals import (
    Action,
    EngagementState,
    Principal,
    Resource,
    Role,
    assert_can,
    may,
)
from workbench.core.sources import SourceLibrary, SourceRef, SourceText, document_id
from workbench.core.store import (
    Claim,
    Engagement,
    NewClaim,
    NewQuestion,
    Question,
    Readout,
    Store,
    SubagentRun,
)

__all__ = [
    "AccessDenied",
    "Action",
    "AlreadyFinal",
    "Claim",
    "Config",
    "CoverageGapsPresent",
    "Engagement",
    "EngagementState",
    "InvalidInput",
    "NewClaim",
    "NewQuestion",
    "NotFound",
    "Principal",
    "ProviderFailed",
    "Question",
    "Readout",
    "Resource",
    "Role",
    "SourceLibrary",
    "SourceOutsideRoot",
    "SourceRef",
    "SourceRefused",
    "SourceText",
    "SourceUnreadable",
    "Store",
    "StoreCorrupt",
    "SubagentRun",
    "Throttled",
    "WorkbenchError",
    "assert_can",
    "classify",
    "document_id",
    "may",
]
