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

from collections.abc import Mapping
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

RETENTION_SCRUTINY: dict[str, Tier] = {
    "normal": Tier.READ_ONLY,
    "legal_hold": Tier.FORBIDDEN,
}
"""Scrutiny each retention classification demands.

A second axis, deliberately orthogonal to sensitivity. A record under legal hold may not be
altered by anything, and that is true whether the table is ``open`` or ``regulated`` — which is
the point: an object tagged ``open`` can still be forbidden, by a different tag.
"""

UNSUPERVISED_CEILING = Tier.DRAFT
"""Requests at or below this tier never touch a real system, so tags do not bind them."""


@dataclass(frozen=True)
class TagPolicy:
    """One governance tag and what each of its values demands of an action.

    The resolver iterates these rather than naming a tag, which is what makes the authority
    model a property of *governance configuration* rather than of this file. Adding a third
    axis — residency, contractual restriction, anything else the organisation already tags — is
    a row here plus a field on :class:`TouchedObject`, not a change to any control flow.
    """

    tag: str
    """Fully-qualified tag name, as SYSTEM$GET_TAG requires."""

    attribute: str
    """Field on :class:`TouchedObject` holding the read value."""

    label: str
    """How this tag reads in an audit rationale."""

    scrutiny: Mapping[str, Tier]
    """Value to the minimum tier an action touching such an object must run at."""

    absent: Tier
    """What an absent or unrecognised value demands."""

    def demand(self, value: str | None) -> Tier:
        """The tier this policy demands for one observed value.

        Args:
            value: The tag value read from the object, or ``None`` if it carries none.

        Returns:
            The demanded :class:`Tier`.
        """
        if value is None:
            return self.absent
        return self.scrutiny.get(value.strip().lower(), self.absent)

    def describe(self, value: str | None) -> str:
        """How this policy's finding should read in an audit rationale."""
        if value is None:
            return f"no {self.label} tag" + (
                ", treated as unclassified" if self.absent > Tier.READ_ONLY else ""
            )
        cleaned = value.strip().lower()
        if cleaned in self.scrutiny:
            return f"{self.label}='{cleaned}'"
        return f"an unrecognised {self.label} tag '{value}', treated as unclassified"


POLICIES: tuple[TagPolicy, ...] = (
    TagPolicy(
        tag="WARRANT.CORE.SENSITIVITY",
        attribute="sensitivity",
        label="sensitivity",
        scrutiny=SENSITIVITY_SCRUTINY,
        # Absent means *unclassified*, which demands approval. Everything has some
        # sensitivity, so not knowing it is itself the risk.
        absent=UNTAGGED_SCRUTINY,
    ),
    TagPolicy(
        tag="WARRANT.CORE.RETENTION",
        attribute="retention",
        label="retention",
        scrutiny=RETENTION_SCRUTINY,
        # Absent means *not under hold*, which demands nothing — and the asymmetry with
        # sensitivity above is deliberate. A legal hold is an affirmative exceptional state
        # somebody puts on a record; its absence is the ordinary case, not missing
        # information. Treating an untagged object as held would freeze the whole estate.
        absent=Tier.READ_ONLY,
    ),
)
"""Every governance tag that can bind an action. Order is presentation only — all are read."""


@dataclass(frozen=True)
class TouchedObject:
    """A fully-qualified object an action reads or writes, and its governance tags."""

    fqn: str
    sensitivity: str | None = None
    retention: str | None = None

    def binding_policy(self) -> tuple[TagPolicy, Tier]:
        """Which tag demands the most of an action touching this object.

        Returns:
            The most demanding :class:`TagPolicy` and the tier it demands. Ties resolve to
            the first policy in :data:`POLICIES`, which is why sensitivity leads it — when
            two axes agree, the primary classification is the one worth naming.
        """
        demands = [(policy, policy.demand(getattr(self, policy.attribute))) for policy in POLICIES]
        return max(demands, key=lambda pair: pair[1])

    def required_scrutiny(self) -> Tier:
        """The minimum tier an action touching this object must run at.

        Returns:
            The most demanding tier across *every* governance tag. ``FORBIDDEN`` means no
            action is permissible at all.
        """
        return self.binding_policy()[1]

    def describe_tag(self) -> str:
        """How this object's classification should read in an audit rationale.

        Returns:
            A description of whichever tag actually bound, so a rationale never names
            sensitivity for a decision that retention made.
        """
        policy, _ = self.binding_policy()
        return policy.describe(getattr(self, policy.attribute))


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
                f"{binding.fqn} is tagged {binding.describe_tag()}. Acting on such records "
                f"is never the agent's to do, at any confidence."
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
