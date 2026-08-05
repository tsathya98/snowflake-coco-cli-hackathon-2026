"""Tests for the self-generated evidence pack.

The pack is assembled from the record, so what is worth testing is the ordering and the honesty:
declines come before completed work, an empty section says so rather than vanishing, model text is
labelled, and the filename cannot silently overwrite an earlier pack.
"""

from snowflake.snowpark import Row

from warrant.authority.tiers import Tier
from warrant.reason.report import TIER_LABELS, audit_pack

from .conftest import DEMO_TAGS, FakeSession

# A fabricated locator, not the build account's. A fixture never needs the real one, and this
# file is the only place in the repo that would otherwise name it.
STAMP = Row(AT="2026-08-05 21:15:00", ACCOUNT="XY00000", ROLE="WARRANT_ROLE")

EXECUTED_ROW = Row(
    ACTION_ID="ACT-1",
    ACTION_TYPE="open_supplier_case",
    EFFECTIVE_TIER=int(Tier.LOW_RISK_ACT),
    DECISION="auto",
    DECIDED_BY="agent",
    BINDING_OBJECT="WARRANT.DATA.SHIPMENTS",
    TIER_RATIONALE="LOW_RISK_ACT already meets the scrutiny demanded.",
    SEVERITY="high",
    ROOT_CAUSE="Sustained delivery failure at SUP-002.",
    GROUNDED_IN="RB-001, RB-002",
    MODEL="claude-sonnet-4-6",
)

REFUSAL_ROW = Row(
    AT="2026-08-05 20:00",
    ACTION_TYPE="release_quality_hold",
    TIER=int(Tier.FORBIDDEN),
    RATIONALE="WARRANT.DATA.QUALITY_HOLDS is tagged sensitivity='regulated'.",
)

REPLAY_ROW = Row(
    ACTION_ID="ACT-1",
    ACTION_TYPE="open_supplier_case",
    EFFECTIVE_TIER=int(Tier.LOW_RISK_ACT),
    DECISION="auto",
    DECIDED_BY="agent",
    DECIDED_AT="2026-08-05 12:00",
    PROPOSED_AT="2026-08-05 11:00",
    EXECUTION_RESULT="executed",
)

CORPUS_ROW = Row(
    DOC_ID="RB-001",
    TITLE="Supplier on-time delivery degradation",
    REVISION="7",
    EFFECTIVE_ON="2025-11-03",
    OWNER="Procurement Operations",
    PAGE_COUNT=1,
)


def session(*, refusals=(REFUSAL_ROW,), executed=(EXECUTED_ROW,), tags=None) -> FakeSession:
    live = DEMO_TAGS if tags is None else tags
    return FakeSession(
        responses={
            "CURRENT_ACCOUNT()": [STAMP],
            "FROM WARRANT.CORE.REFUSALS": list(refusals),
            "WHERE p.execution_result = 'executed'": list(executed),
            "FROM WARRANT.CORE.PENDING_ACTIONS p\n ORDER BY": [REPLAY_ROW],
            "FROM WARRANT.DATA.RUNBOOKS": [CORPUS_ROW],
            "GROUP BY phase, outcome": [Row(PHASE="refuse", OUTCOME="refused", N=2)],
            "SYSTEM$GET_TAG": lambda p: [Row(SENSITIVITY=live.get(p[1]))],
        }
    )


def test_the_pack_leads_with_declines_not_successes():
    """An evidence pack that buries the refusals is marketing."""
    _, pack = audit_pack(session())
    assert pack.index("Declined actions") < pack.index("Completed actions")


def test_model_text_is_quoted_and_labelled():
    _, pack = audit_pack(session())
    assert "> Model-generated (claude-sonnet-4-6): Sustained delivery failure" in pack


def test_an_empty_refusal_section_says_so_rather_than_disappearing():
    _, pack = audit_pack(session(refusals=()))
    assert "No actions were declined" in pack
    assert "worth stating rather than an omission" in pack


def test_an_empty_executed_section_says_so():
    _, pack = audit_pack(session(executed=()))
    assert "No actions were executed" in pack


def test_the_pack_carries_the_replay_and_its_headline_count():
    _, pack = audit_pack(session())
    assert "Re-resolution against the classifications in force today" in pack
    assert "Nothing executed under a policy that has since tightened." in pack


def test_the_replay_section_names_work_that_would_no_longer_be_permitted():
    """The one count in the pack that cannot be fixed going forward."""
    tightened = {**DEMO_TAGS, "WARRANT.DATA.SHIPMENTS": "regulated"}
    _, pack = audit_pack(session(tags=tightened))
    assert "cannot be corrected going forward" in pack
    assert "`ACT-1` **open_supplier_case** ran at" in pack


def test_the_pack_records_the_role_that_composed_it():
    """The pack is subject to the same masking as the agent, and says so."""
    _, pack = audit_pack(session())
    assert "`WARRANT_ROLE`" in pack
    assert "subject to the same masking policies" in pack


def test_the_filename_is_timestamped_so_a_pack_cannot_be_overwritten_in_place():
    name, _ = audit_pack(session())
    assert name == "warrant-audit-pack-2026-08-05-211500.md"


def test_the_pack_lists_the_corpus_with_revisions():
    _, pack = audit_pack(session())
    assert "| RB-001 | Supplier on-time delivery degradation | 7 | 2025-11-03" in pack


def test_every_tier_has_a_label():
    """A pack that printed a bare tier number would be unreadable to the person auditing it."""
    assert set(TIER_LABELS) == {int(t) for t in Tier}
    _, pack = audit_pack(session())
    assert "L4 never permitted" in pack


def test_the_pack_never_writes():
    live = session()
    audit_pack(live)
    assert not any(
        verb in call.sql.upper()
        for call in live.calls
        for verb in ("INSERT", "UPDATE", "DELETE", "MERGE", "ALTER")
    )
