"""Tests for the orchestrator.

Two properties matter more than the routing arithmetic. The loop's outcome is derived by
re-reading persisted rows rather than by trusting the model, and every path — executed,
queued, refused, malformed — terminates in an audit row rather than in silence.
"""

import json
import re

import pytest
from snowflake.snowpark import Row
from snowflake.snowpark.exceptions import SnowparkSQLException

from warrant.authority.tiers import Tier
from warrant.orchestrate.loop import (
    MAX_AUTO_ACTIONS,
    notify_approvers,
    run_loop,
    save_finding,
    settle,
)

from .conftest import DEMO_TAGS, FakeSession, bound

AUDIT = "INSERT INTO WARRANT.AUDIT.ACTION_AUDIT"
QUEUE = "INSERT INTO WARRANT.CORE.PENDING_ACTIONS"
SAVE = "INSERT INTO WARRANT.CORE.FINDINGS"

COUNTS = Row(OPEN_EXCEPTIONS=1, FINDINGS=1, AWAITING_APPROVAL=0, EXECUTED=1, REFUSALS=0)


def exception_row(metric="supplier_otd_rate", entity="SUP-002", objects=None) -> Row:
    return Row(
        EXCEPTION_ID=f"EXC-{entity}",
        METRIC=metric,
        ENTITY=entity,
        OBSERVED="40.5% on-time",
        EXPECTED="90.8% baseline",
        DEVIATION="-50.3pp",
        DETECTION_METHOD="rb001",
        SOURCE_OBJECTS=objects or ["WARRANT.DATA.SHIPMENTS"],
    )


def proposal(action_type="open_supplier_case", params=None) -> dict:
    return {
        "severity": "high",
        "root_cause": "Sustained delivery failure.",
        "evidence": ["40.5% versus 90.8%"],
        "recommended_action": "Open a case.",
        "action_type": action_type,
        "action_params": params
        or {"supplier_id": "SUP-002", "justification": "50.3pp below baseline"},
    }


def loop_session(
    exceptions: list[Row],
    reply: dict | None = None,
    tags: dict | None = None,
    counts: Row = COUNTS,
    already_investigated: bool = False,
    email: bool = True,
    failures=None,
) -> FakeSession:
    live = DEMO_TAGS if tags is None else tags

    def answer(params):
        """Reply as the model would: about the entity the prompt actually asked about.

        A fixed reply naming one supplier would be correctly refused for every other
        exception, since ``validate_proposal`` rejects a proposal aimed at an entity that
        was not flagged.
        """
        if reply is not None:
            body = reply
        else:
            (entity,) = re.findall(r"^Entity: (\S+)$", params[1], re.MULTILINE)
            body = proposal(params={"supplier_id": entity, "justification": "below baseline"})
        return [Row(REPLY=json.dumps({"value": body, "error": None}))]

    return FakeSession(
        responses={
            "ORDER BY metric, entity": exceptions,
            "SELECT 1 FROM WARRANT.CORE.FINDINGS": [Row(ONE=1)] if already_investigated else [],
            "SEARCH_PREVIEW": [Row(DOC_ID="RB-001", TITLE="t", BODY="b")],
            "AI_COMPLETE": answer,
            "SYSTEM$GET_TAG": lambda p: [Row(SENSITIVITY=live.get(p[1]))],
            "AS open_exceptions": [counts],
            "CURRENT_TIMESTAMP()": [Row(NOW="2026-08-05 09:00:00.000")],
            "WHERE key = 'escalation_email'": [Row(VALUE="x@example.invalid")] if email else [],
            # The executor reloads the queued row it was just handed.
            "SELECT action_id, finding_id": [
                Row(
                    ACTION_ID="ACT-1",
                    FINDING_ID="FND-1",
                    ACTION_TYPE=(reply or proposal())["action_type"],
                    ACTION_PARAMS=json.dumps((reply or proposal())["action_params"]),
                    EFFECTIVE_TIER=int(Tier.LOW_RISK_ACT),
                    DECISION="auto",
                    EXECUTED_AT=None,
                    EXECUTION_RESULT=None,
                )
            ],
        },
        failures=failures,
    )


def phases(session: FakeSession) -> list[str]:
    return [bound(c)["phase"] for c in session.calls if AUDIT in c.sql]


def test_a_quiet_run_is_safe_and_still_recorded():
    """The common case for anything on a cron: nothing is wrong."""
    session = loop_session([], counts=Row(**dict.fromkeys(COUNTS.as_dict(), 0)))
    result = run_loop(session)
    assert result["run_id"].startswith("RUN-")
    assert phases(session) == ["detect", "route"]
    assert not any(QUEUE in c.sql for c in session.calls)


def test_an_open_footprint_is_executed_and_every_phase_is_audited():
    session = loop_session([exception_row()])
    run_loop(session)
    assert phases(session) == ["detect", "classify", "execute", "route"]
    queue = next(c for c in session.calls if QUEUE in c.sql)
    assert bound(queue)["decision"] == "auto"
    assert bound(queue)["effective_tier"] == int(Tier.LOW_RISK_ACT)


def test_an_internal_footprint_is_queued_rather_than_executed():
    session = loop_session(
        [exception_row("inventory_days_of_cover", "SKU-1003")],
        reply=proposal(
            "raise_replenishment",
            {"sku": "SKU-1003", "quantity": 49000, "justification": "5.0 days"},
        ),
    )
    run_loop(session)
    queue = next(c for c in session.calls if QUEUE in c.sql)
    assert bound(queue)["decision"] == "pending"
    assert bound(queue)["effective_tier"] == int(Tier.APPROVAL_REQUIRED)
    assert bound(queue)["binding_object"] == "WARRANT.DATA.INVENTORY", "the binding object is named"
    assert "execute" not in phases(session)


