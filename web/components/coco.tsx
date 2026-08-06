/**
 * How an operator actually drives this: the CoCo CLI, over MCP.
 *
 * The rest of the page is output — what the agent decided, and why it was allowed to.
 * This section is the input, and it was missing: a judge reading the deployed link had no
 * way to tell that the whole agent is exposed as an MCP server with a governed tool
 * surface, which for a CLI hackathon is the part that most needs to be visible.
 *
 * The counts here are asserted by tools/check_doc_claims.py against mcp/warrant_mcp/server.py,
 * so a tool added without updating this page fails the repo gate rather than quietly making
 * the page wrong.
 */

import { Mark } from "@/components/mark";

/** Every tool the server exposes, in the order the server defines them. */
const TOOLS: [string, string, "read" | "act"][] = [
  ["governance_posture", "The tags in force, read live", "read"],
  ["authority_manifest", "Every action resolved against them", "read"],
  ["what_if_reclassified", "Price a policy change before making it", "read"],
  ["replay_decisions", "Re-resolve history against today's tags", "read"],
  ["pending_approvals", "What is waiting on a human", "read"],
  ["refusal_ledger", "What it declined, and why", "read"],
  ["decision_log", "The append-only audit trail", "read"],
  ["search_runbooks", "Cortex Search over the procedures", "read"],
  ["detect_exceptions", "Rolling baselines, statistical outliers", "read"],
  ["task_activity", "What ran unattended, and how it went", "read"],
  ["read_runbook", "One procedure, by id", "read"],
  ["run_agent_loop", "One governed pass — AUTO or DRY_RUN", "act"],
  ["execute_approved_action", "Dispatch what a human already approved", "act"],
];

const RESOURCES = [
  "warrant://governance/tags",
  "warrant://capabilities",
  "warrant://audit/recent",
  "warrant://runbooks",
  "warrant://runbooks/{doc_id}",
];

const SKILLS: [string, string][] = [
  ["detect-anomaly", "rolling baselines, every threshold traceable to a runbook clause"],
  ["investigate-root-cause", "structured evidence plus Cortex Search, schema-validated finding"],
  ["propose-action", "a typed, reversible action with an explicit rollback path"],
  ["classify-authority", "the tier, derived from tags rather than a rules list"],
  ["orchestrate-loop", "detect → investigate → classify → route → audit, idempotently"],
  ["operate-warrant", "drive all of the above from the CLI, without choosing your own authority"],
];

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5"
      data-glow
    >
      <div className="mb-3 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
        {title}
      </div>
      {children}
    </div>
  );
}

