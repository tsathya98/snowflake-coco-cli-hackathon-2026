"""Tests for decision replay.

The claim replay makes is narrow and has to stay narrow: it reports which recorded actions today's
classifications would resolve differently, and it never writes. The row that matters is the one
where work **already took effect** under a policy that has since tightened, because that is the only
category which cannot be fixed going forward.
"""

import pytest
from snowflake.snowpark import Row

from warrant.authority.replay import DECIDED_ACTIONS, replay, summarise
from warrant.authority.tiers import Tier

from .conftest import DEMO_TAGS, FakeSession

SOURCE = "FROM WARRANT.CORE.PENDING_ACTIONS"


def action_row(
    action_id="ACT-1",
    action_type="open_supplier_case",
    effective_tier=int(Tier.LOW_RISK_ACT),
    decision="auto",
    execution_result="executed",
) -> Row:
    return Row(
        ACTION_ID=action_id,
        ACTION_TYPE=action_type,
        EFFECTIVE_TIER=effective_tier,
        DECISION=decision,
        DECIDED_BY="TSATHYA98",
        DECIDED_AT="2026-08-05 12:00",
        PROPOSED_AT="2026-08-05 11:00",
        EXECUTION_RESULT=execution_result,
    )


def session(rows: list[Row], tags: dict | None = None) -> FakeSession:
    live = DEMO_TAGS if tags is None else tags
    return FakeSession(
        responses={
            SOURCE: rows,
            "SYSTEM$GET_TAG": lambda p: [Row(SENSITIVITY=live.get(p[1]), RETENTION=None)],
        }
    )


def test_an_unchanged_policy_replays_with_no_divergence():
    (row,) = replay(session([action_row()]))
    assert row.tier_then is Tier.LOW_RISK_ACT
    assert row.tier_now is Tier.LOW_RISK_ACT
    assert row.diverged is False
    assert row.needs_attention is False
    assert row.now_forbidden is False


def test_executed_work_that_todays_policy_would_forbid_needs_attention():
    """The regulator's question, and the only one replay exists to answer."""
    (row,) = replay(
        session([action_row()], tags={**DEMO_TAGS, "WARRANT.DATA.SHIPMENTS": "regulated"})
    )
    assert row.tier_then is Tier.LOW_RISK_ACT
    assert row.tier_now is Tier.FORBIDDEN
    assert row.diverged is True
    assert row.now_forbidden is True
    assert row.needs_attention is True
    assert "regulated" in row.rationale_now


def test_a_queued_action_that_never_ran_does_not_need_attention():
    """Tightening policy around something that never happened is the control working."""
    (row,) = replay(
        session(
            [action_row(decision="pending", execution_result="none")],
            tags={**DEMO_TAGS, "WARRANT.DATA.SHIPMENTS": "regulated"},
        )
    )
    assert row.diverged is True
    assert row.needs_attention is False


def test_an_action_already_refused_and_still_refused_needs_no_attention():
    (row,) = replay(
        session(
            [
                action_row(
                    action_type="release_quality_hold",
                    effective_tier=int(Tier.FORBIDDEN),
                    execution_result="refused",
                )
            ]
        )
    )
    assert row.tier_now is Tier.FORBIDDEN
    assert row.diverged is False
    assert row.needs_attention is False


def test_a_loosened_policy_diverges_but_needs_no_attention():
    """Work done under a stricter policy than today's is not a finding."""
    (row,) = replay(
        session(
            [
                action_row(
                    action_type="raise_replenishment", effective_tier=int(Tier.APPROVAL_REQUIRED)
                )
            ],
            tags={**DEMO_TAGS, "WARRANT.DATA.INVENTORY": "open"},
        )
    )
    assert row.tier_now is Tier.LOW_RISK_ACT
    assert row.diverged is True
    assert row.needs_attention is False


def test_an_action_type_no_longer_in_the_registry_is_reported_not_dropped():
    """An action the code can no longer describe is exactly what an auditor should see."""
    (row,) = replay(session([action_row(action_type="retired_action")]))
    assert row.tier_now is Tier.FORBIDDEN
    assert row.binding_object_now is None
    assert "no longer in the registry" in row.rationale_now
    assert row.needs_attention is True


def test_a_missing_stored_tier_cannot_diverge():
    """Without a recorded tier there is nothing to compare against, so claim nothing."""
    (row,) = replay(session([action_row(effective_tier=None)]))
    assert row.tier_then is None
    assert row.diverged is False
    assert row.needs_attention is False


def test_replay_never_writes():
    live = session([action_row()])
    replay(live)
    assert not any(
        verb in call.sql.upper()
        for call in live.calls
        for verb in ("INSERT", "UPDATE", "DELETE", "MERGE", "ALTER")
    )


def test_an_override_lets_an_auditor_ask_before_changing_anything():
    (row,) = replay(session([action_row()]), overrides={"WARRANT.DATA.SHIPMENTS": "regulated"})
    assert row.needs_attention is True


@pytest.mark.parametrize("empty", [[], None])
def test_replaying_nothing_summarises_to_zeroes(empty):
    replayed = replay(session(empty or []))
    assert summarise(replayed) == {
        "replayed": 0,
        "diverged": 0,
        "now_forbidden": 0,
        "needs_attention": 0,
    }


def test_summarise_counts_each_category_independently():
    replayed = replay(
        session(
            [
                action_row(action_id="ACT-1"),
                action_row(action_id="ACT-2", action_type="expedite_shipment"),
                action_row(action_id="ACT-3", decision="pending", execution_result="none"),
            ],
            tags={**DEMO_TAGS, "WARRANT.DATA.SHIPMENTS": "regulated"},
        )
    )
    assert summarise(replayed) == {
        "replayed": 3,
        "diverged": 3,
        "now_forbidden": 3,
        "needs_attention": 2,
    }


def test_the_source_query_orders_newest_first():
    assert "ORDER BY p.proposed_at DESC" in DECIDED_ACTIONS
