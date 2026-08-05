"""Tests for the live sensitivity tag read.

Two properties here are not stylistic. The tag name must be bound rather than interpolated,
and the read must not be cached — the demo's central claim is that retagging an object
changes the agent's behaviour on the very next iteration.
"""

import pytest
from snowflake.snowpark import Row, Session

from warrant.authority.tags import SENSITIVITY_TAG, read_sensitivity
from warrant.authority.tiers import Tier

from .conftest import DEMO_TAGS, FakeSession


@pytest.mark.parametrize(("fqn", "expected"), sorted(DEMO_TAGS.items()))
def test_reads_the_classification_the_account_actually_carries(tagged_session, fqn, expected):
    touched = read_sensitivity(tagged_session, [fqn])
    assert len(touched) == 1
    assert touched[0].fqn == fqn
    assert touched[0].sensitivity == expected


def test_an_untagged_object_is_unclassified_not_cleared(tagged_session):
    """RUNBOOKS carries no tag. Absence must not read as permission."""
    (runbooks,) = read_sensitivity(tagged_session, ["WARRANT.DATA.RUNBOOKS"])
    assert runbooks.sensitivity is None
    assert runbooks.required_scrutiny() is Tier.APPROVAL_REQUIRED


def test_object_names_are_bound_never_interpolated(tagged_session):
    """The lint in tools/ bans interpolated SQL; this proves the intent, not just the form."""
    read_sensitivity(tagged_session, ["WARRANT.DATA.SHIPMENTS"])
    (call,) = tagged_session.calls
    assert call.params == (SENSITIVITY_TAG, "WARRANT.DATA.SHIPMENTS")
    assert "WARRANT.DATA.SHIPMENTS" not in call.sql
    assert SENSITIVITY_TAG not in call.sql


def test_the_tag_is_fully_qualified():
    """A bare tag name raises 'Tag SENSITIVITY does not exist' — the tag lives in CORE."""
    assert SENSITIVITY_TAG == "WARRANT.CORE.SENSITIVITY"


def test_every_call_re_reads_the_tag(tagged_session):
    """Caching between calls would silently defeat the retag demo."""
    read_sensitivity(tagged_session, ["WARRANT.DATA.SHIPMENTS"])
    read_sensitivity(tagged_session, ["WARRANT.DATA.SHIPMENTS"])
    assert len(tagged_session.calls) == 2


def test_a_repeated_object_within_one_call_is_read_once(tagged_session):
    """Deduplicating inside a single call is fine; remembering between calls is not."""
    touched = read_sensitivity(
        tagged_session,
        ["WARRANT.DATA.SHIPMENTS", "WARRANT.DATA.SUPPLIERS", "WARRANT.DATA.SHIPMENTS"],
    )
    assert [o.fqn for o in touched] == [
        "WARRANT.DATA.SHIPMENTS",
        "WARRANT.DATA.SUPPLIERS",
    ], "input order is preserved"
    assert len(tagged_session.calls) == 2


def test_a_retag_between_calls_changes_the_answer():
    """The flagship demo, in miniature: ALTER TABLE ... SET TAG, then re-run."""
    live = {"WARRANT.DATA.SHIPMENTS": "open"}
    session = FakeSession(
        responses={"SYSTEM$GET_TAG": lambda params: [Row(SENSITIVITY=live.get(params[1]))]}
    )

    (before,) = read_sensitivity(session, ["WARRANT.DATA.SHIPMENTS"])
    assert before.required_scrutiny() is Tier.LOW_RISK_ACT

    live["WARRANT.DATA.SHIPMENTS"] = "regulated"

    (after,) = read_sensitivity(session, ["WARRANT.DATA.SHIPMENTS"])
    assert after.required_scrutiny() is Tier.FORBIDDEN


def test_a_query_returning_no_rows_is_treated_as_untagged():
    """Defensive: SYSTEM$GET_TAG always returns a row, but a NULL result must not crash."""
    session = FakeSession()
    (touched,) = read_sensitivity(session, ["WARRANT.DATA.SHIPMENTS"])
    assert touched.sensitivity is None


def test_no_objects_means_no_queries(tagged_session):
    assert read_sensitivity(tagged_session, []) == []
    assert tagged_session.calls == []


@pytest.mark.integration
def test_against_the_live_account():
    """Proves the fake and the account agree.

    Excluded from the default run (``addopts = -m 'not integration'``) because it needs a
    warehouse. Run with ``uv run pytest -m integration``. This is the test that catches a
    tag drifting between ``sql/10_synthetic_data.sql`` and the live account, and the one
    that would have caught ``SYSTEM$GET_TAG`` rejecting a qualified object name.
    """
    session = Session.builder.config("connection_name", "warrant").create()
    try:
        session.sql("USE ROLE WARRANT_ROLE").collect()
        session.sql("USE WAREHOUSE WARRANT_WH").collect()
        live = {o.fqn: o.sensitivity for o in read_sensitivity(session, sorted(DEMO_TAGS))}
    finally:
        session.close()

    assert live == DEMO_TAGS
