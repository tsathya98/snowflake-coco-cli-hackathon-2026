"""Re-resolving past decisions against the policy in force today.

``ACTION_AUDIT`` is append-only and every queued action records the tier it was resolved at, which
together make a question answerable that usually is not:

> **Which decisions, already taken, would not be permitted under today's classifications?**

That is the question an auditor actually asks. It is not "is the control working now" — it is
"what got through while the control said something different". A system that only enforces policy
at the moment of action can answer the first and has no way to answer the second.

The re-resolution runs the **real resolver** over the **real registry** with **current tags**. It
is not a report over stored tiers; the stored tier is only the comparison point. So a difference
means the governance posture genuinely changed, not that two implementations disagree.

Nothing here writes. Replay is a read, deliberately: an auditor's tool that mutated the record it
was auditing would be worthless, and re-deciding history automatically is not a power anything
should have.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from snowflake.snowpark import Session

from warrant.act.registry import ACTION_TYPES
from warrant.authority.tags import read_sensitivity
from warrant.authority.tiers import Tier, TouchedObject, resolve

# Only settled or queued actions are worth replaying, and `execution_result` distinguishes the two
# cases that matter most: something that ran, versus something that was already refused.
DECIDED_ACTIONS = """
SELECT p.action_id,
       p.action_type,
       p.effective_tier,
       p.decision,
       COALESCE(p.decided_by, 'n/a')                                  AS decided_by,
       COALESCE(TO_VARCHAR(p.decided_at, 'YYYY-MM-DD HH24:MI'), 'n/a') AS decided_at,
       TO_VARCHAR(p.proposed_at, 'YYYY-MM-DD HH24:MI')                AS proposed_at,
       COALESCE(p.execution_result, 'none')                           AS execution_result
  FROM WARRANT.CORE.PENDING_ACTIONS p
 ORDER BY p.proposed_at DESC
"""

EXECUTED = "executed"
"""The ``execution_result`` value that means the action actually took effect."""


@dataclass(frozen=True)
class Replayed:
    """One past action, with the tier it ran at and the tier it would get now."""

    action_id: str
    action_type: str
    proposed_at: str
    decided_at: str
    decided_by: str
    decision: str
    execution_result: str
    tier_then: Tier | None
    tier_now: Tier
    rationale_now: str
    binding_object_now: str | None

    @property
    def diverged(self) -> bool:
        """Whether today's policy would resolve this action differently."""
        return self.tier_then is not None and self.tier_now != self.tier_then

    @property
    def now_forbidden(self) -> bool:
        """Whether today's policy would refuse this action outright."""
        return self.tier_now is Tier.FORBIDDEN

    @property
    def needs_attention(self) -> bool:
        """Whether this row is something an auditor has to look at.

        True when the action **took effect** and today's policy would no longer allow it
        unsupervised. A refusal that is still a refusal needs no attention; a queued action that
        never ran needs none either. What matters is work that happened under a policy that has
        since tightened — which is the only category that cannot be fixed going forward, because
        it already happened.
        """
        return (
            self.execution_result == EXECUTED
            and self.tier_then is not None
            and self.tier_now > self.tier_then
        )


def replay(session: Session, overrides: Mapping[str, str | None] | None = None) -> list[Replayed]:
    """Re-resolve every recorded action against current classifications.

    Args:
        session: An active Snowpark session.
        overrides: Hypothetical sensitivity per object, exactly as
            :func:`warrant.authority.manifest.capabilities` accepts, so an auditor can ask "if we
            reclassified this table, what already-executed work would that call into question?"
            before changing anything.

    Returns:
        One :class:`Replayed` per recorded action, newest first. An action whose type is no longer
        in the registry is returned with ``tier_now = FORBIDDEN`` and a rationale saying so, rather
        than being dropped: an action the code can no longer even describe is precisely what an
        auditor should be shown, and silently omitting it would make the report look cleaner than
        the system is.
    """
    live: dict[str, str | None] = {}
    needed = sorted({fqn for a in ACTION_TYPES.values() for fqn in a.touched_objects})
    live.update({obj.fqn: obj.sensitivity for obj in read_sensitivity(session, needed)})
    if overrides:
        live.update(overrides)

    replayed: list[Replayed] = []
    for row in session.sql(DECIDED_ACTIONS).collect():
        action = ACTION_TYPES.get(row["ACTION_TYPE"])
        stored = row["EFFECTIVE_TIER"]
        tier_then = Tier(int(stored)) if stored is not None else None

        if action is None:
            tier_now, rationale, binding = (
                Tier.FORBIDDEN,
                f"Action type '{row['ACTION_TYPE']}' is no longer in the registry, so its "
                "footprint cannot be established and no authority can be resolved for it.",
                None,
            )
        else:
            touched = [
                TouchedObject(fqn=fqn, sensitivity=live.get(fqn)) for fqn in action.touched_objects
            ]
            decision = resolve(action.requested_tier, touched)
            tier_now, rationale, binding = (
                decision.tier,
                decision.rationale,
                decision.binding_object,
            )

        replayed.append(
            Replayed(
                action_id=row["ACTION_ID"],
                action_type=row["ACTION_TYPE"],
                proposed_at=row["PROPOSED_AT"],
                decided_at=row["DECIDED_AT"],
                decided_by=row["DECIDED_BY"],
                decision=row["DECISION"],
                execution_result=row["EXECUTION_RESULT"],
                tier_then=tier_then,
                tier_now=tier_now,
                rationale_now=rationale,
                binding_object_now=binding,
            )
        )
    return replayed


def summarise(replayed: list[Replayed]) -> dict[str, int]:
    """Reduce a replay to the counts an auditor opens with.

    Args:
        replayed: Output of :func:`replay`.

    Returns:
        Counts of actions replayed, decisions that would differ today, actions that would now be
        refused outright, and — the one that matters — executed work that today's policy would no
        longer permit unsupervised.
    """
    return {
        "replayed": len(replayed),
        "diverged": sum(r.diverged for r in replayed),
        "now_forbidden": sum(r.now_forbidden for r in replayed),
        "needs_attention": sum(r.needs_attention for r in replayed),
    }
