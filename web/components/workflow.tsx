/**
 * What the thing actually does, before any claim about how it is governed.
 *
 * This section exists because a reader who understood the governance still could not answer
 * "so what is the workflow?" — the page led with the mechanism and never showed the job. The
 * mechanism is the differentiator, but it is the answer to a question nobody has yet been asked.
 *
 * Two halves, in the order a person actually needs them:
 *
 *   1. The stages, once. Seven of them, with the gate marked. This is the workflow in the sense
 *      an operations person means it: a thing enters, moves, and leaves in a known state.
 *   2. The same seven stages run three times on three real exceptions, exiting three different
 *      ways. That is the load-bearing claim made visible — one pipeline, no branch on table
 *      name, and the classification of the data decides the exit.
 *
 * The three lanes are hard-coded rather than derived. They are the *explanation* of one measured
 * run, and the figures in them are asserted against the live account by tools/check_doc_claims.py
 * through the README. A version that rebuilt itself from whatever happened to be in the table
 * this minute would be a status board, and this is a diagram.
 */

const STAGES: [string, string, string][] = [
  ["Watch", "Rolling baselines over shipments, inventory and holds", "unattended"],
  ["Detect", "An exception, with the runbook clause that set the threshold", "unattended"],
  ["Investigate", "Grounded reasoning over the procedures, cites its source", "unattended"],
  ["Classify", "Read the governance tags on every table the action touches", "the gate"],
  ["Route", "Act, queue for a human, or refuse — decided by the tags", "the gate"],
  ["Execute", "Re-read the tags. An approval does not survive a policy change", "the gate"],
  ["Audit", "Append-only. Refusals recorded with the same care as actions", "unattended"],
];

type Lane = {
  entity: string;
  what: string;
  table: string;
  tag: string;
  action: string;
  exit: string;
  tone: "good" | "warn" | "bad";
  gate: string;
};

const LANES: Lane[] = [
  {
    entity: "SUP-002",
    what: "On-time delivery fell to 26% against a 91% baseline",
    table: "SHIPMENTS",
    tag: "open",
    action: "open_supplier_case",
    exit: "Done, no human",
    tone: "good",
    gate: "Nobody was asked. The data is tagged open, the action is reversible, and it is logged.",
  },
  {
    entity: "SKU-1003",
    what: "Five days of cover left, 49,000 units below safety stock",
    table: "INVENTORY",
    tag: "internal",
    action: "raise_replenishment",
    exit: "Waiting for a human",
    tone: "warn",
    gate: "Prepared in full — evidence, parameters, undo path — and stopped. A replenishment commits spend.",
  },
  {
    entity: "QH-0034",
    what: "A quality hold, open 82 days, still undispositioned",
    table: "QUALITY_HOLDS",
    tag: "regulated",
    action: "release_quality_hold",
    exit: "Refused outright",
    tone: "bad",
    gate: "It may surface the hold and explain it. Releasing it is never the agent's, at any confidence.",
  },
];

export function Workflow() {
  return (
    <div>
      <ol className="m-0 grid list-none gap-2 p-0 sm:grid-cols-2 lg:grid-cols-4">
        {STAGES.map(([name, what, kind], i) => {
          const gated = kind === "the gate";
          return (
            <li
              key={name}
              className="rounded-xl border bg-[var(--surface)] p-3.5"
              style={{
                borderColor: gated
                  ? "color-mix(in srgb, var(--warn) 38%, transparent)"
                  : "var(--line)",
              }}
              data-glow
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-[0.7rem] text-[var(--text-muted)]">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-[0.9rem] font-bold">{name}</span>
              </div>
              <p className="mt-1 text-[0.79rem] leading-relaxed text-[var(--text-muted)]">{what}</p>
              <div
                className="mt-2 text-[0.6rem] font-bold uppercase tracking-[0.1em]"
                style={{ color: gated ? "var(--warn)" : "var(--good)" }}
              >
                {kind}
              </div>
            </li>
          );
        })}
      </ol>

      <p className="mt-4 max-w-[80ch] text-[0.88rem] leading-relaxed text-[var(--text-soft)]">
        <strong>Stages 4 to 6 are the whole idea.</strong> Everything before them is a pipeline any
        competent team would build. What decides whether an exception is handled, escalated or
        refused is not a rule in the application — it is the governance tag already sitting on the
        table the action would touch. Below: the same seven stages, run three times, on one pass.
      </p>

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        {LANES.map((lane) => (
          <div
            key={lane.entity}
            className="flex flex-col rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4"
            style={{ "--tone": `var(--${lane.tone})` } as React.CSSProperties}
            data-glow
          >
            <div className="font-mono text-[0.9rem] font-bold">{lane.entity}</div>
            <p className="mt-1 text-[0.82rem] leading-relaxed text-[var(--text-soft)]">
              {lane.what}
            </p>

            <div className="mt-3 rounded-lg bg-[var(--page-deep)] p-2.5 font-mono text-[0.72rem] leading-relaxed">
              <div className="text-[var(--text-muted)]">touches</div>
              <div className="text-[var(--text-soft)]">
                {lane.table}{" "}
                <span style={{ color: `var(--${lane.tone})` }}>
                  &middot; sensitivity=&lsquo;{lane.tag}&rsquo;
                </span>
              </div>
              <div className="mt-1.5 text-[var(--text-muted)]">proposes</div>
              <div className="text-[var(--text-soft)]">{lane.action}</div>
            </div>

            <div
              className="mt-3 rounded-lg px-3 py-2 text-[0.8rem] font-extrabold"
              style={{
                color: `var(--${lane.tone})`,
                background: `color-mix(in srgb, var(--${lane.tone}) 12%, transparent)`,
              }}
            >
              {lane.exit}
            </div>
            <p className="mt-2 text-[0.78rem] leading-relaxed text-[var(--text-muted)]">
              {lane.gate}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-4 max-w-[80ch] text-[0.88rem] leading-relaxed text-[var(--text-soft)]">
        Three outcomes from one pass, and{" "}
        <strong>there is no <code className="font-mono">if table_name ==</code> anywhere in the
        code.</strong>{" "}
        Retag <code className="font-mono">INVENTORY</code> as regulated and the middle lane
        stops being an escalation and starts being a refusal — no deploy, no code change. That is
        the difference between an agent with permissions and an agent with a warrant.
      </p>
    </div>
  );
}
