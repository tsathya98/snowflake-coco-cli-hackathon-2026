"""Tests for the decision log.

The audit table is append-only and is where the impact figures come from, so a row written
with a phase no view selects is the same as a row lost.
"""

import pytest

from warrant.authority.tiers import Tier
from warrant.common.audit import PHASES, record

from .conftest import FakeSession, bound


@pytest.mark.parametrize("phase", PHASES)
def test_every_declared_phase_is_accepted(phase):
    session = FakeSession()
    audit_id = record(session, phase=phase, outcome="ok", rationale="because")
    assert audit_id.startswith("AUD-")
    (call,) = session.calls
    assert bound(call)["phase"] == phase


@pytest.mark.parametrize("phase", ["", "REFUSE", "refused", "executed", "audit"])
def test_an_undeclared_phase_is_rejected(phase):
    """A typo would produce a row the console never shows, which is worse than an error."""
    with pytest.raises(ValueError, match="is not one of"):
        record(FakeSession(), phase=phase, outcome="ok", rationale="because")


def test_the_row_is_appended_never_updated():
    session = FakeSession()
    record(session, phase="execute", outcome="executed", rationale="done")
    (call,) = session.calls
    assert call.sql.lstrip().startswith("INSERT INTO WARRANT.AUDIT.ACTION_AUDIT")
    assert "UPDATE" not in call.sql and "DELETE" not in call.sql


def test_every_field_is_bound_and_the_payload_is_json():
    session = FakeSession()
    record(
        session,
        phase="refuse",
        outcome="refused",
        rationale="regulated",
        actor="tsathya98",
        exception_id="EXC-1",
        finding_id="FND-1",
        action_id="ACT-1",
        tier=Tier.FORBIDDEN,
        payload={"touched": {"WARRANT.DATA.QUALITY_HOLDS": "regulated"}},
    )
    (call,) = session.calls
    row = bound(call)
    assert row["phase"] == "refuse"
    assert row["exception_id"] == "EXC-1"
    assert row["finding_id"] == "FND-1"
    assert row["action_id"] == "ACT-1"
    assert row["actor"] == "tsathya98"
    assert row["outcome"] == "refused"
    assert row["tier"] == 4, "the tier is stored as its numeric value, not its name"
    assert row["payload"] == {"touched": {"WARRANT.DATA.QUALITY_HOLDS": "regulated"}}
    assert row["rationale"] == "regulated"
    assert "regulated" not in call.sql, "values are bound, never interpolated"
    assert "EXC-1" not in call.sql and "tsathya98" not in call.sql


def test_omitted_optional_fields_bind_as_null():
    session = FakeSession()
    record(session, phase="detect", outcome="scanned", rationale="0 exceptions")
    (call,) = session.calls
    row = bound(call)
    assert (row["exception_id"], row["finding_id"], row["action_id"]) == (None, None, None)
    assert row["tier"] is None, "no tier means no tier, not zero"
    assert row["payload"] == {}
    assert '"None"' not in call.params[0], "a null must be JSON null, never the text 'None'"
