"""What the agent is allowed to do, right now, and what would change if policy changed.

Every other part of Warrant answers the question *"may this specific action proceed?"* at the
moment it is proposed. That is the right question for the pipeline and the wrong question for a
reviewer, who has to ask the opposite one: **"what is this agent allowed to do at all?"**

Answering that has, until now, meant reading `act/registry.py`, reading `authority/tiers.py`, and
holding the current tags in your head. A control nobody can enumerate is a control nobody can
audit, however correctly it is enforced.

So this module resolves the *whole* registry against the tags as they are, and returns it as data:
one row per action, the objects it touches, the tier it would run at, and the object that binds it.

**The override map is the interesting part.** :func:`capabilities` accepts a hypothetical
sensitivity for any object, which makes the same resolution answer a policy question — *if this
table became `regulated`, what would the agent lose?* — with no `ALTER TABLE`, no write, and no
effect on anything. It is the real resolver on hypothetical inputs, not a second implementation
of the rules that could disagree with the first.

No Snowflake imports beyond the session type, and the resolution itself is pure, so the whole
thing is unit-testable without a warehouse.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from snowflake.snowpark import Session

from warrant.act.registry import ACTION_TYPES
from warrant.authority.tags import read_sensitivity
from warrant.authority.tiers import Tier, TouchedObject, resolve

AUTO = "acts unsupervised"
APPROVAL = "needs human approval"
REFUSED = "refused outright"
"""How a resolved tier reads to a reviewer. Deliberately verbs, not tier numbers: `L3` means
nothing to the quality owner who has to sign the policy off."""


@dataclass(frozen=True)
class Capability:
    """One registered action, resolved against a set of classifications."""

    action: str
    description: str
    requested_tier: Tier
    effective_tier: Tier
    binding_object: str | None
    rationale: str
    touched: tuple[str, ...]
    classifications: tuple[tuple[str, str], ...]
    """Each touched object with the classification used to resolve it, ``'untagged'`` when absent.

    Carried per capability rather than looked up again for display, so what a row *says* and what
    the resolver *used* cannot drift — including under a hypothetical override.
    """

    @property
    def outcome(self) -> str:
        """Plain-language summary of what this capability currently permits."""
        if self.effective_tier is Tier.FORBIDDEN:
            return REFUSED
        if self.effective_tier is Tier.APPROVAL_REQUIRED:
            return APPROVAL
        return AUTO

    @property
    def is_permitted(self) -> bool:
        """Whether the action could proceed at all, with or without a human."""
        return self.effective_tier is not Tier.FORBIDDEN


def registry_objects() -> tuple[str, ...]:
    """Every distinct object any registered action touches.

    Returns:
        Fully-qualified names, sorted. Read once and shared across all capabilities so a manifest
        costs one tag read per object rather than one per action-object pair.
    """
    return tuple(sorted({fqn for a in ACTION_TYPES.values() for fqn in a.touched_objects}))


def _with_override(
    observed: TouchedObject | None,
    fqn: str,
    overrides: Mapping[str, str | None] | None,
) -> TouchedObject:
    """Apply a hypothetical sensitivity to a live reading, preserving every other axis.

    Args:
        observed: What the tag read returned, or ``None`` if the object was not read.
        fqn: The object being resolved.
        overrides: Hypothetical sensitivities, or ``None``.

    Returns:
        The object to resolve against. Only ``sensitivity`` is replaced — ``replace()`` rather
        than a fresh construction, so an axis this function has never heard of still survives.
    """
    base = observed if observed is not None else TouchedObject(fqn=fqn)
    if overrides is not None and fqn in overrides:
        return replace(base, sensitivity=overrides[fqn])
    return base


def capabilities(
    session: Session, overrides: Mapping[str, str | None] | None = None
) -> list[Capability]:
    """Resolve every registered action against current — or hypothetical — classifications.

    Args:
        session: An active Snowpark session.
        overrides: Hypothetical **sensitivity** per fully-qualified object name, replacing what
            is actually tagged. ``None`` as a value models *removing* a tag, which is not the same
            as tagging something ``open`` and must stay expressible. Objects absent from the map
            keep their live classification. Pass ``None`` for the real, current manifest.

            Only sensitivity is overridable. Every other governance axis — retention today,
            whatever :data:`~warrant.authority.tiers.POLICIES` grows next — is carried through
            from the live read untouched, so a hypothetical about one axis cannot silently
            discard another.

    Returns:
        One :class:`Capability` per registered action, most restricted first, so the things the
        agent may **not** do are what a reviewer reads before the things it may.
    """
    # The whole TouchedObject is kept, not just its sensitivity.
    #
    # Flattening to {fqn: sensitivity} and rebuilding silently dropped every other governance
    # axis: an object under legal hold resolved as though it were not, because the retention
    # value never survived the round trip. The live read is authoritative and an override
    # replaces one field of it.
    live: dict[str, TouchedObject] = {
        obj.fqn: obj for obj in read_sensitivity(session, registry_objects())
    }

    resolved: list[Capability] = []
    for action in ACTION_TYPES.values():
        touched = [_with_override(live.get(fqn), fqn, overrides) for fqn in action.touched_objects]
        decision = resolve(action.requested_tier, touched)
        resolved.append(
            Capability(
                action=action.name,
                description=action.description,
                requested_tier=action.requested_tier,
                effective_tier=decision.tier,
                binding_object=decision.binding_object,
                rationale=decision.rationale,
                touched=action.touched_objects,
                classifications=tuple((obj.fqn, obj.sensitivity or "untagged") for obj in touched),
            )
        )
    return sorted(resolved, key=lambda c: (-int(c.effective_tier), c.action))


@dataclass(frozen=True)
class Change:
    """One capability whose permitted outcome differs between two manifests."""

    action: str
    before: Capability
    after: Capability

    @property
    def is_revocation(self) -> bool:
        """Whether the change tightens what the agent may do."""
        return self.after.effective_tier > self.before.effective_tier


def compare(before: list[Capability], after: list[Capability]) -> list[Change]:
    """Diff two manifests, reporting only capabilities whose tier moved.

    This is the blast radius of a policy change: run :func:`capabilities` twice, once as things are
    and once with an override, and the difference is exactly what retagging that object would cost
    or grant.

    Args:
        before: Manifest resolved against current classifications.
        after: Manifest resolved against the hypothetical.

    Returns:
        One :class:`Change` per action whose effective tier differs, most restricted first.
        Actions absent from either side are ignored rather than reported as changes — the registry
        is the same in both manifests by construction, so a mismatch means a caller built one of
        them from something else, and inventing a diff for it would be worse than saying nothing.
    """
    after_by_action = {c.action: c for c in after}
    changed = [
        Change(action=b.action, before=b, after=after_by_action[b.action])
        for b in before
        if b.action in after_by_action
        and after_by_action[b.action].effective_tier != b.effective_tier
    ]
    return sorted(changed, key=lambda c: (-int(c.after.effective_tier), c.action))
