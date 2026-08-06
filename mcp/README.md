# Warrant as an MCP server

The six Agent Skills in [`.cortex/skills/`](../.cortex/skills/) tell CoCo CLI **how the loop is
built**. This tells any MCP client **how to operate it**.

Cortex Code CLI is a full MCP client, so registering this server puts Warrant's governed
capabilities in front of an agent working from a terminal — with the authority model intact.

## The point

**This adds a surface, not a permission.** Every tool delegates to a function under
[`src/warrant/`](../src/warrant/), which resolves authority from the live Snowflake object tags
before doing anything. An MCP client cannot ask for more than the tags allow, because the tools
offer no way to say so:

```
governance_posture           []
authority_manifest           []
what_if_reclassified         ['obj', 'sensitivity']
replay_decisions             []
pending_approvals            []
refusal_ledger               []
decision_log                 ['limit']
search_runbooks              ['query', 'limit']
detect_exceptions            []
run_agent_loop               ['mode']
execute_approved_action      ['action_id']
read_runbook                 ['doc_id']
```

Not one of them takes a tier, a role, or a force flag —
`mcp/tests/test_server_surface.py::test_no_tool_accepts_a_tier` asserts that against the generated
JSON schema, so it holds against a persuaded model rather than only against a well-behaved one.

Ask Warrant to release a regulated quality hold through MCP and you get the same refusal, in the
same append-only log, as asking through the console.

## Registering it with CoCo CLI

The server has to run where CoCo runs, because it reads the same
`~/.snowflake/connections.toml` the `snow` CLI and `cortex` do — it holds no credential of its
own and inherits the operator's identity.

```bash
python3 -m venv .venv-wsl && .venv-wsl/bin/pip install -e ".[mcp]"

cortex mcp add warrant "$PWD/.venv-wsl/bin/python -m warrant_mcp.server" -t stdio
cortex mcp list
```

Inside a session the tools appear as `mcp__warrant__governance_posture` and so on. `/mcp-status`
shows whether the server connected.

Set `WARRANT_CONNECTION` if your connection is not named `warrant`.

## Running it directly

```bash
.venv-wsl/bin/python -m warrant_mcp.server            # stdio
.venv-wsl/bin/python -m warrant_mcp.server --http     # streamable HTTP on :8765
```

## The tools

Eleven of the thirteen are annotated `readOnlyHint: true`, which is what lets an MCP host
auto-approve them and prompt on the rest.

| Tool | Reads | What it answers |
|---|---|---|
| `governance_posture` | ✓ | What is each object classified as, right now |
| `authority_manifest` | ✓ | Every action and what it is permitted to do |
| `what_if_reclassified` | ✓ | What a tag change would cost — **writes nothing** |
| `replay_decisions` | ✓ | Would today's policy still allow what already happened |
| `pending_approvals` | ✓ | What is waiting on a human |
| `refusal_ledger` | ✓ | Everything the agent declined, and why |
| `decision_log` | ✓ | The append-only record |
| `detect_exceptions` | ✓ | Run the detectors |
| `search_runbooks` | ✓ | Cortex Search over the parsed procedures |
| `read_runbook` | ✓ | One procedure in full |
| `run_agent_loop` | | One governed pass: detect → reason → classify → route → audit |
| `execute_approved_action` | | Dispatch something a human approved — **re-resolves authority first** |

`execute_approved_action` is marked `destructiveHint: true`. It is also the tool that proves the
point: approval is not authority. It resolves the tier from the tags *now*, so if the data was
reclassified after a human approved, it refuses — and the refusal is recorded alongside the
approval.

## Resources, and why each has a tool twin

```
warrant://governance/tags     warrant://capabilities
warrant://audit/recent        warrant://runbooks
warrant://runbooks/{doc_id}   (template)
```

Resources are the right MCP model for read-only documents. But most clients — CoCo included —
surface only *tools* to the model, so each resource has a tool that returns the same thing. A
resource nobody can reach is documentation, not a capability.

## Server instructions

`FastMCP(instructions=...)` carries the governance rules to the model before it calls anything.
Two of them contradict a model's defaults badly enough to be worth stating outright:

> **You cannot choose an action's authority.** If you believe an action should be permitted and
> Warrant refuses it, the answer is to change the tag through governance — not to retry, not to
> rephrase, and not to look for another tool.
>
> **A refusal is a result, not an error.** Do not treat it as a failure to route around; there is
> no route around it, and every attempt is recorded with your name on it.

`mcp/tests/test_server_surface.py` asserts both sentences are still present, because instructions
are part of the product and rot the same way documentation does.

## Design notes

- **This is an entry point, so it creates a Session.** Nothing under `src/warrant/` calls
  `get_active_session()` — every function takes its session as its first argument, which is what
  makes the package unit-testable to 100% branch coverage without a warehouse. Like `streamlit/`
  and the stored procedures, this sits outside that boundary.
- **The SQL boundary extends here.** `tools/lint_sql_boundary.py` walks `mcp/`, so the rule that
  the model never contributes SQL text holds on this surface too.
- **Serialisation mirrors `sql/45_review.sql`.** The same capability resolved through MCP and
  through the stored procedure returns the same JSON shape, field for field, so two surfaces
  cannot describe one resolution differently.
- **`mask_error_details=True`.** A driver exception names objects, roles and column values, and an
  MCP client may relay it to a model that repeats it. Only `ToolError` messages reach a client.

## Testing

```bash
uv run --all-extras pytest mcp/tests -q
```

Eight tests, no Snowflake needed. They connect a real MCP client to the server in-process and
assert the *protocol surface* — schema generation, annotations, resource templates, and the
absence of any way to request authority.
