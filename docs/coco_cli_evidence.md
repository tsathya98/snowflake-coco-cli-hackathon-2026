# CoCo CLI usage — plan and evidence

T&C §9(1) makes *use of Cortex Code CLI* a mandatory, scored criterion. This file is both the
session plan and the record, so what was asked and what changed stay in one place.

**Fill the "What happened" blocks in as you go.** An empty block is more useful than a guessed one:
the point of this document is that a reviewer can check it.

---

## Verified environment

| Fact | Value |
|---|---|
| Binary | `cortex`, **v1.1.53**, at `~/.local/bin/cortex` (WSL Ubuntu) |
| Connection | `warrant` — CoCo reads the same `~/.snowflake/connections.toml` the `snow` CLI uses |
| Project skills | All five in `.cortex/skills/` are discovered when `cortex` starts in the repo root |
| Project context | `AGENTS.md` is loaded automatically at session start |

### 🔴 Headless mode is unavailable on this account

```
$ cortex -c warrant -p "…"
Error: --print mode is not available for subscription/trial accounts.
```

All four documented non-interactive paths hit the same server-side, account-tier restriction:

| path | result |
|---|---|
| `cortex -p "…"` | `--print mode is not available for subscription/trial accounts` |
| `cortex exec …` (the dedicated CI/CD mode) | same error — it uses print mode internally |
| `cortex -f` | not a top-level flag; it is `exec --file`, so also blocked |
| `echo … \| cortex` | launches the TUI and consumes the pipe as keystrokes |

So CoCo cannot be scripted on this account and every session below has to be run interactively by
a human. It *does* run against the standard trial — in interactive mode only.

Two flags worth using anyway, both discovered from `cortex exec --help`:

- **`--sql-readonly`** restricts the built-in SQL tool to `SELECT`/`SHOW`/`DESCRIBE`/`EXPLAIN`.
  Use it for any session that is an audit. Note its own printed caveat: it constrains the *SQL
  tool*, not bash, Python or curl, so a session with read-only on can still write if it shells out.
- **confirm-actions** (shift+tab) gates every tool call. `bypass safeguards` is the other position
  of the same toggle and is easy to hit by accident — check the status bar before turning
  read-only off, because both safeguards down at once on a live account is the thing to avoid.

### Start every session the same way

```bash
wsl                     # CoCo lives in the Ubuntu distro, not on the Windows side
cd /mnt/c/Users/tsath/Documents/Projects/snowflake-coco-cli-hackathon-2026
cortex -c warrant
```

Run it **from the repo root** so `AGENTS.md` and `.cortex/skills/` load, and **never** from a
directory near employer repositories — CoCo inherits the launching shell's access to whatever
credentials and files are reachable from there.

---

## How the evidence is verified, not just asserted

CoCo runs SQL **as your Snowflake identity**, so every statement it executes lands in query
history. That is checkable by a third party and is the evidence that matters; a transcript is
something anyone could type.

After each session, capture what CoCo actually ran:

```bash
snow sql -c warrant -q "
USE DATABASE WARRANT;
SELECT START_TIME, LEFT(REPLACE(QUERY_TEXT, CHR(10), ' '), 120) AS statement
  FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
         END_TIME_RANGE_START => DATEADD(hour, -2, CURRENT_TIMESTAMP()), RESULT_LIMIT => 200))
 WHERE QUERY_TAG ILIKE '%cortex%' OR QUERY_TEXT ILIKE '%/* cortex%'
 ORDER BY START_TIME DESC;"
```

If the tag does not identify CoCo's traffic, fall back to the time window: run the session, note
the start and end, and filter `QUERY_HISTORY` on that range.

Note that `.cortex/conversations/`, `.cortex/logs/` and `.cortex/cache/` are **gitignored on
purpose** — they contain account identifiers and full session text. This document is the
deliberate, reviewable record instead.

---

## Session 1 — RBAC least-privilege audit

*Why this one first: the submission's entire claim is about bounded authority, so an
independently-generated finding about its own privilege model is the most on-theme use of the tool
available. CoCo ships a bundled `rbac` skill.*

Prompts:

