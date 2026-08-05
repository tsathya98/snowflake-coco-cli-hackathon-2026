"""Tests for execution.

The property these exist to protect: authority is resolved from the tags **as they are at
execution time**, not from the tier recorded when the action was queued. Everything else in
the governance model rests on that, because a tag that stops being consulted stops being a
control.
"""

import json

import pytest
from snowflake.snowpark import Row
from snowflake.snowpark.exceptions import SnowparkSQLException

from warrant.act.executor import (
    ALREADY_SETTLED,
    AWAITING_APPROVAL,
    EXECUTED,
    FAILED,
    REFUSED,
    UNKNOWN,
    execute,
)
from warrant.authority.tiers import Tier

from .conftest import DEMO_TAGS, FakeSession, bound

LOAD = "SELECT action_id, finding_id"
AUDIT = "INSERT INTO WARRANT.AUDIT.ACTION_AUDIT"
SETTLED = "UPDATE WARRANT.CORE.PENDING_ACTIONS"


def queued(
    action_type: str = "open_supplier_case",
    params: dict | None = None,
    decision: str = "auto",
    tier: int = int(Tier.LOW_RISK_ACT),
    executed_at=None,
    execution_result=None,
) -> Row:
    return Row(
        ACTION_ID="ACT-1",
        FINDING_ID="FND-1",
        ACTION_TYPE=action_type,
        ACTION_PARAMS=json.dumps(
            params or {"supplier_id": "SUP-002", "justification": "50.3pp below baseline"}
        ),
        EFFECTIVE_TIER=tier,
        DECISION=decision,
        EXECUTED_AT=executed_at,
        EXECUTION_RESULT=execution_result,
    )


def session_for(row: Row | None, tags: dict | None = None, failures=None) -> FakeSession:
    live = DEMO_TAGS if tags is None else tags
    return FakeSession(
        responses={
            LOAD: [row] if row is not None else [],
            "SYSTEM$GET_TAG": lambda p: [Row(SENSITIVITY=live.get(p[1]))],
        },
        failures=failures,
    )


def audit_rows(session: FakeSession) -> list[dict]:
    return [bound(c) for c in session.calls if AUDIT in c.sql]


def test_an_open_footprint_executes_unsupervised():
    session = session_for(queued())
    assert execute(session, "ACT-1") == EXECUTED
    assert any("INSERT INTO WARRANT.DATA.OPS_REQUESTS" in c.sql for c in session.calls)
    assert audit_rows(session)[0]["outcome"] == EXECUTED
    assert any(SETTLED in c.sql and bound(c)["ran"] is True for c in session.calls)


def test_a_regulated_footprint_is_refused_even_when_a_human_approved_it():
    """The scenario the whole design exists for.

    A human approved a replenishment against internal data. Governance then reclassified the
    table. The approval does not survive the reclassification, and the rationale says so.
    """
    session = session_for(
        queued(
            "raise_replenishment",
            {"sku": "SKU-1003", "quantity": 49000, "justification": "5.0 days of cover"},
            decision="approved",
            tier=int(Tier.APPROVAL_REQUIRED),
        ),
        tags={**DEMO_TAGS, "WARRANT.DATA.INVENTORY": "regulated"},
    )
    assert execute(session, "ACT-1") == REFUSED
    (row,) = audit_rows(session)
    assert row["phase"] == "refuse" and row["outcome"] == REFUSED
    assert row["tier"] == int(Tier.FORBIDDEN)
    assert "classification in force at execution time" in row["rationale"]
    assert not any("UPDATE WARRANT.DATA" in c.sql for c in session.calls), "nothing was written"


def test_a_refusal_records_the_tier_it_was_queued_at():
    """The audit needs both numbers: what was true then, and what is true now."""
    session = session_for(
        queued("release_quality_hold", {"disposition": "released", "hold_id": "QH-0034"}),
    )
    assert execute(session, "ACT-1") == REFUSED
    payload = audit_rows(session)[0]["payload"]
    assert payload["tier_at_proposal"] == int(Tier.LOW_RISK_ACT)
    assert payload["touched"]["WARRANT.DATA.QUALITY_HOLDS"] == "regulated"


def test_an_unapproved_action_needing_approval_waits():
    session = session_for(
        queued(
            "raise_replenishment",
            {"sku": "SKU-1003", "quantity": 49000, "justification": "low cover"},
            decision="pending",
            tier=int(Tier.APPROVAL_REQUIRED),
        )
    )
    assert execute(session, "ACT-1") == AWAITING_APPROVAL
    assert audit_rows(session)[0]["phase"] == "route"
    assert not any("INSERT INTO WARRANT.DATA" in c.sql for c in session.calls)


