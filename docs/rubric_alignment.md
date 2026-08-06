# Rubric alignment

Written for a reviewer with limited time. Every claim below is followed by the command or file
that settles it, and nothing here needs a Snowflake account unless it says so.

Two rubrics are published for this contest and they do not match each other, so both are
addressed:

| Source | Criteria |
|---|---|
| Event page | Technical Execution **40%** · Real-World Relevance **30%** · Solution Completeness **30%** |
| Terms & Conditions §9 | Four unweighted criteria: Cortex Code CLI · Python/Java/Scala · use of Snowflake's platform · special consideration for Snowpark, Worksheets, Streamlit, Marketplace |

**The two-minute version.** Clone, then:

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run python tools/lint_sql_boundary.py
uv run python tools/build_corpus.py --check
uv run python tools/evaluate_reasoning.py --check
uv run python tools/check_doc_claims.py
uv run pytest --cov --cov-report=term-missing
```

Expected: clean, clean, `no issues found in 19 source files`, `SQL boundary holds across 27
module(s)`, `6 document(s) verified`, `6 case(s) evaluated`, `Every counted claim matches the
repository`, `247 passed … 100.00%` with the coverage gate satisfied.

Every figure in that sentence is checked by the run above it. `tools/check_doc_claims.py` executes
the project's own tools and compares what they print against what this document, the README and
the walkthrough claim — so a reviewer who finds a number here that does not match the repository
has found a CI failure, not a discrepancy.

---

## T&C §9(1) — use of Cortex Code CLI

**Mandatory, and answered twice.**

*Built with it.* Six custom Agent Skills in [`.cortex/skills/`](../.cortex/skills/), each naming
the module that implements it so the skill and the code cannot drift apart silently:

| Skill | Phase | Implemented by |
|---|---|---|
| `detect-anomaly` | ① detect | `warrant/detect/exceptions.py` |
| `investigate-root-cause` | ② reason | `warrant/reason/investigate.py` |
| `classify-authority` | ③ classify | `warrant/authority/tags.py` + `tiers.py` |
| `propose-action` | ④ route | `warrant/act/registry.py` |
| `orchestrate-loop` | ①–⑤ | `warrant/orchestrate/loop.py` |
| `operate-warrant` | driving it | `mcp/warrant_mcp/server.py` |

*Drivable by it.* Cortex Code CLI is a full MCP client, and [`mcp/`](../mcp/) exposes Warrant as
an MCP server: **13 governed tools**, eleven annotated `readOnlyHint` and two that act, of which
one declares `destructiveHint`. Five resources carry the same state for clients that support them,
each with a tool twin for clients that do not. Register it with `cortex mcp add warrant …` and the
governed capabilities appear as `mcp__warrant__*`.

The load-bearing detail is what the tools *do not* accept. Not one takes a tier, a role or a force
flag — authority is resolved from the object tags inside every call, and
`mcp/tests/test_server_surface.py::test_no_tool_accepts_a_tier` asserts that against the generated
JSON schema. So the guarantee holds against a persuaded model, not only a well-behaved one. Asking
Warrant to release a regulated hold over MCP produces the same refusal, in the same append-only
log, as asking through the console.

`AGENTS.md` is the project context loaded at session start. It carries the hard constraints, the
conventions, and — deliberately — the reasons behind them, because a rule without a reason is a
rule the next session breaks.

## T&C §9(2) — Python, Java and/or Scala

**Python throughout.** `src/warrant/` is 100% Python; the stored procedures in
`sql/40_orchestration.sql` are Snowpark Python and import the *packaged* module rather than
inlining a copy, so the code running in Snowflake is byte-for-byte the code the tests cover.

```bash
uv run mypy      # strict, 19 modules, zero errors
```

No TypeScript, no Go. There is deliberately **no token Java component** — a JDBC shim existing
only to satisfy a criterion would be a worse answer than a clean Python one.

## T&C §9(3) and §9(4) — use of the Snowflake platform

**19 services, each cited to the file that uses it** in the [README table](../README.md#snowflake-services-used),
so the list is checkable rather than claimed. Of the four given "special consideration" in
§9(4): **Snowpark** ✓, **Streamlit** ✓, **Worksheets** — the numbered `sql/` files are worksheet
scripts, **Marketplace** — deliberately not used, see below.

Everything runs *inside* Snowflake: no external inference, no external orchestration, no copy of
the data anywhere else. That is partly principle and partly the trial's constraints
(`docs/architecture.md` explains which).

### What is deliberately absent, and why

A service list is only worth anything if it is honest, so:

- **Snowflake Marketplace** — no third-party dataset would be synthetic, and verifiable data
  provenance matters more than one more line item. See `docs/data_licences.md`.
- **`SNOWFLAKE.ML.ANOMALY_DETECTION`** — the detectors implement thresholds quoted from the
  runbook corpus instead. A threshold traceable to a documented procedure is more defensible to
  an auditor than a score from a model that cannot cite one. The seam where it would plug in is
  documented rather than hidden.
- **A `generic` agent tool bound to the executor** — this one is a governance decision, not an
  omission. See Technical Execution below.

---

## Track 1's own strong-vs-weak list

The organisers' walkthrough session named, for this track specifically, what a strong submission
looks like and what a weak one looks like. Those are the sharpest criteria published anywhere for
Problem Statement 1, so they are answered directly rather than left implied.

**What they said is strong.**

| | Where it is |
|---|---|
| **Multi-step reasoning** | Five phases, not one prompt: detect → investigate → classify authority → route → audit. Each is a module and a skill; `warrant/orchestrate/loop.py` runs them idempotently behind a circuit breaker. |
| **Autonomous execution** | It writes. `open_supplier_case` executed with no human in the loop, on data tagged `open`, and the row is in the append-only log. The demonstration is not a draft-only agent. |
| **Reusable modules** | An action is a registry entry, not a code path. Adding one forces it — by invariant test — to declare its footprint, bind parameters in placeholder order, and state an undo path. Governing a new table is `ALTER TABLE … SET TAG`, with no code change at all. |
| **Context-aware triggers** | A Stream on `PENDING_ACTIONS` fires `EXECUTE_ON_APPROVAL` when a human approves; `SCAN_FOR_EXCEPTIONS` sweeps hourly. Both serverless, so an idle schedule costs 0.007 credits — measured, not asserted. |

**What they said is weak, and why this is not that.**

| Anti-pattern | Why this isn't it |
|---|---|
| *A chatbot layer over a database* | There is a conversational surface, and it is deliberately the **least** capable one: two read-only tools and no tool bound to the executor. Acting belongs to the governed console, which has an identity. A chat box wired to `EXECUTE_ACTION` would put the most persuadable surface in the system on the far side of the gate. |
| *A single one-shot prompt* | One model call produces a *finding*, under a JSON schema, grounded by Cortex Search. It never produces SQL, never chooses its own authority, and never names the objects it touches — those come from the registry. Removing the model entirely would still leave a governed pipeline; removing the governance would leave an agent nobody would deploy. |
| *A dashboard with alerts* | The output is not a notification. Five of six exceptions ended in an executed action or a queued one with an undo path. What a dashboard cannot do — and this does — is **refuse**, record why, and re-check the policy again at execution time. |

---

## Technical Execution (40%)

### Multi-step orchestration

One `CALL WARRANT.CORE.RUN_LOOP('AUTO')` runs detect → reason → classify → route → act → audit.
Observed on the live account:

```json
{"run_id": "RUN-072ab9eb5dd9", "mode": "AUTO", "open_exceptions": 6, "findings": 6,
 "awaiting_approval": 1, "executed": 5, "refusals": 0, "emailed": 1}
