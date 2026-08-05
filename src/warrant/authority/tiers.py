"""Authority tier resolution.

The core idea of Warrant: an action's authority tier is derived from the governance
metadata already attached to the data it touches, rather than from a hardcoded rules
list that drifts out of sync with policy.

Concretely, every table carries a ``SENSITIVITY`` object tag. When the agent proposes an
action, we look at every object that action reads or writes and ask what level of
scrutiny each one demands. The most demanding object wins. Ambiguity always resolves
toward more scrutiny — an untagged object is treated as unclassified, not as cleared.

Three rules, in precedence order:

1. **Reading and drafting are always permitted.** Nothing at or below
   :attr:`Tier.DRAFT` changes a real system, so no tag constrains it. The agent has to
   be able to detect an aging quality hold and explain it even though it may never act
   on one — see runbook RB-003.
2. **Regulated data is an absolute stop for anything that acts.** If any touched object
   is tagged ``regulated``, an action against it is refused outright — not squeezed
   under a limit.
3. **Otherwise the tags set a floor on scrutiny.** ``open`` data may be acted on
   unsupervised; ``internal`` or untagged data forces the action through human approval.

This module is deliberately free of Snowflake imports so the policy logic can be unit
tested without a warehouse. Tag lookup lives in :mod:`warrant.authority.tags`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Tier(IntEnum):
    """What the agent is permitted to do, in increasing order of consequence.

    Ordered so that ``max()`` over a set of demands yields the most restrictive one.
    """

    READ_ONLY = 0
    """Inspect, summarise, explain. Always permitted."""

    DRAFT = 1
    """Prepare a message or task but never send it."""

    LOW_RISK_ACT = 2
    """Execute a routine, reversible, non-regulated action automatically."""

    APPROVAL_REQUIRED = 3
    """Escalations and status changes. A human approves before execution."""

    FORBIDDEN = 4
    """Never the agent's to take, regardless of confidence."""


# Defined separately from Tier because these are two different vocabularies that happen
# to share a scale: one describes actions, the other describes data. The value here is
# the *minimum* tier an action against such data must run at.
SENSITIVITY_SCRUTINY: dict[str, Tier] = {
    "open": Tier.LOW_RISK_ACT,
    "internal": Tier.APPROVAL_REQUIRED,
    "regulated": Tier.FORBIDDEN,
}
"""Scrutiny each sensitivity classification demands of an action touching it."""

UNTAGGED_SCRUTINY = Tier.APPROVAL_REQUIRED
"""Scrutiny demanded by an object with no recognised sensitivity tag.

Deliberately not ``LOW_RISK_ACT``: an object nobody has classified is not the same as an
object someone classified as open, and the agent should not be the one to assume.
"""

UNSUPERVISED_CEILING = Tier.DRAFT
"""Requests at or below this tier never touch a real system, so tags do not bind them."""


@dataclass(frozen=True)
class TouchedObject:
    """A fully-qualified object an action reads or writes, and its sensitivity tag."""

    fqn: str
    sensitivity: str | None = None

    def required_scrutiny(self) -> Tier:
        """The minimum tier an action touching this object must run at.

        Returns:
            The demanded :class:`Tier`. ``FORBIDDEN`` means no action is permissible at
            all; an unrecognised or absent tag yields :data:`UNTAGGED_SCRUTINY`.
        """
        if self.sensitivity is None:
            return UNTAGGED_SCRUTINY
        return SENSITIVITY_SCRUTINY.get(self.sensitivity.strip().lower(), UNTAGGED_SCRUTINY)

    def describe_tag(self) -> str:
        """How this object's classification should read in an audit rationale."""
        if self.sensitivity is None:
            return "no sensitivity tag, treated as unclassified"
        if self.sensitivity.strip().lower() in SENSITIVITY_SCRUTINY:
            return f"sensitivity='{self.sensitivity.strip().lower()}'"
        return f"an unrecognised sensitivity tag '{self.sensitivity}', treated as unclassified"


@dataclass(frozen=True)
class Decision:
    """The outcome of tier resolution, with the reasoning kept for the audit log."""

    tier: Tier
    binding_object: str | None
    rationale: str

    @property
    def is_auto_executable(self) -> bool:
        return self.tier <= Tier.LOW_RISK_ACT

    @property
    def needs_approval(self) -> bool:
        return self.tier == Tier.APPROVAL_REQUIRED

    @property
    def is_refused(self) -> bool:
        return self.tier == Tier.FORBIDDEN


def resolve(requested: Tier, touched: list[TouchedObject]) -> Decision:
    """Resolve the tier an action may actually run at.

    Args:
        requested: The tier the proposed action would need in order to execute.
        touched: Every object the action reads or writes. An empty list is treated as
            suspicious rather than harmless.

    Returns:
        A :class:`Decision` carrying the effective tier and why it landed there. The
        effective tier is never *below* ``requested`` — governance can only add
        scrutiny, never grant capability the action did not ask for.
    """
    if not touched:
        return Decision(
            tier=Tier.APPROVAL_REQUIRED,
            binding_object=None,
            rationale=(
                "No touched objects were declared. An action that cannot say what it "
                "touches cannot be auto-executed."
            ),
        )

    # The most demanding object always binds. max() over demands, never min() — taking
    # the minimum is what previously let an open table dilute a regulated one.
    binding = max(touched, key=lambda o: o.required_scrutiny())
    demanded = binding.required_scrutiny()

    # Rule 1: nothing at or below DRAFT reaches a real system, so no tag binds it. This
    # is what lets the agent detect and explain an exception it may never act on.
    if requested <= UNSUPERVISED_CEILING:
        return Decision(
            tier=requested,
            binding_object=binding.fqn,
            rationale=(
                f"{requested.name} does not act on any system, so the classification of "
                f"{binding.fqn} ({binding.describe_tag()}) does not constrain it."
            ),
        )

    # Rule 2: regulated data is an absolute stop for anything that acts.
    if demanded is Tier.FORBIDDEN:
        return Decision(
            tier=Tier.FORBIDDEN,
            binding_object=binding.fqn,
            rationale=(
                f"{binding.fqn} is tagged sensitivity='regulated'. Acting on regulated "
                f"records is never the agent's to do, at any confidence."
            ),
        )

    # Rule 3: the most demanding object sets the floor.
    if requested >= demanded:
        return Decision(
            tier=requested,
            binding_object=binding.fqn,
            rationale=(
                f"{requested.name} already meets the scrutiny demanded by "
                f"{binding.fqn} ({binding.describe_tag()})."
            ),
        )

    return Decision(
        tier=demanded,
        binding_object=binding.fqn,
        rationale=(
            f"Requested tier {requested.name} was raised to {demanded.name} because "
            f"{binding.fqn} has {binding.describe_tag()}."
        ),
    )
