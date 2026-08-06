# Warrant — the deck, slide by slide

Build source for the submission PPT. Working material rather than a judge-facing document — it is
tracked so it travels between machines, and written knowing it is public.

## Six slides. Here is why, measured rather than guessed

The organiser's template (`docs/submission_template/`) is six physical slides, and reading its XML
settles the question:

| # | What is actually on it |
|---|---|
| 1 | Cover — four fields to fill: team name, problem statement, team leader, team size |
| 2 | **Instructions to you**, not content: *"Submission Guidelines: things to add on the submission deck — 1. Problem Brief, 2. Architecture Diagram, 3. Impact Statement"* |
| 3, 4, 6 | Blank canvases. Branding art only, no placeholders |
| 5 | Blank, captioned **"Additional Slide"** — singular |

So slide 2 is a checklist, not a section. **Delete it before submitting** — leaving the organiser's
own instructions in your deck reads as not having read them. That leaves the cover plus four
canvases, and the three mandated sections have to live in them.

**Build exactly these six.** One section per slide, and their "Additional Slide" allowance used
twice — once for the thing that carries 40% of the score, once for the close:

| Slide | Section | Why it earns the space |
|---|---|---|
| 1 | Cover | Mandated |
| 2 | **Problem Brief** | Mandated. Opens with a scene, not a thesis |
| 3 | **Architecture Diagram** | Mandated. The mechanism *is* the architecture, so they share a slide |
| 4 | **Impact Statement** | Mandated. Measured figures only |
| 5 | *Additional* — CoCo CLI + MCP | Technical Execution is 40% and names CLI, Skills and tools explicitly |
| 6 | *Additional* — the boundary, and what isn't proven | The close, plus stated limitations, which judges reward |

If you are cut to **three**: keep 2, 3, 4. Slide 3 is the one nobody else will have. If cut to
**four**, add 5 — it is the only slide that answers the 40% criterion head-on.

Every figure below was measured on the live account. Nothing is projected, illustrative or rounded
in our favour. Where something is unproven, it says so — slide 6 exists for that.

**Design notes.** The template supplies branding as a full-bleed image: navy header bar, gradient
footer. Content lives between them. Canvas is **10 × 5.625 in**, not 13.3. Their palette: navy
`#0A1B33`, cyan `#00B8A9`. Use the semantic accents this project uses everywhere else — green
`#15803D` acts, amber `#B45309` needs a human, red `#B91C1C` refused. No accent lines under titles,
no decorative stripes. **One idea per slide; if a slide needs a paragraph, it is two slides.**

---

## Slide 1 — Cover

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
**Title:** The automation that would actually help is the one that never ships

**Open with the scene, not the thesis.** Three numbers, large, across the top. Every one is real and
live on the deployed site:

| 82 days | 5 days | 26% |
|---|---|---|
| A QUALITY HOLD, STILL OPEN | OF STOCK COVER LEFT ON ONE SKU | ON-TIME DELIVERY AT ONE SUPPLIER |

**Say, don't write:** *"All three of these are on a dashboard right now. None of them is fixed.
Because a dashboard tells you — and then waits for a person."*

**The paragraph that does the work**

That person opens six tabs on Monday morning, works out which of the forty open holds actually
matters, writes the supplier email, raises the replenishment, files the note. Analytics stopped at
the insight. The work starts after.

An agent could do all of it. It doesn't get deployed, because in a regulated operation the first
question is always the same — **"so it can change a quality record?"** If the answer is *yes*,
nobody signs off. If the answer is *no, it only drafts emails*, it isn't worth building.

**Red callout — THE REAL BLOCKER**

> The blocker was never capability. It was **authority**. Nobody could say, in advance and in
> writing, what the agent was allowed to touch.

**Three personas, small, along the bottom**

| Operations analyst | Quality / compliance owner | Data platform owner |
|---|---|---|
| Owns the exception queue. Wants routine responses to stop reaching them at all. | Needs a defensible answer to "what is this agent allowed to do, and who decided?" | Refuses to maintain a second copy of the access policy inside an application. |

