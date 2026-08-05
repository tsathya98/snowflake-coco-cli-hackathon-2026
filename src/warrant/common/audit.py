"""The decision log.

``WARRANT.AUDIT.ACTION_AUDIT`` is append-only: never updated, never deleted. Every phase of
every loop lands here, including — especially — the refusals. An audit trail that records
only what the agent did, and not what it declined to do, cannot answer the question a
regulator actually asks.

Every value is bound as one JSON object rather than as a list of positional parameters, and
that is not a stylistic choice. Inside a Python stored procedure, Snowpark renders a bound
``None`` as the **string** ``'None'``: a numeric column rejects it loudly, and a ``VARCHAR``
column accepts it silently and stores the four characters. Routing through ``PARSE_JSON``
means a JSON ``null`` becomes a SQL ``NULL`` by construction, on both the client path and the
stored-procedure path. Positional binding worked perfectly until the same code ran inside a
procedure, which is exactly the kind of difference an integration test exists to find.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import Any

from snowflake.snowpark import Session

from warrant.authority.tiers import Tier

PHASES = ("detect", "reason", "classify", "route", "execute", "refuse")
"""The loop stages an audit row can belong to."""

APPEND = """
INSERT INTO WARRANT.AUDIT.ACTION_AUDIT
       (audit_id, phase, exception_id, finding_id, action_id,
        actor, tier, outcome, rationale, payload)
SELECT r:audit_id::STRING,
       r:phase::STRING,
       r:exception_id::STRING,
       r:finding_id::STRING,
       r:action_id::STRING,
       r:actor::STRING,
       r:tier::NUMBER,
       r:outcome::STRING,
       r:rationale::STRING,
       r:payload
  FROM (SELECT PARSE_JSON(?) AS r)
"""


def record(
    session: Session,
    *,
    phase: str,
    outcome: str,
    rationale: str,
    actor: str = "warrant-agent",
    exception_id: str | None = None,
    finding_id: str | None = None,
    action_id: str | None = None,
    tier: Tier | None = None,
    payload: Mapping[str, Any] | None = None,
) -> str:
    """Append one decision to the audit log.

    Args:
        session: An active Snowpark session.
        phase: Which stage of the loop this row belongs to; one of :data:`PHASES`.
        outcome: What happened, as a short stable token the console can group on.
        rationale: Why, in prose, written for a human reviewer rather than for a developer.
        actor: ``warrant-agent`` or the username of the approver.
        exception_id: The exception under investigation, when there is one.
        finding_id: The finding acted on, when there is one.
        action_id: The queued action, when there is one.
        tier: The effective authority tier the decision was taken at.
        payload: Any structured detail worth keeping — bound parameters, error text,
            the touched objects and their tags at the moment of the decision.

    Returns:
        The generated ``audit_id``.

    Raises:
        ValueError: If ``phase`` is not one of :data:`PHASES`. A typo here would produce a
            row that no console view selects, which is the same as losing it.
    """
    if phase not in PHASES:
        raise ValueError(f"phase {phase!r} is not one of {', '.join(PHASES)}")

    audit_id = f"AUD-{uuid.uuid4().hex[:12]}"
    session.sql(
        APPEND,
        params=[
            json.dumps(
                {
                    "audit_id": audit_id,
                    "phase": phase,
                    "exception_id": exception_id,
                    "finding_id": finding_id,
                    "action_id": action_id,
                    "actor": actor,
                    "tier": int(tier) if tier is not None else None,
                    "outcome": outcome,
                    "rationale": rationale,
                    "payload": dict(payload or {}),
                }
            )
        ],
    ).collect()
    return audit_id
