# Warrant — slide-by-slide deck content

Build source for the submission PPT. **Gitignored** — this is working material, not a judge-facing
document.

**Target: 9 slides.** Slide 1 is the organizer's mandated cover. Slide 2 must carry all three
sections they name (Problem Brief · Architecture Diagram · Impact Statement) — but nothing stops
those from spanning several slides, and a judge reading eight breathing slides takes more away than
from one dense one. Slides 3–8 *are* those three sections, expanded.

Every figure below was measured on the live account. Nothing is projected, illustrative or rounded
in our favour. Where something is unproven, it says so — slide 8 exists for that.

**Design notes for the build.** The organizer's template supplies branding as a full-bleed image:
navy header bar, gradient footer. Content lives between them. Canvas is **10 × 5.625 in**, not 13.3.
Their palette: navy `#0A1B33`, cyan `#00B8A9`. Use the semantic accents this project uses everywhere
else — green `#15803D` acts, amber `#B45309` needs a human, red `#B91C1C` refused. No accent lines
under titles, no decorative stripes.

---

## Slide 1 — Cover *(template's own layout, just fill the fields)*

```
Team Name         : Argmax
Team Leader Name  : Sathya T
Team Size         : 1
Problem Statement : PS1 — Intelligent Workflow Automation Agent
```

One line beneath, if it fits above the footer:

> **Warrant** — a governed autonomous operations agent on Snowflake. *No action without a warrant.*

---

## Slide 2 — Problem Brief

**Eyebrow:** PROBLEM BRIEF
**Title:** Agents that can act don't get deployed

**Lead paragraph**

Enterprise operations teams do not lack insight. They lack *action*. Someone still has to notice the
red KPI, work out why, decide what to do, and do it — analytics stops exactly where the work starts.

**The paragraph that does the work**

Every agentic pilot that dies in a regulated operation dies at the same place. Someone in quality
asks *"so it can write to the inventory system?"* and the answer is either **yes** (rejected) or
**no, it only drafts emails** (pointless). The capability was never the bottleneck. **Trust was.**

**And the usual fix makes it permanent**

Authority gets encoded as a rules list in application code. It drifts from the real data-governance
policy the moment either changes — and a control that has drifted is worse than no control, because
people still believe it.

**Three personas, as three cards**

| Persona | What they need |
|---|---|
| Operations analyst | Owns the exception queue. Wants routine responses to stop reaching them at all. |
| Quality / compliance owner | A defensible answer to "what is this agent allowed to do, and who decided?" |
| Data platform owner | Refuses to maintain a second copy of the access policy inside an application. |

**Domain footer:** Supply chain and manufacturing operations. 100% synthetic data — 2,400 shipments,
6 suppliers, 40 quality holds, 6 SKUs, 5 operating procedures.

---

## Slide 3 — The mechanism *(this is the differentiator; give it a whole slide)*

**Eyebrow:** THE MECHANISM
**Title:** Authority is read from the data's own governance tags

**Lead**

An action's permission tier is resolved at runtime from the Snowflake `SENSITIVITY` object tag on
every table it touches — read live with `SYSTEM$GET_TAG`, never cached, never from `ACCOUNT_USAGE`
(which lags two hours). Retag a table and the agent's next decision changes. No code change, no
redeploy, no rules list.

**Table — the whole model in five rows**

| Tag on the data | The agent may | Observed in one pass |
|---|---|---|
| `open` | Act unsupervised (L2) | SUP-002 — supplier case opened, no human |
| `internal` | Act only with approval (L3) | SKU-1003 — queued for a human + email |
| `regulated` | Read and explain, never act (L4) | 4 quality holds — drafted only |
| *untagged* | Treated as unclassified, **not** cleared | RUNBOOKS — demands approval |

Sub-line under the table: *The most demanding object in an action's footprint binds — never the
least, or one `open` table could dilute a `regulated` one.*

**And it is not one hardcoded tag — say this out loud, it is the first objection**

A second axis, `RETENTION`, is already live and independent. Same table, sensitivity untouched at
`open`: setting `retention = 'legal_hold'` on `OPS_REQUESTS` turns `open_supplier_case` from *acts
unsupervised* into *refused outright*, and the rationale names retention rather than sensitivity —
because pointing a reviewer at the wrong tag sends them to change the wrong thing. Adding a third
axis is a row in `POLICIES`, not a control-flow change.

**Red callout box — THE CLAIM THAT MATTERS**

