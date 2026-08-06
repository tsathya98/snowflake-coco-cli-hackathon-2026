# Snowflake setup & services

## 🚨 Three trial blockers — test these in hour 1

### 1. CoCo CLI may NOT run on the standard $400 trial
The docs **contradict themselves**. The [trial limitations page](https://docs.snowflake.com/en/user-guide/admin-trial-account)
lists among features **not** available on trial accounts, verbatim:

> "Cortex Code CLI (requires a Cortex Code CLI trial account; sign up here)."

But the [Getting Started guide](https://www.snowflake.com/en/developers/guides/getting-started-with-coco-cli/)
lists the prerequisite as merely "Access to a Snowflake account (or sign up for a free Snowflake
CoCo CLI trial)" + `SNOWFLAKE.CORTEX_USER` (granted to PUBLIC by default).

There are **two separate signup funnels**:

| | Standard | CoCo CLI |
|---|---|---|
| URL | https://signup.snowflake.com/ | https://signup.snowflake.com/cortex-code |
| Includes | **$400 credits** | **$40 free inferences** |
| Duration | 30 days or until depleted | 30 days |
| At expiry | Account **suspended** | 🚨 **Auto-converts to PAID unless cancelled** |

**Unverified:** whether the CoCo trial provisions a *full* account (databases, warehouses,
tasks, Streamlit) or inference access only. You need all of it.

**Action:** sign up standard first, try `cortex` against it. If rejected, sign up for the
cortex-code trial and immediately test `CREATE DATABASE`. **Diarise the CoCo trial cancellation
date** — it bills you otherwise. Trial accounts can't be cancelled in the UI; you must contact support.

### 2. External network access is OFF on trial accounts
> "By default, Snowflake does not enable external access for trial accounts. Contact your account
> representative to get external access enabled for a trial account."

→ Kills any plan to POST to your own endpoint from a UDF.

### 3. Snowpark Container Services is unavailable on trial
> "A Snowflake account: Note that trial accounts are not supported."

→ No containers, no GPU, no Streamlit container runtime.

**Consequence — and it's actually good news:** the entire agent must live *inside* Snowflake using
native primitives. That maximises "use of the Snowflake platform," which the T&C mandates.

---

## Account setup

### Edition: **Enterprise**
Required for masking policies, **row access policies**, materialized views, search optimization,
data classification, and access history. Standard edition would block the entire governance story —
which matters because the approval gate is built on it.

### Region: **AWS US West 2 (Oregon)** ⚠️ irreversible choice

| Feature | Native regions | Mumbai (ap-south-1)? |
|---|---|---|
| Cortex AI functions | AWS us-west-2, us-east-1, eu-central-1, eu-west-1, **ap-northeast-1 (Tokyo)**, **ap-southeast-2 (Sydney)**; several Azure | ❌ No |
| Cortex Analyst | AWS ap-northeast-1, ap-southeast-2, us-east-1, us-west-2, eu-central-1, eu-west-1; Azure East US 2, West Europe | ❌ No |
| Cortex Search | ~25 regions **incl. Mumbai** — but only arctic-embed models | ⚠️ Partial |

us-west-2 is the only region with everything. **Viable APJ options are Tokyo and Sydney — not
Mumbai, not Singapore.**

Enable cross-region inference regardless (CoCo requires it):
```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';  -- ACCOUNTADMIN only
```
No egress charges; cost is latency only. Default for new orgs created after Mar 9, 2026.

### Cost control
Warehouse credits/hour: **XS 1**, S 2, M 4, L 8, XL 16… Billing per-second, 60s minimum per start.

$400 ≈ 130–200 credits. **An XS warehouse running 24/7 for 30 days burns 720 credits.**
→ **X-Small everywhere, `AUTO_SUSPEND = 60`.**

```sql
CREATE RESOURCE MONITOR <name> WITH CREDIT_QUOTA = <n>
  TRIGGERS ON 80 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;
```
🚨 **Critical gap:** *"Resource monitors work for warehouses only. You can't use a resource monitor
to track spending associated with serverless features and AI services."* — i.e. they will **not**
stop a runaway Cortex bill and **will not cover serverless tasks**, both central here.

For those use **[Budgets](https://docs.snowflake.com/en/user-guide/budgets)** (covers serverless
tasks, alerts, AI Services) — but Budgets are **notification-only, never suspend**. Use both, and
watch Admin » Billing.

Also: trial accounts without a payment method are capped at ~10 credits/day of Cortex AI functions.

### Hackathon/student extended trials
The 120-day `?trial=streamlit-hackathon` / `?trial=student` URLs are indexed but the live pages no
longer show 120-day text — **treat as expired**, though trying costs nothing. Snowflake for Startups
requires a sales conversation (useless on this timeline). No permanently free tier exists.

---

## ⭐ The confirmed architecture

The critical question — *can Snowflake send email or call a webhook?* — is now answered, and it
constrains the design.

**Email: YES but internal-only.**
> "You must specify email addresses of users in the current account. These users must verify their
> email addresses." / "You can send email notifications only to Snowflake users within the same account."

**You cannot email an arbitrary external address.** Fine for a demo; not a real channel.
```sql
CALL SYSTEM$SEND_EMAIL('<integration>','<recipients>','<subject>','<content>'[,'text/html']);
```

**Webhooks: YES but only 5 allowlisted providers** — Slack, Microsoft Teams, PagerDuty, Jira,
ServiceNow. **There is no generic webhook target.** POSTing to your own endpoint needs an EAI →
blocked on trial.

⚠️ **Unverified, on the critical path:** whether webhook notification integrations work on trial
accounts at all. The trial limitation names "external network access" (the EAI feature), and
webhook integrations are a different object type. **Test `CREATE NOTIFICATION INTEGRATION ...
TYPE = WEBHOOK` in the first hour.** Fallback: email + in-Streamlit inbox.

### The design

```
① DETECT   Dynamic Table (TARGET_LAG='1 minute') computes rolling baselines
             ↓
           SNOWFLAKE.ML.ANOMALY_DETECTION  →  EXCEPTIONS table
             ↓
           Serverless Task (USING CRON, no warehouse)
           or Triggered Task WHEN SYSTEM$STREAM_HAS_DATA('exceptions_stream')

② REASON   Snowpark Python stored procedure   ← satisfies the language mandate
             calls AI_COMPLETE(..., response_format => <json schema>)
             grounded by Cortex Search over runbooks / past incidents
             returns {severity, root_cause, recommended_action, sensitive: bool}

③ ROUTE    sensitive = FALSE → execute immediately, log it
           sensitive = TRUE  → INSERT into PENDING_APPROVALS
                             → SYSTEM$SEND_SNOWFLAKE_NOTIFICATION (Slack / email)

④ APPROVE  Streamlit in Snowflake console: reviewer sees the anomaly, the agent's
           reasoning, and the proposed action; clicks Approve / Reject
             ↓ writes decision back to PENDING_APPROVALS

⑤ EXECUTE  Stream on PENDING_APPROVALS + Triggered Task fires the approved action
```

**Key insight for human-in-the-loop:** Snowflake cannot *receive* an inbound webhook, so Slack
interactive buttons are impossible (they need a public endpoint you can't host). The clean pattern
is **Streamlit approval console → table → Stream → Triggered Task**. Fully in-platform, and it
uses Streamlit — a bonus-credit technology.

**Governance-driven approval gate (strong judging story):** use **object tagging** to mark which
tables/actions are sensitive, then have the agent read the tag to decide whether approval is
needed — rather than a hardcoded list. Requires Enterprise edition.

### Where each bonus technology lands
| Bonus tech (T&C "special consideration") | Use |
|---|---|
| **Snowpark** | The reasoning + action stored procedures |
| **Worksheets** | Setup and demo scripts |
| **Streamlit** | The approval console |
| **Marketplace** | Enrichment data for anomaly context |

**CoCo CLI** — use it to scaffold ("generate a Streamlit app", "find tables with PII tags") and
**narrate that in the submission**. It's the hackathon's namesake; make its use visible, not incidental.

---

## Service notes that matter

### AI_COMPLETE
```sql
AI_COMPLETE(<model>, <prompt> [, <model_parameters>, <response_format>, <show_details>])
```
`response_format` (JSON schema) is the one to build on — forces `{severity, root_cause,
recommended_action}` instead of prose you have to regex. Use `return_error_details` too; silent
NULLs in a scheduled pipeline are miserable to debug.

**Hosted models run inside the Snowflake perimeter** — Claude (`claude-opus-5`, `claude-sonnet-5`,
`claude-haiku-4-5`…), Llama, Mistral, OpenAI (`openai-gpt-5`…), Gemini 3.1 Pro. Data doesn't leave
Snowflake to reach Anthropic or OpenAI. ⚠️ Model-name strings churn — verify before hardcoding.

Pricing: separate **AI Credit** currency, $2.00/AI Credit (global routing), $2.20 (regional).

### Tasks / Streams / Alerts / Dynamic Tables
- **Serverless tasks:** omit `WAREHOUSE`, set `USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE`. Right
  call for a periodic scan — no idle warehouse.
- **Triggered tasks:** `WHEN SYSTEM$STREAM_HAS_DATA('<stream>')`, evaluated every 30s (lowerable to 10s).
- 🚨 **Streams' #1 bug:** *"a stream advances its offset only when it is used in a DML transaction."*
  A plain `SELECT` does **not** consume it. Your task must `INSERT`/`MERGE` from the stream or it
  reprocesses the same rows forever.
- 🚨 **Alerts are created SUSPENDED.** `ALTER ALERT <name> RESUME;` — the #1 reason a demo alert
  "doesn't fire."
- **Dynamic Tables:** `TARGET_LAG` minimum 60s. **No stored procedures or external functions in the
  definition** — which is why the reasoning step can't live inside one.
- **Rule of thumb:** Dynamic Tables replace most hand-rolled Stream+Task pipelines. Use Streams+Tasks
  when you need imperative logic. **This project needs both.**

### Cortex Agents — `CREATE AGENT` is a real GA SQL object
Orchestration: Plan → Use tools → Reflect and respond. Tool types confirmed:
`cortex_analyst_text_to_sql`, `cortex_search`, `data_to_chart`, `generic`, `mcp`, `web_search`.
**The `generic` (custom tool) type is your action layer** — lets the agent call your stored procedure.
Set the `budget:` block (`seconds`, `tokens`) so a scheduled agent can't run away with the $400.

### Snowflake CoWork (formerly Snowflake Intelligence)
Renamed at Summit 26; the SQL object is still `SNOWFLAKE INTELLIGENCE`. URL **https://ai.snowflake.com**.
**Highest demo-value-per-hour item on the platform** — register the agent once, get a polished chat
UI free. Good for the "reason over the anomaly" half of the demo.

### Semantic Views > YAML
> "Snowflake recommends using semantic views for all new implementations."

Also: the managed MCP server's `CORTEX_ANALYST_MESSAGE` tool accepts **semantic views only**, not
stage YAML.

### Cortex Search
Hybrid vector + keyword + reranking. This is where **runbooks / SOPs / past incident write-ups** go,
so the reasoning step grounds its recommendation in prior remediations.
Gotchas: index build "may take up to several hours"; dedicated warehouse **no larger than MEDIUM**;
`AUTO_SUSPEND` min 1800s; **serving compute bills per GB/month whenever resumed, regardless of query
volume**.

### Streamlit in Snowflake
🚨 **Cost trap:** the WebSocket keeps the warehouse hot until ~15 min after last activity — **and
mouse movement over the app counts as activity**. An open tab burns credits. Set
`streamlitSleepTimeoutMinutes` (5–240).
🚨 **No public/anonymous sharing** — viewers must be Snowflake users in your account.

### Document AI is DEAD
🚨 Document AI's model-build UI and `<model>!PREDICT` were **decommissioned March 16, 2026**
([BCR-2156](https://docs.snowflake.com/en/release-notes/bcr-bundles/un-bundled/bcr-2156)). Every
tutorial referencing it is dead. Use **`AI_PARSE_DOCUMENT`** (GA) and **`AI_EXTRACT`** (preview).
Legacy `SNOWFLAKE.CORTEX.PARSE_DOCUMENT` deprecates end of 2026.

### Snowflake MCP Server
Managed and GA. ⚠️ The open-source `Snowflake-Labs/mcp` repo is **DEPRECATED** — its README points
at the managed server. Third-party `snowflake-mcp` repos are unofficial.

---

## Deployment options

| Option | Cost | Public link? | Verdict |
|---|---|---|---|
| **Streamlit in Snowflake** | Warehouse credits while active (incl. idle tabs) | ❌ Snowflake users only | ✅ **Correct choice** — governed identity, zero infra, zero auth code |
| **Snowflake CoWork** | AI Credits/token | ❌ Login required | ✅ **Free bonus surface** — polished chat UI at zero build cost |
| Streamlit Community Cloud | Free | ✅ Genuinely public | ⚠️ Only if a clickable public URL is required. 0.078–2 cores, 690MB–2.7GB RAM, sleeps after 12h |
| Vercel / Netlify | Free tier | ✅ Yes | ❌ Pulls logic *out* of Snowflake — opposite of what the T&C rewards |
| SPCS | Pool credits, bills while IDLE | ❌ Still redirects to sign-in | ❌ Unavailable on trial |

Note: **a deployed link is not a required artifact** (see `01-hackathon-rules.md`). Screen-recording
the SiS app during the live finale demo is sufficient.

---

## Combining with other tech

The asymmetry that governs everything:
- **Snowflake → internet (outbound):** needs EAI → **blocked on trial**
- **Your app → Snowflake (inbound):** fully supported, works fine on trial

So: external frontends/backends are fine (authenticate with a **PAT**: `Authorization: Bearer <token>`
+ `X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN`), but calling *out* from
Snowflake is not. Design around notification integrations.

⚠️ PATs require the user be subject to a network policy unless an authentication policy says
otherwise — budget 20 min the first time. Never expose a PAT to the browser.

**External LLM APIs are rarely necessary** — Claude Opus 5, GPT-5 and Gemini 3.1 Pro all run
*inside* the Snowflake perimeter via `AI_COMPLETE`.

**Native Apps: skip.** It's a distribution mechanism, more effort than Streamlit, and not in the
bonus list.

---

## ⚠️ Unverified — test or re-check before relying on

1. **Whether the CoCo CLI trial provisions a full account** (databases/warehouses) or inference only.
   *Highest-priority unknown.*
2. **Whether webhook notification integrations work on trial accounts.** On the critical path.
3. Whether converting trial→paid lifts the SPCS / external-access restrictions.
4. Exact `SNOWFLAKE.ML.ANOMALY_DETECTION` syntax — function confirmed to exist via an official
   quickstart, but its reference page wasn't read.
5. Task `SCHEDULE` minimum — only a `'10 SECONDS'` example is documented, no explicit floor.
6. Snowflake Postgres on trial accounts (GA Feb 2026, `CREATE POSTGRES INSTANCE`) — trial
   availability, edition and cost all undocumented.
7. `SYSTEM$SEND_EMAIL_HTML` — no live reference page found; use the MIME-type argument instead.
8. Exact `tool_spec.type` strings for code-execution and agent-skills agent tools.
