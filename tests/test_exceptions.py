"""Tests for detection.

The properties worth asserting are governance properties: that every threshold is traceable
to a runbook, that re-running cannot duplicate an open exception, and that nothing which
varies per call is ever interpolated into SQL text.
"""

import json

import pytest
from snowflake.snowpark import Row

from warrant.detect.exceptions import DETECTORS, OPEN_EXCEPTIONS, detect

from .conftest import FakeSession

EXCEPTION_ROW = Row(
    EXCEPTION_ID="EXC-0001",
    METRIC="supplier_otd_rate",
    ENTITY="SUP-002",
    OBSERVED="40.5% on-time over the last 14 days (42 deliveries)",
    EXPECTED="90.8% on-time baseline (358 deliveries)",
    DEVIATION="-50.3pp below baseline, robust z-score -3.63",
    DETECTION_METHOD="rb001_threshold_with_robust_z_corroboration",
    SOURCE_OBJECTS=["WARRANT.DATA.SHIPMENTS", "WARRANT.DATA.SUPPLIERS"],
)


@pytest.fixture
def detecting_session() -> FakeSession:
    """A session where the MERGEs are no-ops and the read-back returns one exception."""
    return FakeSession(responses={"ORDER BY metric, entity": [EXCEPTION_ROW]})


@pytest.mark.parametrize("detector", DETECTORS, ids=lambda d: d.metric)
def test_every_detector_is_self_consistent(detector):
    assert detector.sql.count("?") == 2, "binds exactly detection method and source objects"
    assert detector.source_objects, "an exception must say what it was derived from"
    assert detector.runbook.startswith("RB-"), "thresholds must cite a runbook clause"
    assert detector.metric in detector.sql, "the finder must label its own metric"


@pytest.mark.parametrize("detector", DETECTORS, ids=lambda d: d.metric)
def test_every_detector_merges_rather_than_inserts(detector):
    """RB-005: one open exception per (metric, entity). A blind INSERT would breach it."""
    assert detector.sql.lstrip().startswith("MERGE INTO")
    assert "t.metric = s.metric AND t.entity = s.entity AND t.state = 'open'" in detector.sql


def test_metrics_are_distinct():
    """Two detectors sharing a metric would collide on the MERGE predicate."""
    metrics = [d.metric for d in DETECTORS]
    assert len(metrics) == len(set(metrics))


def test_detect_runs_every_detector_then_reads_the_open_set(detecting_session):
    detect(detecting_session)
    statements = [c.sql for c in detecting_session.calls]
    assert len(statements) == len(DETECTORS) + 1
    assert statements[-1] == OPEN_EXCEPTIONS
    assert all(s.lstrip().startswith("MERGE INTO") for s in statements[:-1])


def test_detect_binds_the_method_and_footprint_of_each_detector(detecting_session):
    detect(detecting_session)
    for detector, call in zip(DETECTORS, detecting_session.calls, strict=False):
        assert call.params == (
            detector.detection_method,
            json.dumps(list(detector.source_objects)),
        )
        assert detector.detection_method not in call.sql, "bound, not interpolated"


def test_detect_returns_parsed_records(detecting_session):
    (record,) = detect(detecting_session)
    assert record.exception_id == "EXC-0001"
    assert record.entity == "SUP-002"
    assert record.source_objects == (
        "WARRANT.DATA.SHIPMENTS",
        "WARRANT.DATA.SUPPLIERS",
    )


def test_detect_returns_the_whole_open_set_not_just_new_rows():
    """Returning a delta would make a re-run skip work it had not finished."""
    session = FakeSession(responses={"ORDER BY metric, entity": [EXCEPTION_ROW, EXCEPTION_ROW]})
    assert len(detect(session)) == 2


def test_detect_is_safe_with_nothing_to_report():
    """The common case: the loop runs on a schedule and usually finds nothing."""
    session = FakeSession()
    assert detect(session) == []
    assert len(session.calls) == len(DETECTORS) + 1