> Authority is resolved **again at execution time**. Approve an action, reclassify the table it
> touches, run the executor — it refuses, and records why. A human's own approval does not survive
> a governance change, and nothing was deployed in between.

---

## Slide 4 — Architecture

**Eyebrow:** ARCHITECTURE
**Title:** Six Agent Skills, one loop, everything inside Snowflake

**Put the sequence diagram here, not the flowchart.** The flowchart shows what connects to what; the
sequence diagram shows *when*, and the ordering is the argument. Export it from the README's
`sequenceDiagram` block. If space forces one only, the sequence wins.

**The five skills, as a table**

| # | CoCo Agent Skill | What it owns | Feeds |
|---|---|---|---|
| 1 | `detect-anomaly` | Dynamic-table baselines → `EXCEPTIONS`. Every threshold quoted from a runbook clause, deduplicated per RB-005 | 2 |
| 2 | `investigate-root-cause` | `AI_COMPLETE` under a JSON schema, grounded by Cortex Search over the parsed procedures | 3 |
| 3 | `classify-authority` | `SYSTEM$GET_TAG` live, then `resolve()` — most demanding object binds | 4 |
| 4 | `propose-action` | Typed, parameterised, reversible actions from a closed registry | 5 |
| 5 | `orchestrate-loop` | Runs 1–4 idempotently with a circuit breaker; every path ends in an audit row | audit |

A sixth, `operate-warrant`, is not a phase — it is how you drive all five from a terminal, and it
gets its own slide.

Each is a real file in `.cortex/skills/`, and each names the module implementing it — so the skill
and the code cannot drift apart silently.

**Two side panels**

*Structured and unstructured.* Five tables carrying three classifications plus one deliberately
untagged. Five operating procedures authored as Markdown, rendered to PDFs, staged, and read back
with `AI_PARSE_DOCUMENT` — parsed documents, not a `VARCHAR` of prose. That parsed text is what
Cortex Search indexes, what the reasoning cites, **and** where every detector threshold comes from,
so a conclusion can cite the clause that set the threshold that raised it.

*Two controls, different jobs.* The `SENSITIVITY` tag decides what the agent may **do**. A masking
policy on `QUALITY_HOLDS.lot_ref` decides what it may **see** — so it can report a hold is 82 days
old and cannot report which physical lot it is, because identifying the lot is what would make the
record actionable. Same table, same query, two answers by role.

---

## Slide 5 — Impact

**Eyebrow:** IMPACT
**Title:** Measured on the live account, not projected

**Five stat tiles across the top**

| 6 | 20–95s | 5 | 1 | 3 |
|---|---|---|---|---|
| EXCEPTIONS FROM 2,400 SHIPMENTS | DETECTION TO PROPOSED ACTION | HANDLED WITH NO HUMAN TOUCH | ESCALATED WITH EVIDENCE | REFUSED, WITH A REASON |

Colours: first two navy, then green / amber / red.

**Supporting table**

| What was measured | Result |
|---|---|
| Reasoning evaluation — scenarios × scoring dimensions passed | 6 × 5, all |
| Hostile document planted in the grounding corpus: findings that cited it / routings it changed | 6 of 6  /  **0** |
| Statistical separation of the planted anomaly (robust *z*) | −3.63 vs −0.46 next-worst |
| Tests / branch coverage / mypy-strict errors | 251 / 100% / 0 |
| Unattended task runs in 24h / failed | 34 / **0** — both tasks started, sweep hourly |

**Navy callout — THE NUMBER THAT MATTERS**

> Not agent-versus-human on speed — **deployable versus not**. An agent with blanket write access
> isn't 10× faster than a review meeting; it is never switched on. The same loop safely spans open,
> internal and regulated data in one pass, and the boundary is auditable after the fact.

---

## Slide 6 — Why you can believe it

**Eyebrow:** VERIFICATION
**Title:** Every claim here is checkable without a Snowflake account

**Lead:** Clone the repository and run one command. Seven gates, all of them in CI.

| The claim | What enforces it |
|---|---|
| The model never contributes SQL text | An AST lint fails the build if any module composes SQL from runtime data — and it fails **on purpose** against a deliberately bad file |
| The agent cannot escalate its own authority | Tier and footprint come from the registry; the model's reply schema has no field for either |
| It cannot read what it may not act on | A masking policy on one column, with `APPLY` on that policy only — not on the account |
| The reasoning is not hard-coded | Six scenarios scored on five dimensions, recorded and gated in CI |
| The documentation is not stale | A checker runs the project's own tools and fails if a counted claim disagrees with the repository |

