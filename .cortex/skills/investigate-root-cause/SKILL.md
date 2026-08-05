---
name: investigate-root-cause
description: Reason over a detected exception using structured evidence plus Cortex Search over runbooks and prior incidents, returning a schema-validated finding.
---

# investigate-root-cause

Turn "this number is wrong" into "this is why, and here is the evidence."

## Approach
1. Pull the exception row and its surrounding context (same entity, prior periods, related metrics).
2. Query the Cortex Search service over runbooks and past incident write-ups for prior art.
3. Call `AI_COMPLETE` with `response_format` pinned to the finding schema and
   `return_error_details` enabled.

## Output schema
`{severity, root_cause, evidence[], recommended_action, action_type, action_params}`

Built by `finding_response_format()` in `src/warrant/common/models.py`, with `action_type` pinned to
an enum of the action names the executor actually implements.

`requested_tier` and `touched_objects[]` are deliberately **not** in the schema. They are copied onto
the finding from the action registry, because an action allowed to nominate its own authority or
under-declare its own footprint would defeat the governance model entirely. The model chooses *what
to do*; the registry declares *what that costs*.

## Rules
- Never parse prose. If the model cannot fill the schema, that is a refusal to record, not a string
  to regex. Pass `return_error_details => TRUE` so a model error arrives as
  `{"value": NULL, "error": "..."}` — a displayable row rather than an aborted statement.
- Schema conformance gates *shape*, not *truth*. After it validates, independently verify that the
  `action_type` is registered, that every `action_params` key matches that action's declared
  parameters, and that the entity it names actually exists. A failure here is a `Refusal` with
  outcome `malformed_proposal`.
- Every claim in `root_cause` must be traceable to an entry in `evidence[]`.
- Carry the `doc_id`s returned by Cortex Search into `grounded_in[]`, so a reviewer can see which
  runbook clause the conclusion leaned on.
