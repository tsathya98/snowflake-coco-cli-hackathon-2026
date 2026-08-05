"""detect → reason → classify → route → audit.

Three properties make this safe to run on a schedule against a live system.

**The model's reply never decides what happens next.** A reasoning turn returns a proposal;
what the loop does with it is decided by re-reading persisted state. :func:`settle` derives
the run's outcome by counting rows in the tables afterwards, not by trusting anything the
model said about what it had done. A model that hallucinates having acted cannot make the
loop believe it.

**Every path terminates in a row.** Auto-executed, queued for approval, refused, or
malformed — each ends as an ``ACTION_AUDIT`` entry someone can point at. A refusal is not an
absence of output.

**It is safe to run when nothing is wrong**, which is the common case for anything on a
cron, and safe to run twice, which is the common case for anything a judge is testing.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException

from warrant.act.executor import EXECUTED, execute
from warrant.act.registry import ACTION_TYPES
from warrant.authority.tags import read_sensitivity
from warrant.authority.tiers import resolve
from warrant.common.audit import record
from warrant.common.models import Finding
from warrant.detect.exceptions import detect
from warrant.reason.investigate import investigate

MAX_AUTO_ACTIONS = 10
"""Circuit breaker.

Beyond this many unsupervised actions in a single pass, the loop stops executing and routes
the remainder for human approval instead. A detector bug that flags a thousand entities
should produce a thousand approval requests, not a thousand actions.
"""

FINDING_EXISTS = "SELECT 1 FROM WARRANT.CORE.FINDINGS WHERE exception_id = ?"

# Bound as one JSON object, not as positional parameters: inside a stored procedure a bound
# None renders as the string 'None'. See the note in warrant.common.audit.
SAVE_FINDING = """
INSERT INTO WARRANT.CORE.FINDINGS
       (finding_id, exception_id, severity, root_cause, evidence, grounded_in,
        recommended_action, action_type, action_params, requested_tier,
        touched_objects, model)
SELECT r:finding_id::STRING,        r:exception_id::STRING,
       r:severity::STRING,          r:root_cause::STRING,
       r:evidence,                  r:grounded_in,
       r:recommended_action::STRING, r:action_type::STRING,
       r:action_params,             r:requested_tier::NUMBER,
       r:touched_objects,           r:model::STRING
  FROM (SELECT PARSE_JSON(?) AS r)
"""

QUEUE_ACTION = """
INSERT INTO WARRANT.CORE.PENDING_ACTIONS
       (action_id, finding_id, action_type, action_params, effective_tier,
        binding_object, tier_rationale, rollback_plan, decision)
SELECT r:action_id::STRING,      r:finding_id::STRING,
       r:action_type::STRING,    r:action_params,
       r:effective_tier::NUMBER, r:binding_object::STRING,
       r:tier_rationale::STRING, r:rollback_plan::STRING,
       r:decision::STRING
  FROM (SELECT PARSE_JSON(?) AS r)
"""

# Refusals are counted from a timestamp rather than in total, because ACTION_AUDIT is
# append-only and deliberately survives sql/90_reset.sql. Counting every refusal ever logged
# would make a run summary read as though this pass had refused things a previous one did.
SETTLE = """
SELECT (SELECT COUNT(*) FROM WARRANT.CORE.EXCEPTIONS
         WHERE state = 'open')                    AS open_exceptions,
       (SELECT COUNT(*) FROM WARRANT.CORE.FINDINGS)                AS findings,
       (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS
         WHERE decision = 'pending')              AS awaiting_approval,
       (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS
         WHERE execution_result = 'executed')     AS executed,
       (SELECT COUNT(*) FROM WARRANT.AUDIT.ACTION_AUDIT
         WHERE phase = 'refuse'
           AND ts >= TO_TIMESTAMP_NTZ(?))         AS refusals