**Teal callout — AND THE CORPUS IS TREATED AS UNTRUSTED INPUT**

> A planted document claims to supersede RB-003 and grant the agent release authority. It ranks
> **first** for a quality query and is cited by **all six** findings — and the routing does not move.
> Ten tests then **assume the model complied** and assert the outcome anyway. *"The model resisted"*
> is a property of a model that changes under you; *"the model's compliance changed nothing"* is a
> property of the architecture.

---

## Slide 7 — Driven from the CLI *(new — do not cut this one)*

**Eyebrow:** COCO CLI + MCP
**Title:** The whole agent is an MCP server, and CoCo operates it

This is the slide that answers *"where does CoCo CLI actually come in?"* — Technical Execution is
40% of the score and names *"strong use of Snowflake CoCo CLI, Agent Skills and tools"* explicitly.

**Screenshot:** `docs/images/web/coco-cli.png` — it carries the whole slide on its own if space is
tight. Otherwise use the two tables below and put the callout under them.

| | |
|---|---|
| **13 tools** | 11 annotated `readOnlyHint: true`, 2 that act. `execute_approved_action` declares `destructiveHint: true`, because it is. |
| **5 resources** | `warrant://governance/tags`, `capabilities`, `audit/recent`, `runbooks`, `runbooks/{doc_id}` — each with a tool twin, because not every client supports resources. |
| **6 Agent Skills** | The five loop phases plus `operate-warrant`. |

**Red callout — THE INVARIANT**

> **No tool on this server accepts an authority tier.** A tool taking `tier` as a parameter would
> hand the model the one decision the design exists to keep away from it. Every tool resolves the
> tier itself from the live tag — so prompt-engineering the model into higher authority has no
> parameter to aim at. Asserted by a test that walks every registered tool's live input schema.

**And the server holds no credential of its own.** It reads the same
`~/.snowflake/connections.toml` that `snow` and `cortex` do, so it inherits the operator's identity
rather than acquiring one. An agent should not be able to reach further than the person running it.

The server's `instructions` tell the model this before it calls anything:

> *"You cannot choose an action's authority… If you believe an action should be permitted and
> Warrant refuses it, the answer is to change the tag through governance — not to retry, not to
> rephrase, and not to look for another tool."*
> *"A refusal is a result, not an error."*

---

## Slide 8 — Two surfaces, deliberately asymmetric

**Eyebrow:** SOLUTION COMPLETENESS
**Title:** Where a decision can be made, and where it cannot

| Surface | Can it act? |
|---|---|
| **Streamlit console, inside Snowflake** — approval queue, capability manifest, replay, refusal ledger, live tag table | **Yes**, through the governed path: approve → re-resolve authority → execute. Runs on the reviewer's own Snowflake identity, so an approval is attributable to a person. |
| **Public web viewer** (Next.js on Vercel) — same evidence, live from Snowflake | **No — and it lets you prove that yourself.** The approve, reject and defer buttons are live and send the real statements. Snowflake refuses them in front of you. |
| **Cortex Agent in CoWork** — conversational, over Cortex Search + Cortex Analyst | **No.** Two read-only tools and no `generic` tool bound to the executor. |

**The two refusals differ, and the difference is the slide's best moment**

| Press | Snowflake answers | Why |
|---|---|---|
| Reject / Defer | `SQL access control error: Insufficient privileges to operate on table 'PENDING_ACTIONS'` | the role can see the queue and is told no |
| Approve | `SQL compilation error: Unknown user-defined function WARRANT.CORE.EXECUTE_ACTION` | without `USAGE`, Snowflake will not concede the executor exists |

Denial by non-disclosure is the stronger of the two: the role cannot be talked into calling
something it cannot name. Both statements bind an `action_id` that cannot exist, so neither would
do anything even if a grant were mis-applied — the demonstration cannot become the incident it
describes.

**If you screenshot this, screenshot the whole panel.** The page reports the result as a *passing
check* — green, ticked, "the boundary held" — and keeps Snowflake's error text inside it labelled
as verbatim. Cropped to just the red block it reads as a broken demo, which is the one way to
lose the point of the slide.

**The point to land:** that asymmetry is the design, not a limitation. A chat box wired to
`EXECUTE_ACTION` routes around the console, the queue and the human — it puts the most persuadable
surface in the system on the far side of the gate. Approving is a governed act, so it belongs only
to the surface that has an identity.