```
/sql SHOW GRANTS TO ROLE WARRANT_ROLE;

Using the rbac skill, audit WARRANT_ROLE against least privilege for what this project
actually does. #WARRANT.CORE.PENDING_ACTIONS #WARRANT.DATA.QUALITY_HOLDS

Specifically: is any grant wider than the code needs? Pay attention to APPLY MASKING POLICY,
EXECUTE TASK, EXECUTE MANAGED TASK and IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE. Tell me
which grants could be narrowed without breaking sql/40_orchestration.sql or sql/45_review.sql.
```

**What happened — a real finding, confirmed and fixed.**

CoCo was given the hypothesis as something to **disprove**, not confirm:

> `GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE WARRANT_ROLE` is unnecessary, and the
> comment justifying it ("reading tags at runtime") is wrong.

It read `sql/00_setup.sql`, the build's working notes (not published — they carry the account
locator) and `src/warrant/authority/tags.py`, grepped
for `ACCOUNT_USAGE|INFORMATION_SCHEMA` across `src/ sql/ streamlit/`, searched the Snowflake docs
for what `SYSTEM$GET_TAG` actually requires, and returned **verdict: the grant is unnecessary and
the comment is wrong**, with the reasoning:

- **`SYSTEM$GET_TAG`** (`authority/tags.py:36`) needs USAGE on the **tag's** parent database and
  schema — `WARRANT` + `WARRANT.CORE`, already granted at `00_setup.sql:79-81`. Nothing on the
  `SNOWFLAKE` database, *because the tag lives in `WARRANT`*.
- **`SNOWFLAKE.CORTEX.SEARCH_PREVIEW`** (`reason/investigate.py:55`) needs the
  `SNOWFLAKE.CORTEX_USER` database role, already granted at line 94. A database role carries
  implicit USAGE on its parent for the objects it covers; `IMPORTED PRIVILEGES` adds nothing.
- What the grant *did* provide — `ACCOUNT_USAGE`, `ORGANIZATION_USAGE`, `READER_ACCOUNT_USAGE`, and
  eight class privileges visible in `SHOW GRANTS` (`SNOWFLAKE.CORE.BUDGET`, `ORG_BUDGET`, `QUOTA`,
  `MARKETPLACE_ANALYTICS`, `ML.DOCUMENT_INTELLIGENCE`) — is used by **nothing** in the project.
- And the comment conflated *reading tags* (needs USAGE on `WARRANT.CORE`) with *accessing the
  SNOWFLAKE database* (needed by nothing here). Gotcha #3 already forbids reading tags from
  `ACCOUNT_USAGE` because it lags two hours, so the grant's stated purpose contradicted the
  project's own design decision.

**Then it tested the claim rather than asserting it.** Revoked the grant live, ran
`sql/90_reset.sql`, ran `RUN_LOOP('AUTO')`, and checked the one signal that would reveal a broken
`SEARCH_PREVIEW` — `grounded_in`, which the pipeline records as an honest empty rather than an
error, so `findings: 6` alone would not have caught it:

| entity | action | tier | grounded_in |
|---|---|---|---|
| SKU-1003 | `raise_replenishment` | 3 | RB-002, RB-001, RB-004 |
| SUP-002 | `open_supplier_case` | 2 | RB-001, RB-002, RB-003 |
| QH-0010 / 0031 / 0034 / 0036 | `notify_quality_owner` | 1 | RB-003, RB-001, … |

Both dependencies intact: grounding populated on every row, and the 5-auto vs 1-approval split
proves `SYSTEM$GET_TAG` still distinguished `open`/`internal` from `regulated`.

**Outcome:** grant revoked on the live account and removed from `sql/00_setup.sql` (+3 −2), with the
comment corrected. Verified independently afterwards: no `IMPORTED`/`CLASS` rows remain in
`SHOW GRANTS TO ROLE WARRANT_ROLE`, `CORTEX_USER` is still granted, and `00_setup.sql` still runs
clean so idempotency holds.

**Session conditions, for honesty about scope:**

- Launched `cortex -c warrant --sql-readonly`, so the audit itself could not mutate anything.
  Read-only was turned off (`/sql-readonly off`) only for the revoke-and-test step, and
  confirm-actions stayed on so every command was approved individually.
- The connection's role is `ACCOUNTADMIN`, so CoCo audited `WARRANT_ROLE` **without being
  constrained by it**. That is what let it see all the grants; it also means this was an audit of
  the role, not a demonstration that the role is confined.
