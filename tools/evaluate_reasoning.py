#!/usr/bin/env python3
"""Score the reasoning step against a fixed set of exceptions, and gate on the result.

Why this exists as a separate thing from the test suite. The unit tests pin the *boundary* around
the model: given a reply, the right thing happens. They say nothing about whether the model
chooses well, because a test that asserted that would be asserting against a component that can
change under you without a commit. This measures that, and records the measurement.

Two modes, because the honest split is not the convenient one:

``--live``
    Calls the real pipeline against a Snowflake account — retrieval, ``AI_COMPLETE``, proposal
    validation, tier resolution — for every case in ``eval/cases.json``, then writes
    ``eval/scorecard.json``. This is the only mode that measures anything.

``--check``
    What CI runs. There is no account in CI, so it cannot re-measure; instead it verifies the
    committed scorecard still covers every case and still meets the thresholds. Adding a case
    without re-running the eval fails the build, which is the failure mode worth catching: a
    scorecard that silently describes a smaller problem than the one being solved.

The gate is deliberately not 100% on every dimension. ``grounded_in_expected`` is 0.8 because
retrieval ranking is not a promise, and a threshold set where a healthy system fails is a
threshold that gets removed.

Usage:
    uv run python tools/evaluate_reasoning.py --live --connection warrant
    uv run python tools/evaluate_reasoning.py --check
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

from snowflake.snowpark import Session

from warrant.authority.tags import read_sensitivity
from warrant.authority.tiers import resolve
from warrant.common.models import ExceptionRecord, Finding
from warrant.reason.investigate import MODEL, investigate

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "eval" / "cases.json"
SCORECARD = ROOT / "eval" / "scorecard.json"

DIMENSIONS = (
    "action_selected",
    "entity_targeted",
    "tier_correct",
    "forbidden_avoided",
    "grounded_in_expected",
)
"""What each case is scored on.

