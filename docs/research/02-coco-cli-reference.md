# Snowflake CoCo CLI — reference

## What it is

**CoCo is an agentic coding CLI in the Claude Code / Gemini CLI mold, but data-native.**
The binary is literally named `cortex`. It runs an agent loop in your terminal, reads/writes
local files, runs bash and git, and additionally executes SQL against your Snowflake account
as your identity.

Official definition (docs.snowflake.com):
> "Snowflake CoCo is an AI-driven intelligent agent integrated into the Snowflake platform,
> optimized for complex data engineering, analytics, machine learning, and agent-building tasks."

### Naming history (matters when reading docs — names changed twice)
- **Nov 2025** — launches as "Cortex Code" (Snowsight + CLI)
- **Feb 2–3, 2026** — CLI reaches GA
- **June 2, 2026** — renamed **CoCo** at Snowflake Summit 2026 (same product).
  Simultaneously **Snowflake Intelligence → Snowflake CoWork**.

So: *Cortex Code == CoCo*. The T&C still says "Cortex Code CLI". Docs URLs still use `cortex-code`.

Reported (secondary sources, not stated on a Snowflake-owned page): built on the Claude Agent SDK.

### Surfaces
CoCo in Snowsight (web) · CoCo Desktop (macOS/Windows) · **CoCo CLI (terminal)** · VS Code
extension (private preview) · Claude Code plugin (preview) · ACP for 30+ editors.

---

## Installation

Not brew, not npm, not pip, and **not** a `snow` CLI extension — a standalone install script.

```bash
# macOS / Linux / WSL
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```
```powershell
# Windows native
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

- Installs to `~/.local/bin` (macOS/Linux) or `%LOCALAPPDATA%\cortex` (Windows)
- Verify: `cortex --version` · Update: `cortex update` or `/update`
- OS: macOS (arm64/x64), Linux (x64/arm64), Windows (WSL **and** native x64)
- Latest version seen: **1.1.52**

**Prerequisites:** Snowflake account · `SNOWFLAKE.CORTEX_USER` database role ·
cross-region inference enabled · Snowflake CLI installed · HTTPS/443 access

---

## Authentication

Run `cortex` — an interactive setup wizard launches. It reads **`~/.snowflake/connections.toml`**,
the *same* file the Snowflake CLI (`snow`) uses.

Methods: **external browser SSO** (default interactive) · **PAT** (recommended headless/CI,
Snowsight → My Profile → Programmatic Access Tokens, ≤90-day expiry) · **key-pair RSA JWT**
(`authenticator = "snowflake_jwt"` + `private_key_path`) · password (discouraged).

Switching: `-c <name>` flag · `/connections` (`/conn`) · `cortex profile` · `cortex connections set`

### Required account setup SQL
```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';  -- required
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <role>;
GRANT DATABASE ROLE SNOWFLAKE.COPILOT_USER TO ROLE <role>;     -- for the Snowsight surface

-- some accounts additionally needed:
ALTER ACCOUNT SET CORTEX_MODELS_ALLOWLIST = 'All';
CALL SNOWFLAKE.MODELS.CORTEX_BASE_MODELS_REFRESH();
```
`chmod 600 ~/.snowflake/connections.toml`. Credentials stay local — stated design point.

**Common first-run stumble:** no warehouse selected in the connection.

---

## Command surface

### Launch flags
| Flag | Meaning |
|---|---|
| `-c, --connection <name>` | Snowflake connection |
| `-w, --workdir <path>` | working dir for file ops |
| `-m, --model <name>` | choose model |
| `--plan` | require approval before all actions |
| `--bypass` | auto-approve planned actions |
| `--dangerously-allow-all-tool-calls` | disable permission prompts |
| `--continue` / `-r, --resume <id\|last>` | session resume |
| `-p, --print "<prompt>"` | headless single prompt, print, exit |
| `-f, --file <file>` | read prompt from file, exit |
| `--output-format stream-json` | machine-readable output |

Subcommands: `cortex update` · `cortex mcp list|add|get|remove|start` · `cortex profile` ·
`cortex connections set` · `cortex airflow health|dags list|runs trigger`

Exit codes: 0 ok · 1 general · 2 config · 3 connection · 4 permission denied · 130 Ctrl+C

### Slash commands
- **Session:** `/help` `/new` `/rename` `/resume` (`/r`) `/rewind` `/fork` `/clear` `/exit` `/compact`
- **Mode/model:** `/model` `/plan` `/plan-off` `/bypass` `/bypass-off` `/status`
- **Snowflake:** `/sql <query> [--limit n]` `/table` `/csv` `/connections` `/lineage` `/dbt`
- **Dev:** `/sh` or `! <cmd>` · `/diff` (`/changes`, `/review`) · `/worktree create|list|switch|delete`
- **Config:** `/settings` `/theme` `/sandbox [on|off|status|...]` `/add-dir <path>`
- **Extensibility:** `/skill` `/skills` `/mcp` `/mcp-status` `/hooks` `/commands` `/agents`
- **Utility:** `/tasks` `/monitors` `/airflow` `/automation history` `/feedback` `/update`

### Inline context syntax
- `#DB.SCHEMA.TABLE` — injects table schema + sample rows (**the standout Snowflake-only feature**)
- `@file$10-50` — include file line ranges
- `$skill-name` — explicitly invoke a skill
- `AGENTS.md` — project context auto-loaded at session start
- `Ctrl+T` table viewer · `Ctrl+P` plan mode · `Ctrl+L` clear

