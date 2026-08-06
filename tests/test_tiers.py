"""Tests for authority tier resolution.

These are the rules that decide whether an AI agent is allowed to act on real systems,
so they get exhaustive coverage. Nothing here touches Snowflake.
"""

import pytest

from warrant.authority.tiers import (
    UNTAGGED_SCRUTINY,
    Decision,
    Tier,
    TouchedObject,
    resolve,
)

OPEN = TouchedObject("DB.S.OPEN", "open")
INTERNAL = TouchedObject("DB.S.INT", "internal")
REGULATED = TouchedObject("DB.S.GXP", "regulated")
UNTAGGED = TouchedObject("DB.S.MYSTERY")


@pytest.mark.parametrize(
    ("sensitivity", "expected"),
    [
        ("open", Tier.LOW_RISK_ACT),
        ("internal", Tier.APPROVAL_REQUIRED),
        ("regulated", Tier.FORBIDDEN),
        (None, UNTAGGED_SCRUTINY),
        ("banana", UNTAGGED_SCRUTINY),
        ("REGULATED", Tier.FORBIDDEN),
        (" regulated ", Tier.FORBIDDEN),
        ("Regulated", Tier.FORBIDDEN),
        ("  Internal  ", Tier.APPROVAL_REQUIRED),
    ],
)
def test_required_scrutiny_maps_tags_case_and_whitespace_insensitively(sensitivity, expected):
    assert TouchedObject("DB.S.T", sensitivity).required_scrutiny() is expected


def test_untagged_is_not_treated_as_open():
    """The whole governance story fails if unclassified silently means cleared."""
    assert UNTAGGED.required_scrutiny() is not Tier.LOW_RISK_ACT


@pytest.mark.parametrize(
    ("requested", "touched", "expected"),
    [
        # Open data permits unsupervised action.
        (Tier.LOW_RISK_ACT, [OPEN], Tier.LOW_RISK_ACT),
        # Internal and untagged data force the action through approval.
        (Tier.LOW_RISK_ACT, [INTERNAL], Tier.APPROVAL_REQUIRED),
        (Tier.LOW_RISK_ACT, [UNTAGGED], Tier.APPROVAL_REQUIRED),
        # Regulated data refuses any action, whatever tier was asked for.
        (Tier.LOW_RISK_ACT, [REGULATED], Tier.FORBIDDEN),
        (Tier.APPROVAL_REQUIRED, [REGULATED], Tier.FORBIDDEN),
        # ...but it can still be read and drafted about. The detector has to be able to
        # surface an aging quality hold, and the agent to notify its owner, per RB-003.
        (Tier.READ_ONLY, [REGULATED], Tier.READ_ONLY),
        (Tier.DRAFT, [REGULATED], Tier.DRAFT),
        # Reading and drafting touch nothing, so tags do not constrain them.
        (Tier.READ_ONLY, [OPEN], Tier.READ_ONLY),
        (Tier.READ_ONLY, [INTERNAL], Tier.READ_ONLY),
        (Tier.READ_ONLY, [UNTAGGED], Tier.READ_ONLY),
        (Tier.DRAFT, [OPEN], Tier.DRAFT),
        # Authority is never promoted: open data must not turn a draft into an act.
        (Tier.DRAFT, [OPEN, OPEN], Tier.DRAFT),
        # An action that already asks for approval keeps it.
        (Tier.APPROVAL_REQUIRED, [OPEN], Tier.APPROVAL_REQUIRED),
    ],
)
def test_resolve_returns_the_expected_tier(requested, touched, expected):
    assert resolve(requested, touched).tier is expected


def test_most_demanding_object_binds():
    decision = resolve(Tier.LOW_RISK_ACT, [OPEN, INTERNAL, TouchedObject("DB.S.ALSO_OPEN", "open")])
    assert decision.tier is Tier.APPROVAL_REQUIRED
    assert decision.binding_object == "DB.S.INT"


def test_regulated_object_is_not_diluted_by_an_open_one():
    """The regression that made the whole authority model unsound.

    A single regulated object must refuse the action even when it is listed alongside
    open objects. Previously the least-sensitive object won and the action executed.
    """
    decision = resolve(Tier.LOW_RISK_ACT, [OPEN, REGULATED, TouchedObject("DB.S.X", "open")])
    assert decision.is_refused
    assert decision.binding_object == "DB.S.GXP"


def test_regulated_object_binds_regardless_of_position():
    assert resolve(Tier.LOW_RISK_ACT, [REGULATED, OPEN]).is_refused
    assert resolve(Tier.LOW_RISK_ACT, [OPEN, REGULATED]).is_refused


def test_untagged_object_is_not_diluted_by_an_open_one():
    decision = resolve(Tier.LOW_RISK_ACT, [OPEN, UNTAGGED])
    assert decision.tier is Tier.APPROVAL_REQUIRED
    assert decision.binding_object == "DB.S.MYSTERY"


def test_empty_touched_list_escalates_rather_than_permitting():
    decision = resolve(Tier.LOW_RISK_ACT, [])
    assert decision.tier is Tier.APPROVAL_REQUIRED
    assert decision.binding_object is None
    assert "cannot say what it touches" in decision.rationale


@pytest.mark.parametrize(
    ("requested", "touched", "must_contain"),
    [
        (Tier.LOW_RISK_ACT, [REGULATED], ["DB.S.GXP", "regulated"]),
        (Tier.LOW_RISK_ACT, [INTERNAL], ["DB.S.INT", "internal"]),
        (Tier.LOW_RISK_ACT, [UNTAGGED], ["DB.S.MYSTERY", "unclassified"]),
        (Tier.LOW_RISK_ACT, [TouchedObject("DB.S.ODD", "banana")], ["DB.S.ODD", "unclassified"]),
        (Tier.LOW_RISK_ACT, [OPEN], ["DB.S.OPEN", "open"]),
        (Tier.READ_ONLY, [INTERNAL], ["DB.S.INT", "does not act"]),
    ],
)
def test_every_decision_explains_itself(requested, touched, must_contain):
    """Rationales are written to the audit log verbatim, so they must name the cause."""
    rationale = resolve(requested, touched).rationale
    for fragment in must_contain:
        assert fragment in rationale


# Two predicates, not three: a `needs_approval` property also existed, used by nothing but
# this test — dead code wearing a coverage badge. The approval case is simply the tier where
# neither of the real predicates is true, which is what the executor and the loop actually
# branch on.
@pytest.mark.parametrize(
    ("tier", "auto", "refused"),
    [
        (Tier.READ_ONLY, True, False),
        (Tier.DRAFT, True, False),
        (Tier.LOW_RISK_ACT, True, False),
        (Tier.APPROVAL_REQUIRED, False, False),
        (Tier.FORBIDDEN, False, True),
    ],
)
def test_decision_predicates_are_mutually_consistent(tier, auto, refused):
    decision = Decision(tier=tier, binding_object=None, rationale="")
    assert decision.is_auto_executable is auto
    assert decision.is_refused is refused
