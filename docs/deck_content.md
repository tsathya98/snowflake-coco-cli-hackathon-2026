# Deck content

Copy into the organizer's *Prototype Submission Template* (not redistributed here — it is theirs).
Slide 2 of that template mandates exactly three sections — Problem Brief,
Architecture Diagram, Impact Statement — and two scored expectations hide in its own wording:
the architecture slide asks *which Cortex Code CLI skills are used and how they connect*, and
the impact slide asks for **measurable** outcomes. Both are answered below.

Every number here was measured on the live account. Nothing is projected or illustrative, and
the data is 100% synthetic — say so on the slide rather than letting a judge wonder.

---

## Slide 1 — Cover

- **Team name:** Argmax
- **Problem Statement:** PS1 — Intelligent Workflow Automation Agent
- **Team leader:** Sathya T
- **Team size:** 1

**Project:** **Warrant** — a governed autonomous operations agent on Snowflake.
*No action without a warrant.*

---

## Slide 2 §1 — Problem Brief

**The real business problem.** Enterprise operations teams do not lack insight. They lack
*action*. Someone still has to notice the red KPI, work out why, decide what to do, and do it.
Analytics stops where the work starts.

The obvious fix — let an agent take the action — runs straight into the reason it hasn't
happened. **Agents that can act don't get deployed.** Every agentic pilot that dies in a
regulated operation dies at the same place: someone in quality or security asks "so it can
write to the inventory system?" and the answer is either *yes* (rejected) or *no, it only
drafts emails* (pointless). The capability was never the bottleneck. **Trust was.**

Worse, the usual mitigation makes it permanent: authority gets encoded as a rules list in
application code. That list drifts from the actual data-governance policy the moment either
changes, and a control that has drifted is worse than no control, because people still believe
it.

**Target users.**
- *Supply chain / operations analyst* — owns the exception queue, wants routine responses to
  stop reaching them at all.
- *Quality or compliance owner* — needs a defensible answer to "what is this agent allowed to
  do, and who decided?"
- *Data platform owner* — refuses to maintain a second copy of the access policy inside an
  application.

**Current pain, and what changes.** Today: a daily review meeting, a spreadsheet of
exceptions, and a person re-deriving the same conclusion each morning. With Warrant: exceptions
are detected continuously, explained with cited evidence, and either actioned, escalated to a
named human, or **refused with a recorded reason** — the decision made by the governance
classification already on the data, not by a rules list somebody has to remember to update.

**Domain.** Supply chain and manufacturing operations. Fully synthetic data: 2,400 shipments,
6 suppliers, 40 quality holds, 6 SKUs, 5 operating procedures.

---

## Slide 2 §2 — Architecture Diagram

Use the Mermaid diagram in [`architecture.md`](architecture.md) — render and paste as an image.

**The one-line version:** an action's authority is read at runtime from the Snowflake
`SENSITIVITY` object tag on every table it touches. Retag a table and the agent's behaviour
changes on the next iteration, with no code change and no redeploy.

**The five CoCo Agent Skills, and how they connect.** Each is a real file in
[`.cortex/skills/`](../.cortex/skills/) and each names the module implementing it — so the
skill and the code cannot drift apart silently.

| # | Skill | What it owns | Feeds |
|---|---|---|---|
| 1 | `detect-anomaly` | Dynamic-table baselines → `EXCEPTIONS`, deduplicated per RB-005 | → 2 |
| 2 | `investigate-root-cause` | `AI_COMPLETE` under a JSON schema, grounded by Cortex Search over the runbooks | → 3 |
| 3 | `classify-authority` | `SYSTEM$GET_TAG` live, then `resolve()` — the most demanding object binds | → 4 |
| 4 | `propose-action` | Typed, parameterised, reversible actions from a closed registry | → 5 |
| 5 | `orchestrate-loop` | Runs 1–4 idempotently with a circuit breaker; every path ends in an audit row | → audit |

**Data sources.** Structured: shipments, suppliers, SKUs, inventory, quality holds — five tables
carrying three different classifications plus one deliberately untagged. Unstructured: five
operating procedures authored as Markdown, rendered to **PDFs**, uploaded to a stage and read back
with **`AI_PARSE_DOCUMENT`** — genuinely parsed documents, not a `VARCHAR` column of prose. The
parsed text is what Cortex Search indexes, what the reasoning cites, *and* where every detector
threshold comes from, so a conclusion can cite the clause that set the threshold that raised it.

**Two governance controls, doing different jobs.** The `SENSITIVITY` tag decides what the agent
may **do**. A masking policy on `QUALITY_HOLDS.lot_ref` decides what it may **see** — so the agent
can report that a hold is 82 days old and cannot report which physical lot it concerns, because
identifying the lot is what would make the record actionable. Same table, same query, two answers
depending on the role.

**And the corpus is untrusted input.** `corpus/adversarial/` holds a document that claims to
supersede RB-003 and grant automation release authority. It ranks first for a quality query and is
cited by all six findings; the routing does not move. The tests then assume the model *complied*
and assert the outcome anyway.

