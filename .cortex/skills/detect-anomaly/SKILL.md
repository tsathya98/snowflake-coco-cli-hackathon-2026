---
name: detect-anomaly
description: Establish rolling baselines over operational metrics and surface statistically significant exceptions into the EXCEPTIONS table, with every threshold traceable to a runbook clause.
---

# detect-anomaly

Find operational exceptions worth a human's attention — not every fluctuation.

## Approach
1. Maintain baselines in a Dynamic Table, not an ad-hoc query. Set `TARGET_LAG` to match the
   cadence of whatever reads it — currently `'60 minutes'`, matching the hourly sweep. A lag
   shorter than the read interval refreshes around the clock for nothing, which on a trial
   account is a real charge.
2. **Take every threshold from the runbook corpus, never from your own judgement.** The
   detectors implement RB-001's twenty percentage points, RB-002's fourteen days of cover and
   RB-003's sixty days, and record which clause they came from. A threshold chosen to make a
   demo work is the thing this rule exists to prevent — and because the same documents are what
   Cortex Search retrieves for the reasoning step, a conclusion can cite the clause that set the
   threshold that raised it.
3. Pair the runbook threshold with a **robust z-score** — median and MAD, never mean and standard
   deviation, because the outlier being hunted would otherwise inflate the spread it is measured
   against. The threshold decides; the z-score corroborates that the move is an outlier against
   the population rather than a broad seasonal shift. Where both agree independently, say so.
4. Write to `WARRANT.CORE.EXCEPTIONS` with the metric, observed value, expected range, deviation,
   and the detection method actually used.

Implemented in `src/warrant/detect/exceptions.py` as a tuple of `Detector` records, each owning
one `MERGE`. Adding a detector is adding a row, not editing control flow.

`SNOWFLAKE.ML.ANOMALY_DETECTION` is deliberately **not** used, and step 3 is why: a threshold
quoted from a documented procedure is more defensible to an auditor than a score from a model
that cannot cite one. The detector records `detection_method` per row precisely so the seam where
the ML function would plug in stays visible and honest.

## Rules
- Never emit an exception without recording *why* it was flagged. "The model said so" is not
  an explanation a judge or an operator can act on.
- Deduplicate per RB-005: one open exception per (metric, entity) while it is open. Use `MERGE`
  and refresh the readings on a match. Note that Snowflake does not enforce `UNIQUE`, so the
  constraint in `sql/20_pipeline.sql` is documentation — the `MERGE` predicate is the control.
- **Do detect on regulated objects.** Detection is a read, and reads are exempt from the
  sensitivity tags by design — see `classify-authority`. The agent must be able to surface an
  aging quality hold on a `regulated` table and explain it, because RB-003 explicitly permits
  exactly that and nothing further. A detector that skipped regulated data would make the agent
  silent about the one class of problem a human most needs surfaced. **The tags constrain what
  may be acted on, never what may be looked at.**
- Detect only what the composing step is allowed to compose. Statements live at module scope and
  every varying value binds, so no detector can be steered by the data it reads.
