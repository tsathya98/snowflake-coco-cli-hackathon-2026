"use client";

/**
 * The approval controls from the governed console, reproduced here so they can be refused.
 *
 * The obvious way to build a read-only page is to leave the buttons out. That teaches a
 * visitor nothing: an absent button is indistinguishable from a hidden one, and "trust us,
 * this page cannot act" is exactly the claim an audience should not have to take on faith.
 *
 * So the controls are present and live. Pressing one sends the real statement the console
 * sends and prints Snowflake's own refusal, error code and all. The boundary is not drawn
 * by this component — it is drawn by a role with no grant on EXECUTE_ACTION, and pressing
 * the button is how you check.
 *
 * The note field is here for the same reason. In the console it becomes `decision_note` on
 * the audit row; here it is never sent anywhere, because there is no decision to annotate.
 */

import { useState, useTransition } from "react";
import { attemptDecision, type DecisionAttempt } from "@/app/actions";

const CHOICES: [string, string, string][] = [
  ["approved", "Approve and execute", "bad"],
  ["rejected", "Reject", "muted"],
  ["deferred", "Defer", "muted"],
];

export function Decide({ actionType }: { actionType: string }) {
  const [result, setResult] = useState<DecisionAttempt | null>(null);
  const [tried, setTried] = useState<string | null>(null);
  const [pending, start] = useTransition();

  const attempt = (decision: string) => {
    setTried(decision);
    start(async () => setResult(await attemptDecision(decision)));
  };

  return (
    <div className="mt-5 rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5">
      <div className="text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
        Try to decide it
      </div>
      <p className="mt-1.5 text-[0.84rem] leading-relaxed text-[var(--text-soft)]">
        These are the controls a reviewer sees in the Snowflake console, wired to the same
        statements. Press one. The refusal you get back is the database&apos;s, not this
        page&apos;s.
      </p>

      <label className="mt-4 block">
        <span className="mb-1.5 block text-[0.62rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">
          Your reason (required to reject)
        </span>
        <textarea
          rows={2}
          placeholder="What did you check? What made this the right call?"
          className="w-full resize-y rounded-lg border border-[var(--line)] bg-[var(--page-deep)] px-3 py-2 text-[0.88rem] text-[var(--text)] transition-colors placeholder:text-[var(--text-muted)] hover:border-[var(--line-hi)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--info)]"
        />
        <span className="mt-1 block text-[0.72rem] text-[var(--text-muted)]">
          Goes nowhere. In the console this lands on the audit row as{" "}
          <code className="font-mono">decision_note</code>; there is no audit row to write
          here.
        </span>
      </label>

      <div className="mt-3 flex flex-wrap gap-2.5">
        {CHOICES.map(([decision, label, tone]) => (
          <button
            key={decision}
            type="button"
            disabled={pending}
            onClick={() => attempt(decision)}
            style={{ "--tone": `var(--${tone})` } as React.CSSProperties}
            className="min-h-11 rounded-lg border border-[var(--line-hi)] bg-[var(--surface-hi)] px-4 text-[0.84rem] font-bold text-[var(--text)] transition-all hover:border-[var(--tone)] hover:text-[var(--tone)] disabled:cursor-wait disabled:opacity-50"
          >
            {pending && tried === decision ? "Asking Snowflake…" : label}
          </button>
        ))}
      </div>

      <div aria-live="polite" className="mt-4">
        {result?.outcome === "refused" ? (
          <div
            className="rounded-xl border p-3.5 sm:px-4"
            style={{
              borderColor: "color-mix(in srgb, var(--bad) 45%, transparent)",
              background: "color-mix(in srgb, var(--bad) 10%, transparent)",
            }}
          >
            <div className="text-[0.66rem] font-extrabold uppercase tracking-[0.11em] text-[var(--bad)]">
              Refused by Snowflake
            </div>
            <p className="mt-1.5 text-[0.86rem] leading-relaxed">
              The statement below was sent as{" "}
              <code className="font-mono text-[0.85em]">WARRANT_PUBLIC</code> and rejected before
              it ran. Nothing about <code className="font-mono text-[0.85em]">{actionType}</code>{" "}
              changed.
            </p>
            <pre className="mt-2.5 overflow-x-auto rounded-lg bg-[var(--page-deep)] p-3 font-mono text-[0.74rem] leading-relaxed text-[var(--text-soft)]">
              {result.statement}
            </pre>
            <pre className="mt-2 overflow-x-auto rounded-lg bg-[var(--page-deep)] p-3 font-mono text-[0.74rem] leading-relaxed text-[var(--bad)]">
              {result.error}
            </pre>
            <p className="mt-2.5 text-[0.78rem] leading-relaxed text-[var(--text-muted)]">
              {/* The two refusals differ in kind, and the stronger one is easy to miss. */}
              {result.error.includes("Unknown user-defined function")
                ? "Read that carefully — it is not “permission denied”. Without USAGE on the procedure, Snowflake will not concede that the executor exists. This role cannot be tricked into calling something it cannot name."
                : "The role can see the queue and is told no. Approval is a write, and writes belong to an identity that can be held to them."}
            </p>
          </div>
        ) : null}

        {/* Should never render. If it does, a grant is wrong and saying so loudly is more
            use than a page that quietly keeps claiming to be read-only. */}
        {result?.outcome === "permitted" ? (
          <div
            className="rounded-xl border p-3.5"
            style={{ borderColor: "var(--bad)", background: "color-mix(in srgb, var(--bad) 22%, transparent)" }}
          >
            <strong>Boundary failure.</strong> That statement was permitted. It bound an action
            id that cannot exist, so nothing was executed — but a grant on this role is wrong
            and should be revoked.
          </div>
        ) : null}

        {result?.outcome === "unavailable" ? (
          <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-3.5 text-[0.86rem] text-[var(--text-soft)]">
            Could not reach Snowflake. Try again in a moment.
          </div>
        ) : null}
      </div>
    </div>
  );
}