def test_a_regulated_footprint_is_refused_and_never_queued():
    session = loop_session(
        [exception_row("quality_hold_age", "QH-0034")],
        reply=proposal("release_quality_hold", {"disposition": "released", "hold_id": "QH-0034"}),
    )
    run_loop(session)
    assert phases(session) == ["detect", "classify", "refuse", "route"]
    assert not any(QUEUE in c.sql for c in session.calls), "a refused action is not queued"


def test_propose_mode_queues_what_auto_mode_would_have_executed():
    session = loop_session([exception_row()])
    run_loop(session, mode="PROPOSE")
    queue = next(c for c in session.calls if QUEUE in c.sql)
    assert bound(queue)["decision"] == "pending"
    assert "ran in PROPOSE mode" in bound(queue)["tier_rationale"]
    assert "execute" not in phases(session)


def test_the_circuit_breaker_routes_the_overflow_for_approval():
    """A detector bug should produce approval requests, not a thousand actions."""
    session = loop_session(
        [exception_row(entity=f"SUP-{n:03d}") for n in range(MAX_AUTO_ACTIONS + 3)]
    )
    run_loop(session)
    decisions = [bound(c)["decision"] for c in session.calls if QUEUE in c.sql]
    assert decisions.count("auto") == MAX_AUTO_ACTIONS
    assert decisions.count("pending") == 3
    rationale = [bound(c)["tier_rationale"] for c in session.calls if QUEUE in c.sql][-1]
    assert "circuit breaker" in rationale


def test_an_exception_already_investigated_is_not_reasoned_about_again():
    """Re-queueing an action a human already rejected would be worse than doing nothing."""
    session = loop_session([exception_row()], already_investigated=True)
    run_loop(session)
    assert not any("AI_COMPLETE" in c.sql for c in session.calls)
    assert phases(session) == ["detect", "route"]


def test_a_refused_proposal_is_audited_under_the_reason_phase():
    session = loop_session([exception_row()], reply=proposal(params={"supplier_id": "SUP-999"}))
    run_loop(session)
    assert phases(session) == ["detect", "reason", "route"]
    reason = next(c for c in session.calls if AUDIT in c.sql and bound(c)["phase"] == "reason")
    assert bound(reason)["outcome"] == "malformed_proposal"


def test_settle_reads_the_world_rather_than_remembering_it():
    session = FakeSession(responses={"AS open_exceptions": [COUNTS]})
    assert settle(session, "2026-08-05 09:00:00.000") == {
        "open_exceptions": 1,
        "findings": 1,
        "awaiting_approval": 0,
        "executed": 1,
        "refusals": 0,
    }
    assert session.calls[0].params == ("2026-08-05 09:00:00.000",), (
        "refusals are counted from the run start, not from the beginning of time"
    )


def test_the_summary_comes_from_settle_not_from_an_accumulator():
    """A model that hallucinates having acted must not be able to inflate the summary."""
    counts = Row(OPEN_EXCEPTIONS=9, FINDINGS=9, AWAITING_APPROVAL=4, EXECUTED=3, REFUSALS=2)
    session = loop_session([exception_row()], counts=counts)
    result = run_loop(session)
    assert result["executed"] == 3 and result["refusals"] == 2


def test_a_finding_is_persisted_with_its_arrays_as_json():
    from warrant.common.models import Finding

    session = FakeSession()
    save_finding(
        session,
        Finding(
            finding_id="FND-1",
            exception_id="EXC-1",
            severity="high",
            root_cause="cause",
            evidence=("a", "b"),
            recommended_action="do it",
            action_type="open_supplier_case",
            action_params={"supplier_id": "SUP-002"},
            requested_tier=Tier.LOW_RISK_ACT,
            touched_objects=("WARRANT.DATA.SHIPMENTS",),
            grounded_in=("RB-001",),
            model="claude-sonnet-4-6",
        ),
    )
    (call,) = session.calls
    row = bound(call)
    assert row["evidence"] == ["a", "b"]
    assert row["grounded_in"] == ["RB-001"]
    assert row["action_params"] == {"supplier_id": "SUP-002"}
    assert row["requested_tier"] == int(Tier.LOW_RISK_ACT)


@pytest.mark.parametrize("pending", [0])
def test_nothing_pending_sends_no_email(pending):
    session = FakeSession()
    assert notify_approvers(session, pending) is False
    assert session.calls == []


def test_escalation_degrades_rather_than_failing_the_run():
    """Email is best-effort: a trial account may have no verified recipient at all."""
    session = FakeSession(
        responses={"WHERE key = 'escalation_email'": [Row(VALUE="x@example.invalid")]},
        failures={"SYSTEM$SEND_EMAIL": SnowparkSQLException("not allowed")},
    )
    assert notify_approvers(session, 3) is False


def test_no_configured_recipient_is_not_an_error():
    session = FakeSession(responses={"WHERE key = 'escalation_email'": []})
    assert notify_approvers(session, 3) is False


def test_a_pending_queue_notifies_a_human():
    counts = Row(OPEN_EXCEPTIONS=1, FINDINGS=1, AWAITING_APPROVAL=2, EXECUTED=0, REFUSALS=0)
    session = loop_session([], counts=counts)
    assert run_loop(session)["emailed"] == 1
    body = next(c for c in session.calls if "SYSTEM$SEND_EMAIL" in c.sql).params
    assert "2 action(s) awaiting approval" in body[1]
