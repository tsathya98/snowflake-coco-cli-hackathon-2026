"""Tests for the action registry.

The registry is the boundary between model output and executed SQL, so its validation is
security-relevant, not merely defensive.
"""

import re

import pytest

from warrant.act.registry import (
    ACTION_TYPES,
    ActionValidationError,
    get_action_type,
)
from warrant.authority.tiers import Tier

BOUND_COLUMN = re.compile(r"(\w+)\s*=\s*\?")
"""Matches the ``column = ?`` shape, which is self-describing about its binding."""

QUALIFIED_TABLE = re.compile(r"\bWARRANT\.[A-Z_]+\.[A-Z_]+\b")
"""Matches a fully-qualified object name appearing in a statement."""


@pytest.mark.parametrize("name", sorted(ACTION_TYPES))
def test_no_action_touches_an_object_it_did_not_declare(name):
    """The invariant the whole governance model rests on.

    ``notify_quality_owner`` once declared only ``QUALITY_HOLDS`` while writing its
    notification into ``OPS_REQUESTS``. Nothing failed — the action ran correctly and the
    audit trail recorded a footprint that was missing a table. An action that under-declares
    what it touches under-declares its own risk, and authority is resolved from exactly that
    declaration.
    """
    action = ACTION_TYPES[name]
    statements = [action.sql, action.rollback_sql or ""]
    referenced = {t for s in statements for t in QUALIFIED_TABLE.findall(s)}
    undeclared = referenced - set(action.touched_objects)
    assert not undeclared, f"{name} touches undeclared objects: {sorted(undeclared)}"


@pytest.mark.parametrize("name", sorted(ACTION_TYPES))
def test_every_registered_action_is_self_consistent(name):
    """A registry entry that lies about itself would corrupt tier resolution."""
    action = ACTION_TYPES[name]
    assert action.name == name, "registry key must match the action's own name"
    assert action.touched_objects, "an action must declare what it touches"
    assert action.description.strip(), "actions are shown to human approvers"
    assert action.sql.count("?") == len(action.parameters), (
        "every parameter must have exactly one placeholder, or binding silently misaligns"
    )
    if action.rollback_sql is None:
        assert not action.rollback_parameters, "no rollback statement, so no rollback parameters"
    else:
        assert action.rollback_sql.count("?") == len(action.rollback_parameters)
        assert set(action.rollback_parameters) <= set(action.parameters), (
            "a rollback binds a subset of the action's own parameters"
        )


@pytest.mark.parametrize("name", sorted(ACTION_TYPES))
def test_parameters_are_declared_in_placeholder_order(name):
    """Counting placeholders is not enough.

    ``release_quality_hold`` once declared ``("hold_id", "disposition")`` against
    ``SET disposition = ? WHERE hold_id = ?``. The count matched, so the previous
    invariant passed, and every execution silently wrote the hold id into the disposition
    column. Where a statement names the column each placeholder fills, assert the order.
    """
    action = ACTION_TYPES[name]
    bound = BOUND_COLUMN.findall(action.sql)
    if len(bound) != action.sql.count("?"):
        pytest.skip(f"{name} binds positionally in a SELECT list, so order is not inferable")
    assert bound == list(action.parameters)


@pytest.mark.parametrize("name", sorted(ACTION_TYPES))
def test_no_action_interpolates_model_output_into_sql(name):
    """The model must never be able to contribute SQL text, only bound values."""
    action = ACTION_TYPES[name]
    for forbidden in ("{", "}", "%s", "' ||", "|| '"):
        assert forbidden not in action.sql


def test_get_action_type_returns_the_registered_action():
    assert get_action_type("expedite_shipment") is ACTION_TYPES["expedite_shipment"]


def test_get_action_type_rejects_an_unregistered_name():
    with pytest.raises(ActionValidationError, match="unknown action type"):
        get_action_type("drop_everything")


def test_bind_orders_values_to_match_placeholders():
    action = get_action_type("raise_replenishment")
    sql, values = action.bind(
        {"sku": "SKU-1003", "quantity": 250000, "justification": "4.9 days of cover"}
    )
    assert sql == action.sql
    assert values == ["SKU-1003", 250000, "4.9 days of cover"]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"shipment_id": "SHP-000001"}, None),
        ({}, "missing shipment_id"),
        ({"shipment_id": "SHP-1", "priority": "high"}, "unexpected priority"),
        ({"priority": "high"}, "missing shipment_id"),
    ],
)
def test_bind_validates_the_parameter_contract(params, expected):
    action = get_action_type("expedite_shipment")
    if expected is None:
        assert action.bind(params)[1] == ["SHP-000001"]
        return
    with pytest.raises(ActionValidationError, match=expected):
        action.bind(params)


@pytest.mark.parametrize(
    ("name", "expected_tier"),
    [
        ("open_supplier_case", Tier.LOW_RISK_ACT),
        ("expedite_shipment", Tier.LOW_RISK_ACT),
        ("raise_replenishment", Tier.LOW_RISK_ACT),
        ("notify_quality_owner", Tier.DRAFT),
        ("release_quality_hold", Tier.LOW_RISK_ACT),
    ],
)
def test_requested_tiers_are_as_designed(name, expected_tier):
    """These tiers drive the demo's three branches; a change here changes the story."""
    assert ACTION_TYPES[name].requested_tier is expected_tier


def test_reversible_actions_declare_a_rollback():
    """RB-004 requires a stated undo path for anything executed unsupervised."""
    for name in ("open_supplier_case", "expedite_shipment", "raise_replenishment"):
        assert ACTION_TYPES[name].rollback_sql, f"{name} executes and must be reversible"


def test_rollback_binds_a_subset_of_the_action_parameters():
    """The executor holds one parameter mapping and uses it for both directions."""
    action = get_action_type("raise_replenishment")
    params = {"sku": "SKU-1003", "quantity": 250000, "justification": "5.0 days of cover"}
    sql, values = action.bind(params, rollback=True)
    assert sql == action.rollback_sql
    assert values == ["SKU-1003"], "surplus keys are permitted on the rollback path"


def test_rollback_is_refused_for_an_action_that_declares_none():
    action = get_action_type("release_quality_hold")
    with pytest.raises(ActionValidationError, match="declares no rollback"):
        action.bind({"disposition": "released", "hold_id": "QH-0034"}, rollback=True)
