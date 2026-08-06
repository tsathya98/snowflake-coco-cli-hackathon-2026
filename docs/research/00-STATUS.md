# STATUS — read this first

_Last updated: 2026-08-03_

## 🔴 URGENT — act today

### 1. Deadline conflict: submissions may ALREADY be closed
The authoritative **Terms & Conditions** and the marketing page disagree:

| Source | Submission closes |
|---|---|
| **T&C (authoritative)** | **Aug 2, 2026, 11:59 PM IST** — *already passed* |
| hack2skill event page | Aug 6, 2026 (no time, no timezone) |

T&C judging window is "Aug 3–22"; the event page says "Evaluations Aug 7–22". No published
extension was found. **Resolve immediately:**
- Email: support+cococlihack@hack2skill.com
- Discord: https://discord.gg/KMKtbxBJpW
- Check the participant dashboard: https://hack2skill.com/event/cococlihack/dashboard/interactions

Registration is confirmed done (user registered before Aug 2 close).

### 2. ⚠️ EMPLOYER IP — the Takeda code CANNOT be reused
This invalidates the "lift these assets" plan in the first draft of `BRIEF.md`.

T&C §4.4(e), verbatim:
> "Participants must not include any proprietary, confidential, or unauthorized datasets or
> code unless they have full rights and licenses to do so. Plagiarism or unauthorized use
> may result in disqualification."

T&C §4.1 warranty: the Entry "does not contain any confidential or proprietary information
of any entity or person."

And the license granted to Snowflake is **irrevocable and worldwide** — contamination is
not recoverable after submission.

**Code written for Takeda/Altimetrik is the employer's IP, not the participant's.** Copying
from `agentic-central-reporting`, `takOS`, or the `ai/` repos would be both a disqualification
trigger and a genuine IP exposure event.

**What is still safe:**
- ✅ Generic architectural *patterns* you hold as professional knowledge (an exception→drill-down→action
  loop is a generic ops pattern, not Takeda IP)
- ✅ Publicly-documented techniques (sqlglot AST validation, SDUI, MCP wiring)
- ✅ Generic supply-chain / manufacturing domain vocabulary that is industry-standard
- ✅ 100% synthetic data

**What is NOT safe:**
- ❌ Any file copied or adapted from a Takeda repo
- ❌ Takeda-specific business logic (measure-pack SQL, `plant_rnk` leg-selection rules, the
  CMO-first-hop rule, QA-release workday semantics — these are client-verified Takeda logic)
- ❌ Real personas, interview content, the $7.6M / 31,416-report figures
- ❌ Any Takeda data, real or derived

**Practical stance: clean-room build.** Write fresh code against synthetic data. The value
you carry over is judgment about *what to build and why*, not source.

### 3. Language requirement is a scored criterion
T&C §9(2): the Prototype must use **Python, Java, and/or Scala**. Not TypeScript, not Go.
A Python core is effectively mandatory.

---

## Confirmed event facts

- **Registered:** yes, Standard (APJ) edition
- **Edition:** Standard/APJ (NOT the GCC edition — different problem statements)
- **Team:** 1–4 members, one entry per person, cannot be on multiple teams
- **Grand Finale:** Sept 1–4, 2026 — virtual, **live** demo before judges
- **Induction:** Aug 26, 2026 — this is when presentation guidelines are issued
- **Finalists announced:** Aug 24, 2026

## Chosen problem statement

**PS1 — Intelligent Workflow Automation Agent.** See `03-problem-statement-decision.md`.

## Next actions — in order

### Blocking
- [ ] **Confirm the real deadline** — Discord `discord.gg/KMKtbxBJpW` (fastest), or
      support+cococlihack@hack2skill.com, or check whether the dashboard submission form is open
- [ ] **Watch the two gated workshop recordings** —
      https://hack2skill.com/event/cococlihack/dashboard/interactions
      (Workshop 1: Abhay Singh · Workshop 2: Sarita Priyadarshini, both Snowflake).
      Likely contain submission mechanics not published publicly.

### Hour 1 — three experiments that decide the architecture
- [ ] Sign up standard trial (https://signup.snowflake.com/), **Enterprise edition, AWS US West 2**
- [ ] `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';`
- [ ] **Test 1:** does `cortex` run against the standard trial? (docs contradict themselves —
      if rejected, use https://signup.snowflake.com/cortex-code and verify `CREATE DATABASE` works)
- [ ] **Test 2:** does `CREATE NOTIFICATION INTEGRATION ... TYPE = WEBHOOK` work on trial?
      (determines whether the action stage is real or in-app only)
- [ ] **Test 3:** confirm `SNOWFLAKE.ML.ANOMALY_DETECTION` is callable
- [ ] Set `AUTO_SUSPEND = 60` on every warehouse; create a resource monitor **and** a budget

### Build
- [ ] Clone the [Supply Chain Risk Intelligence quickstart](https://www.snowflake.com/en/developers/guides/supply-chain-risk-intelligence-with-snowflake/)
      for a synthetic vendor/PO/BOM schema (self-generating, no data loading)
- [ ] Detect → Reason → Route → Approve → Execute (see `04-snowflake-setup.md` for the design)
- [ ] Reasoning + action logic as **Snowpark Python stored procedures** (language mandate + bonus)
- [ ] Streamlit in Snowflake approval console
- [ ] Register the agent with **CoWork** (ai.snowflake.com) for a free second demo surface

### Submit
- [ ] Presentation deck (REQUIRED)
- [ ] Repo with clear documentation (REQUIRED) — make CoCo CLI usage **visible**, it's a scored criterion
- [ ] No video needed. Live demo is at the Sept 1–4 finale.

### Housekeeping
- [ ] 🚨 If using the cortex-code trial: **diarise the cancellation date** — it auto-converts to
      paid, unlike the standard trial which just suspends. Cancellation requires contacting support.
