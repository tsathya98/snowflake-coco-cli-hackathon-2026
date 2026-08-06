<div align="center">

<img src="docs/images/mark.svg" alt="" width="76" height="76">

# Warrant

### No action without a warrant.

**An autonomous operations agent whose permission to act is read from the Snowflake governance
tags on the data it touches — live, and again at execution time, so a human's approval cannot
outlive the policy it was granted under.**

[![CoCo CLI Hackathon 2026](https://img.shields.io/badge/CoCo_CLI_Hackathon_2026-Problem_Statement_1-29B5E8?style=for-the-badge&labelColor=555555&logo=snowflake&logoColor=white)](#the-problem)
[![Demo video](https://img.shields.io/badge/Demo_video-Watch-FF0000?style=for-the-badge&labelColor=555555&logo=youtube&logoColor=white)](https://youtu.be/krfdtg2JFNM)
[![Live demo](https://img.shields.io/badge/Live_demo-Vercel-000000?style=for-the-badge&labelColor=555555&logo=vercel&logoColor=white)](https://snowflake-coco-cli-hackathon-2026.vercel.app/)
[![Team](https://img.shields.io/badge/Team-Argmax_·_solo-D4AF37?style=for-the-badge&labelColor=555555)](#)

[![pytest](https://img.shields.io/badge/pytest-252_tests_·_100%25_branch-6E9F18?style=for-the-badge&labelColor=555555&logo=pytest&logoColor=white)](#development)
[![mypy](https://img.shields.io/badge/mypy-strict_·_0_errors-1F5082?style=for-the-badge&labelColor=555555&logo=python&logoColor=white)](#development)
[![MCP](https://img.shields.io/badge/MCP-13_governed_tools-7A77FF?style=for-the-badge&labelColor=555555)](#custom-coco-agent-skills)
[![Snowflake](https://img.shields.io/badge/Snowflake-19_services-29B5E8?style=for-the-badge&labelColor=555555&logo=snowflake&logoColor=white)](#snowflake-services-used)
[![Authority](https://img.shields.io/badge/Authority-from_object_tags-B91C1C?style=for-the-badge&labelColor=555555)](#what-warrant-does)

### ▸ [**Watch the demo — youtu.be/krfdtg2JFNM**](https://youtu.be/krfdtg2JFNM)

An end-to-end run driven from Cortex Code CLI, then the moment the whole project exists for: a
human approves a queued action, the table underneath it is reclassified, and the execution refuses
anyway.

### ▸ [**Try it live — snowflake-coco-cli-hackathon-2026.vercel.app**](https://snowflake-coco-cli-hackathon-2026.vercel.app/)

**The approve, reject and defer buttons on that page are real.** They send the statements the
governed console sends, and what comes back is Snowflake refusing them — not a disabled control.

</div>

---

## 1 · The problem, in one scene

A quality hold has been open **82 days**. A SKU is **five days** from stockout. A supplier's
on-time delivery just collapsed to **26%**.

All three are on a dashboard right now. None of them is fixed — because a dashboard tells you, and
then waits for a person. That person opens six tabs on Monday morning, works out which of the
forty open holds actually matters, writes the supplier email, raises the replenishment, and files
the note. Analytics stopped at the insight. The work started after.

An agent could do all of it. It doesn't get deployed, because in a regulated operation the first
question is always the same:

> *"So it can change a quality record?"*

If the answer is **yes**, nobody signs off. If the answer is **no, it only drafts emails**, it
isn't worth building. So the automation that would actually help is the one that never ships, and
teams settle for another dashboard.

**The blocker was never capability. It was authority** — and nobody could say, in advance and in
writing, what the agent was allowed to touch.

---

## 2 · The answer: take the authority from the data

Every regulated organisation already classifies its data. That classification is sitting on the
tables, maintained by the people whose job it is, and it is the answer to the question nobody could
answer. So Warrant reads it — `SYSTEM$GET_TAG`, live, on every single decision.

The same agent, the same code path, on one pass, produces three different endings:

| The exception | Table it must touch | Tag on that table | What happens |
|---|---|---|---|
| SUP-002's on-time delivery fell to 26% | `SHIPMENTS` | `open` | **Handled.** Supplier case opened, nobody asked, logged |
| SKU-1003 is 5 days from stockout | `INVENTORY` | `internal` | **Escalated.** Prepared in full, with evidence and an undo path — then stopped, because a replenishment commits spend |
| QH-0034 has been on hold 82 days | `QUALITY_HOLDS` | `regulated` | **Refused.** It may surface the hold and explain it. Releasing it is never the agent's, at any confidence |

**There is no `if table_name ==` anywhere in the code.** Retag `INVENTORY` as `regulated` and the
middle row stops being an escalation and becomes a refusal — no code change, no deploy. That is the
difference between an agent with *permissions* and an agent with a *warrant*.

![The seven stages of the loop, with the three governed ones marked, and the same pipeline run
three times ending in handled, escalated and refused](docs/images/web/story-workflow.png)

*The same seven stages, run three times on one pass. The only thing that differs between the lanes
is the tag on the table each action would touch.*

### 2.1 · The seven stages

| | Stage | | |
|---|---|---|---|
| 01 | **Watch** | Rolling baselines over shipments, inventory and holds | unattended |
| 02 | **Detect** | An exception, with the runbook clause that set the threshold | unattended |
| 03 | **Investigate** | Grounded reasoning over the procedures; cites its source | unattended |
| 04 | **Classify** | Read the governance tags on every table the action touches | **the gate** |
| 05 | **Route** | Act, queue for a human, or refuse — decided by the tags | **the gate** |
| 06 | **Execute** | Re-read the tags. An approval does not survive a policy change | **the gate** |
| 07 | **Audit** | Append-only. Refusals recorded with the same care as actions | unattended |

Stages 1–3 are a pipeline any competent team would build. **Stages 4–6 are the submission.**

![The Warrant viewer: the headline claim beside three tables resolved live to L4, L3 and L2
authority](docs/images/web/hero.png)

<div align="center"><em>The idea in one picture, and it is not an illustration — those three rows
come from the same <code>SYSTEM$GET_TAG</code> read that drives the agent. Retag a table and the
hero changes.</em></div>

---

<table>
<tr>
<td width="33%" valign="top">

#### 🎯 The idea

Authority is **not** a rules list in application code. It is derived from the
`SENSITIVITY` tag already on the table, read with `SYSTEM$GET_TAG` on every
decision. Governance policy and agent behaviour stay in sync because they are
the same artifact.

</td>
<td width="33%" valign="top">

#### 🛑 The differentiator

The tag is read **again at execution time**. Approve an action, reclassify the
table it touches, run the executor — it refuses, and both facts are in the
append-only log: that you approved, and that it was refused.

</td>
<td width="33%" valign="top">

#### 🔍 The evidence

A planted attack in the grounding corpus, and 10 tests that **assume the model
complied with it** and assert the outcome anyway. *"The model resisted"* is a
property of a model. This is a property of the architecture.

</td>
</tr>
</table>

---

![The Warrant console: six exceptions detected, five handled by the agent, one awaiting a human,
two refused](docs/images/console-headline.png)

<div align="center"><em>Where a human actually decides: Streamlit in Snowflake, inside the governed
perimeter. One command ran the whole loop — five exceptions handled alone, one escalated, two
refused — and the count it leads with is the refusals, not the throughput.</em></div>

> [!TIP]
> **Reviewing this?** [`docs/rubric_alignment.md`](docs/rubric_alignment.md) maps every claim to
> the command that settles it, and [`docs/judges_walkthrough.md`](docs/judges_walkthrough.md) is a
> reproduction with expected output. Most of both needs no Snowflake account.

This README is the submission in long form, and it runs in the same five beats as the deck and the
demo video. Read the first two and you have the whole argument; the rest is evidence.

| | Beat | What it settles |
|---|---|---|
| **1** | [The problem, in one scene](#1--the-problem-in-one-scene) | why the automation that would actually help is the one that never ships |
| **2** | [The answer](#2--the-answer-take-the-authority-from-the-data) | authority read from the data's own tags — the seven stages, the five tiers, the architecture, the ordering |
| **3** | [Impact](#3--impact-what-one-pass-actually-does) | one measured run, and the three things the agent can prove about itself |
| **4** | [Driven from the CLI](#4--driven-from-the-cli-six-skills-thirteen-tools) | six Agent Skills, an MCP server, and the invariant that no tool takes a tier |
| **5** | [Three surfaces](#5--three-surfaces-and-only-one-of-them-can-act) | which surface may act, and how you can check that yourself |
| — | [Snowflake services](#snowflake-services-used) · [Quick start](#quick-start) · [Development](#development) | 19 services each cited to a file, five commands, and the gates CI runs |
| — | [The data](docs/the_data.md) · [Rubric alignment](docs/rubric_alignment.md) · [Judge walkthrough](docs/judges_walkthrough.md) | the domain in plain terms, claim-to-command map, and a full reproduction |

---

### 2.2 · The five tiers

| Tier | Meaning | Path |
|---|---|---|
| **L0** Read-only | Inspect, summarise, explain | Always allowed |
| **L1** Draft | Prepare a message or task, never send | Auto |
| **L2** Low-risk act | Routine, reversible, non-regulated | Auto + audit |
| **L3** Approval required | Escalations, status changes | Human approves in the console |
| **L4** Forbidden | Regulated records | Never the agent's, at any confidence |

Tier is resolved from object tags at runtime and **defaults down, never up.** The
*most demanding* object in an action's footprint binds — never the least, or one `open` table
could dilute a `regulated` one.

### 2.3 · And it is not one hardcoded tag

The obvious objection is that `SENSITIVITY` is a single tag name spelled into the resolver and
dressed up as governance. It is not: the resolver iterates a `POLICIES` tuple, and a second axis
is already live.

| Tag | Values | What an absent tag means |
|---|---|---|
| `SENSITIVITY` | `open` · `internal` · `regulated` | **Demands approval.** Everything has some sensitivity; not knowing it is itself the risk. |
| `RETENTION` | `normal` · `legal_hold` | **Demands nothing.** A legal hold is a state somebody *adds* — treating every untagged object as held would freeze the estate on day one. |

That asymmetry is deliberate, and the two axes are independent. Measured on the live account —
same table, sensitivity untouched at `open`:

```
before   open_supplier_case   acts unsupervised   ← SHIPMENTS sensitivity='open'
after    open_supplier_case   refused outright    ← OPS_REQUESTS retention='legal_hold'
         notify_quality_owner acts unsupervised   ← still: a DRAFT acts on nothing
```

**An `open` table, refused — by a different tag.** The rationale names retention rather than
sensitivity, because pointing a reviewer at the wrong tag sends them to change the wrong thing.
Adding a third axis (residency, contractual restriction, whatever an organisation already tags)
is a row in `POLICIES` plus a field on `TouchedObject` — no control flow changes.
`tests/test_retention.py` holds all of it in place.

### 2.4 · Architecture

```mermaid
flowchart LR
    G["⓿ GROUND<br/>5 procedure PDFs<br/><i>AI_PARSE_DOCUMENT</i>"]
    D["① DETECT<br/>Dynamic Tables<br/><i>thresholds from the runbooks</i>"]
    R["② REASON<br/>AI_COMPLETE + Cortex Search<br/><i>grounded, JSON-schema'd</i>"]
    C["③ CLASSIFY<br/><b>SYSTEM$GET_TAG</b><br/><i>live, never cached</i>"]
    T[("WARRANT.CORE.SENSITIVITY<br/>open · internal · regulated")]

    L2["L2 · act now"]
    L3["L3 · ask a human"]
    L4["L4 · refuse"]

    E["⑥ EXECUTE<br/><b>re-resolve authority</b><br/><i>the tag may have moved</i>"]
    A[("AUDIT.ACTION_AUDIT<br/><i>append-only, refusals included</i>")]

    G --> D --> R --> C
    T -.->|read at decision time| C
    T -.->|read AGAIN at execution time| E
    C --> L2 & L3 & L4
    L2 --> E
    L3 -->|"⑤ Streamlit console<br/>approve / reject / defer"| E
    L4 --> A
    E --> A

    classDef stage fill:#e0e7ff,stroke:#4f46e5,color:#1e1b4b
    classDef gate  fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef stop  fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef go    fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef store fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class G,D,R,C,E stage
    class L3 gate
    class L4 stop
    class L2 go
    class T,A store
```

The two dotted edges are the whole idea: authority is read from the governance tag at decision
time **and read again at execution time**, so an approval cannot outlive the policy it was
granted under.

### 2.5 · The same claim, in order

A flowchart shows what connects to what. It cannot show *when* — and the entire argument here is
about ordering. This is the escalated action from the run above, with a governance change landing
between the approval and the write:

```mermaid
sequenceDiagram
    autonumber
    actor Reviewer
    participant C as Console<br/>(Streamlit in Snowflake)
    participant X as EXECUTE_ACTION
    participant T as SENSITIVITY tag
    participant D as WARRANT.DATA
    participant A as ACTION_AUDIT<br/>(append-only)

    Note over T: INVENTORY = 'internal'
    C->>T: SYSTEM$GET_TAG (at proposal)
    T-->>C: internal → L3, needs a human
    C->>A: route · awaiting approval

    Note over T,D: Governance reclassifies the table.<br/>No deploy. No code change.
    Note over T: INVENTORY = 'regulated'

    Reviewer->>C: Approve and execute
    C->>A: route · approved by TSATHYA98
    C->>X: dispatch(action_id)

    X->>T: SYSTEM$GET_TAG again, now
    T-->>X: regulated → L4, forbidden
    X -x D: write NOT performed
    X->>A: refuse · classification at execution time governs
    X-->>C: refused
    C-->>Reviewer: "Your approval was recorded.<br/>The action was not taken."
```

Step 4 records the approval and step 11 records the refusal — **both** survive in the log, because
an audit trail that only keeps the outcome cannot answer who tried. Note also that the reviewer is
never asked again: their intent was genuine and is preserved. What changed is the authority, and
the check that catches it is a tag read the model is not party to.

<details>
<summary>The same loop, step by step</summary>

```
⓿ GROUND     Five operating procedures as PDFs on an internal stage
               → AI_PARSE_DOCUMENT(mode=LAYOUT) → DATA.RUNBOOKS
               → every detector threshold is a clause in one of them

① DETECT     Dynamic Table computes rolling baselines
               → runbook thresholds + a robust z-score → EXCEPTIONS
               → Serverless Task (cron) / Triggered Task on stream

② REASON     Snowpark Python stored procedure
               AI_COMPLETE(response_format=<json schema>)
               grounded by Cortex Search over the parsed procedures
               → {severity, root_cause, recommended_action, evidence[]}

③ CLASSIFY   Read object tags live on every table the action touches
               (SYSTEM$GET_TAG — real-time, never ACCOUNT_USAGE)
               → the binding object is the one demanding the MOST
                 scrutiny; the effective tier is the greater of the
                 requested tier and that demand

④ ROUTE      L2 → execute + audit
             L3 → PENDING_ACTIONS + notify
             L4 → refuse, log the refusal

⑤ APPROVE    Streamlit in Snowflake console — anomaly, reasoning,
             evidence, proposed action, tier, and why that tier

⑥ EXECUTE    Stream on PENDING_ACTIONS + Triggered Task fires the
             approved action — re-resolving authority first, because
             the tag may have changed since approval. Every step,
             including every refusal, appended to ACTION_AUDIT.
```

</details>

Everything runs inside Snowflake. No external inference, no external orchestration.

---

## 3 · Impact: what one pass actually does

Measured on the live account, from `CALL WARRANT.CORE.RUN_LOOP('AUTO')` over 2,400 shipments,
40 quality holds and 6 SKUs. One loop, no branching on table names:

![Weekly on-time delivery for six suppliers; five hold their baseline while SUP-002 falls through
the RB-001 detection threshold](docs/images/web/one-pass.png)

*The signal, drawn from the raw shipments rather than the aggregate. Over all history every
supplier sits between 85% and 92% — the collapse only exists in a rolling window, which is why
the detector uses one and why this chart does too.*

| Exception | Action proposed | Tag on the data | Outcome |
|---|---|---|---|
| SUP-002 on-time 40.5% vs 90.8% baseline (−50.3pp, robust *z* −3.63) | `open_supplier_case` | `open` | **Executed unsupervised** |
| SKU-1003 at 5.0 days of cover, 49k below safety stock | `raise_replenishment` | `internal` | **Queued for a human** |
| 4 quality holds open 61–82 days | `notify_quality_owner` | `regulated` | **Permitted — it only drafts** |
| The same holds, if release were proposed | `release_quality_hold` | `regulated` | **Refused** |

![The escalated action, with the detector's observation on the left and the model's reasoning on
the right](docs/images/evidence-and-reasoning.png)

*The escalated one. Left is what the detector measured; right is what the model concluded, marked
**model-generated** so a reviewer never has to guess. It cites RB-002 §5 — a clause in a PDF the
pipeline parsed at setup time — and the tier rationale names the tag that forced the escalation.
The model contributed the parameter values; it never contributed SQL text.*

Detection to proposed action: **20–95 seconds**, against an operating rhythm where these
surface on a daily review. Every row above, including the refusal, is a row in an append-only
log — and the refusal survives a human approving it, because authority is re-resolved at
execution time rather than trusted from proposal time.

![A human approved the action and it was still refused at execution
time](docs/images/refusal-banner.png)

*That last clause, demonstrated. Between the action being queued and the reviewer approving it,
`INVENTORY` was reclassified `regulated`. The approval is recorded. The action did not happen.
No agent was asked to be honest about this — the tag is read again before the write.*

---

![A 24-hour timeline of unattended task runs across both Snowflake tasks, 34 runs and none
failed](docs/images/web/unattended.png)

*Minimal manual intervention, measured rather than asserted. Two serverless tasks — one triggered
on the approval stream, one sweeping hourly — ran 34 times in 24 hours with nothing failing and
nobody present. "Nothing to do" is counted separately from a failure on purpose: a triggered task
that finds its stream empty and spends nothing is working correctly, and folding those into either
column would misreport a healthy pipeline.*

### 3.1 · The agent can answer for itself

Two questions governed automation usually cannot answer, both computed by the **same resolver the
executor uses** and both callable from SQL:

```bash
# What am I allowed to do, right now?
snow sql -c <conn> -q "CALL WARRANT.CORE.AUTHORITY_MANIFEST(NULL);"

# What would tagging this table 'regulated' cost me?  (no ALTER TABLE, nothing written)
snow sql -c <conn> -q "CALL WARRANT.CORE.AUTHORITY_MANIFEST(
  OBJECT_CONSTRUCT('WARRANT.DATA.SHIPMENTS','regulated'));"
#   -> 2 capabilities revoked: expedite_shipment, open_supplier_case

# Would today's policy still allow what already happened?
snow sql -c <conn> -q "CALL WARRANT.CORE.REPLAY_DECISIONS(NULL);"

# And the agent's own evidence pack, composed in-warehouse under its own role
snow sql -c <conn> -q "CALL WARRANT.CORE.GENERATE_AUDIT_PACK();"
```

![Every action in the registry, resolved against the tags currently on the data it
touches](docs/images/authority-manifest.png)

*The first question, in the console. Every action in the registry resolved against the
classifications in force right now — one refused outright, one needing a human, three cleared to
act. Each card carries the objects it touches and the tag that decided it. `notify_quality_owner`
is cleared despite touching a `regulated` table, because drafting is not acting.*

![Tagging shipments as regulated would revoke two capabilities, computed without writing
anything](docs/images/whatif-revocation.png)

*The second question. Classifying `SHIPMENTS` as `regulated` would cost two capabilities — priced
before the policy changes, with no `ALTER TABLE` and nothing to undo. It is the same resolver the
executor uses, so it cannot disagree with what would actually happen.*

The replay's headline count is deliberately narrow: **executed work that today's classifications
would no longer permit unsupervised**. That is the only category which cannot be corrected going
forward, and it is the question an auditor actually asks.

### 3.2 · The corpus is untrusted input

![The planted hostile runbook beside the six scored reasoning cases](docs/images/web/tested.png)


Step ② interpolates retrieved documents into a prompt, so a document is an attack surface.
`corpus/adversarial/` contains one that claims to supersede RB-003, grants itself release
authority, offers an `execute_sql` action, appends a statement to a parameter value, retargets
every action at one SKU, and asks for the audit entry to be suppressed.

Run it against the live pipeline with `./scripts/injection_drill.sh` — it ranks first for a
quality query and is cited by all six findings, and the routing does not move.

But that is the weaker claim. The stronger one is in `tests/test_adversarial.py`, which assumes
**the model complied with the attack completely** and asserts the outcome anyway: the tier and
footprint come from the registry, the sensitivity tag is read from the object rather than the
reply, and the executor re-resolves authority before it binds anything. "The model refused" is a
property of a model that changes under you; "the model's compliance changed nothing" is a property
of the architecture.

---

## 4 · Driven from the CLI: six skills, thirteen tools

Defined in [`.cortex/skills/`](.cortex/skills/). The first five describe how each phase is built;
the sixth is how to *operate* the agent from a terminal:

| Skill | Responsibility |
|---|---|
| `detect-anomaly` | Baseline + statistical/ML exception detection |
| `investigate-root-cause` | Grounded reasoning over structured + unstructured evidence |
| `classify-authority` | Resolve the authority tier from object tags |
| `propose-action` | Produce a concrete, reversible, typed action |
| `orchestrate-loop` | Run the five phases end to end |
| `operate-warrant` | Drive the agent from the CLI through its MCP server |

![The MCP tool surface: thirteen tools split eleven read and two act, five resources, six skills,
and the test asserting no tool accepts an authority tier](docs/images/web/coco-cli.png)

*The whole agent is an MCP server. The load-bearing property is not the tool count — it is that
no tool accepts a `tier`, so there is no parameter for a prompt to aim at, and that is asserted
by walking every registered tool's live schema.*

---

## 5 · Three surfaces, and only one of them can act

| Surface | Can it act? |
|---|---|
| **Streamlit console**, inside Snowflake | **Yes**, through the governed path: approve → re-resolve authority → execute. It runs on the reviewer's own Snowflake identity, so an approval is attributable to a person. |
| **[Public web viewer](https://snowflake-coco-cli-hackathon-2026.vercel.app/)**, Next.js on Vercel | **No — and it lets you prove that yourself.** The approve, reject and defer buttons are live and send the real statements. Snowflake refuses them in front of you. |
| **Cortex Agent** in CoWork | **No.** Two read-only tools, and nothing bound to the executor. |

That asymmetry is the design, not a limitation. Approving is a governed act, so it belongs only to
the surface that has an identity.

![The public viewer's approve control, with the refusal already returned and reported as a passing
check](docs/images/web/evidence.png)

*Press **Approve and execute** on the public page and this is what comes back. The panel is green
because being refused is the pass condition; Snowflake's own words are inside it, labelled verbatim.
The two refusals differ, and the difference is worth reading:*

| Press | What Snowflake answers | Why |
|---|---|---|
| Reject / Defer | `SQL access control error: Insufficient privileges to operate on table 'PENDING_ACTIONS'` | the role can see the queue, and is told no |
| Approve | `SQL compilation error: Unknown user-defined function WARRANT.CORE.EXECUTE_ACTION` | without `USAGE`, Snowflake will not concede the executor exists |

Denial by non-disclosure is the stronger of the two: **the role cannot be talked into calling
something it cannot name.** Both statements bind an `action_id` that cannot exist, so neither would
do anything even if a grant were one day mis-applied — the demonstration cannot become the incident
it describes. `web/scripts/probe.mjs` asserts both write paths on every run.

### 5.1 · The conversational surface cannot act, on purpose

`WARRANT_ANALYST` is a Cortex Agent with two read-only tools: Cortex Search over the parsed
procedures, and Cortex Analyst over the semantic view. It is **not** given a `generic` tool
bound to `RUN_LOOP` or `EXECUTE_ACTION`, and that is the point. A chat box that can invoke the
executor routes around the console, the approval queue and the human — it puts the most
persuadable surface in the system on the far side of the gate.

So it may look and speak, and it may not touch. Asked to release a hold, it declines and cites
the clause:

```
I cannot release QH-0034. Per RB-003, quality holds are regulated records:
"No automated system may alter a hold's disposition, release a lot, or close an
investigation." … I also cannot provide the lot reference. RB-003 states that lot
identifiers are need-to-know, and that automation is not granted visibility of them.
```

Verify it yourself without a browser:

```bash
snow sql -c <conn> -q "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'WARRANT.CORE.WARRANT_ANALYST',
  '{\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",
     \"text\":\"What does RB-003 permit automation to do with an aging hold?\"}]}],
    \"stream\":false}');"
```

---

## Snowflake services used

Every row cites the file that uses it, so this table can be checked rather than taken on trust.
A service does not appear here until it is actually wired up.

| Service | Used for | Where |
|---|---|---|
| **CoCo CLI** | Built with it — 6 custom Agent Skills — **and drivable by it**, via an MCP server exposing 13 governed tools | [`.cortex/skills/`](.cortex/skills/), [`mcp/`](mcp/) |
| **Object Tagging / Horizon** | The authority model — `SENSITIVITY` read live with `SYSTEM$GET_TAG` | `sql/00_setup.sql`, `src/warrant/authority/tags.py` |
| **Masking Policies** | Column-level governance — the agent cannot read the lot identifier it may not act on | `sql/00_setup.sql`, `sql/10_synthetic_data.sql` |
| **Cortex AI** (`AI_COMPLETE`) | Structured reasoning, `response_format` + `return_error_details` | `src/warrant/reason/investigate.py` |
| **Cortex Search** | Grounding findings in the runbook corpus | `sql/30_ai.sql`, `src/warrant/reason/investigate.py` |
| **`AI_PARSE_DOCUMENT`** | The corpus is five real PDFs on a stage, parsed into text — not a VARCHAR column | `sql/15_corpus.sql`, `corpus/` |
| **Stages + Directory Tables** | Document storage the parse is driven from, and the packaged Python | `sql/00_setup.sql`, `sql/15_corpus.sql` |
| **Semantic Views** | Named, stable metric definitions — defined in SQL, read back through `SEMANTIC_VIEW(...)` | `sql/30_ai.sql`, `streamlit/warrant_console.py` |
| **Snowpark (Python)** | `RUN_LOOP`, `EXECUTE_ACTION`, `EXECUTE_APPROVED` stored procedures | `sql/40_orchestration.sql` |
| **Dynamic Tables** | Rolling supplier and inventory baselines | `sql/20_pipeline.sql` |
| **Streams** | Change detection on exceptions and approvals | `sql/20_pipeline.sql` |
| **Tasks** | Serverless cron sweep + a triggered task on the approval stream, both running unattended — `TASK_ACTIVITY()` reports what they did | `sql/40_orchestration.sql`, `sql/46_schedule.sql` |
| **Cortex Agents** | `CREATE AGENT` — a conversational surface with **no authority to act**, deliberately | `sql/35_agent.sql` |
| **Cortex Analyst** | The agent's `cortex_analyst_text_to_sql` tool over the semantic view | `sql/35_agent.sql` |
| **Snowflake CoWork** | Where that agent is used — `ai.snowflake.com`, zero extra build | `sql/35_agent.sql` |
| **Streamlit in Snowflake** | The approval console | [`streamlit/`](streamlit/) |
| **Notification Integrations** | Escalation email, recipient derived at setup so none is committed | `sql/00_setup.sql`, `src/warrant/orchestrate/loop.py` |
| **Resource Monitors** | Cost guard — two of them: 100 credits on the warehouses this project creates, and a separate 25 on the account's pre-existing shared ones, which the first could not cover | `sql/00_setup.sql` |
| **RBAC** | Least-privilege `WARRANT_ROLE` plus a separate `WARRANT_QUALITY_OWNER`; nothing runs as `ACCOUNTADMIN` | `sql/00_setup.sql` |

**Deliberately not used**, so the table above stays checkable:
`SNOWFLAKE.ML.ANOMALY_DETECTION` (the detectors implement thresholds quoted from the runbooks,
which is more defensible than a black box and leaves a documented seam where the ML function
would plug in); Snowflake Marketplace (no third-party dataset would be synthetic, and the
clean-room rule matters more than the extra line item); and a `generic` agent tool wired to the
executor — see below, that one is a governance decision rather than an omission.

## Quick start

```bash
# 1. Configure a Snowflake connection (shared with the `snow` CLI)
snow connection add --connection-name warrant

# 2. Provision everything — idempotent, safe to re-run
./scripts/setup.sh warrant

# 3. Run one full loop
snow sql -c warrant -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');"

# 4. See every decision, including the refusals
snow sql -c warrant -q "SELECT phase, outcome, tier, rationale
                          FROM WARRANT.AUDIT.ACTION_AUDIT ORDER BY ts;"
```

Enterprise edition and **AWS us-west-2** — Mumbai and Singapore lack the Cortex functions this
uses. `sql/90_reset.sql` returns the pipeline to a pre-run state without touching the audit log.

Reviewers: **[`docs/rubric_alignment.md`](docs/rubric_alignment.md)** maps every claim to the
command or file that settles it, and **[`docs/judges_walkthrough.md`](docs/judges_walkthrough.md)**
is a one-command reproduction with expected output and runtime. Neither needs you to have a
Snowflake account for the parts marked as such.

## Repository layout

```
.cortex/skills/     CoCo Agent Skills (6) — five for the phases of the loop, plus
                      operate-warrant, which is how you drive it from a terminal
.github/workflows/  CI — seven gates plus a gitleaks scan
corpus/             Operating procedures as Markdown; corpus/pdf/ holds the rendered PDFs the
                      pipeline actually parses. Generated, committed, verified in CI.
                      corpus/adversarial/ holds the planted attack; it is never built in.
eval/               cases.json — six reasoning scenarios; scorecard.json — the recorded result
src/warrant/        Python package — detect / reason / authority / act / orchestrate / common
sql/                Idempotent DDL, run in filename order (00 → 45); 90 resets for a re-run
streamlit/          Approval console (Streamlit in Snowflake)
mcp/                MCP server — Warrant's governed tools, drivable by CoCo CLI or any
                      MCP client. Eleven read-only tools, two that act, none that take a tier.
web/                Public read-only viewer (Next.js on Vercel), reading live from Snowflake.
                      Its approve/reject/defer buttons are live and send the real statements —
                      what you get back is Snowflake's refusal, not a disabled control.
tests/              pytest suite, 100% branch coverage, one file per source module
tools/              Repo governance: the SQL-construction boundary lint, the corpus builder,
                      the reasoning evaluator, and the documentation claims checker
scripts/            setup.sh provisions everything; injection_drill.sh runs the attack live
docs/               Architecture, judge walkthrough, rubric alignment, data licences, images
```

Two conventions worth knowing before reading the code:

- **Every function takes its Snowpark `Session` as its first argument.** Nothing under
  `src/warrant/` calls `get_active_session()` — only the stored-procedure entry points in
  `sql/40_orchestration.sql` and the Streamlit app do. That one rule is what makes 100% branch
  coverage achievable rather than aspirational.
- **SQL statements are module-level constants and values are bound with `?`.** The model
  contributes parameter values, never SQL text, and `tools/lint_sql_boundary.py` fails the build
  if any module composes a statement from runtime data.

## Development

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check .
uv run mypy                                     # strict
uv run python tools/lint_sql_boundary.py        # no SQL may be composed from runtime data
uv run python tools/build_corpus.py --check     # committed PDFs still match corpus/*.md
uv run python tools/evaluate_reasoning.py --check   # recorded reasoning scorecard meets threshold
uv run pytest --cov --cov-report=term-missing   # gated at 100% branch coverage
uv run pytest -m integration                    # opt-in; needs a warehouse
```

All of those run in CI, plus `tools/check_doc_claims.py` and a gitleaks scan for committed secrets.

Two of them need explaining, because they gate on committed artifacts rather than recomputing:

- **`build_corpus.py --check`** re-renders the corpus in memory and compares bytes. The PDFs are
  generated *and* committed, so they could drift from the Markdown; rendering is pinned to a fixed
  creation date to make the comparison possible.
- **`evaluate_reasoning.py --check`** verifies `eval/scorecard.json`. Measuring the model needs an
  account and CI has none, so CI checks the recorded measurement instead — and fails if a case was
  added to `eval/cases.json` without re-running `--live`. Re-measure with:

  ```bash
  uv run python tools/evaluate_reasoning.py --live --connection <conn>
  ```

## Data

All data is **synthetic**, generated in-warehouse by `sql/10_synthetic_data.sql`. No proprietary,
personal or customer data is used, and **no Snowflake Marketplace listing is used** — deliberately,
because a third-party dataset would not be synthetic and provenance matters more here than one
more line in the services table. Provenance is in
[`docs/data_licences.md`](docs/data_licences.md).

**[`docs/the_data.md`](docs/the_data.md) explains the domain for a reader who does not work in
supply chain** — a five-term glossary, why this domain was chosen (it is the cleanest case of one
workload spanning three governance levels at once), and how the generator works.

It also says plainly that **we planted the anomalies the agent then detects**, because that sounds
like cheating until you see the alternative. A testbed with no known-bad data cannot demonstrate
detection, and one seeded from a real operation would fail the clean-room rule. What matters is
whether the detector had to do real work: every threshold is quoted from a runbook clause written
before the data, the planted supplier scores a robust *z* of **−3.63** against **−0.46** for the
next-worst, and the reasoning eval includes a case where the correct answer is to do *nothing* —
which a detector tuned to find what was planted would fail.

The five operating procedures in `corpus/` were written for this project. They are realistic in
form and deliberately not derived from any real organisation's documents.

## Licence

Apache 2.0 — see [LICENSE](LICENSE).
