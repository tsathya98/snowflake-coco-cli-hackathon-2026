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
        statements. <strong>The buttons are live.</strong> Press one — nothing to fill in
        first — and the refusal you get back is the database&apos;s, not this page&apos;s.
      </p>

      {/* Deliberately not a textarea.
       *
       * This started as one, reproducing the console's reason field for fidelity. Two readers in
       * a row stopped and asked what they were supposed to type in it — which is the answer:
       * nothing, and a control whose correct use is "leave it alone" is the wrong control. No
       * amount of label rewriting fixed that, because the input itself is the thing making the
       * promise. So the field became an exhibit of what a reviewer writes, which is the only part
       * that was ever worth showing. */}
      <div className="mt-4">
        <div className="mb-1.5 text-[0.62rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">
          In the console, a reviewer also writes their reason
        </div>
        <blockquote className="m-0 rounded-lg border border-dashed border-[var(--line-hi)] bg-[var(--page-deep)] px-3.5 py-2.5 text-[0.86rem] italic leading-relaxed text-[var(--text-soft)]">
          &ldquo;Checked in-transit is zero and SKU-1003 is not on quality hold. Quantity restores
          to safety-stock minimum.&rdquo;
        </blockquote>
        <p className="mt-1.5 text-[0.75rem] leading-relaxed text-[var(--text-muted)]">
          Required to reject, and written to the audit row as{" "}
          <code className="font-mono">decision_note</code> — so a later reader learns what was
          checked, not just what was decided. There is no box here because there is no decision to
          annotate: press a button and Snowflake refuses it.
        </p>
      </div>

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