```

Six exceptions, **three different routings, from one loop with no branching on table names.** The
counts come from `settle()`, which derives them by re-reading the tables afterwards rather than
accumulating what the code believed as it went — so a model that hallucinated having acted could
not inflate them.

### Decision branches

The authority tier is resolved from Snowflake object tags on the data an action touches, and
**re-resolved at execution time**:

| Source | Tag | Outcome |
|---|---|---|
| `SHIPMENTS`, `SUPPLIERS` | `open` | executes unsupervised |
| `INVENTORY` | `internal` | queued for a human |
| `QUALITY_HOLDS` | `regulated` | draft permitted (RB-003), action refused |
| `RUNBOOKS` | *untagged* | treated as unclassified, not as cleared |

And authority is not one hardcoded tag. `RETENTION` is a second, independent axis resolved
through the same `POLICIES` mechanism: an object tagged `open` — which sensitivity alone would
wave through — is refused outright when it carries `retention='legal_hold'`, with the rationale
naming retention rather than sensitivity. Verified on the live account and held by
`tests/test_retention.py`.

The strongest single claim in the submission: **a human's own approval does not survive a
reclassification.** Approve an action, retag the table, run the executor — it refuses and says
why. `docs/judges_walkthrough.md` §"Verifying the central claim" has the exact commands, and
`tests/test_executor.py::test_a_regulated_footprint_is_refused_even_when_a_human_approved_it`
holds it in place.

### Error handling

Nothing in the governance path raises. A refusal is a returned status and an audit row, because
the loop must refuse one action and carry on with the next. `REFUSAL_OUTCOMES` is a closed
vocabulary carried end to end rather than reconstructed by pattern-matching prose, and every
outcome — including a model error and a malformed proposal — lands in `ACTION_AUDIT`.

A circuit breaker caps unsupervised actions per pass, so a detector bug produces approval
requests rather than a thousand actions.

### Not hard-coded

The sub-criterion most often asserted and least often evidenced, so it gets a measurement rather
than a claim:

```bash
uv run python tools/evaluate_reasoning.py --check
```

Six exception scenarios spanning all three tiers, scored on five dimensions, recorded in
`eval/scorecard.json`. Two exist to be hard: a hold open **341 days with no owner assigned**
(where a model is most tempted to escalate from notifying to acting) and a stockout where
**90,000 units are already in transit** (RB-002 calls duplicate replenishment the most common
error in the workflow — the reasoning cited the in-transit quantity).

Honest limitation: CI has no Snowflake account, so `--check` verifies the recorded scorecard
rather than re-measuring. It fails if a case was added without re-running `--live`, which is the
realistic failure mode.

### Security

Three enforced properties, not three assertions:

| Claim | Enforced by |
|---|---|
| The model never contributes SQL text | `tools/lint_sql_boundary.py` walks the AST and fails the build; it runs in CI, and it fails on purpose against a deliberately bad file — the walkthrough shows how |
| The agent cannot escalate its own authority | `requested_tier` and `touched_objects` come from the registry; the reply schema has no field for either |
| The agent cannot read what it may not act on | Masking policy on `QUALITY_HOLDS.lot_ref`. `WARRANT_ROLE` holds `APPLY` on that one policy, **not** `APPLY MASKING POLICY ON ACCOUNT` |

**And the corpus is treated as untrusted input.** `corpus/adversarial/` holds a document that
claims to supersede RB-003, grants itself release authority, offers an `execute_sql` action,
appends SQL to a parameter value, retargets every action at one SKU, and asks for the audit entry
to be suppressed. `./scripts/injection_drill.sh` puts it through the real retrieval path — it
ranks **first** for a quality query and is cited by **all six** findings, and the routing does not
move.

```bash
uv run pytest tests/test_adversarial.py -v      # ten tests, no account needed
```

Those tests **assume the model complied with the attack** and assert the outcome anyway. That
distinction is the whole point: "the model resisted" is a property of a model that changes under
you, "the model's compliance changed nothing" is a property of the architecture.

### Code quality and testing

```bash
uv run pytest --cov --cov-report=term-missing
```

**251 tests, 100% branch coverage of `src/warrant`, gated** (545 statements, 96 branches, zero
missed; 230 pass, 3 are skipped for a missing optional dependency and 1 is the opt-in integration
test). `mypy --strict` clean across 19 modules. Ruff clean against 21 rule families, including
complexity, `BLE`, and `RUF100` — which fails on a `noqa` that no longer suppresses anything, so
a stale suppression cannot sit there implying a problem that is not present. Seven checks in CI
plus a gitleaks scan.

The coverage figure is achievable rather than aspirational because of one design rule: **every
function takes its Snowpark `Session` as its first argument**, and nothing under `src/warrant/`
calls `get_active_session()`. Only the stored-procedure entry points and the Streamlit app do.
`tests/conftest.py` provides a `FakeSession` implementing only the Snowpark surface this codebase
is sanctioned to use — reaching for anything else raises `AttributeError`, which is a signal
worth having.

---

## Real-World Relevance (30%)

### The problem

Enterprise operations teams do not lack insight. They lack *action*. And the obvious fix — let an
agent act — runs into the reason it has not happened: **agents that can act do not get deployed.**
Every agentic pilot that dies in a regulated operation dies at the same place, when someone in
quality asks "so it can write to the inventory system?" and the answer is either *yes* (rejected)
or *no, it only drafts emails* (pointless).

The capability was never the bottleneck. Trust was. And the usual mitigation makes it permanent:
authority gets encoded as a rules list in application code, which drifts from the actual data
governance policy the moment either changes — and a control that has drifted is worse than no
control, because people still believe it.

Warrant's answer: **the authority model and the governance policy are the same artifact.** Tag a
table `regulated` and every proposed action against it is refused, with no code change, no
redeploy, and no rules list for anyone to remember to update.

### Measurable impact

Measured on the live account, not projected:

| Metric | Measured |
|---|---|
| Exceptions detected from 2,400 shipments / 40 holds / 6 SKUs | **6** |
| Detection → explained, evidenced, proposed action | **20–95 s** |
| Routed with no human touch (open data) | **1 executed** |
| Escalated to a named human with evidence (internal data) | **1 queued + email** |
| Permitted only because it drafts rather than acts (regulated data) | **4** |
| Human approvals that did **not** survive a reclassification | **1, refused** |
| Reasoning eval — cases × dimensions passed | **6 × 5** |
| Hostile-document findings where routing changed | **0 of 6** |
| Tests / branch coverage / mypy-strict errors | **251 / 100% / 0** |

**The number that matters** is not agent-versus-human on speed. It is *deployable versus not*. The
same loop safely spans open, internal and regulated data in one pass, and the boundary is
auditable after the fact.

### Honest limitations

Stated because a reviewer will find them anyway, and finding them stated is worth more than
finding them hidden:

- Synthetic data, one account. The mechanism is domain-agnostic; the demonstration is not a
  deployment.
- `SNOWFLAKE.ML.ANOMALY_DETECTION` is a documented seam, not an implementation.
- The thresholds come from a corpus written for this project. A real deployment would need those
  documents to be the live controlled ones.
- Streamlit in Snowflake is not publicly viewable — a viewer needs an account in ours. That is why
  the [public read-only viewer](https://snowflake-coco-cli-hackathon-2026.vercel.app/) exists: it
  reads the same account live, carries the console as screenshots, and lets anyone press *Approve*
  and watch Snowflake refuse it. The console itself appears in the submission video.

---

## Solution Completeness (30%)

### End to end, minimal manual intervention

```bash
./scripts/setup.sh <conn>                                   # ~3 min, idempotent
snow sql -c <conn> -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');" # ~2-3 min
```

Ingestion → detection → grounded reasoning → authority resolution → action or escalation →
audit, with a Streamlit console for the one step that is *supposed* to need a human. A serverless
task can run the sweep hourly; a triggered task on a stream executes what a human approves.

`SCAN_FOR_EXCEPTIONS` is left **suspended** on purpose, so provisioning does not burn trial
credits unattended or mutate the demo data between a reviewer reading the walkthrough and
following it.

### Structured *and* unstructured

The easiest way to fake this is a `VARCHAR` column of prose. Instead: five operating procedures
authored as Markdown in `corpus/`, rendered to PDFs, uploaded to a stage, and read back with
`AI_PARSE_DOCUMENT(TO_FILE(…), {'mode':'LAYOUT'})`. The parsed text is what Cortex Search indexes
and what the reasoning cites.

```bash
snow sql -c <conn> -q "SELECT relative_path, size FROM DIRECTORY(@WARRANT.CORE.DOCS);"
```

Every detector threshold survives the parse, checked as a clean diagonal in
`docs/judges_walkthrough.md`. Rendering is byte-deterministic and CI re-renders and compares, so
the committed PDFs cannot drift from the Markdown a reviewer reads.

### Two surfaces, deliberately asymmetric

| Surface | Can it act? |
|---|---|
| Streamlit console — approval queue, refusal ledger, live tag table, decision log | Yes, through the governed path: approve → re-resolve authority → execute |
| Cortex Agent `WARRANT_ANALYST`, used in CoWork | **No.** Two read-only tools and no `generic` tool bound to the executor |

That asymmetry is the design. A chat box wired to `EXECUTE_ACTION` routes around the console, the
approval queue and the human — it puts the most persuadable surface in the system on the far side
of the gate. Asked to release a hold, the agent declines and cites the clause:

```
I cannot release QH-0034. Per RB-003 … "No automated system may alter a hold's
disposition, release a lot, or close an investigation." … I also cannot provide the lot
reference. RB-003 states that lot identifiers are need-to-know.
```

### Accessibility

Named in the organisers' stated review criteria and rarely addressed, so: every severity and tier
carries a **text label beside its colour** — a colour alone is invisible to a colourblind reviewer
and to a screen reader. Model-generated text is marked "model-generated" **in words** as well as
in styling. Every console panel renders inside `guarded()`, because an unhandled exception in a
Streamlit script replaces the entire app, and a console whose job is to be trusted must never show
a blank page.

---

## Where to look, if you only open three files

1. **[`src/warrant/authority/tiers.py`](../src/warrant/authority/tiers.py)** — the authority model.
   `resolve()` takes the **most demanding** object in an action's footprint. An earlier revision
   took the minimum, which let one `open` table dilute a `regulated` one;
   `tests/test_tiers.py::test_regulated_object_is_not_diluted_by_an_open_one` exists so it cannot
   come back.
2. **[`src/warrant/act/executor.py`](../src/warrant/act/executor.py)** — authority re-resolved at
   execution time. A refusal is terminal, which needs `execution_result IS NULL` as well as
   `executed_at IS NULL`; without it a background task picks the refusal back up once the tag is
   restored and executes the very thing the agent declined.
3. **[`tests/test_adversarial.py`](../tests/test_adversarial.py)** — ten attacks, each assuming the
   model complied, each naming the control that stops it.