**Domain footer:** Supply chain and manufacturing operations. 100% synthetic data — 2,400
shipments, 6 suppliers, 40 quality holds, 6 SKUs, 5 operating procedures.

---

## Slide 3 — Architecture *(the mandated diagram, and the mechanism, together)*

**Eyebrow:** ARCHITECTURE
**Title:** One loop, three endings, decided by the tag on the data

The mechanism is not separate from the architecture — it *is* the architecture's point — so they
share the slide. Lead with the three lanes, then the diagram.

**The three lanes — this is the slide's best moment**

| The exception | Table it must touch | Tag | Ending |
|---|---|---|---|
| SUP-002 on-time collapsed to 26% | `SHIPMENTS` | `open` | **Handled**, nobody asked |
| SKU-1003 five days from stockout | `INVENTORY` | `internal` | **Escalated** — prepared in full, then stopped |
| QH-0034 on hold 82 days | `QUALITY_HOLDS` | `regulated` | **Refused**, and it says why |

Say out loud: *"Same code path, three endings. There is no `if table_name` anywhere in this."*

**The diagram is already rendered for you.** Both are in `docs/images/deck/`, produced from the
same mermaid source the README uses — so the deck and the repo cannot show different diagrams —
at 3× on a **transparent** background, which means they sit on the template's navy without a white
box around them.

| File | Size | Use it for |
|---|---|---|
| `deck/sequence.png` | 4434 × 2880 | **The one to use.** The approval that doesn't survive: propose → reclassify → refuse, twelve numbered steps |
| `deck/sequence-dark.png` | same | If the slide background is dark |
| `deck/architecture.png` | 7467 × 1242 | Wide and short — fits as a full-width strip under the title |
| `deck/architecture-dark.png` | same | Dark-background variant |

**Prefer the sequence diagram if you can only fit one.** The flowchart shows what connects to
what; the sequence diagram shows *when*, and the ordering is the entire argument — the tag is read
at step 1, the reclassification lands at step 4, and the second read at step 7 is what refuses it.
Regenerate after changing a README diagram with:
`node tools/render_deck_diagrams.mjs . docs/images/deck` (needs `puppeteer-core` and Chrome).

**The seven stages, as a strip under the diagram** — mark 4, 5 and 6 in amber:

`01 Watch → 02 Detect → 03 Investigate → 04 Classify → 05 Route → 06 Execute → 07 Audit`

Stages 1–3 are a pipeline any competent team would build. **Stages 4–6 are the submission.**

**Six Agent Skills, one line each** — each is a real file in `.cortex/skills/` naming the module
that implements it, so skill and code cannot drift apart silently:

`detect-anomaly` · `investigate-root-cause` · `classify-authority` · `propose-action` ·
`orchestrate-loop` — plus `operate-warrant`, which is how you drive all five from a terminal.

**Red callout — THE CLAIM THAT MATTERS**

> Authority is resolved **again at execution time**. Approve an action, reclassify the table it
> touches, run the executor — it refuses, and records why. A human's own approval does not survive
> a governance change, and nothing was deployed in between.

**If there is room, one line on each of these — all three are real and cheap to say:**

- *Structured and unstructured together.* Five procedures authored as Markdown, rendered to PDFs,
  read back with `AI_PARSE_DOCUMENT`. That parsed text is what Cortex Search indexes, what the
  reasoning cites, **and** where every detector threshold comes from — so a conclusion can cite the
  clause that set the threshold that raised it.
- *Two controls, different jobs.* The tag decides what the agent may **do**. A masking policy on
  `QUALITY_HOLDS.lot_ref` decides what it may **see** — it can report a hold is 82 days old and
  cannot report which lot, because naming the lot is what would make the record actionable.
- *It is not one hardcoded tag.* A second axis, `RETENTION`, is already live and independent:
  `legal_hold` on an `open` table turns *acts unsupervised* into *refused outright*.

---

## Slide 4 — Impact Statement

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
| Unattended task runs in 24h / failed | 34 / **0** — both tasks started, hourly sweep |
| Credits to build the entire project | 8.39 of 400 — AI functions were 6.5% of it |

