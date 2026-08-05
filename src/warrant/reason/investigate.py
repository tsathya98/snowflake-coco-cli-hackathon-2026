"""Turning an exception into a finding, or into a refusal.

This is the only module that calls a language model, and it is built on the assumption that
the model will sometimes be wrong in ways a JSON schema cannot catch.

**Schema conformance gates shape, not truth.** ``response_format`` guarantees the reply has
a ``severity`` from the allowed set and an ``action_type`` from the registry. It guarantees
nothing about whether the proposed parameters match that action's contract, or whether the
action even refers to the entity that was flagged. Those are checked here, and a failure is
a :class:`~warrant.common.models.Refusal` rather than an exception — the agent declining to
act on a proposal it cannot validate is a result worth recording.

**The model never nominates its own authority.** It chooses *what to do*; the registry
declares what that costs, and ``requested_tier`` and ``touched_objects`` are copied from
there. An action allowed to under-declare its own footprint would defeat the governance
model, because footprint is exactly what authority is resolved from.

**Nothing is interpolated into SQL.** The prompt, the response schema and the search payload
are all bound parameters — verified to work, including ``response_format => PARSE_JSON(?)``.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import Any

from snowflake.snowpark import Session

from warrant.act.registry import ACTION_TYPES, ActionValidationError, get_action_type
from warrant.common.models import (
    ExceptionRecord,
    Finding,
    Refusal,
    finding_response_format,
)

MODEL = "claude-sonnet-4-6"
"""Pinned deliberately.

Leaving the model unset lets the platform resolve it, which can silently select a weaker
model. This id was probed in-account rather than read off a docs page: two fetches of
Snowflake's regional availability table disagreed about which models us-west-2 offers.
"""

GROUNDING_LIMIT = 3
"""How many runbook clauses to retrieve. Enough to cover the case, few enough to stay read."""

SEARCH_RUNBOOKS = """
SELECT res.value:DOC_ID::STRING AS doc_id,
       res.value:TITLE::STRING  AS title,
       res.value:BODY::STRING   AS body
  FROM TABLE(FLATTEN(PARSE_JSON(
           SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WARRANT.CORE.RUNBOOK_SEARCH', ?)
       ):results)) res
"""

REASON = """
SELECT AI_COMPLETE(
         model                => ?,
         prompt               => ?,
         model_parameters     => {'temperature': 0, 'max_tokens': 2000},
         response_format      => PARSE_JSON(?),
         return_error_details => TRUE
       ) AS reply
"""

# Built at module scope from the registry, so the catalogue the model is shown and the
# contract the executor enforces cannot drift apart.
ACTION_CATALOGUE = "\n".join(
    f"- {action.name}({', '.join(action.parameters)}): {action.description}"
    for action in ACTION_TYPES.values()
)

PROMPT = """You are an operations analyst reviewing an exception raised by an automated detector.

EXCEPTION
{context}

OPERATING PROCEDURES
These are authoritative. Where they constrain what automation may do, follow them in
preference to your own judgement.

{grounding}

ACTIONS AVAILABLE
{catalogue}

Choose exactly one action_type from that list and populate action_params with precisely the
parameters it names — no more and no fewer. The action must concern {entity}, the entity
flagged above.

Every statement in root_cause must be supported by an entry in evidence, quoting the
specific figures given. Do not introduce figures that do not appear above.

