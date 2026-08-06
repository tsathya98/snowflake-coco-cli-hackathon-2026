# Problem statement decision

## The four Standard-edition problem statements

1. **Intelligent Workflow Automation Agent** — AI system that understands enterprise data and
   autonomously executes multi-step workflows; reasons to identify anomalies, generate insights,
   trigger contextual actions. Domains: operations, finance, supply chain, customer support.
2. **Unstructured Data Intelligence System** — process contracts, reports, tickets, logs,
   mixed-media documents; integrate findings with structured data.
3. **AI-Native Data Application** — fully functional app on Snowflake's AI Data Cloud enabling
   natural-language interaction with enterprise data; insights, summaries, recommendations.
4. **Domain-Specific AI Copilot** — industry-tailored copilot (healthcare, finance, retail,
   manufacturing, agriculture, education) with domain awareness and actionable recommendations.

## ✅ Decision: PS1 — Intelligent Workflow Automation Agent

### Why

The strongest professional experience here is with an operating model best described as
**Exception → Drill-down → Action**:

- **Exception** — an agent watches metrics against per-user thresholds continuously and surfaces
  breaches, rather than making people hunt for the red KPI
- **Drill-down** — the user interrogates the exception in natural language against governed data,
  with the agent showing its evidence rather than asserting
- **Action** — routine responses execute automatically; sensitive ones escalate for human approval,
  bounded by a tiered authority model where regulated decisions are never the agent's to make

Read PS1's wording against that and it's the same system with different words. PS1 is the only
statement that asks for the *full loop* — detection, reasoning, **and** action-taking.

### Why not the others

| PS | Verdict |
|---|---|
| **PS3** (AI-Native Data App) | Closest to existing NL-over-data experience, but it is what **every other team will build**. Lowest differentiation on Technical Execution (the heaviest-weighted criterion). A text-to-SQL chat app is the default submission. |
| **PS4** (Domain-Specific Copilot) | Manufacturing is explicitly listed and the domain instinct is real — but the technical ceiling is lower than PS1. **Better move: fold domain depth into PS1** rather than choosing PS4. |
| **PS2** (Unstructured Data) | The strongest *unique* prior experience is Power BI `.pbix` lineage tracing — but that's PowerBI-specific, doesn't port to Snowflake, and PS2 wants contracts/tickets/logs instead. Also the most likely to become a plain RAG demo. |

### Scoring fit

Against the hack2skill rubric (Technical Execution 40% · Real-World Relevance 30% ·
Solution Completeness 30%) *and* the T&C's four criteria:

- **Technical Execution (40%)** — autonomous multi-step workflows + scheduled anomaly detection +
  governed action-taking with an approval ladder is a materially higher ceiling than "chat over a
  warehouse." It also naturally exercises Snowflake-native primitives (Tasks, Alerts, Dynamic
  Tables, Cortex Agents), which is what a Snowflake-sponsored judge rewards.
- **Real-World Relevance (30%)** — enterprise operations monitoring is a genuine, widely-felt
  problem, and the framing can be argued from first principles without any employer specifics.
- **Solution Completeness (30%)** — the full loop (detect → explain → act → approve) *is* a
  complete story, which is exactly what this criterion asks for.
- **T&C criterion (4)** — "special consideration" for Snowpark, Worksheets, Streamlit, Marketplace.
  All four fit naturally into PS1.

---

## 🔴 Constraint that shapes everything: clean-room build

**No code, data, business logic, or documentation may be carried over from Takeda/Altimetrik work.**
See `00-STATUS.md` §2 for the T&C language. This is both a disqualification risk and an IP
exposure risk, and the license granted to Snowflake is irrevocable.

### What carries over
- ✅ **Judgment** — knowing that the exception→action loop is the valuable shape, that governed
  SQL execution needs an allowlist/validator, that agents need bounded authority, that live
  bindings beat frozen snapshots. This is professional knowledge, not employer property.
- ✅ **Publicly documented techniques** — AST-based SQL validation, server-driven UI, MCP wiring,
  LOWESS/Holt-Winters forecasting. All published, all reimplementable from public sources.
- ✅ **Industry-standard domain vocabulary** — generic supply chain and manufacturing operations
  concepts that any practitioner in the field would know.

### What does NOT carry over
- ❌ Any file copied or adapted from a Takeda repo
- ❌ Employer-specific business logic (leg-selection rules for delivery lateness, workday-vs-calendar
  release semantics, tolerance grace windows — these are client-verified proprietary logic)
- ❌ Real personas, interview content, internal cost/estate figures
- ❌ Any Takeda data, real or derived

### Practical consequence
Write everything fresh, in Python, against synthetic data, using CoCo CLI to generate it.
Ironically this is *also* the better hackathon strategy — Snowflake-native code written for
Snowflake primitives will score higher than a port of a Postgres-shaped architecture.

---

## Domain framing

**Supply chain / manufacturing operations**, built on synthetic data.

Rationale: it's a listed PS1 domain, it plays to genuine expertise, it's the richest source of
natural "exception" events (late deliveries, stockouts, quality holds, supplier risk), and there
are two strong Snowflake quickstarts that ship synthetic schemas for exactly this — see
`05-datasets.md`.

Candidate starting schema: the **Supply Chain Risk Intelligence (N-Tier Visibility)** quickstart,
which generates synthetic vendor masters, POs, BOMs, trade data and regional risk via a stored
procedure, then builds a Cortex Agent + Streamlit dashboard.

**Do not use a pharma-specific framing that mirrors current employer work.** Generic supply chain
is safer and loses nothing competitively.

---

## Shape of the build (draft — refine after `04-snowflake-setup.md` lands)

The loop, mapped onto Snowflake-native primitives:

| Stage | Likely Snowflake mechanism |
|---|---|
| **Watch** | Scheduled **Task** (or Serverless Task) scanning metrics against per-persona thresholds |
| **Detect** | **Dynamic Tables** / **Streams** for change detection; SQL + statistical thresholds for anomalies |
| **Reason** | **Cortex Agent** with **Cortex Analyst** (semantic view) + **Cortex Search** tools |
| **Explain** | Natural-language drill-down with cited evidence rows |
| **Act** | Notification integration (email/webhook) — **pending verification of Snowflake's outbound capability** |
| **Approve** | Human-in-the-loop gate before any sensitive action; tiered authority model |
| **Surface** | **Streamlit in Snowflake** app (also satisfies the "special consideration" criterion) |

**Open questions blocking the design** — answers pending from research:
- Can Snowflake send email / call a webhook natively? (critical to the Action stage)
- Serverless Tasks vs Alerts — which fits threshold-watching better?
- Cortex Agent object vs. hand-rolled agent loop in Snowpark?

**Mandatory:** the whole thing must be *built using CoCo CLI* (T&C criterion 1), in
**Python/Java/Scala** (criterion 2), **on Snowflake** (criterion 3). Document the CoCo CLI usage
visibly in the repo and the deck — it's an explicit scoring criterion, not a suggestion.