``forbidden_avoided`` is the one that matters most and the one that should never be interesting:
it asks whether the model proposed an action the tags would refuse. A model doing that is not a
security failure — the executor stops it — but it is a *reasoning* failure worth measuring
separately, because a model that keeps reaching for a forbidden action is a model that has
misunderstood the procedure.
"""


def load_cases() -> dict[str, Any]:
    """Read the case definitions.

    Returns:
        The parsed ``eval/cases.json``.
    """
    return json.loads(CASES.read_text(encoding="utf-8"))


def score_case(case: dict[str, Any], outcome: dict[str, Any]) -> dict[str, bool]:
    """Score one observed outcome against one case's expectations.

    Args:
        case: A case from ``eval/cases.json``.
        outcome: What the pipeline actually produced — ``action_type``, ``params``,
            ``effective_tier``, ``grounded_in``, and ``root_cause``.

    Returns:
        One boolean per dimension in :data:`DIMENSIONS`.
    """
    expect = case["expect"]
    action = outcome.get("action_type")
    params = outcome.get("params") or {}
    grounded = set(outcome.get("grounded_in") or ())

    return {
        "action_selected": action in expect["action_in"],
        # The entity check is the one a JSON schema cannot express: a well-formed action aimed at
        # something that was never flagged would execute perfectly and be entirely wrong.
        "entity_targeted": case["exception"]["entity"] in {str(v) for v in params.values()},
        "tier_correct": outcome.get("effective_tier") == expect["effective_tier"],
        "forbidden_avoided": action not in set(expect.get("must_not_propose", ())),
        "grounded_in_expected": bool(grounded & set(expect.get("grounded_in_any", ()))),
    }


def aggregate(results: list[dict[str, Any]]) -> dict[str, float]:
    """Reduce per-case scores to a rate per dimension.

    Args:
        results: One entry per case, each carrying a ``scores`` mapping.

    Returns:
        Dimension name to pass rate in ``[0, 1]``. An empty run scores zero rather than one —
        vacuous success is the failure mode a gate exists to prevent.
    """
    if not results:
        return dict.fromkeys(DIMENSIONS, 0.0)
    return {
        dimension: sum(r["scores"][dimension] for r in results) / len(results)
        for dimension in DIMENSIONS
    }


def run_live(connection: str) -> list[dict[str, Any]]:
    """Evaluate every case against a live account.

    Args:
        connection: A connection name from ``~/.snowflake/connections.toml``.

    Returns:
        One result per case, ready to aggregate and record.
    """
    # Only the connection is unavailable in CI, not the imports — snowflake-snowpark-python is a
    # project dependency, so these live at module scope like everything else. `--check` never
    # reaches this function.
    session = Session.builder.config("connection_name", connection).create()
    session.sql("USE ROLE WARRANT_ROLE").collect()
    session.sql("USE WAREHOUSE WARRANT_WH").collect()

    results: list[dict[str, Any]] = []
    for case in load_cases()["cases"]:
        record = ExceptionRecord(
            exception_id=case["exception"]["exception_id"],
            metric=case["exception"]["metric"],
            entity=case["exception"]["entity"],
            observed=case["exception"]["observed"],
            expected=case["exception"]["expected"],
            deviation=case["exception"]["deviation"],
            detection_method=case["exception"]["detection_method"],
            source_objects=tuple(case["exception"]["source_objects"]),
        )
        produced = investigate(session, record)

        if isinstance(produced, Finding):
            decision = resolve(
                produced.requested_tier, read_sensitivity(session, produced.touched_objects)
            )
            outcome = {
                "action_type": produced.action_type,
                "params": dict(produced.action_params),
                "effective_tier": int(decision.tier),
                "grounded_in": list(produced.grounded_in),
                "root_cause": produced.root_cause,
                "refused": False,
            }
        else:
            # A refusal scores zero on every dimension rather than being skipped. A harness that
            # quietly dropped the cases it could not evaluate would report a rate over the cases
            # that happened to work.
            outcome = {
                "action_type": None,
                "params": {},
                "effective_tier": None,
                "grounded_in": [],
                "root_cause": produced.reason,
                "refused": True,
            }

        mentions = [
            phrase
            for phrase in case["expect"].get("report_if_mentions", ())
            if phrase.lower() in str(outcome["root_cause"]).lower()
        ]
        results.append(
            {
                "case_id": case["case_id"],
                "model": MODEL,
                "outcome": outcome,
                "scores": score_case(case, outcome),
                # Reported, never gated. Whether the reasoning happened to mention the in-transit
                # quantity is interesting and not a pass condition; gating on prose would be
                # gating on phrasing.
                "mentions": mentions,
            }
        )
    return results


def report(results: list[dict[str, Any]], rates: dict[str, float], thresholds: dict[str, float]):
    """Print a scorecard a human can read at a glance.

    Args:
        results: Per-case results.
        rates: Aggregated pass rate per dimension.
        thresholds: Required rate per dimension.
    """
    print(f"\n{'case':34s} " + " ".join(f"{d[:11]:>12s}" for d in DIMENSIONS))
    for entry in results:
        marks = " ".join(f"{'pass' if entry['scores'][d] else 'FAIL':>12s}" for d in DIMENSIONS)
        print(f"{entry['case_id']:34s} {marks}")

    print()
    for dimension in DIMENSIONS:
        rate, required = rates[dimension], thresholds.get(dimension, 1.0)
        verdict = "ok" if rate >= required else "BELOW THRESHOLD"
        print(f"  {dimension:24s} {rate:6.0%}  (required {required:.0%})  {verdict}")

    noted = [e for e in results if e["mentions"]]
    if noted:
        print("\n  reported, not gated:")
        for entry in noted:
            print(f"    {entry['case_id']}: mentioned {', '.join(entry['mentions'])}")


def main() -> int:
    """Run or verify the evaluation.

    Returns:
        ``0`` when every dimension meets its threshold and the scorecard covers every case.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="evaluate against a Snowflake account")
    mode.add_argument("--check", action="store_true", help="verify the committed scorecard")
    parser.add_argument("--connection", default="warrant", help="connection name for --live")
    args = parser.parse_args()

    spec = load_cases()
    thresholds = spec["thresholds"]
    expected_ids = [case["case_id"] for case in spec["cases"]]

    if args.live:
        results = run_live(args.connection)
        rates = aggregate(results)
        SCORECARD.write_text(
            json.dumps(
                {
                    "note": (
                        "Written by tools/evaluate_reasoning.py --live against a real account. "
                        "CI verifies this file rather than re-measuring, because CI has no "
                        "account. Re-run --live after changing eval/cases.json."
                    ),
                    "cases_evaluated": expected_ids,
                    "rates": rates,
                    "results": results,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"scorecard written to {SCORECARD.relative_to(ROOT)}")
    else:
        if not SCORECARD.exists():
            print(
                f"{SCORECARD.relative_to(ROOT)} is missing.\n"
                "Run: uv run python tools/evaluate_reasoning.py --live",
                file=sys.stderr,
            )
            return 1
        recorded = json.loads(SCORECARD.read_text(encoding="utf-8"))
        results = recorded["results"]
        rates = recorded["rates"]

        # The check that earns this file its place in CI: a case added and never evaluated.
        missing = sorted(set(expected_ids) - {r["case_id"] for r in results})
        if missing:
            print(
                "the scorecard does not cover every case: " + ", ".join(missing) + "\n"
                "Run: uv run python tools/evaluate_reasoning.py --live",
                file=sys.stderr,
            )
            return 1

    report(results, rates, thresholds)
    below = [d for d in DIMENSIONS if rates[d] < thresholds.get(d, 1.0)]
    if below:
        print(f"\nbelow threshold: {', '.join(below)}", file=sys.stderr)
        return 1
    print(f"\n{len(results)} case(s) evaluated, every dimension at or above threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