### Models
`auto` (recommended) · Claude Opus 4.8 (Preview) · Claude Opus 4.6 · Claude Sonnet 4.6 · OpenAI GPT options

---

## What it can build (relevant to PS1)

- **SQL:** write, run, explain, optimize; performance analysis via `ACCOUNT_USAGE`
- **Cortex Agents:** create, configure with Cortex Analyst + Cortex Search tools, system prompts,
  evaluate, deploy to **CoWork** — via the `cortex-agent` skill
- **Semantic Views:** auto-generate from table metadata with descriptions/synonyms/sample values
- **Cortex Search services**, document intelligence, AI-function pipelines
- **Streamlit in Snowflake:** create/style/deploy apps
- **Data engineering:** Dynamic Tables, **Tasks/DAGs**, Snowpipe, Iceberg, Openflow, Snowpark
- **Governance:** lineage (incl. column-level), PII tagging, RBAC debugging, masking/row policies
- **Cost/FinOps:** cost-intelligence skill, budgets, warehouse anomaly detection
- **Synthetic data generation at scale** — docs cite 10k-txn fraud sets, 100k-customer churn sets,
  clinical trial data. **Directly useful: this is how to build the demo dataset.**
- dbt project generation, Airflow DAG authoring, Native Apps, ML/model registry

## Extensibility

- **Skills** — 50+ bundled. Custom skills via `$skill-development` → `.cortex/skills/` (project)
  or `~/.snowflake/cortex/skills/` (global)
- **MCP** — full client. `cortex mcp add <name> <cmdOrUrl> -t stdio|http|sse`.
  Config `~/.snowflake/cortex/mcp.json`. OAuth 2.0 + DCR. Tools namespaced `mcp__<server>__<tool>`.
  Permissions in `~/.snowflake/cortex/permissions.json`
- **Subagents** (`/agents`), **hooks**, custom slash commands, plugins (preview),
  **Team mode** (multi-agent, v1.1.41), **Automations** (scheduled/event-driven),
  **Cloud Agents** (private preview — agent loop runs server-side in Snowflake)
- **Agent SDK:** `npm install cortex-code-agent-sdk` (Node ≥22) / `pip install cortex-code-agent-sdk`
  (Python ≥3.10). Still requires the CLI installed.

Config layout: `~/.snowflake/cortex/` → `settings.json`, `mcp.json`, `permissions.json`,
`conversations/`, `skills/`, `commands/`, `hooks/`, `profiles/`, `cache/`, `logs/`

---

## Pricing

- **Free 30-day trial** at https://signup.snowflake.com/cortex-code — includes **$40 USD of
  inference credits** for the first 30 days ✅ verified
- After trial: paid monthly subscription, **reported at $20/month** ⚠️ *from a search snippet
  only — not independently confirmed*
- Exceeding subscription usage → CoCo CLI **unavailable until next billing period**
- Existing Snowflake customers: pay-as-you-go by token consumption
- Snowflake compute + storage billed separately at standard rates

### Cost controls (rolling 24h window; `-1` unlimited, `0` blocked)
- `CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER`
- `CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER`
- `CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER`

Real datapoint: Capital One's 30-day TPC-DS 10TB evaluation consumed 71.71 credits ≈ $215.

---

## Limitations / gotchas

