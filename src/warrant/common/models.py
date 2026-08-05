"""Types shared across the detect → reason → classify → act boundary.

Near-leaf module by design: it depends only on :mod:`warrant.authority.tiers`, which is
itself a leaf, so every other module can depend on this one without any risk of a
circular import.

The dataclasses here mirror the pipeline tables in ``sql/20_pipeline.sql`` one-for-one.
Where a name differs between Python and SQL that is a bug, not a convention.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from warrant.authority.tiers import Tier

SEVERITIES: tuple[str, ...] = ("low", "medium", "high", "critical")
"""Permitted values of ``FINDINGS.severity``, ordered least to most urgent."""

REFUSAL_OUTCOMES: tuple[str, ...] = (
    "attempted_and_blocked",
    "nothing_to_act_on",
    "malformed_proposal",
    "model_error",
)
"""Why the agent declined, as a closed vocabulary.

A refusal is a *result*, not a failure, so it carries a structured code end to end rather
than being reconstructed later by pattern-matching the model's prose. The console renders
each of these differently, and none of them renders as an error.
"""


@dataclass(frozen=True)
class ExceptionRecord:
    """A detected operational exception — one row of ``CORE.EXCEPTIONS``."""

    exception_id: str
    metric: str
    entity: str
    observed: str
    expected: str
    deviation: str
    detection_method: str
    source_objects: tuple[str, ...]

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> ExceptionRecord:
        """Build a record from a Snowpark row.

        Args:
            row: Mapping keyed by uppercase Snowflake column name, as Snowpark's
                ``Row.as_dict()`` returns.

        Returns:
            The corresponding :class:`ExceptionRecord`.
        """
        return cls(
            exception_id=row["EXCEPTION_ID"],
            metric=row["METRIC"],
            entity=row["ENTITY"],
            observed=row["OBSERVED"],
            expected=row["EXPECTED"],
            deviation=row["DEVIATION"],
            detection_method=row["DETECTION_METHOD"],
            source_objects=tuple(row["SOURCE_OBJECTS"] or ()),
        )

    def as_prompt_context(self) -> str:
        """Render the exception as the factual block of the reasoning prompt.

        Returns:
            A compact, stable, human-readable summary. Deliberately not JSON: the model
            grounds better on prose, and this string is also what a reviewer sees in the
            approval console.
        """
        return (
            f"Metric: {self.metric}\n"
            f"Entity: {self.entity}\n"
            f"Observed: {self.observed}\n"
            f"Expected: {self.expected}\n"
            f"Deviation: {self.deviation}\n"
            f"Detected by: {self.detection_method}\n"
            f"Source objects: {', '.join(self.source_objects)}"
        )


@dataclass(frozen=True)
class Finding:
    """What the agent concluded about an exception — one row of ``CORE.FINDINGS``.

    ``requested_tier`` and ``touched_objects`` are copied from the action registry, not
    from the model: an action that could nominate its own authority or under-declare its
    own footprint would defeat the entire governance model. They are stored on the finding
    so the audit trail records what was true at proposal time, which is not necessarily
    what is true at execution time — see :mod:`warrant.act.executor`.
    """

    finding_id: str
    exception_id: str
    severity: str
    root_cause: str
    evidence: tuple[str, ...]
    recommended_action: str
    action_type: str
    action_params: Mapping[str, Any]
    requested_tier: Tier
    touched_objects: tuple[str, ...]
    grounded_in: tuple[str, ...] = ()
    model: str = ""

    def __post_init__(self) -> None:
        """Reject a finding the FINDINGS table would not accept.

        Raises:
            ValueError: If ``severity`` is outside :data:`SEVERITIES`, or if
                ``touched_objects`` is empty. The model is constrained by a JSON schema,
                but a schema-constrained model is still a model; the boundary is checked
                rather than trusted. An empty footprint is rejected here because
                ``resolve()`` would escalate it to approval-required, which reads as a
                deliberate policy decision when it is really missing data.
        """
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity {self.severity!r} is not one of {', '.join(SEVERITIES)}")
        if not self.touched_objects:
            raise ValueError(f"finding {self.finding_id!r} declares no touched objects")


@dataclass(frozen=True)
class Refusal:
    """A declined action — a first-class outcome, never an error.

    The agent refusing to act is the behaviour Warrant exists to demonstrate, so it is
    persisted with the same care as a successful action: its own audit row, its own
    structured outcome code, and its own presentation in the console.
    """

    exception_id: str
    outcome: str
    reason: str
    binding_object: str | None = None
    model: str = ""

    def __post_init__(self) -> None:
        """Reject an outcome code outside the closed vocabulary.

        Raises:
            ValueError: If ``outcome`` is outside :data:`REFUSAL_OUTCOMES`.
        """
        if self.outcome not in REFUSAL_OUTCOMES:
            raise ValueError(
                f"refusal outcome {self.outcome!r} is not one of {', '.join(REFUSAL_OUTCOMES)}"
            )


def finding_response_format(action_types: Sequence[str]) -> dict[str, Any]:
    """Build the ``AI_COMPLETE`` ``response_format`` schema for a reasoning call.

    Constraining the model to a closed set of ``action_type`` values is the difference
    between an agent that proposes actions the executor can run and one that invents
    plausible-sounding actions that fail at dispatch.

    Args:
        action_types: The action names the executor actually implements.

    Returns:
        A ``response_format`` argument suitable for ``AI_COMPLETE``.
    """
    return {
        "type": "json",
        "schema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": list(SEVERITIES)},
                "root_cause": {"type": "string"},
                "evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific figures or rows supporting the conclusion.",
                },
                "recommended_action": {"type": "string"},
                "action_type": {"type": "string", "enum": list(action_types)},
                "action_params": {"type": "object"},
            },
            "required": [
                "severity",
                "root_cause",
                "evidence",
                "recommended_action",
                "action_type",
                "action_params",
            ],
        },
    }
