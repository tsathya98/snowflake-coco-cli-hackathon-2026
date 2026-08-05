"""Tests for the reasoning step.

The model is the one component here that cannot be made deterministic, so these tests cover
the boundary around it: what happens when it errors, when it returns nothing, and when it
returns something well-formed but wrong.
"""

import json

import pytest
from snowflake.snowpark import Row

from warrant.authority.tiers import Tier
from warrant.common.models import ExceptionRecord, Finding, Refusal
from warrant.reason.investigate import (
    ACTION_CATALOGUE,
    MODEL,
    investigate,
    retrieve_grounding,
    validate_proposal,
)

from .conftest import FakeSession

EXCEPTION = ExceptionRecord(
    exception_id="EXC-0001",
    metric="supplier_otd_rate",
    entity="SUP-002",
    observed="40.5% on-time over the last 14 days",
    expected="90.8% on-time baseline",
    deviation="-50.3pp below baseline, robust z-score -3.63",
    detection_method="rb001_threshold_with_robust_z_corroboration",
    source_objects=("WARRANT.DATA.SHIPMENTS", "WARRANT.DATA.SUPPLIERS"),
)

GOOD_PAYLOAD = {
    "severity": "high",
    "root_cause": "Sustained delivery failure at SUP-002.",
    "evidence": ["40.5% versus a 90.8% baseline", "robust z-score -3.63"],
    "recommended_action": "Open a supplier performance case.",
    "action_type": "open_supplier_case",
    "action_params": {"supplier_id": "SUP-002", "justification": "50.3pp below baseline"},
}

RUNBOOK_ROWS = [
    Row(DOC_ID="RB-001", TITLE="Supplier on-time delivery degradation", BODY="…20 points…"),
    Row(DOC_ID="RB-004", TITLE="Expedite authorisation thresholds", BODY="…2000 units…"),
]


def envelope(value=None, error=None) -> FakeSession:
    """A session whose search returns runbooks and whose model returns ``value``."""
    return FakeSession(
        responses={
            "SEARCH_PREVIEW": RUNBOOK_ROWS,
            "AI_COMPLETE": [Row(REPLY=json.dumps({"value": value, "error": error}))],
        }
    )


def test_grounding_binds_its_payload_and_returns_citable_ids():
    session = envelope()
    doc_ids, text = retrieve_grounding(session, EXCEPTION)
    assert doc_ids == ("RB-001", "RB-004")
    assert "RB-001" in text and "20 points" in text
    (call,) = session.calls
    assert json.loads(call.params[0])["query"].startswith("supplier_otd_rate SUP-002")
    assert "SUP-002" not in call.sql, "the query text is bound, never interpolated"


def test_a_valid_proposal_becomes_a_finding():
    finding = validate_proposal(EXCEPTION, GOOD_PAYLOAD, ("RB-001",))
    assert isinstance(finding, Finding)
    assert finding.action_type == "open_supplier_case"
    assert finding.grounded_in == ("RB-001",)
    assert finding.model == MODEL
    assert finding.finding_id.startswith("FND-")


def test_authority_is_taken_from_the_registry_not_the_model():
    """The model chooses what to do; the registry declares what that costs."""
    hostile = {**GOOD_PAYLOAD, "requested_tier": 0, "touched_objects": []}
    finding = validate_proposal(EXCEPTION, hostile, ())
    assert finding.requested_tier is Tier.LOW_RISK_ACT
    assert finding.touched_objects == (
        "WARRANT.DATA.SHIPMENTS",
        "WARRANT.DATA.SUPPLIERS",
        "WARRANT.DATA.OPS_REQUESTS",
    )


@pytest.mark.parametrize(
    ("mutation", "because"),
    [
        ({"action_type": "drop_everything"}, "an action outside the registry"),
        ({"action_params": {"supplier_id": "SUP-002"}}, "a missing required parameter"),
        (
            {"action_params": {**GOOD_PAYLOAD["action_params"], "extra": 1}},
            "a parameter the action does not take",
        ),
        ({"action_params": {}}, "no parameters at all"),
    ],
)
def test_a_proposal_the_registry_rejects_becomes_a_refusal(mutation, because):
    """Schema conformance gates shape; the registry gates the contract."""
    refusal = validate_proposal(EXCEPTION, {**GOOD_PAYLOAD, **mutation}, ())
    assert isinstance(refusal, Refusal), because
    assert refusal.outcome == "malformed_proposal"


def test_a_proposal_aimed_at_the_wrong_entity_is_refused():
    """The schema pins the action name but not its subject.

    This one would execute flawlessly and be entirely wrong: a well-formed case opened
    against a supplier that was never flagged.
    """
    wrong = {
        **GOOD_PAYLOAD,
        "action_params": {"supplier_id": "SUP-999", "justification": "…"},
    }
    refusal = validate_proposal(EXCEPTION, wrong, ())
    assert isinstance(refusal, Refusal)
    assert "SUP-002" in refusal.reason


def test_a_model_error_is_a_refusal_not_an_exception():
    """One bad exception must not abandon the others in the same loop."""
    result = investigate(envelope(error="budget exceeded"), EXCEPTION)
    assert isinstance(result, Refusal)
    assert result.outcome == "model_error"
    assert "budget exceeded" in result.reason


@pytest.mark.parametrize("value", [None, {}])
def test_an_empty_reply_is_a_refusal(value):
    result = investigate(envelope(value=value), EXCEPTION)
    assert isinstance(result, Refusal)
    assert result.outcome == "model_error"


def test_investigate_binds_model_prompt_and_schema():
    session = envelope(value=GOOD_PAYLOAD)
    assert isinstance(investigate(session, EXCEPTION), Finding)
    reasoning = next(c for c in session.calls if "AI_COMPLETE" in c.sql)
    model, prompt, schema = reasoning.params
    assert model == MODEL
    assert "SUP-002" in prompt and "SUP-002" not in reasoning.sql
    assert json.loads(schema)["schema"]["properties"]["action_type"]["enum"]


def test_the_prompt_shows_the_model_every_action_and_its_parameters():
    """A model that cannot see the parameter contract cannot satisfy it."""
    session = envelope(value=GOOD_PAYLOAD)
    investigate(session, EXCEPTION)
    prompt = next(c for c in session.calls if "AI_COMPLETE" in c.sql).params[1]
    assert ACTION_CATALOGUE in prompt
    assert "open_supplier_case(supplier_id, justification)" in prompt


def test_no_grounding_is_recorded_honestly_rather_than_hidden():
    session = FakeSession(
        responses={"AI_COMPLETE": [Row(REPLY=json.dumps({"value": GOOD_PAYLOAD, "error": None}))]}
    )
    finding = investigate(session, EXCEPTION)
    assert isinstance(finding, Finding)
    assert finding.grounded_in == ()
    prompt = next(c for c in session.calls if "AI_COMPLETE" in c.sql).params[1]
    assert "No procedure was retrieved" in prompt


def test_a_missing_reply_row_does_not_raise():
    session = FakeSession(responses={"SEARCH_PREVIEW": RUNBOOK_ROWS})
    result = investigate(session, EXCEPTION)
    assert isinstance(result, Refusal)
    assert result.outcome == "model_error"