**One line, not a table — the verification claim**

> Every number on this slide is a CI gate. Clone the repository, run one command, and a checker
> executes the project's own tools and fails if any figure here disagrees with the code.

**Navy callout — THE NUMBER THAT MATTERS**

> Not agent-versus-human on speed — **deployable versus not**. An agent with blanket write access
> isn't 10× faster than a review meeting; it is never switched on. The same loop safely spans open,
> internal and regulated data in one pass, and the boundary is auditable after the fact.

---

## Slide 5 — *Additional:* driven from the CLI

**Eyebrow:** COCO CLI + MCP
**Title:** The whole agent is an MCP server, and CoCo operates it

The slide that answers *"where does CoCo CLI actually come in?"* Technical Execution is 40% and
names *"strong use of Snowflake CoCo CLI, Agent Skills and tools"* explicitly. **Do not cut this.**

**Screenshot:** `docs/images/web/coco-cli.png` carries the whole slide on its own if space is
tight. Otherwise the three facts below, then the callout.

| | |
|---|---|
| **13 tools** | 11 annotated `readOnlyHint: true`, 2 that act. `execute_approved_action` declares `destructiveHint: true`, because it is. |
| **5 resources** | `warrant://governance/tags`, `capabilities`, `audit/recent`, `runbooks`, `runbooks/{doc_id}` — each with a tool twin, because not every client supports resources. |
| **6 Agent Skills** | The five loop phases plus `operate-warrant`. |

**Red callout — THE INVARIANT**

> **No tool on this server accepts an authority tier.** A tool taking `tier` as a parameter would
> hand the model the one decision the design exists to keep away from it. Every tool resolves the
> tier itself from the live tag — so prompt-engineering the model into higher authority has no
> parameter to aim at. Asserted by a test that walks every registered tool's live input schema,
> names *and* enum values.

**One line, bottom:** the server holds no credential of its own. It reads the same
`~/.snowflake/connections.toml` that `snow` and `cortex` do, so it inherits the operator's identity
rather than acquiring one. An agent should not reach further than the person running it.

---

## Slide 6 — *Additional:* the boundary, and what isn't proven

**Eyebrow:** SOLUTION COMPLETENESS
**Title:** Three surfaces, and only one of them can act

| Surface | Can it act? |
|---|---|
| **Streamlit console**, inside Snowflake | **Yes**, through the governed path. The reviewer's own identity, so an approval is attributable to a person. |
| **Public web viewer** (Next.js on Vercel) | **No — and you can prove it yourself.** The approve, reject and defer buttons are live and send the real statements. Snowflake refuses them in front of you. |
| **Cortex Agent in CoWork** | **No.** Two read-only tools, nothing bound to the executor. |

**The two refusals differ, and that difference is worth ten seconds**

| Press | Snowflake answers | Why |
|---|---|---|
| Reject / Defer | `Insufficient privileges to operate on table 'PENDING_ACTIONS'` | the role can see the queue and is told no |
| Approve | `Unknown user-defined function WARRANT.CORE.EXECUTE_ACTION` | without `USAGE`, Snowflake will not concede the executor exists |

Denial by non-disclosure is the stronger of the two: the role cannot be talked into calling
something it cannot name.

> **If you screenshot this, screenshot the whole panel.** The page reports the result as a *passing
> check* — green, ticked, "the boundary held" — with Snowflake's error text inside it labelled
> verbatim. Cropped to the red block it reads as a broken demo, which is the one way to lose the
> slide.

**Honest limitations — say these out loud, they buy credibility**

- Synthetic data, one account. The mechanism is domain-agnostic; the demonstration is not a
  deployment.
- `SNOWFLAKE.ML.ANOMALY_DETECTION` is a documented seam, not an implementation — a threshold
  traceable to a procedure is more defensible to an auditor than a score that cannot cite one.
- Thresholds come from a corpus written for this project; a real deployment needs the live
  controlled documents.

**Closing line across the bottom**

> The loop needs a classified table and an action registry — **not a supply chain.** `SENSITIVITY`
> is one tag, and the same lookup already reads a second. Residency or contractual restriction
> would bind an action exactly the same way.