- Two CoCo quirks worth recording: its read-only classifier **false-positived on a `SHOW`**
  statement (`Show grants on SNOWFLAKE database` was blocked though `SHOW` is permitted), and the
  SQL result panel truncates at 10 rows, which understates `SHOW GRANTS` output.

---

## Session 2 — Trial credit burn

*Why: the trial is $400 or 30 days, whichever ends first, and resource monitors deliberately do
not cover Cortex AI or serverless tasks. This is real operational need, not a demo.*

```
How many credits has this account consumed so far, broken down by warehouse, serverless
task, and AI services? Project the burn to 2026-09-04 at the current rate and tell me
whether the demo survives to the Grand Finale.
```

**What happened — the numbers, and a gap CoCo reported without recognising.**

Total consumed: **8.39 credits in ~30 hours of account life**, 391.61 of 400 remaining.

| Category | Credits | Share |
|---|---|---|
| Warehouse `WARRANT_WH` | 4.15 | 49% |
| Warehouse **`COMPUTE_WH`** | **3.24** | **39%** |
| Warehouse `WARRANT_SEARCH_WH` | 0.34 | 4% |
| AI functions (`AI_COMPLETE`) | 0.55 | 6.5% |
| Cortex Agents | 0.25 | 3% |
| Serverless tasks (`EXECUTE_ON_APPROVAL`) | 0.007 | <0.1% |

Projection to the Sept 1–4 finale: ~210 credits sustaining a heavy-development rate, ~57 on a
realistic mix. Either survives 400 comfortably, and idle burn measured at **~0.012 credits/hour**
shows the 60-second `AUTO_SUSPEND` doing its job.

**The gap.** CoCo concluded "no action required", which is right about survival and wrong about the
cost guard. `COMPUTE_WH` is the account's default warehouse and the second-largest consumer at 39%
— and `sql/00_setup.sql` attaches `WARRANT_MONITOR` only to `WARRANT_WH` and `WARRANT_SEARCH_WH`.
So the 100-credit cap does not cover it. Same shape as the session-1 finding: a control that looks
complete with a hole in it. Worth noting that the tool surfaced the data that makes the gap visible
even though it did not draw the conclusion — which is the honest way to describe what an assistant
did.

Partly self-inflicted and now partly fixed: the `warrant` connection had **no `warehouse` key** at
all (the documented CoCo first-run stumble — its banner read `Warehouse: N/A` and the SQL tool
silently did nothing). Adding `warehouse = "WARRANT_WH"` fixed the tool *and* moved subsequent CLI
and CoCo traffic onto a monitored warehouse.

**Three measured figures worth using rather than projecting:**

- **8.39 credits built the entire project** — 2% of the allowance.
- **AI functions are 6.5% of spend.** The reasoning is the cheap part; warehouse compute dominates.
- **Serverless tasks are 0.007 credits.** This *measures* the claim that an idle schedule costs
  nothing, instead of asserting it.

**Follow-up: the gap closed, and it was bigger than the finding said.**

Challenged on its own "no action required", CoCo changed the conclusion rather than defending it —
*"'No action required' was wrong. The cost guard has a gap over the second-largest consumer."* It
then identified what actually uses `COMPUTE_WH` (Snowsight worksheets, `snow` CLI, MFA checks, and
CoCo itself — all interactive, none of it the pipeline) and proposed adding it to
`WARRANT_MONITOR`.

**That first fix was rejected.** A shared 100-credit quota with a `SUSPEND` trigger would couple
interactive dev traffic to the demo's availability: a Snowsight session that burned the quota would
suspend `WARRANT_WH` along with it — a self-inflicted outage waiting for the worst possible moment.
A separate `WARRANT_DEV_MONITOR` (25 credits, ~8x current burn) keeps the budgets independent, so a
browsing binge can only suspend the browsing.

**And verifying the fix found more.** CoCo inferred the end state from "CREATE and ALTER both
returned success" — `ACCOUNT_USAGE.RESOURCE_MONITORS` lags up to 45 minutes, its
`INFORMATION_SCHEMA` query errored on an identifier, and `DESCRIBE WAREHOUSE` does not show the
monitor. Checking properly with `SHOW WAREHOUSES` (which carries a `resource_monitor` column)
confirmed the assignment *and* revealed **`SNOWFLAKE_LEARNING_WH` was also unmonitored** — a third
trial-default warehouse nobody had looked at.