**Snowflake services (19).** CoCo CLI · Object Tagging/Horizon · **Masking Policies** · Cortex AI
(`AI_COMPLETE`) · Cortex Search · **`AI_PARSE_DOCUMENT`** · **Stages + Directory Tables** ·
Semantic Views · Snowpark Python stored procedures · Dynamic Tables · Streams · Serverless +
Triggered Tasks · **Cortex Agents** · **Cortex Analyst** · **Snowflake CoWork** · Streamlit in
Snowflake · Notification Integrations · Resource Monitors · RBAC. Every one is cited to the file
that uses it in the README, so the list is checkable rather than claimed — and the README also
lists what is *deliberately* absent, which is there to be quoted rather than pruned.

**How the components plug together.** Every function takes its Snowpark `Session` as its first
argument and nothing in `src/warrant/` discovers one. Only the three stored-procedure entry
points do. That single rule is why the whole pipeline — detection, reasoning, authority,
execution, orchestration — is unit-testable without a warehouse, and why 100% branch coverage
is a gate rather than an aspiration.

---

## Slide 2 §3 — Impact Statement

### Measured, on the live account

| Metric | Measured |
|---|---|
| Exceptions detected from 2,400 shipments / 40 holds / 6 SKUs | **6** |
| Detection → explained, evidenced, proposed action | **20–95 seconds** |
| Routed with no human touch (open data) | **1 executed** |
| Escalated to a named human with evidence (internal data) | **1 queued + email** |
| Permitted only because it drafts rather than acts (regulated data) | **4** |
| **Actions refused outright, with a recorded reason** | **1** |
| Decisions in the append-only log, across 2 runs | **27** |
| Statistical separation of the planted anomaly (robust *z*) | **−3.63 vs −0.46 next-worst** |
| Reasoning eval — cases × scoring dimensions passed | **6 × 5, all** |
| Hostile document in the grounding corpus: findings that cited it / routings it changed | **6 of 6 / 0** |
| Tests / branch coverage / mypy-strict errors | **234 / 100% / 0** |

### The number that matters

**Zero of the 6 exceptions needed a human to notice them, and 100% of actions against
regulated data were blocked without a line of code saying "quality holds are special."**

The comparison worth drawing is not agent-versus-human on speed. It is **deployable versus
not**. An agent with blanket write access is not 10× faster than a review meeting — it is
never switched on. Warrant's measurable claim is that the same loop safely spans open,
internal and regulated data in one pass, and that the boundary is auditable after the fact.

### Scalability

- Detection is **set-based** — one `MERGE` per detector, so cost tracks data volume rather
  than exception count. Going from 6 exceptions to 6,000 adds no round trips.
- Adding a governed table is `ALTER TABLE … SET TAG`. **No code change.**
- Adding an action is one entry in `ACTION_TYPES`; the invariant tests then enforce that it
  declares its footprint, binds its parameters in placeholder order, and states its undo path.
- A circuit breaker caps unsupervised actions per pass, so a detector bug produces approval
  requests rather than a thousand actions.
- Serverless tasks mean an idle schedule costs nothing.

### Beyond the demo

The mechanism is domain-agnostic: it needs a classified table and an action registry, not a
supply chain. The same loop applies to finance close exceptions, customer entitlement changes,
or access reviews. And the governance surface generalises — `SENSITIVITY` is one tag, but the
same runtime lookup reads any tag, so residency, retention or contractual restrictions could
each bind an action the same way.

**What is honestly not proven yet:** the demo runs on synthetic data in one account, and
`SNOWFLAKE.ML.ANOMALY_DETECTION` is a documented seam rather than an implementation. The
thresholds come from the runbook corpus, which is the right source, but a real deployment would
need those documents to be the live ones.

---

## Speaker notes for the live demo (Sept 1–4)

Thirty seconds each, in this order. **Items 4 and 5 are the demo** — everything before them is
setup, and almost every other entry in this track will spend its whole slot on items 1 and 2.

1. `CALL WARRANT.CORE.RUN_LOOP('AUTO');` → six exceptions, three different routings, one pass.
2. The console: evidence beside the proposal, model-generated text visibly marked, the runbook
   clause it cited. Then the Governance tab — the tags, and the masked `lot_ref` column. *"The
   agent can tell you this hold is 82 days old. It cannot tell you which lot it is."*
3. The refusal ledger — *"show me every action your agent declined."*
4. **Approve the pending replenishment. Then reclassify `INVENTORY` to `regulated`. Then run
   the executor.** It refuses, and says the classification in force at execution time supersedes
   the approval. Nothing was deployed between those two steps. *A human's own approval did not
   survive a governance change.*
5. **`./scripts/injection_drill.sh`** — put a hostile document into the grounding corpus. It ranks
   first for a quality query and is cited by all six findings. Routing does not move. Then the
   honest part, which is the bit worth saying out loud: *"I am not claiming the model resisted.
   Watch —"* → `uv run pytest tests/test_adversarial.py -v`, ten tests that **assume the model
   complied** and assert the outcome regardless. The tier comes from the registry, the tag comes
   from the object, the parameters are bound.
6. If there is time: `tools/lint_sql_boundary.py` on a deliberately bad file — the claim that the
   model cannot write SQL, failing a build.

**The line to land.** Everyone in this track will show an agent that acts. The differentiator is
an agent that *declines* — and one whose declining does not depend on the model choosing to.