- **Cross-region inference must be enabled** — hard requirement
- Scope limited to objects the session role can see; cannot exceed grants
- **No persistent cross-session memory** by default — `AGENTS.md` is the workaround
- **Streamlit deploy gap:** "Deploying to Snowsight as a Streamlit-in-Snowflake app breaks the
  terminal-native workflow at certain steps" (Capital One)
- Generated Streamlit apps typically need several iterations; first pass is basic
- Timeouts on very large scans with undersized warehouses
- No native cross-system lineage (Fivetran/Airflow/Tableau), no external business glossary

### Security
- **Prompt-injection vulnerability** — a malicious README could cause CoCo to execute arbitrary
  commands under your Snowflake credentials. **Patched in v1.0.25, Feb 28, 2026.** Keep updated.
- CoCo inherits the launching process's permissions — can read `~/.aws/credentials`, `.env`,
  `~/.ssh`, browser session data. `WEB_ACCESS` + `curl` enable exfiltration.
- Built-in Podman sandbox often can't run on corporate workstations (needs cgroup v2 / userns)
- Mitigations: three-tier approval (Confirm/Plan/Bypass), risk classification SAFE→CRITICAL,
  `/sandbox`, RBAC enforcement, MCP URL allowlists, audit via `ACCOUNT_USAGE.QUERY_HISTORY`

> ⚠️ **Given the Takeda machine:** be deliberate about which directory you launch `cortex` in.
> Do not run it inside or adjacent to Takeda repos. Use a clean workspace with no employer
> credentials reachable.

---

## Docs

**Core:**
- Overview — https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code
- CLI — https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli
- CLI reference — https://docs.snowflake.com/en/user-guide/cortex-code/cli-reference
- Bundled skills — https://docs.snowflake.com/en/user-guide/cortex-code/bundled-skills
- Workflows — https://docs.snowflake.com/en/user-guide/cortex-code/workflows
- MCP — https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-mcp
- Security — https://docs.snowflake.com/en/user-guide/cortex-code/security
- Credit limits — https://docs.snowflake.com/en/user-guide/cortex-code/credit-usage-limit
- Changelog — https://docs.snowflake.com/en/user-guide/cortex-code/changelog
- Agent SDK — https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk

**Guides (note: moved off quickstarts.snowflake.com):**
- Getting started — https://www.snowflake.com/en/developers/guides/getting-started-with-coco-cli/
- Best practices — https://www.snowflake.com/en/developers/guides/best-practices-coco-cli/
- CoCo Foundations — https://www.snowflake.com/en/developers/guides/coco-foundations/
- **Cortex Agents with CoCo** — https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-agents-with-coco/
  ← closest template to PS1; builds a "Summit Gear Co." assistant with synthetic data,
  Cortex Search service, semantic view, and an agent
- Control Hub — https://www.snowflake.com/en/developers/guides/cortex-code-control-hub/

**GitHub (Snowflake-Labs):**
- https://github.com/Snowflake-Labs/coco-skills — curated Agent Skills (Apache 2.0)
- https://github.com/Snowflake-Labs/cocoplus — agentic OS for CoCo
- https://github.com/Snowflake-Labs/mcp — Snowflake MCP server (separate product)
- https://github.com/Snowflake-Labs/subagent-cortex-code — route work from Claude Code into CoCo

**Community:**
- Capital One TPC-DS review — https://capitalonesoftware.com/blog/snowflake-coco-cli
- 7Rivers security hardening — https://7riversinc.com/insights/securing-snowflake-coco-cli/
- Atlan overview — https://atlan.com/know/snowflake/snowflake-coco/

## Hackathon sessions

- **Intro & Problem Statement Explainer** — https://www.youtube.com/watch?v=96mM6o5DxLA
  (Hack2skill, streamed June 25, 2026). ⚠️ Transcript/captions not publicly retrievable.
- **Workshop 1** — "CoCo CLI Starter", Jul 2, 2026 — Abhay Singh, Staff Data Engineer, Snowflake
- **Workshop 2** — "CoCo CLI Hands-on", Jul 9, 2026 — Sarita Priyadarshini, Principal SE, Snowflake
- Recordings are **gated behind the participant dashboard**:
  https://hack2skill.com/event/cococlihack/dashboard/interactions
  → **You're registered — go watch these. They likely contain undocumented submission detail.**
- Discord: https://discord.gg/KMKtbxBJpW