Final state, verified real-time rather than inferred:

| warehouse | monitor |
|---|---|
| `WARRANT_WH`, `WARRANT_SEARCH_WH` | `WARRANT_MONITOR` (100 credits) |
| `COMPUTE_WH`, `SNOWFLAKE_LEARNING_WH` | `WARRANT_DEV_MONITOR` (25 credits) |
| `SYSTEM$STREAMLIT_NOTEBOOK_WH` | none — system-managed, and the console runs on `WARRANT_WH` |

Committed to `sql/00_setup.sql` with each `ALTER` in its own exception handler, because those
warehouses belong to the account rather than to this project and may not exist in a judge's — a
bare `ALTER` would abort `setup.sh` for them.

---

## Session 3 — Extend the semantic view

*Why: a real gap. `CORE.OPS_ANALYSIS` covers shipments, suppliers and SKUs only, so the Cortex
Analyst tool on the agent cannot answer anything about inventory or quality. CoCo ships
`semantic-view-patterns` and can generate semantic views from table metadata.*

```
#WARRANT.DATA.INVENTORY #WARRANT.DATA.QUALITY_HOLDS #WARRANT.CORE.OPS_ANALYSIS

Extend the semantic view CORE.OPS_ANALYSIS to cover inventory cover and quality-hold ageing,
following the naming already used for shipments. Keep the logical/physical name distinction —
the view declares `suppliers.supplier AS supplier_name`, and queries use the logical name.
Do not expose QUALITY_HOLDS.lot_ref: it carries a masking policy and the agent must not
surface it.
```

**What happened:** _(fill in: the DDL, whether `sql/30_ai.sql` changed, and the verifying query)_

---

## Session 4 — Exercise the project's own skills

*Why: the deck template explicitly asks **which Cortex Code CLI skills are used and how they
connect**. Skills that exist but were never invoked answer that question weakly.*

```
$classify-authority

Resolve the authority tier for release_quality_hold against the live tags, then check your
answer against CALL WARRANT.CORE.AUTHORITY_MANIFEST(NULL). Do they agree? If not, which is
wrong and why?
```

```
$detect-anomaly

Review src/warrant/detect/exceptions.py against the thresholds in the corpus:
#WARRANT.DATA.RUNBOOKS. Is every number in the detectors actually quoted from a clause, and
is any clause implemented incorrectly?
```

**What happened:** _(fill in: whether the skill's answer matched the implementation)_

---

## Session 5 — Adversarial review of the submission

*Why: an outside reading of the repo against the problem statement, from a tool that has the
project context loaded and no investment in the existing design.*

```
Read AGENTS.md, README.md and docs/rubric_alignment.md. You are a hackathon judge scoring
against: Technical Execution 40%, Real-World Relevance 30%, Solution Completeness 30%, plus
T&C §9 (Cortex Code CLI, Python, Snowflake platform, and special consideration for Snowpark /
Worksheets / Streamlit / Marketplace).

Where is this submission weakest? Name the three claims you would most want to disprove, and
tell me exactly how you would try.
```

**What happened:** _(fill in: the three claims, and what was done about each)_

---

## Summary for the deck and the portal

_(fill in once the sessions are done)_

| Session | Skill(s) used | Outcome | Commit |
|---|---|---|---|
| 1 RBAC audit | `rbac`, docs search | **Found a real over-grant.** `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` was unnecessary and its justifying comment contradicted Gotcha #3. Revoked live, removed from `sql/00_setup.sql`, verified by re-running the loop and checking `grounded_in`. | `sql/00_setup.sql` +3 −2 |
| 2 Credit burn | cost intelligence | **8.39 of 400 credits used**; survives to Sept 4 on any projection. Surfaced that `COMPUTE_WH` is 39% of spend and sits outside `WARRANT_MONITOR` — a hole in the cost guard. AI functions only 6.5%; serverless tasks 0.007. Gap closed with a separate `WARRANT_DEV_MONITOR`; verification found `SNOWFLAKE_LEARNING_WH` unguarded too. | `sql/00_setup.sql` |
| 3 Semantic view | `semantic-view-patterns` | | |
| 4 Own skills | `$classify-authority`, `$detect-anomaly` | | |
| 5 Adversarial review | project context | | |
