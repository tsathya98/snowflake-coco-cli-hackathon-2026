"use client";

/**
 * Ask a policy question before answering it destructively.
 *
 * Two dropdowns and a live re-resolution of the whole capability registry. This is the
 * one interactive control on a read-only page, and it belongs here for the same reason
 * approving does not: it computes and writes nothing. The distinction the project argues
 * for — a read is not an act — is what decides which controls a surface with no identity
 * may have.
 *
 * Rendered from the server's manifest on first paint so the list is present without
 * JavaScript; the dropdowns then swap in a hypothetical via a server action.
 */

import { useState, useTransition } from "react";
import { whatIf } from "@/app/actions";
import { OUTCOME_TONE, type Capability, type ManifestPayload } from "@/lib/queries";
import { Card, Reveal, Tag } from "@/components/ui";

const OBJECTS = [
  "WARRANT.DATA.SHIPMENTS",
  "WARRANT.DATA.SUPPLIERS",
  "WARRANT.DATA.SKUS",
  "WARRANT.DATA.INVENTORY",
  "WARRANT.DATA.QUALITY_HOLDS",
  "WARRANT.DATA.OPS_REQUESTS",
  "WARRANT.DATA.RUNBOOKS",
];

const SENSITIVITIES = ["open", "internal", "regulated", "untagged"];

const field =
  "w-full min-h-11 rounded-lg border border-[var(--line)] bg-[var(--surface)] px-3 py-2 " +
  "text-[0.88rem] text-[var(--text)] transition-colors hover:border-[var(--line-hi)] " +
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-[var(--info)]";

function CapabilityCard({ capability }: { capability: Capability }) {
  const name = OUTCOME_TONE[capability.outcome] ?? "muted";
  return (
    <Card tone={name}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <span className="font-mono text-[0.92rem] font-bold">{capability.action}</span>
        <span
          className="text-[0.66rem] font-extrabold uppercase tracking-[0.11em]"
          style={{ color: `var(--${name})` }}
        >
          {capability.outcome}
        </span>
      </div>
      <div className="mt-2">
        {capability.classifications.map((c) => (
          <Tag key={c.object}>
            {c.object.split(".").pop()} &middot; {c.sensitivity ?? "untagged"}
          </Tag>
        ))}
      </div>
      <div className="mt-2 text-[0.8rem] leading-relaxed text-[var(--text-muted)]">
        {capability.rationale}
      </div>
    </Card>
  );
}

export function WhatIf({ initial }: { initial: ManifestPayload }) {
  const [payload, setPayload] = useState(initial);
  const [object, setObject] = useState("none");
  const [sensitivity, setSensitivity] = useState("regulated");
  const [error, setError] = useState<string | null>(null);
  const [pending, start] = useTransition();

  const run = (nextObject: string, nextSensitivity: string) => {
    setObject(nextObject);
    setSensitivity(nextSensitivity);
    start(async () => {
      const result = await whatIf(nextObject, nextSensitivity);
      if (result.ok) {
        setPayload(result.payload);
        setError(null);
      } else {
        setError(result.error);
      }
    });
  };

  const revoked = (payload.changes ?? []).filter((c) => c.revocation);
  const widened = (payload.changes ?? []).filter((c) => !c.revocation);
  const hypothetical = object !== "none";

  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-[1fr_auto_14rem]">
        <label className="block">
          <span className="mb-1.5 block text-[0.62rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">
            If this object were reclassified…
          </span>
          <select
            className={field}
            value={object}
            onChange={(e) => run(e.target.value, sensitivity)}
          >
            <option value="none">(nothing — show the live position)</option>
            {OBJECTS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </label>

        <div className="hidden items-end pb-2.5 text-[var(--text-muted)] sm:flex">→</div>

        <label className="block">
          <span className="mb-1.5 block text-[0.62rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">
            …to
          </span>
          <select
            className={field}
            value={sensitivity}
            disabled={!hypothetical}
            onChange={(e) => run(object, e.target.value)}
          >
            {SENSITIVITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div
        aria-live="polite"
        className={`mt-4 transition-opacity duration-200 ${pending ? "opacity-50" : "opacity-100"}`}
      >
        {error ? (
          <div
            className="rounded-xl border p-3.5 text-[0.86rem]"
            style={{
              borderColor: "color-mix(in srgb, var(--bad) 45%, transparent)",
              background: "color-mix(in srgb, var(--bad) 10%, transparent)",
            }}
          >
            {error}
          </div>
        ) : null}

        {!error && hypothetical && revoked.length > 0 ? (
          <div
            className="rounded-xl border p-3.5 text-[0.88rem] leading-relaxed sm:px-4"
            style={{
              borderColor: "color-mix(in srgb, var(--bad) 45%, transparent)",
              background: "color-mix(in srgb, var(--bad) 10%, transparent)",
            }}
          >
            <strong>
              {revoked.length} {revoked.length === 1 ? "capability" : "capabilities"} would be
              revoked
            </strong>{" "}
            by tagging <code className="font-mono">{object.split(".").pop()}</code> as{" "}
            <code className="font-mono">{sensitivity}</code>:{" "}
            {revoked.map((c, i) => (
              <span key={c.action}>
                {i > 0 ? ", " : ""}
                <code className="font-mono">{c.action}</code> ({c.from_outcome} → {c.to_outcome})
              </span>
            ))}
          </div>
        ) : null}

        {!error && hypothetical && widened.length > 0 ? (
          <div
            className="mt-2.5 rounded-xl border p-3.5 text-[0.88rem] leading-relaxed sm:px-4"
            style={{
              borderColor: "color-mix(in srgb, var(--warn) 45%, transparent)",
              background: "color-mix(in srgb, var(--warn) 10%, transparent)",
            }}
          >
            <strong>
              {widened.length} {widened.length === 1 ? "capability" : "capabilities"} would be
              widened
            </strong>
            :{" "}
            {widened.map((c, i) => (
              <span key={c.action}>
                {i > 0 ? ", " : ""}
                <code className="font-mono">{c.action}</code> ({c.from_outcome} → {c.to_outcome})
              </span>
            ))}
          </div>
        ) : null}

        {!error && hypothetical && revoked.length === 0 && widened.length === 0 ? (
          <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-3.5 text-[0.88rem] text-[var(--text-soft)]">
            No capability changes. This reclassification would cost the agent nothing.
          </div>
        ) : null}

        <div className="mt-4 space-y-2.5">
          {payload.capabilities.map((capability, i) => (
            <Reveal key={capability.action} delay={i * 45}>
              <CapabilityCard capability={capability} />
            </Reveal>
          ))}
        </div>
      </div>

      <p className="mt-3 text-[0.78rem] leading-relaxed text-[var(--text-muted)]">
        Nothing above was written. This resolves the <em>real</em> rules against hypothetical
        inputs — no <code className="font-mono">ALTER TABLE</code>, no row touched, nothing to
        undo. It is the same resolver the executor uses, so it cannot disagree with what would
        actually happen.
      </p>
    </div>
  );
}
