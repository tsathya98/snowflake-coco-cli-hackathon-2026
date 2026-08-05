---
name: orchestrate-loop
description: Run detect → investigate → classify → route → audit end to end, idempotently, with a circuit breaker.
---

# orchestrate-loop

## Phases
1. `detect-anomaly` → new rows in `EXCEPTIONS`
2. `investigate-root-cause` → findings
3. `classify-authority` → effective tier per proposed action
4. Route: `L2` execute + audit · `L3` → `PENDING_ACTIONS` + notify · `L4` refuse + audit
5. Append every step to `ACTION_AUDIT`

## Rules
- Idempotent throughout — use `MERGE`, never blind `INSERT`. Judges will re-run this.
- Consume streams with DML. A bare `SELECT` does not advance the offset and the task will
  reprocess the same rows forever.
- Circuit breaker: if more than N actions fire in one window, halt and escalate the whole batch.
- The loop must be safe to call with zero new exceptions — that is the common case.
