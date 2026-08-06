"""Tests for the capability manifest.

The manifest is the only place that answers "what is this agent allowed to do *at all*", so the
property worth protecting is that it agrees with the resolver the pipeline uses — not that it
produces a plausible-looking table. Every expectation below is stated in terms of the demo account's
real classifications.
"""

import pytest
from snowflake.snowpark import Row

from warrant.act.registry import ACTION_TYPES
from warrant.authority.manifest import (
    APPROVAL,
    AUTO,
    REFUSED,
    Capability,
    capabilities,
    compare,
    registry_objects,
)
from warrant.authority.tiers import Tier

from .conftest import DEMO_TAGS, FakeSession


def session(tags: dict | None = None) -> FakeSession:
    live = DEMO_TAGS if tags is None else tags
    return FakeSession(
        responses={"SYSTEM$GET_TAG": lambda p: [Row(SENSITIVITY=live.get(p[1]), RETENTION=None)]}
    )


def by_action(manifest: list[Capability]) -> dict[str, Capability]:
    return {c.action: c for c in manifest}


def test_the_manifest_covers_every_registered_action():
    """A manifest that silently omitted an action would understate what the agent can do."""
    manifest = capabilities(session())
    assert {c.action for c in manifest} == set(ACTION_TYPES)


def test_registry_objects_are_deduplicated():
    """One tag read per object, not one per action-object pair."""
    objects = registry_objects()
    assert objects == tuple(sorted(set(objects)))
    assert "WARRANT.DATA.OPS_REQUESTS" in objects, "shared by several actions"


def test_one_tag_read_per_object():
    live = session()
    capabilities(live)
    tag_reads = [c for c in live.calls if "SYSTEM$GET_TAG" in c.sql]
    assert len(tag_reads) == len(registry_objects())


@pytest.mark.parametrize(
    ("action", "tier", "outcome"),
    [
        ("open_supplier_case", Tier.LOW_RISK_ACT, AUTO),
        ("expedite_shipment", Tier.LOW_RISK_ACT, AUTO),
        ("raise_replenishment", Tier.APPROVAL_REQUIRED, APPROVAL),
        ("notify_quality_owner", Tier.DRAFT, AUTO),
        ("release_quality_hold", Tier.FORBIDDEN, REFUSED),
    ],
)
def test_the_manifest_matches_the_demo_accounts_real_posture(action, tier, outcome):
    """These are the five branches the whole submission rests on, enumerated in one call."""
    capability = by_action(capabilities(session()))[action]
    assert capability.effective_tier is tier
    assert capability.outcome == outcome


def test_the_most_restricted_capability_is_listed_first():
    """A reviewer should read what the agent may NOT do before what it may."""
    manifest = capabilities(session())
    assert manifest[0].effective_tier is Tier.FORBIDDEN
    assert [int(c.effective_tier) for c in manifest] == sorted(
        (int(c.effective_tier) for c in manifest), reverse=True
    )


def test_each_capability_reports_the_classifications_actually_used():
    """What a row says and what the resolver used must not be able to drift."""
    capability = by_action(capabilities(session()))["release_quality_hold"]
    assert capability.classifications == (("WARRANT.DATA.QUALITY_HOLDS", "regulated"),)
    assert capability.is_permitted is False


def test_an_untagged_object_is_labelled_untagged_not_blank():
    manifest = capabilities(session(tags={}))
    for capability in manifest:
        assert all(value == "untagged" for _, value in capability.classifications)
    # Untagged is not cleared: everything that acts needs approval.
    assert by_action(manifest)["open_supplier_case"].effective_tier is Tier.APPROVAL_REQUIRED


# ---------------------------------------------------------------------------
# The what-if. This is the part that makes the manifest a policy tool rather
# than a status page.
# ---------------------------------------------------------------------------


def test_an_override_changes_resolution_without_touching_anything():
    live = session()
    hypothetical = capabilities(live, overrides={"WARRANT.DATA.SHIPMENTS": "regulated"})
    assert by_action(hypothetical)["expedite_shipment"].effective_tier is Tier.FORBIDDEN
    assert not any(
        verb in call.sql.upper() for call in live.calls for verb in ("ALTER", "UPDATE", "INSERT")
    ), "a what-if must not write"


def test_an_override_of_none_models_removing_a_tag_not_clearing_it():
    """`None` and `'open'` are different hypotheses and both must be expressible."""
    manifest = by_action(capabilities(session(), overrides={"WARRANT.DATA.SHIPMENTS": None}))
    assert manifest["expedite_shipment"].effective_tier is Tier.APPROVAL_REQUIRED
    assert manifest["expedite_shipment"].classifications == (
        ("WARRANT.DATA.SHIPMENTS", "untagged"),
    )


def test_compare_reports_the_blast_radius_of_a_reclassification():
    before = capabilities(session())
    after = capabilities(session(), overrides={"WARRANT.DATA.SHIPMENTS": "regulated"})
    changes = compare(before, after)

    changed = {c.action for c in changes}
    assert changed == {"open_supplier_case", "expedite_shipment"}
    assert all(c.is_revocation for c in changes)
    assert changes[0].after.effective_tier is Tier.FORBIDDEN


def test_compare_reports_a_grant_as_a_change_but_not_a_revocation():
    before = capabilities(session())
    after = capabilities(session(), overrides={"WARRANT.DATA.INVENTORY": "open"})
    (change,) = compare(before, after)
    assert change.action == "raise_replenishment"
    assert change.is_revocation is False
    assert change.before.effective_tier is Tier.APPROVAL_REQUIRED
    assert change.after.effective_tier is Tier.LOW_RISK_ACT


def test_compare_is_empty_when_nothing_moved():
    manifest = capabilities(session())
    assert compare(manifest, manifest) == []


def test_compare_ignores_an_action_missing_from_the_other_manifest():
    """Inventing a diff for an action only one side knows about would overstate the change."""
    before = capabilities(session())
    after = [c for c in capabilities(session()) if c.action != "expedite_shipment"]
    assert all(c.action != "expedite_shipment" for c in compare(before, after))