export function Coco() {
  const reads = TOOLS.filter((t) => t[2] === "read").length;
  const acts = TOOLS.length - reads;

  return (
    <div className="space-y-5">
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Panel title={`The tool surface — ${TOOLS.length} tools, ${reads} read, ${acts} act`}>
          <ul className="m-0 list-none space-y-1.5 p-0">
            {TOOLS.map(([name, what, kind]) => (
              <li key={name} className="flex flex-wrap items-baseline gap-x-2.5 gap-y-0.5">
                <span
                  className="rounded px-1.5 py-px text-[0.58rem] font-extrabold uppercase tracking-[0.08em]"
                  style={{
                    color: kind === "act" ? "var(--warn)" : "var(--good)",
                    background: `color-mix(in srgb, var(--${kind === "act" ? "warn" : "good"}) 14%, transparent)`,
                  }}
                >
                  {kind}
                </span>
                <code className="font-mono text-[0.79rem] font-bold">{name}</code>
                <span className="text-[0.78rem] text-[var(--text-muted)]">{what}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3.5 text-[0.78rem] leading-relaxed text-[var(--text-muted)]">
            Every one carries MCP <code className="font-mono">ToolAnnotations</code>, so a client
            knows before calling which tools only read. The two that act are marked truthfully —{" "}
            <code className="font-mono">execute_approved_action</code> declares{" "}
            <code className="font-mono">destructiveHint: true</code>, because it is.
          </p>
        </Panel>

        <div className="space-y-5">
          <Panel title={`${RESOURCES.length} resources, each with a tool twin`}>
            <ul className="m-0 list-none space-y-1 p-0">
              {RESOURCES.map((uri) => (
                <li key={uri} className="font-mono text-[0.76rem] text-[var(--text-soft)]">
                  {uri}
                </li>
              ))}
            </ul>
            <p className="mt-3 text-[0.78rem] leading-relaxed text-[var(--text-muted)]">
              Resources are the right shape for state a client should be able to subscribe to.
              But not every client supports them, and a governance posture nobody can read is
              worse than a duplicated surface — so each is also reachable as a tool.
            </p>
          </Panel>

          <Panel title="6 CoCo skills">
            <ul className="m-0 list-none space-y-1.5 p-0">
              {SKILLS.map(([name, what]) => (
                <li key={name}>
                  <code className="font-mono text-[0.78rem] font-bold">{name}</code>
                  <span className="text-[0.77rem] text-[var(--text-muted)]"> — {what}</span>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      {/* The invariant. This is the part worth stopping on. */}
      <div
        className="rounded-xl border p-4 sm:p-5"
        style={{
          borderColor: "color-mix(in srgb, var(--info) 42%, transparent)",
          background: "color-mix(in srgb, var(--info) 8%, transparent)",
        }}
        data-glow
      >
        <div className="flex items-start gap-2.5">
          <Mark size={17} />
          <div className="min-w-0">
            <div className="text-[0.95rem] font-bold">
              No tool on this server accepts an authority tier.
            </div>
            {/* Measure capped across this panel. Full-bleed at 1152px these ran to about 130
             *  characters a line — legible in isolation, tiring for three paragraphs running. */}
            <p className="mt-1.5 max-w-[78ch] text-[0.86rem] leading-relaxed text-[var(--text-soft)]">
              A tool that took <code className="font-mono">tier</code> as a parameter would hand
              the model the one decision the whole design exists to keep away from it. Every tool
              resolves the tier itself, from the live tag. There is nothing to pass and no
              elevated value to ask for — so prompt-engineering the model into a higher authority
              has no parameter to aim at.
            </p>
            <p className="mt-2.5 max-w-[78ch] text-[0.86rem] leading-relaxed text-[var(--text-soft)]">
              That is an easy claim to make and an easy one to break by accident, so it is a test
              rather than a comment. It walks the live schema of every registered tool:
            </p>
            <pre className="mt-2.5 overflow-x-auto rounded-lg bg-[var(--page-deep)] p-3 font-mono text-[0.73rem] leading-relaxed text-[var(--text-soft)]">
              {`async def test_no_tool_accepts_a_tier():
    for tool in await client.list_tools():
        for field in (tool.inputSchema or {}).get("properties", {}):
            assert "tier" not in field.lower()`}
            </pre>
            <p className="mt-2 text-[0.78rem] text-[var(--text-muted)]">
              <code className="font-mono">mcp/tests/test_server_surface.py</code>, run through an
              in-process client against the real server object.
            </p>
          </div>
        </div>
      </div>

      <Panel title="Drive it yourself">
        <p className="max-w-[78ch] text-[0.86rem] leading-relaxed text-[var(--text-soft)]">
          The agent has no privileged path of its own. What CoCo can do is exactly what the tool
          surface above allows, and the server tells the model so in its{" "}
          <code className="font-mono">instructions</code> before it calls anything:
        </p>
        <blockquote className="mt-3 border-l-2 border-[var(--line-hi)] pl-3.5 text-[0.85rem] italic leading-relaxed text-[var(--text-soft)]">
          &ldquo;You cannot choose an action&rsquo;s authority… If you believe an action should be
          permitted and Warrant refuses it, the answer is to change the tag through governance —
          not to retry, not to rephrase, and not to look for another tool.&rdquo;
          <br />
          &ldquo;A refusal is a result, not an error.&rdquo;
        </blockquote>
        <pre className="mt-3.5 overflow-x-auto rounded-lg bg-[var(--page-deep)] p-3 font-mono text-[0.74rem] leading-relaxed text-[var(--text-soft)]">
          {`cortex mcp add warrant "$PWD/.venv-wsl/bin/python -m warrant_mcp.server" -t stdio
cortex mcp list

# then, in a session — the skills in .cortex/skills/ are already loaded
> what is the agent allowed to do right now, and what would it cost me
  to reclassify INVENTORY as regulated?`}
        </pre>
        <p className="mt-2 text-[0.78rem] leading-relaxed text-[var(--text-muted)]">
          The server holds no credential of its own. It reads the same{" "}
          <code className="font-mono">~/.snowflake/connections.toml</code> that{" "}
          <code className="font-mono">snow</code> and <code className="font-mono">cortex</code> do,
          so it inherits the operator&rsquo;s identity rather than acquiring one — an agent should
          not be able to reach further than the person running it.
        </p>
      </Panel>
    </div>
  );
}