`snowflake-coco-cli-hackathon-2026.vercel.app` · `github.com/tsathya98/snowflake-coco-cli-hackathon-2026`

---

## Screenshots — which file goes on which slide

All re-captured from the deployed site after the final round of changes, at 1440 CSS px,
`deviceScaleFactor: 2`, so every file is 2880px wide and survives a projector. Section shots are
clipped to the section's measured bounding box, so nothing is cut mid-heading.

| File | Slide | Why this one |
|---|---|---|
| `web/hero.png` | 1 or 2 | The claim and the live tag resolution in one frame. Strongest single image in the set. |
| `web/hero-light.png` | — | Light-theme alternative if the template's background fights the dark one. |
| `web/story-workflow.png` | **3** | The seven stages and the three lanes in one picture — the closest thing to the mandated "architecture diagram" that is also the mechanism. |
| `web/one-pass.png` | 4 | The detection chart. SUP-002's line going through the RB-001 threshold is the most legible "something happened here" in the deck. |
| `web/coco-cli.png` | **5** | Carries slide 5 on its own if space is tight. |
| `web/evidence.png` | 6 | Evidence beside reasoning, the live controls, **and the refusal already fired** — captured with the green verdict panel showing, so it needs no explanation. |
| `web/tested.png` | 4 or 6 | The planted attack and the scored reasoning, side by side. |
| `web/unattended.png` | 4 | The 24-hour task timeline. Both tasks started, **0 failed**, hourly sweep visibly running. |
| `web/authority-whatif.png`, `web/replay.png`, `web/refusals.png`, `web/governance.png` | spares | Use if a slide is thin. `refusals.png` is the merged **record** section — three refusals, the replay tiles, and the two folded tables. `replay.png` and `governance.png` are the same section with a disclosure opened, so they are tall; crop before using. |
| `web/mobile.png`, `web/mobile-refusal.png` | — | Only if you want to show it works on a phone. Usually cut. |
| `refusal-banner.png` | 6 | The Streamlit console. If you keep exactly one console shot, keep this one: a human approved it and it was refused anyway. |
| the other seven console shots | spares | `console-headline`, `evidence-and-reasoning`, `queue-already-decided`, `authority-manifest`, `whatif-revocation`, `replay`, `column-governance` |

All under `docs/images/`. Web shots are in `docs/images/web/`.

---

## Speaker notes for the live demo (Sept 1–4)

Thirty seconds each, in this order. **Items 4 and 5 are the demo** — everything before them is
setup, and almost every other entry in this track will spend its whole slot on items 1 and 2.

1. `CALL WARRANT.CORE.RUN_LOOP('AUTO');` → six exceptions, three different routings, one pass.
2. The console: evidence beside the proposal, model-generated text visibly marked, the runbook
   clause it cited. Then the Governance tab — the tags, and the masked `lot_ref` column. *"The
   agent can tell you this hold is 82 days old. It cannot tell you which lot it is."*
3. The refusal ledger — *"show me every action your agent declined."*
4. **Approve the pending replenishment. Then reclassify `INVENTORY` to `regulated`. Then run the
   executor.** It refuses, and says the classification in force at execution time supersedes the
   approval. Nothing was deployed between those two steps. *A human's own approval did not survive
   a governance change.*
5. **`./scripts/injection_drill.sh`** — put a hostile document into the grounding corpus. It ranks
   first for a quality query and is cited by all six findings. Routing does not move. Then the
   honest part, which is the bit worth saying out loud: *"I am not claiming the model resisted.
   Watch —"* → `uv run pytest tests/test_adversarial.py -v`, ten tests that **assume the model
   complied** and assert the outcome regardless. The tier comes from the registry, the tag comes
   from the object, the parameters are bound.
6. If there is time: `tools/lint_sql_boundary.py` on a deliberately bad file — the claim that the
   model cannot write SQL, failing a build.

## The one line to land, wherever it fits

> Everyone in this track will show you an agent that acts. This is one that **declines** — and whose
> declining does not depend on the model choosing to.