**Add the live URL prominently:** `snowflake-coco-cli-hackathon-2026.vercel.app`

---

## Slide 9 — Beyond the demo, and what isn't proven

**Eyebrow:** BEYOND THE DEMO
**Title:** It generalises — and here is what is not proven yet

**Left panel — SCALES WITHOUT REWRITING**

- Detection is set-based — one `MERGE` per detector, so cost tracks data volume, not exception
  count. Six to six thousand adds no round trips.
- Governing a new table is `ALTER TABLE … SET TAG`. No code change.
- Adding an action is one registry entry; invariant tests then force it to declare its footprint,
  bind its parameters in placeholder order, and state its undo path.
- A circuit breaker caps unsupervised actions per pass, so a detector bug produces approval requests
  rather than a thousand actions.
- Serverless tasks mean an idle schedule costs nothing.

**Right panel — HONEST LIMITATIONS**

- Synthetic data, one account. The mechanism is domain-agnostic; the demonstration is not a
  deployment.
- `SNOWFLAKE.ML.ANOMALY_DETECTION` is a documented seam, not an implementation — a threshold
  traceable to a procedure is more defensible to an auditor than a score that cannot cite one.
- Thresholds come from a corpus written for this project. A real deployment needs those documents to
  be the live controlled ones.
- Streamlit in Snowflake cannot be shared publicly, which is why the read-only web viewer exists.

**Closing line across the bottom**

> `SENSITIVITY` is one tag, and the same runtime lookup already reads a second — `RETENTION` is
> live, independent, and refuses an action on an `open` table. Residency or contractual restriction
> would bind the same way. The loop needs a classified table and an action registry, **not a supply
> chain.**

`github.com/tsathya98/snowflake-coco-cli-hackathon-2026`

---

## Screenshots — which file goes on which slide

All re-captured from the deployed site after the final round of changes, at 1440 CSS px, `deviceScaleFactor: 2`, so every file is
2880px wide and survives a projector. Section shots are clipped to the section's measured bounding
box, so nothing is cut mid-heading.

| File | Slide | Why this one |
|---|---|---|
| `web/hero.png` | 1 or 2 | The claim and the live tag resolution in one frame. Strongest single image in the set. |
| `web/hero-light.png` | — | Light-theme alternative if the template's background fights the dark one. |
| `web/one-pass.png` | 5 (Impact) | The detection chart. SUP-002's line going through the RB-001 threshold is the most legible "something happened here" in the deck. |
| `web/evidence.png` | 3 or 8 | Evidence beside reasoning, the live controls, **and the refusal already fired** — captured with the green verdict panel showing, so it needs no explanation on the slide. |
| `web/coco-cli.png` | 7 | Carries slide 7 on its own if space is tight. |
| `web/tested.png` | 6 | The planted attack and the scored reasoning, side by side. |
| `web/authority-whatif.png` | 3 | The capability manifest plus the policy what-if. |
| `web/replay.png` | 6 | Decision replay — the auditor's question. |
| `web/refusals.png` | 5 | The refusal ledger. |
| `web/governance.png` | 3 | The live tag table, light theme. |
| `web/unattended.png` | 5 or 9 | The 24-hour task timeline — the picture of "nobody was present". Both tasks started, **0 failed**, hourly sweep visibly running. |
| `web/mobile.png`, `web/mobile-refusal.png` | 8 | Only if you want to show it works on a phone. Usually cut. |
| `console-headline.png`, `evidence-and-reasoning.png`, `refusal-banner.png`, `queue-already-decided.png`, `authority-manifest.png`, `whatif-revocation.png`, `replay.png`, `column-governance.png` | 8 | The Streamlit console — the governed surface. `refusal-banner.png` is the one to keep if you keep one: a human approved it and it was refused anyway. |

All under `docs/images/`. Web shots are in `docs/images/web/`.

---

## If you are cut to three slides

Keep **2 (problem)**, **3 (the mechanism)**, **5 (impact)**. Slide 3 is the one nobody else will
have. Everything on 4, 6, 8 and 9 is supporting evidence for it.

**If you are cut to four, add 7 (CoCo CLI).** It is the only slide that answers the 40% Technical
Execution criterion directly, and it is the one a judge scanning for "did they actually use the
CLI?" is looking for.

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

---

## The one line to land, wherever it fits

> Everyone in this track will show you an agent that acts. This is one that **declines** — and whose
> declining does not depend on the model choosing to.
