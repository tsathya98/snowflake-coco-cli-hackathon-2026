"""Executing a queued action, and refusing to.

The one idea worth stating plainly: **authority is resolved again here, at execution time,
against the tags as they are now.** The tier stored on the queued row records what was true
when the action was proposed, which is evidence, not permission. If a table was reclassified
between proposal and execution — or between a human approving an action and the executor
reaching it — the newer classification wins and the action does not run.

That is what makes the governance tag load-bearing rather than decorative. A model that is
consulted once at proposal time and then trusted forever is a model that documents policy
instead of enforcing it.

Nothing here raises on a governance outcome. A refusal is a returned status and an audit
row, because the loop must be able to refuse one action and carry on with the next.
"""

from __future__ import annotations

import json

from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException

from warrant.act.registry import ActionValidationError, get_action_type
from warrant.authority.tags import read_sensitivity
from warrant.authority.tiers import resolve
from warrant.common.audit import record

EXECUTED = "executed"
REFUSED = "refused"
AWAITING_APPROVAL = "awaiting_approval"
ALREADY_SETTLED = "already_settled"
FAILED = "failed"
UNKNOWN = "unknown_action"

# execution_result is selected, not just executed_at, and that distinction is the difference
# between a refusal being final and a refusal being a pause. A refused action keeps
# executed_at NULL — nothing ran — while decision stays 'approved', because a human really did
# approve it. Any query that claims work on `decision = 'approved' AND executed_at IS NULL`
# alone would therefore pick a refused action straight back up, and if the tag had since been
# restored it would execute the very thing the agent declined to do.
LOAD_ACTION = """
SELECT action_id, finding_id, action_type, action_params, effective_tier, decision,
       executed_at, execution_result
  FROM WARRANT.CORE.PENDING_ACTIONS
 WHERE action_id = ?
"""

# Bound as one JSON object: inside a stored procedure a bound None renders as the string
# 'None', and a bound bool as 'True'. See the note in warrant.common.audit.
SETTLE_ACTION = """
UPDATE WARRANT.CORE.PENDING_ACTIONS AS p
   SET executed_at = IFF(s.r:ran::BOOLEAN, CURRENT_TIMESTAMP(), NULL),
       execution_result = s.r:result::STRING
  FROM (SELECT PARSE_JSON(?) AS r) AS s
 WHERE p.action_id = s.r:action_id::STRING
"""

AUTHORISED = ("auto", "approved")
"""Queue decisions that permit execution. Anything else has not been cleared by a human."""


def execute(session: Session, action_id: str) -> str:
    """Run one queued action, if it is still permitted.

    Args:
        session: An active Snowpark session.
        action_id: The ``PENDING_ACTIONS`` row to act on.

    Returns:
        One of :data:`EXECUTED`, :data:`REFUSED`, :data:`AWAITING_APPROVAL`,
        :data:`ALREADY_SETTLED`, :data:`FAILED` or :data:`UNKNOWN`. Every outcome except
        :data:`ALREADY_SETTLED` writes an audit row; a repeat call writes nothing because the
        first call already recorded the decision, and re-recording it would inflate the very
        counts the impact figures are drawn from.

        An action that has already been settled — executed, refused or failed — is terminal.
        Reversing a refusal requires a human to clear ``execution_result`` deliberately, not a
        background task noticing the row again after a tag changed back.
    """
    rows = session.sql(LOAD_ACTION, params=[action_id]).collect()
    if not rows:
        record(
            session,
            phase="execute",
            outcome=UNKNOWN,
            rationale=f"No queued action {action_id}.",
            action_id=action_id,
        )
        return UNKNOWN
    row = rows[0]

    if row["EXECUTED_AT"] is not None or row["EXECUTION_RESULT"] is not None:
        return ALREADY_SETTLED

    try:
        action = get_action_type(row["ACTION_TYPE"])
    except ActionValidationError as error:
        record(
            session,
            phase="execute",
            outcome=UNKNOWN,
            rationale=str(error),
            action_id=action_id,
            finding_id=row["FINDING_ID"],
        )
        return UNKNOWN

    # Re-read the tags. Not the stored tier — the tags, now.
    touched = read_sensitivity(session, action.touched_objects)
    decision = resolve(action.requested_tier, touched)
    footprint = {obj.fqn: obj.sensitivity for obj in touched}
    stored_tier = row["EFFECTIVE_TIER"]
    reclassified = stored_tier is not None and int(stored_tier) != int(decision.tier)

    if decision.is_refused:
        rationale = decision.rationale
        if reclassified:
            rationale += (
                " This action was queued when the data carried a lower classification;"
                " the classification in force at execution time is what governs."
            )
        record(
            session,
            phase="refuse",
            outcome=REFUSED,
            rationale=rationale,
            action_id=action_id,
            finding_id=row["FINDING_ID"],
            tier=decision.tier,
            payload={"touched": footprint, "tier_at_proposal": stored_tier},
        )
        session.sql(
            SETTLE_ACTION,
            params=[json.dumps({"action_id": action_id, "result": REFUSED, "ran": False})],
        ).collect()
        return REFUSED

    if not decision.is_auto_executable and row["DECISION"] not in AUTHORISED:
        record(
            session,
            phase="route",
            outcome=AWAITING_APPROVAL,
            rationale=decision.rationale,
            action_id=action_id,
            finding_id=row["FINDING_ID"],
            tier=decision.tier,
            payload={"touched": footprint},
        )
        return AWAITING_APPROVAL

    params = json.loads(row["ACTION_PARAMS"] or "{}")
    try:
        statement, values = action.bind(params)
        session.sql(statement, params=values).collect()
    except (ActionValidationError, SnowparkSQLException) as error:
        record(
            session,
            phase="execute",
            outcome=FAILED,
            rationale=f"{action.name} failed: {error}",
            action_id=action_id,
            finding_id=row["FINDING_ID"],
            tier=decision.tier,
            payload={"params": params, "rollback_available": action.rollback_sql is not None},
        )
        session.sql(
            SETTLE_ACTION,
            params=[json.dumps({"action_id": action_id, "result": FAILED, "ran": False})],
        ).collect()
        return FAILED

    record(
        session,
        phase="execute",
        outcome=EXECUTED,
        rationale=f"{action.name} executed. {decision.rationale}",
        action_id=action_id,
        finding_id=row["FINDING_ID"],
        tier=decision.tier,
        payload={"params": params, "touched": footprint},
    )
    session.sql(
        SETTLE_ACTION,
        params=[json.dumps({"action_id": action_id, "result": EXECUTED, "ran": True})],
    ).collect()
    return EXECUTED
