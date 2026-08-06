"""The second governance axis, and the claim it exists to settle.

The obvious objection to this project is that `SENSITIVITY` is hardcoded — that the authority
model is one tag name spelled into the resolver, dressed up as governance. These tests answer it.

`RETENTION` is a genuinely independent axis. Its values map to tiers through the same
:class:`~warrant.authority.tiers.TagPolicy` mechanism, it is read in the same statement, and it
binds through the same ``max()``. Adding a third — residency, contractual restriction, whatever
the organisation already tags — is a row in ``POLICIES`` and a field on ``TouchedObject``.

The case worth reading is `test_an_open_table_can_still_be_forbidden`: an object classified
`open`, which the sensitivity axis would wave through, refused because a different tag says so.
"""

from snowflake.snowpark import Row

from warrant.authority.tags import read_sensitivity
from warrant.authority.tiers import POLICIES, Tier, TouchedObject, resolve

from .conftest import FakeSession


def held(**tags: str | None) -> TouchedObject:
    return TouchedObject(fqn="WARRANT.DATA.OPS_REQUESTS", **tags)


def test_an_open_table_can_still_be_forbidden():
    """The whole point of a second axis.

    `OPS_REQUESTS` is tagged `open`, which on its own permits unsupervised action. Put it
    under legal hold and acting on it becomes forbidden — with nothing about its sensitivity
    changed. If authority were one hardcoded tag, this could not happen.
    """
    ordinary = held(sensitivity="open")
    assert ordinary.required_scrutiny() is Tier.LOW_RISK_ACT

    under_hold = held(sensitivity="open", retention="legal_hold")
    assert under_hold.required_scrutiny() is Tier.FORBIDDEN

    decision = resolve(Tier.LOW_RISK_ACT, [under_hold])
    assert decision.is_refused
    assert "retention='legal_hold'" in decision.rationale


def test_the_rationale_names_whichever_tag_actually_bound():
    """An audit line that blamed sensitivity for a retention decision would be a lie.

    Not a cosmetic concern: the rationale is what a reviewer reads to decide what to change,
    and pointing them at the wrong tag sends them to change the wrong thing.
    """
    by_retention = resolve(Tier.LOW_RISK_ACT, [held(sensitivity="open", retention="legal_hold")])
    assert "retention" in by_retention.rationale
    assert "sensitivity" not in by_retention.rationale

    by_sensitivity = resolve(
        Tier.LOW_RISK_ACT,
        [TouchedObject(fqn="WARRANT.DATA.QUALITY_HOLDS", sensitivity="regulated")],
    )
    assert "sensitivity='regulated'" in by_sensitivity.rationale


def test_an_absent_retention_tag_demands_nothing():
    """The deliberate asymmetry with sensitivity.

    An absent *sensitivity* tag demands approval, because everything has some sensitivity and
    not knowing it is itself the risk. An absent *retention* tag demands nothing, because a
    legal hold is an affirmative state somebody puts on a record — treating every untagged
    object as held would freeze the entire estate on day one.
    """
    assert held(sensitivity="open", retention=None).required_scrutiny() is Tier.LOW_RISK_ACT
    assert held(sensitivity=None).required_scrutiny() is Tier.APPROVAL_REQUIRED


def test_normal_retention_is_recognised_and_permits():
    """`normal` is a real value, not merely the absence of `legal_hold`."""
    assert held(sensitivity="open", retention="normal").required_scrutiny() is Tier.LOW_RISK_ACT


def test_an_unrecognised_retention_value_does_not_silently_permit():
    """A typo in a tag value must not read as 'no restriction'.

    It falls back to the policy's `absent` tier rather than raising — a governance path that
    throws on bad input stops the loop, and stopping the loop is a worse failure than being
    conservative about one object.
    """
    assert held(sensitivity="open", retention="lgeal_hold").required_scrutiny() is Tier.LOW_RISK_ACT
    described = held(sensitivity="open", retention="lgeal_hold").describe_tag()
    assert "sensitivity='open'" in described


def test_a_hold_still_does_not_constrain_a_read_or_a_draft():
    """Reads stay exempt on every axis, not just on sensitivity.

    The agent must be able to surface and explain a record under legal hold. What it may not do
    is alter one.
    """
    decision = resolve(Tier.DRAFT, [held(sensitivity="open", retention="legal_hold")])
    assert decision.tier is Tier.DRAFT
    assert not decision.is_refused


def test_the_most_demanding_axis_across_the_most_demanding_object_binds():
    """Two objects, two different axes, one answer.

    Neither object is forbidden by the axis the other is bound by, and the resolution still
    lands on FORBIDDEN — the maximum is taken across every object *and* every tag.
    """
    footprint = [
        TouchedObject(fqn="WARRANT.DATA.SHIPMENTS", sensitivity="open"),
        TouchedObject(fqn="WARRANT.DATA.OPS_REQUESTS", sensitivity="open", retention="legal_hold"),
    ]
    decision = resolve(Tier.LOW_RISK_ACT, footprint)
    assert decision.is_refused
    assert decision.binding_object == "WARRANT.DATA.OPS_REQUESTS"


def test_both_tags_are_read_in_one_statement():
    """Two sequential reads could straddle a governance change.

    Reading both in one statement means the pair is observed at a single instant, so a
    resolution can never combine a sensitivity from before a change with a retention from
    after — a state that was never true of the object.
    """
    session = FakeSession(
        responses={
            "SYSTEM$GET_TAG": lambda p: [Row(SENSITIVITY="open", RETENTION="legal_hold")],
        }
    )
    [touched] = read_sensitivity(session, ["WARRANT.DATA.OPS_REQUESTS"])

    assert touched.sensitivity == "open"
    assert touched.retention == "legal_hold"
    assert len(session.calls) == 1, "one object should cost one round trip, not one per tag"


def test_every_policy_is_fully_qualified_and_distinct():
    """A bare tag name raises 'does not exist or not authorized' at runtime.

    The tags live in `CORE` while the tables live in `DATA`. Cheap to assert here; expensive to
    discover from a Snowflake error in the middle of a loop.
    """
    names = [policy.tag for policy in POLICIES]
    assert len(names) == len(set(names))
    for policy in POLICIES:
        assert policy.tag.count(".") == 2, f"{policy.tag} is not fully qualified"
        assert policy.attribute in TouchedObject.__dataclass_fields__