"""

NOW = "SELECT TO_VARCHAR(CURRENT_TIMESTAMP(), 'YYYY-MM-DD HH24:MI:SS.FF3') AS now"

ESCALATION_EMAIL = "SELECT value FROM WARRANT.CORE.CONFIG WHERE key = 'escalation_email'"

SEND_EMAIL = "CALL SYSTEM$SEND_EMAIL('WARRANT_EMAIL', ?, ?, ?)"


def settle(session: Session, since: str) -> dict[str, int]:
    """Derive the state of the world by reading it, not by remembering it.

    Args:
        session: An active Snowpark session.
        since: Timestamp the run began, as ``YYYY-MM-DD HH:MM:SS.mmm``. Refusals are counted
            from here rather than in total, because the audit log outlives any single run.

    Returns:
        Counts of open exceptions, findings, actions awaiting approval, actions executed, and
        refusals recorded during this run. This is the loop's only source of truth about what
        happened — deliberately not accumulated in memory as it runs, because an accumulator
        records what the code believed rather than what the database accepted.
    """
    row = session.sql(SETTLE, params=[since]).collect()[0]
    return {key.lower(): int(value) for key, value in row.as_dict().items()}


def save_finding(session: Session, finding: Finding) -> None:
    """Persist a finding to ``CORE.FINDINGS``.

    Args:
        session: An active Snowpark session.
        finding: The validated finding to store.
    """
    session.sql(
        SAVE_FINDING,
        params=[
            json.dumps(
                {
                    "finding_id": finding.finding_id,
                    "exception_id": finding.exception_id,
                    "severity": finding.severity,
                    "root_cause": finding.root_cause,
                    "evidence": list(finding.evidence),
                    "grounded_in": list(finding.grounded_in),
                    "recommended_action": finding.recommended_action,
                    "action_type": finding.action_type,
                    "action_params": dict(finding.action_params),
                    "requested_tier": int(finding.requested_tier),
                    "touched_objects": list(finding.touched_objects),
                    "model": finding.model,
                }
            )
        ],
    ).collect()


def notify_approvers(session: Session, pending: int) -> bool:
    """Tell a human that something is waiting for them.

    Args:
        session: An active Snowpark session.
        pending: How many actions are awaiting approval.

    Returns:
        ``True`` if an email was sent. Escalation is best-effort by design: on a trial
        account email reaches only verified users in the same account, so a missing
        integration must degrade to "the console is the notification surface" rather than
        failing a run that has already done its work correctly.
    """
    if not pending:
        return False
    try:
        rows = session.sql(ESCALATION_EMAIL).collect()
        if not rows:
            return False
        session.sql(
            SEND_EMAIL,
            params=[
                rows[0][0],
                f"Warrant :: {pending} action(s) awaiting approval",
                (
                    f"{pending} proposed action(s) need a decision.\n\n"
                    "Each was raised because the data it touches is classified in a way "
                    "that requires human approval. Open the Warrant console to review the "
                    "evidence and approve, reject or defer."
                ),
            ],
        ).collect()
    except SnowparkSQLException:
        return False
    # In the `else`, not the `try`: only the two statements above are being guarded. A `return
    # True` inside the block would sit under an exception handler it has no business being
    # under, and would quietly start swallowing failures if anything were ever added below it.
    else:
        return True


def run_loop(session: Session, mode: str = "AUTO") -> dict[str, Any]:
    """Run one full pass of the agent loop.

    Args:
        session: An active Snowpark session.
        mode: ``AUTO`` executes actions the tags permit unsupervised. ``PROPOSE`` routes
            everything for human approval regardless — useful for a first run against
            unfamiliar data, and for a demo where nothing should change without a keystroke.

    Returns:
        A summary containing the run id, the mode, and the counts from :func:`settle`.
    """
    run_id = f"RUN-{uuid.uuid4().hex[:12]}"
    started = session.sql(NOW).collect()[0]["NOW"]
    exceptions = detect(session)
    record(
        session,
        phase="detect",
        outcome="scanned",
        rationale=f"{len(exceptions)} open exception(s) after this pass.",
        payload={"run_id": run_id, "mode": mode},
    )

    auto_executed = 0
    for exception in exceptions:
        # RB-005 in spirit: one finding per exception. Re-reasoning an exception already
        # investigated would duplicate the finding and re-queue an action a human may have
        # already rejected.
        if session.sql(FINDING_EXISTS, params=[exception.exception_id]).collect():
            continue

        outcome = investigate(session, exception)
        if not isinstance(outcome, Finding):
            record(
                session,
                phase="reason",
                outcome=outcome.outcome,
                rationale=outcome.reason,
                exception_id=exception.exception_id,
                payload={"run_id": run_id},
            )
            continue

        save_finding(session, outcome)
        touched = read_sensitivity(session, outcome.touched_objects)
        decision = resolve(outcome.requested_tier, touched)
        record(
            session,
            phase="classify",
            outcome=decision.tier.name,
            rationale=decision.rationale,
            exception_id=exception.exception_id,
            finding_id=outcome.finding_id,
            tier=decision.tier,
            payload={
                "run_id": run_id,
                "touched": {obj.fqn: obj.sensitivity for obj in touched},
            },
        )

        if decision.is_refused:
            record(
                session,
                phase="refuse",
                outcome="refused",
                rationale=decision.rationale,
                exception_id=exception.exception_id,
                finding_id=outcome.finding_id,
                tier=decision.tier,
                payload={"run_id": run_id, "action_type": outcome.action_type},
            )
            continue

        breaker_tripped = auto_executed >= MAX_AUTO_ACTIONS
        unsupervised = decision.is_auto_executable and mode == "AUTO" and not breaker_tripped
        rationale = decision.rationale
        if breaker_tripped:
            rationale += (
                f" Routed for approval instead: the circuit breaker limit of "
                f"{MAX_AUTO_ACTIONS} unsupervised actions in one pass was reached."
            )
        elif decision.is_auto_executable and mode != "AUTO":
            rationale += f" Routed for approval instead because the loop ran in {mode} mode."

        action_id = f"ACT-{uuid.uuid4().hex[:12]}"
        session.sql(
            QUEUE_ACTION,
            params=[
                json.dumps(
                    {
                        "action_id": action_id,
                        "finding_id": outcome.finding_id,
                        "action_type": outcome.action_type,
                        "action_params": dict(outcome.action_params),
                        "effective_tier": int(decision.tier),
                        "binding_object": decision.binding_object,
                        "tier_rationale": rationale,
                        # RB-004 treats a missing undo path as grounds for more scrutiny,
                        # not less, so the approver is shown it — or shown its absence.
                        "rollback_plan": ACTION_TYPES[outcome.action_type].rollback_sql,
                        "decision": "auto" if unsupervised else "pending",
                    }
                )
            ],
        ).collect()

        if unsupervised and execute(session, action_id) == EXECUTED:
            auto_executed += 1

    counts = settle(session, started)
    counts["emailed"] = int(notify_approvers(session, counts["awaiting_approval"]))
    record(
        session,
        phase="route",
        outcome="settled",
        rationale=(
            f"{counts['executed']} executed, {counts['awaiting_approval']} awaiting "
            f"approval, {counts['refusals']} refused."
        ),
        payload={"run_id": run_id, **counts},
    )
    return {"run_id": run_id, "mode": mode, **counts}
