"""The three principals and `assert_can`, the one place an action is allowed or refused.

A principal is not a web session: each `wb` command run acts as one, named on the command line. The
three roles come from the spec:

| Role      | May                                                                             |
| --------- | ------------------------------------------------------------------------------- |
| `analyst` | read its engagements' sources, run discovery, read a draft readout, trace claims |
| `lead`    | all of that, plus finalise a readout and run `--live` against Bedrock            |
| `sponsor` | read a **finalised** readout of its own engagement, and nothing else at all      |

The sponsor's row is the narrow one, and "nothing else" is load-bearing. `READ_READOUT` means the
rendered readout and nothing that went into it: not a claim and its verbatim quote, not a question,
not a subagent run, not the engagement brief. Those are `READ_DISCOVERY`, which no sponsor holds.
Collapsing the two is the mistake this split exists to prevent -- a `TRACE_CLAIM` refusal is
decorative if a bulk claim reader beside it returns a superset, unverified claims included.

`assert_can` is pure: it reads only the `Principal` handed to it and the `Resource` describing what
is being reached. Assignment is resolved once, by `store.load_principal`, into
`Principal.engagements`, so this module never opens a database and can be exhaustively tested
without one. The store calls it on every accessor; callers never make the decision themselves.

Two refusals, in this order, because the order is itself a rule:

1. **Scope.** The resource's engagement is not one this principal is assigned to. Refused before
   anything looks at a row, so a cross-engagement read cannot reach data on its way to a refusal.
2. **Role.** The principal is assigned, but its role does not carry this action -- or, for a
   sponsor, the readout is not `final` yet.

Both raise `AccessDenied` (`permission`, not retryable) with a message built only from the closed
`Role` and `Action` sets: see `errors.py` on why no engagement id appears in it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from workbench.core.errors import AccessDenied


class Role(StrEnum):
    """The closed set of principal roles."""

    ANALYST = "analyst"
    LEAD = "lead"
    SPONSOR = "sponsor"


class Action(StrEnum):
    """The closed set of things a principal can ask to do. Every store accessor names one."""

    LIST_SOURCES = "list_sources"
    READ_SOURCE = "read_source"
    RUN_DISCOVERY = "run_discovery"
    #: Read the engagement's working material: its brief, its questions, its subagent runs and its
    #: claims with their quotes. Distinct from READ_READOUT, which is the finished document only.
    READ_DISCOVERY = "read_discovery"
    READ_READOUT = "read_readout"
    TRACE_CLAIM = "trace_claim"
    FINALISE_READOUT = "finalise_readout"
    RUN_LIVE = "run_live"


class EngagementState(StrEnum):
    """An engagement is `open` until a lead finalises its readout."""

    OPEN = "open"
    FINAL = "final"


# What each role may do, stated positively and ENUMERATED -- including the lead's. A new `Action` is
# then refused to everyone until it is added here on purpose, which is the safe direction and the
# whole point of writing the table out. `frozenset(Action)` for the lead would have said the
# opposite of that: it auto-grants whatever anyone adds later, and the lead is the role that can
# finalise and spend money on Bedrock. `tests/test_access_rules.py` asserts every `Action` appears
# in this table, so adding one without deciding its roles fails the suite rather than defaulting.
_ALLOWED: dict[Role, frozenset[Action]] = {
    Role.ANALYST: frozenset(
        {
            Action.LIST_SOURCES,
            Action.READ_SOURCE,
            Action.RUN_DISCOVERY,
            Action.READ_DISCOVERY,
            Action.READ_READOUT,
            Action.TRACE_CLAIM,
        }
    ),
    Role.LEAD: frozenset(
        {
            Action.LIST_SOURCES,
            Action.READ_SOURCE,
            Action.RUN_DISCOVERY,
            Action.READ_DISCOVERY,
            Action.READ_READOUT,
            Action.TRACE_CLAIM,
            Action.FINALISE_READOUT,
            Action.RUN_LIVE,
        }
    ),
    Role.SPONSOR: frozenset({Action.READ_READOUT}),
}


@dataclass(frozen=True, slots=True)
class Principal:
    """Who a command run acts as, with its engagement assignment already resolved.

    `engagements` is every engagement this principal may reach at all: for an `analyst` or a `lead`
    the ones it is assigned to, for a `sponsor` the ones it sponsors. Built by
    `store.load_principal`; constructing one by hand is how a test states an assignment.
    """

    id: str
    role: Role
    engagements: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class Resource:
    """What is being reached: its owning engagement, and that engagement's state.

    One resource type covers every action because every action in this app is scoped to exactly one
    engagement -- a source file, a question, a claim and a readout all belong to one. `state` is the
    engagement's own state, which is what gates the sponsor's read; `store.py` reads it from the
    `engagement` row rather than from the readout, so there is one answer to "is this final".
    """

    engagement_id: str
    state: EngagementState


def may(principal: Principal, action: Action, resource: Resource) -> bool:
    """Whether `action` is allowed, as a bool. `assert_can` is the form callers should use."""
    if resource.engagement_id not in principal.engagements:
        return False
    if action not in _ALLOWED[principal.role]:
        return False
    # The sponsor's one action, narrowed: a draft readout is not theirs to see. Checked here rather
    # than in `_ALLOWED` because it depends on the row, not only on the role.
    return not (principal.role is Role.SPONSOR and resource.state is not EngagementState.FINAL)


def assert_can(principal: Principal, action: Action, resource: Resource) -> None:
    """Raise `AccessDenied` unless `action` is allowed. Called by every store accessor."""
    if resource.engagement_id not in principal.engagements:
        raise AccessDenied("the acting principal is not assigned to the requested engagement")
    if action not in _ALLOWED[principal.role]:
        raise AccessDenied(f"role {principal.role.value} may not {action.value}")
    if principal.role is Role.SPONSOR and resource.state is not EngagementState.FINAL:
        raise AccessDenied(
            f"role {Role.SPONSOR.value} may {Action.READ_READOUT.value} "
            f"only once the engagement state is {EngagementState.FINAL.value}"
        )
