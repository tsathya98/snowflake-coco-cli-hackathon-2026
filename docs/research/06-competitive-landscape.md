# Competitive landscape & judging intel

Sponsor: Snowflake. Administrator: **YourStory Media**, with Hack2skill as platform subcontractor.

---

## 🔴 Two rules that appear NOWHERE in the T&C or event page

Both stated verbatim in the [intro session](https://www.youtube.com/watch?v=96mM6o5DxLA)
(Jun 25, 2026, 48 min — transcript extracted via `yt-dlp` auto-captions).

### 1. Your GitHub repo will be statically analysed
Rohan (technical presenter), verbatim:
> "Typically what happens in hackathons is that only the functionality of the prototype is being
> scrutinised… But now, in the age of AI, and especially how powerful CoCo CLI is, it is very easy
> to generate very high quality code. That is why we have created this format wherein not only will
> your functionalities and functional relevance be checked, but at the same time **the GitHub
> repository that you'll be submitting will also be statically analysed for its code quality,
> security, efficiency, testing and accessibility.**"

→ **Tests, linting, CI, and no committed secrets are effectively scored.**

### 2. Snowflake-maximalism is explicitly rewarded
Rohan: *"The expectation is for you to utilise as many Snowflake services as possible and **you will
be positively rewarded for it** while we are evaluating the submissions."*

Shubhangi Singh (Head of Developer Marketing India, Snowflake): *"All things Snowflake is highly,
highly recommended if you want to be in the top winning list… your evaluation is going to be very
Snowflake-product-heavy… it is mandatory to include Snowflake as solution."*

→ Non-Snowflake components are permitted but must be flagged for review.

---

## Submission fields (organizer, verbatim)

> "The entire submission consists of two different phases, which is one is your **GitHub and your
> deployment link**… The other is where you have to add your **video link**. You have to add your
> **presentation**… And which is the **problem statement**? … **What all are the services that you
> have included specifically that you need to mention right there.**"

So the portal collects: **repo link · deployment link · video link · presentation ·
problem-statement selection · an explicit declaration of which Snowflake services you used.**

That last field is the mechanism by which "use more Snowflake" gets scored.

### ⚠️ Corrections to earlier notes in this repo
- **A video IS expected.** Earlier docs said "not required" based on the T&C — that was correct for
  the T&C (§4.5 lists only deck, code, live demo, technical readiness) but wrong for the portal.
  T&C §7.2 also grants Snowflake rights to publish the *"video URL"*, confirming a video is part of
  an Entry.
- **The "3-minute" figure is NOT verified** — it came from a different Hack2skill event's guide.
  Counter-evidence from *this* event: one competitor recorded **4:40** and logged it compliant;
  another planned **90 seconds**. Target ~3 min as a safe default, but **confirm the cap and whether
  it must be public vs unlisted from your own dashboard.**
- **A deployment link IS expected** — earlier docs said it was never mentioned.

### You can re-submit until the deadline
From Hack2skill's participant guide:
> "You can upload multiple times, but the **latest submission before the deadline is recorded** and
> used for evaluation."

→ **Upload a rough draft immediately and keep overwriting.** No downside, protects against portal
failure, and reveals the real required-field list.

---

## Per-track guidance from the intro session (most actionable content found)

### Track 1 — Intelligent Workflow Automation Agent ← *our track*
> "If your solution stops at showing insights, you have solved analytics. But if it **takes action**
> on those insights, then you have solved this problem statement."

Summed up in three words: **"get AI to take action."**

- ✅ **Good:** multi-step reasoning, autonomous execution, reusable modules, context-aware actions
- ❌ **Bad:** *"a chatbot layer over a database"*, a single one-shot prompting solution, or
  **a dashboard with alerts**
- **Worked example given:** complaints spike 40% → AI detects the anomaly, investigates root cause,
  summarises, **opens a support ticket and alerts the right team** — without the user doing those
  steps manually

### Track 2 — Unstructured Data Intelligence
> "Don't think about document search. Think about enterprise intelligence. The goal is to understand
> information, not merely retrieve it."

❌ Bad: *"a basic RAG demo. Everyone knows about RAG… simple keyword matching will not cut it."*
Target is a system that internally builds a graph of how documents relate.

### Track 3 — AI-Native Data Application
> "The winner of this track will likely build a product that people feel like using tomorrow. It
> should not be a technical proof of concept."

UX weighted unusually heavily. A chat interface is **not** mandatory.

### Track 4 — Domain-Specific Copilot
> "This track rewards depth over breadth."

Should behave like a **junior expert** — *"a finance copilot should think like a financial analyst."*
Must help with *indecisiveness*, not just answer questions.
❌ Bad: *"just another generic wrapper over an LLM"*, *"surface-level industry branding."*

### Other Q&A
- Technical Execution 40% described as: does it logically work, is it architecturally sound,
  **is anything hard-coded versus genuinely fetching from an API**, how much works in a real scenario
- No track is "easier"; no level hierarchy
- AI need not be user-facing — but if you omit an interactive layer, **say so in the deck and
  describe what production would look like**
- *"The more feature-rich you can make it without sacrificing quality, the better"*

---

## Detailed sub-criteria

Found **identically worded in two independent competitor repos** — almost certainly from the
participant dashboard, but not verified against the gated portal.

| Criterion | Weight | Sub-criteria |
|---|---|---|
| **Technical Execution** | 40% | multi-step orchestration, error handling, decision branches, strong use of CoCo CLI + **Agent Skills** + tools |
| **Real-World Relevance** | 30% | clearly defined business problem, realistic context, **measurable impact** |
| **Solution Completeness** | 30% | end-to-end ingestion → reasoning → actionable output, **minimal manual intervention** |

### The GCC edition's T&C publishes a more explicit four-axis rubric
Worth reading even for our track — it reveals Snowflake's actual thinking:
- **Platform Execution & Rigor**
- **System Design & Engineering** — *"structural partitioning, API interactions, **token management**,
  performance optimization"*
- **Enterprise Viability & Value**
- **Governance & Security Guardrails** — *"RBAC, data privacy laws, and mitigation of LLM
  hallucination risks"*

---

## ⚠️ Track 1 is the most crowded track

~25 identifiable public competitor repos found via the GitHub search API. Two are well clear.

### A. VF Logistics — `hoachauphuoc/vf-logistics-hackathon`
https://github.com/hoachauphuoc/vf-logistics-hackathon

PS-1. Autonomous fraud/compliance detection for maritime Bills of Lading. Five-step orchestrator:
anomaly detection → Cortex AI investigation → **live Marketplace sanctions screening** → AI-decided
remediation (BLOCK/ESCALATE/CLEAR) → ERP posting, writing every step *including the AI's stated
reason* to `WORKFLOW_AUDIT_LOG`.

**Snowflake surface:** Cortex Agent, Cortex AI (`COMPLETE`, `AI_COMPLETE`), Cortex Analyst, Cortex
Search, **Marketplace** (free listing `GZTSZ290BV255`), Dynamic Tables, Streams & Tasks, Snowpark,
Streamlit-in-Snowflake.

**Notable moves:**
- **Deliberately uses Python *and* Java** to satisfy T&C §9(2) — the Java is a Mendix JDBC
  integration existing largely to tick that box
- **Mendix public web prototype** as the primary judge entry point — *no Snowflake login required
  to evaluate*. Streamlit is the secondary "technical proof surface."
- `docs/COCO_CLI_EVIDENCE.md` — eight engineering sessions with **the exact SQL a judge can re-run**
  to verify each claim. Opens by citing "Judging Criteria §9(1)."
- `COMPLIANCE_CHECKLIST.md` — self-audit against every T&C section, with a dataset licence table
  and a transparently disclosed exception
- One-command entry: `snow sql -q "CALL MENDIX_APP.AGENTS.WORKFLOW_FULL_PIPELINE_V2('AUTO');"`

### B. LedgerLink — `planksconstant-arch/LedgerLink-snowflake-`
https://github.com/planksconstant-arch/LedgerLink-snowflake- (default branch **`master`**)

PS-1. Multi-agent detection of supply-chain financial anomalies → root-cause investigation across
structured + unstructured → contextual recovery actions. **Live app:**
https://ledgerlink--demo.streamlit.app/

5-phase pipeline run by **six custom CoCo Agent Skills** in `.cortex/skills/`: `ml-anomaly-agent`,
`rule-anomaly-agent`, `root-cause-agent`, `action-agent`, `notification-agent`,
`orchestrate-supply-chain`. Uses `AI_COMPLETE`, `SENTIMENT`, Snowflake ML functions, idempotent
MERGEs, a global circuit-breaker, and an **HMAC-signed audit log** so each automated action is
cryptographically attributable to the AI.

**Notable moves:**
- `docs/judges_walkthrough.md` — **"1-click Judge Mode"** with exact `cortex -p "..."` commands,
  expected runtime (2–4 min), warehouse size, required role privileges
- `docs/judging_rubric_alignment.md` — maps every feature to a rubric line with evidence tables
- Quantified **Business Impact Scorecard** in the README (capital protected $1.2M, precision 99.2%,
  time-to-detect <45s) — explicitly labelled *simulated*
- Real hygiene: `.github` CI, `tests/`, `Dockerfile`, `LICENSE`, `CONTRIBUTING.md`, `.env.example`

### The transferable lesson
> **Both leaders independently wrote a rubric-alignment document addressed to the judges, and both
> made it trivially cheap for a judge to verify claims. Neither relies on the judge having a working
> Snowflake account.**

Other entries: `sergiobuilds/bidpilot` (RFP agent), `stran1023/FarmTwin-AI-Copilot`,
`TanvirIslam-BD/FinOps-Guardian`, `EthannMK/contract-risk-obligation-auditor` (13 KB, barely started),
`rtjajangsurat-del/cybercopilot`, `imdevedugame/sahabat-siaga`.

---

## The official deck template (leaked to a public repo)

A team committed the gated-dashboard template publicly:
https://github.com/casafurix/bodhix-snowflake-cococli-hackathon/tree/main/docs
→ `Prototype Submission Template _ Cortex Code CLI Hackathon.pptx`

Six slides. **Slide 1 cover fields:** Team Name · Problem Statement · Team Leader Name · Team Size.
**Slide 2** mandates three sections:

1. **Problem Brief** — what real business problem does this solve; target user/persona; current pain
   point and how this improves it; industry/domain context
2. **Architecture Diagram** — system design showing data flow; **which Cortex Code CLI skills are
   used and how they connect**; data sources (structured/unstructured); how modular components plug together
3. **Impact Statement** — **measurable** outcomes (time saved, accuracy improvement); scalability
   potential; how this extends beyond the demo

Slides 3–4 blank working slides, slide 5 "Additional Slide", slide 6 blank.

> **Two things to take from this.** The architecture slide **explicitly asks which CoCo Agent Skills
> you used** — a scored expectation, which is why LedgerLink shipped six named skills. And the Impact
> Statement demands *measurable* outcomes, which is why both leaders lead with quantified scorecards.

That repo also contains a 40 KB `STRATEGY.md` — a competitor's full strategic reasoning, including
their estimate that ~200 teams will converge on Track 1 (**their estimate, unverified**).

---

## Prior Snowflake hackathon winners

### Closest analogue: AI for Good Hackathon (APJ) — same sponsor, same region, same YourStory admin, concluded Jan 2026
https://yourstory.com/2026/05/ai-hackathon-apj-innovators-showcased-real-world-impact-snowflake-ai

- **1st — "ADA / EduAI Insights"** (student dropout-risk): *"I used a complete bouquet of services
  from a Cortex AI standpoint — **Cortex Analyst** for natural-language Q&A, **Cortex Search** for
  document answering, **Snowflake Intelligence** for agentic workflows, **Streamlit** for
  visualisation, native classifiers."* Built **entirely inside Snowflake**.
- **2nd — "Dream Weavers"** (building inspection): `AI_CLASSIFY`, `AI_COMPLETE`, Cortex Analyst,
  internal stages, **dynamic tables + streams + tasks**. Her lesson: *"It's very easy right now to
  add AI everywhere and call it innovation… is it actually solving the problem, or are we just
  making it look smarter?"*
- **3rd — warehouse inventory copilot:** **multi-agent architecture** (agent 1 queries, agent 2
  reasons over extracted data) + streams, dynamic tables, views, Streamlit.

> **Every winner used deep native Cortex primitives. None was an external LLM wrapper.**

### DevPost "RAG 'n' ROLL" (Snowflake + Mistral)
Grand prize **SnowTrail** won by *measuring* rather than feature-checking: A/B-tested retrieval with
TruLens, reported "90% answer relevance," and openly documented **rejecting** `PARSE_DOCUMENT` in
favour of Amazon Textract with a stated reason. Honest counter-evidence: 2nd-place ChefMate used
Snowflake as a plain warehouse — mid-tier judging is noisier than the top.

### Rubric calibration across sponsored hackathons
| Event | Weights |
|---|---|
| GenAI Hackathon APAC (Google Cloud) | Vision 30 · Technical 30 · UX 20 · Innovation 20 |
| Intel AI Hackathon 2025 | Prototype 50 · Technical 30 · Business 20 |
| Microsoft Code for the Future | Code/Concept 45 · Impact 35 · Originality 20 |
| Snowflake x Capgemini (live now) | Innovation 30 · Technical 25 · Business Value 25 · UX 20 |

Technical/prototype execution is the heaviest bucket almost everywhere; CoCo's 40% is on the high end.

---

## Two official assets most competitors appear unaware of

- **`Snowflake-Labs/coco-skills`** — https://github.com/Snowflake-Labs/coco-skills — curated Agent
  Skills on top of the 50+ bundled ones (`/skill` to browse). Includes `ontology-stack-builder`
  (5-layer ontology → semantic views → Cortex Agent), `semantic-view-patterns`, `rbac`, `mlops`,
  `well-architected-framework-assessment`.
- **[Best Practices for CoCo CLI](https://www.snowflake.com/en/developers/guides/best-practices-coco-cli/)**
  — use `/plan` for complex tasks, never commit secrets, review RBAC grants, set agent **evaluation
  pass thresholds as CI gates**. Plus CoCo's lifecycle **hooks** (`PreToolUse`, `PostToolUse`,
  `SessionStart`, `SessionStop`; exit code 2 = hard block) for guardrails-as-code — a cheap, legible
  way to score on the governance axis the static analysis will look at.

---

## Community intel: essentially nonexistent

No participant writeups on LinkedIn, X, Medium, dev.to, Reddit, or YouTube. Only official promotion.

| Asset | Reach |
|---|---|
| Intro session video | 659 views |
| Hands-on workshop | 88 views |
| Launch post on X | **84 views, 1 like, 0 retweets** |
| Predecessor winners video | 161 views |

Second workshop found: ["Hands on with CoCo CLI workshop"](https://www.youtube.com/watch?v=Xsorj-C-KdM)
— Jul 17, 2026, 48 min, 88 views. Pure product walkthrough, **no additional submission/judging detail.**
No public recording of Workshop 1 (Jul 2) or the AMA (Jul 23).

Discord `discord.gg/KMKtbxBJpW` is live and valid but is the **general Hack2skill server**, not
CoCo-specific, with membership gating. Support: support+cococlihack@hack2skill.com, 9 AM–5 PM IST.

**Inference:** this is a low-visibility event, so competitive intelligence lives in the **GitHub repo
sweep**, not social media.

---

## Synthesis — the winning shape

**Sourced pattern:** Cortex Agents orchestrating **Cortex Analyst (structured) + Cortex Search
(unstructured)** over a governed semantic model, surfaced in Streamlit-in-Snowflake, with dynamic
tables/streams/tasks for automation, a **Marketplace dataset** to claim the §9(4) bonus, and a
**quantified accuracy or time-saved claim**.

**Inference:** breadth of native feature use is unusually safe to optimise for here, because "use as
many Snowflake services as possible" is *stated policy* and the portal has a dedicated field where
you declare them. But SnowTrail's win shows a **measured, justified** choice beats an unmeasured
checklist — pair breadth with at least one honest number.

**The cheapest big differentiator, given how few competitors do it:** a **judge-facing verification
path** — rubric-alignment doc + one-command reproduction + a no-login demo surface.