def test_an_approved_action_on_internal_data_executes():
    session = session_for(
        queued(
            "raise_replenishment",
            {"sku": "SKU-1003", "quantity": 49000, "justification": "low cover"},
            decision="approved",
            tier=int(Tier.APPROVAL_REQUIRED),
        )
    )
    assert execute(session, "ACT-1") == EXECUTED


def test_a_draft_against_regulated_data_is_permitted():
    """RB-003: automation may surface a hold and notify, and nothing further.

    The agent must be able to speak about what it may never touch, or it could not explain
    the exception it detected.
    """
    session = session_for(
        queued("notify_quality_owner", {"hold_id": "QH-0034", "message": "aging hold"}),
    )
    assert execute(session, "ACT-1") == EXECUTED


@pytest.mark.parametrize(
    ("executed_at", "result"),
    [("2026-08-05 10:00:00", EXECUTED), (None, REFUSED), (None, FAILED)],
    ids=["executed", "refused", "failed"],
)
def test_a_settled_action_is_never_run_again_and_writes_no_audit_row(executed_at, result):
    """Re-recording a decision would inflate the counts the impact figures come from."""
    session = session_for(queued(executed_at=executed_at, execution_result=result))
    assert execute(session, "ACT-1") == ALREADY_SETTLED
    assert audit_rows(session) == []
    assert len(session.calls) == 1


def test_a_refusal_survives_the_tag_being_restored():
    """A refusal must be terminal, not a pause.

    A refused action keeps ``executed_at`` NULL while ``decision`` stays ``approved`` — a human
    really did approve it. So anything claiming work on ``executed_at IS NULL`` alone would pick
    the refusal straight back up, and once the classification was restored it would execute the
    exact action the agent had declined. ``execution_result`` is what makes it final.
    """
    refused = queued(
        "raise_replenishment",
        {"sku": "SKU-1003", "quantity": 49000, "justification": "5.0 days of cover"},
        decision="approved",
        tier=int(Tier.APPROVAL_REQUIRED),
        execution_result=REFUSED,
    )
    # INVENTORY is back to 'internal', so authority alone would now permit this.
    session = session_for(refused, tags=DEMO_TAGS)
    assert execute(session, "ACT-1") == ALREADY_SETTLED
    assert not any("INSERT INTO WARRANT.DATA" in c.sql for c in session.calls)


def test_a_missing_action_is_recorded_rather_than_raised():
    session = session_for(None)
    assert execute(session, "ACT-1") == UNKNOWN
    assert audit_rows(session)[0]["outcome"] == UNKNOWN


def test_an_unregistered_action_type_is_recorded_rather_than_raised():
    session = session_for(queued(action_type="drop_everything"))
    assert execute(session, "ACT-1") == UNKNOWN
    assert "unknown action type" in audit_rows(session)[0]["rationale"]


def test_a_failed_statement_is_audited_with_its_rollback_availability():
    session = session_for(
        queued(), failures={"INSERT INTO WARRANT.DATA.OPS_REQUESTS": SnowparkSQLException("boom")}
    )
    assert execute(session, "ACT-1") == FAILED
    (row,) = audit_rows(session)
    assert row["outcome"] == FAILED and "boom" in row["rationale"]
    assert row["payload"]["rollback_available"] is True
    assert any(SETTLED in c.sql and bound(c)["result"] == FAILED for c in session.calls)


def test_parameters_are_bound_into_the_action_statement():
    session = session_for(queued())
    execute(session, "ACT-1")
    call = next(c for c in session.calls if "INSERT INTO WARRANT.DATA.OPS_REQUESTS" in c.sql)
    assert call.params == ("SUP-002", "50.3pp below baseline")
    assert "SUP-002" not in call.sql


@pytest.mark.parametrize("stored", [None, int(Tier.FORBIDDEN)])
def test_a_refusal_reads_naturally_when_nothing_was_reclassified(stored):
    """The reclassification note must appear only when a reclassification actually happened."""
    session = session_for(
        queued("release_quality_hold", {"disposition": "released", "hold_id": "QH-1"}, tier=stored)
    )
    assert execute(session, "ACT-1") == REFUSED
    assert "classification in force at execution time" not in audit_rows(session)[0]["rationale"]
