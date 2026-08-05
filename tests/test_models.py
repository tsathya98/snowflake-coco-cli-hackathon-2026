"""Tests for the shared pipeline types.

These types are the contract between the SQL tables and the Python that fills them, so
the column names below are deliberately spelled out rather than generated.
"""

import pytest

from warrant.authority.tiers import Tier
from warrant.common.models import (
    REFUSAL_OUTCOMES,
    SEVERITIES,
    ExceptionRecord,
    Finding,
    Refusal,
    finding_response_format,
)

FINDING_FIELDS = {
    "finding_id": "FND-0001",
    "exception_id": "EXC-0001",
    "root_cause": "Supplier capacity shortfall.",
    "evidence": ("on-time rate 40.5% over 14 days",),
    "recommended_action": "Open a supplier performance case.",
    "action_type": "open_supplier_case",
    "action_params": {"supplier_id": "SUP-002", "justification": "sustained miss"},
    "requested_tier": Tier.LOW_RISK_ACT,
    "touched_objects": ("WARRANT.DATA.SHIPMENTS",),
}

EXCEPTION_ROW = {
    "EXCEPTION_ID": "EXC-0001",
    "METRIC": "supplier_otd_rate",
    "ENTITY": "SUP-002",
    "OBSERVED": "35.0%",
    "EXPECTED": "92.0%",
    "DEVIATION": "-57.0pp",
    "DETECTION_METHOD": "rolling_baseline_z_score",
    "SOURCE_OBJECTS": ["WARRANT.DATA.SHIPMENTS", "WARRANT.DATA.SUPPLIERS"],
}


def test_exception_record_maps_every_column_from_a_snowpark_row():
    record = ExceptionRecord.from_row(EXCEPTION_ROW)
    assert record.exception_id == "EXC-0001"
    assert record.metric == "supplier_otd_rate"
    assert record.entity == "SUP-002"
    assert record.observed == "35.0%"
    assert record.expected == "92.0%"
    assert record.deviation == "-57.0pp"
    assert record.detection_method == "rolling_baseline_z_score"
    assert record.source_objects == (
        "WARRANT.DATA.SHIPMENTS",
        "WARRANT.DATA.SUPPLIERS",
    )


def test_exception_record_tolerates_a_null_source_objects_array():
    """Snowflake returns NULL, not an empty array, when the column was never set."""
    record = ExceptionRecord.from_row({**EXCEPTION_ROW, "SOURCE_OBJECTS": None})
    assert record.source_objects == ()


def test_prompt_context_carries_the_facts_the_model_needs():
    context = ExceptionRecord.from_row(EXCEPTION_ROW).as_prompt_context()
    for fragment in ("SUP-002", "35.0%", "92.0%", "-57.0pp", "WARRANT.DATA.SHIPMENTS"):
        assert fragment in context


@pytest.mark.parametrize("severity", SEVERITIES)
def test_finding_accepts_every_severity_the_table_allows(severity):
    finding = Finding(severity=severity, **FINDING_FIELDS)
    assert finding.severity == severity
    assert finding.grounded_in == ()


@pytest.mark.parametrize("severity", ["", "SEVERE", "high ", "urgent", "medium-high"])
def test_finding_rejects_a_severity_the_table_would_refuse(severity):
    """A schema-constrained model is still a model; the boundary is checked."""
    with pytest.raises(ValueError, match="is not one of"):
        Finding(severity=severity, **FINDING_FIELDS)


def test_finding_rejects_an_empty_footprint():
    """An undeclared footprint must not masquerade as a policy decision to escalate."""
    with pytest.raises(ValueError, match="declares no touched objects"):
        Finding(severity="high", **{**FINDING_FIELDS, "touched_objects": ()})


@pytest.mark.parametrize("outcome", REFUSAL_OUTCOMES)
def test_refusal_accepts_every_outcome_in_the_vocabulary(outcome):
    refusal = Refusal(exception_id="EXC-0003", outcome=outcome, reason="regulated object")
    assert refusal.outcome == outcome
    assert refusal.binding_object is None


@pytest.mark.parametrize("outcome", ["", "refused", "ERROR", "blocked"])
def test_refusal_rejects_an_outcome_outside_the_vocabulary(outcome):
    """A refusal carries a structured code end to end, never free text."""
    with pytest.raises(ValueError, match="is not one of"):
        Refusal(exception_id="EXC-0003", outcome=outcome, reason="x")


def test_response_format_pins_the_model_to_the_implemented_actions():
    schema = finding_response_format(["expedite_shipment", "raise_replenishment"])
    assert schema["type"] == "json"
    properties = schema["schema"]["properties"]
    assert properties["action_type"]["enum"] == [
        "expedite_shipment",
        "raise_replenishment",
    ]
    assert properties["severity"]["enum"] == list(SEVERITIES)
    assert set(schema["schema"]["required"]) == set(properties)
