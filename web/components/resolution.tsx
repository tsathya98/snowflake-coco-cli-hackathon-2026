/**
 * The idea, above the fold, in one picture.
 *
 * Everything below the hero is evidence for a single claim, and a reader who does not get
 * the claim in the first five seconds will not read the evidence. The claim is: a tag on
 * a table decides what an agent may do to it. So the picture is three rows of
 * `tag → resolver → tier`, and nothing else.
 *
 * It is not an illustration. The rows come from the same `SYSTEM$GET_TAG` read that feeds
 * the governance table further down, so if someone reclassifies a table in Snowflake this
 * diagram changes on the next request — which is the property being claimed, demonstrated
 * by the thing doing the claiming. A hand-drawn SVG of the same three rows would look
 * identical and prove nothing, and that difference is worth the extra prop.
 *
 * Three rows, not seven: the hero shows one object per outcome, because the point is that
 * the three outcomes exist and are decided by the tag. The full seven are in the
 * governance section for anyone who wants them.
 */

import type { Row } from "@/lib/snowflake";
import { Mark } from "@/components/mark";

const OUTCOME: Record<string, { tier: string; label: string; tone: string }> = {
  open: { tier: "L2", label: "acts unsupervised", tone: "good" },
  internal: { tier: "L3", label: "needs human approval", tone: "warn" },
  regulated: { tier: "L4", label: "never permitted", tone: "bad" },
  untagged: { tier: "L3", label: "needs human approval", tone: "warn" },
};

/** One object per outcome, most-restricted first — the same ordering the manifest uses. */
const SHOWN = [
  "WARRANT.DATA.QUALITY_HOLDS",
  "WARRANT.DATA.INVENTORY",
  "WARRANT.DATA.SHIPMENTS",
];

export function Resolution({ governance }: { governance: Row[] }) {
  const rows = SHOWN.map((fqn) => {
    const found = governance.find((g) => String(g.OBJECT) === fqn);
    const sensitivity = String(found?.SENSITIVITY ?? "untagged");
    return { fqn, sensitivity, ...(OUTCOME[sensitivity] ?? OUTCOME.untagged) };
  });

  return (
    <div
      className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5"
      data-glow
    >
      <div className="flex items-center justify-between gap-3">
        <div className="text-[0.6rem] font-bold uppercase tracking-[0.13em] text-[var(--text-muted)]">
          Authority, resolved
        </div>
        <div className="text-[0.6rem] font-bold uppercase tracking-[0.13em] text-[var(--text-muted)]">
          read live &middot; not drawn
        </div>
      </div>

      <div className="mt-3.5 space-y-2">
        {rows.map((row, i) => (
          <div
            key={row.fqn}
            className="resolve-row grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-2 rounded-xl border border-[var(--line)] bg-[var(--page-deep)] px-3 py-2.5 sm:grid-cols-[minmax(0,1fr)_2.5rem_minmax(0,1fr)]"
            style={{ "--tone": `var(--${row.tone})`, animationDelay: `${i * 130}ms` } as React.CSSProperties}
          >
            {/* what the tag says */}
            <div className="min-w-0">
              <div className="truncate font-mono text-[0.78rem] font-bold">
                {row.fqn.split(".").pop()}
              </div>
              <div className="mt-0.5 text-[0.72rem] text-[var(--text-muted)]">
                sensitivity =&nbsp;
                <span className="font-mono text-[var(--text-soft)]">
                  &lsquo;{row.sensitivity}&rsquo;
                </span>
              </div>
            </div>

            {/* the resolver. A pulse travels the wire on a loop — the only moving part. */}
            <div className="hidden justify-self-center sm:block" aria-hidden>
              <div className="resolve-wire" />
            </div>

            {/* what it may do */}
            <div className="justify-self-end text-right sm:justify-self-start sm:text-left">
              <div
                className="text-[0.78rem] font-extrabold"
                style={{ color: `var(--${row.tone})` }}
              >
                {row.tier} &middot; {row.label}
              </div>
              <div className="mt-0.5 text-[0.72rem] text-[var(--text-muted)]">
                no code change to alter this
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3.5 flex items-start gap-2 text-[0.76rem] leading-relaxed text-[var(--text-muted)]">
        <Mark size={15} />
        <span>
          Read with <code className="font-mono">SYSTEM$GET_TAG</code> on this request, and again
          when the action runs. Retag a table and the row above changes — no deploy.
        </span>
      </div>
    </div>
  );
}