If the procedures say automation may not take a particular action, choose the action that
only surfaces or notifies instead.
"""


def retrieve_grounding(session: Session, exception: ExceptionRecord) -> tuple[tuple[str, ...], str]:
    """Retrieve the operating procedures relevant to an exception.

    Args:
        session: An active Snowpark session.
        exception: The exception to find prior art for.

    Returns:
        A ``(doc_ids, text)`` pair. ``doc_ids`` is recorded on the finding as
        ``grounded_in`` so a reviewer can see which clause the conclusion leaned on;
        ``text`` is the block interpolated into the prompt. Both are empty if the search
        returns nothing, which leaves the model to reason unaided — recorded honestly as
        an empty ``grounded_in`` rather than hidden.
    """
    payload = json.dumps(
        {
            "query": f"{exception.metric} {exception.entity} {exception.observed}",
            "columns": ["DOC_ID", "TITLE", "BODY"],
            "limit": GROUNDING_LIMIT,
        }
    )
    rows = session.sql(SEARCH_RUNBOOKS, params=[payload]).collect()
    doc_ids = tuple(row["DOC_ID"] for row in rows)
    text = "\n\n".join(f"[{row['DOC_ID']}] {row['TITLE']}\n{row['BODY']}" for row in rows)
    return doc_ids, text


def validate_proposal(
    exception: ExceptionRecord,
    payload: Mapping[str, Any],
    grounded_in: tuple[str, ...],
) -> Finding | Refusal:
    """Check a schema-valid proposal against the things a schema cannot express.

    Args:
        exception: The exception the proposal responds to.
        payload: The model's structured reply, already conforming to
            :func:`~warrant.common.models.finding_response_format`.
        grounded_in: Runbook ids retrieved for this exception.

    Returns:
        A :class:`~warrant.common.models.Finding` if the proposal is coherent, or a
        :class:`~warrant.common.models.Refusal` with outcome ``malformed_proposal`` if it
        names an unregistered action, supplies the wrong parameters, or proposes acting on
        an entity other than the one that was flagged.
    """
    params = payload.get("action_params") or {}
    try:
        action = get_action_type(payload["action_type"])
        action.bind(params)
    except (ActionValidationError, KeyError) as error:
        return Refusal(
            exception_id=exception.exception_id,
            outcome="malformed_proposal",
            reason=f"The proposed action does not satisfy the registry: {error}",
            model=MODEL,
        )

    # The model is pinned to an action *name* by the schema but not to a *subject*. An
    # action aimed at some other entity would be executed perfectly and be entirely wrong.
    if exception.entity not in {str(value) for value in params.values()}:
        return Refusal(
            exception_id=exception.exception_id,
            outcome="malformed_proposal",
            reason=(
                f"The proposal targets {sorted(params.values())!r} but the exception "
                f"concerns {exception.entity}."
            ),
            model=MODEL,
        )

    return Finding(
        finding_id=f"FND-{uuid.uuid4().hex[:12]}",
        exception_id=exception.exception_id,
        severity=payload["severity"],
        root_cause=payload["root_cause"],
        evidence=tuple(payload.get("evidence") or ()),
        recommended_action=payload["recommended_action"],
        action_type=action.name,
        action_params=dict(params),
        # From the registry, never from the model.
        requested_tier=action.requested_tier,
        touched_objects=action.touched_objects,
        grounded_in=grounded_in,
        model=MODEL,
    )


def investigate(session: Session, exception: ExceptionRecord) -> Finding | Refusal:
    """Reason about one exception.

    Args:
        session: An active Snowpark session.
        exception: The exception to investigate.

    Returns:
        A :class:`~warrant.common.models.Finding` carrying a validated, executable
        proposal, or a :class:`~warrant.common.models.Refusal` explaining why no proposal
        could be made. A model error yields ``model_error``; an incoherent proposal yields
        ``malformed_proposal``. Neither raises: the loop must survive one bad exception
        without abandoning the others.
    """
    doc_ids, grounding = retrieve_grounding(session, exception)
    prompt = PROMPT.format(
        context=exception.as_prompt_context(),
        grounding=grounding or "No procedure was retrieved for this exception.",
        catalogue=ACTION_CATALOGUE,
        entity=exception.entity,
    )
    schema = json.dumps(finding_response_format(sorted(ACTION_TYPES)))

    rows = session.sql(REASON, params=[MODEL, prompt, schema]).collect()
    # return_error_details wraps the reply, so a model failure arrives as a row to record
    # rather than as an aborted statement mid-loop.
    envelope = json.loads(rows[0]["REPLY"]) if rows else {}

    if envelope.get("error") or not envelope.get("value"):
        return Refusal(
            exception_id=exception.exception_id,
            outcome="model_error",
            reason=str(envelope.get("error") or "The model returned no structured reply."),
            model=MODEL,
        )

    return validate_proposal(exception, envelope["value"], doc_ids)
