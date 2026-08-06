/**
 * The unattended-run timeline, drawn as SVG from live rows. No chart library.
 *
 * Not asceticism: a charting library would ship a client bundle to render a picture the server
 * already has all the numbers for, and could not inherit the theme from CSS variables without
 * re-rendering on every theme change. This one stays a server component — its only interaction
 * is a native <title>, which needs no JavaScript. The detection chart wanted real crosshair
 * behaviour, so it moved to components/trend.tsx and pays for hydration; this one does not.
 *
 * Deliberately plain. A page arguing that you should not have to trust it is a bad place for a
 * chart that flatters: no truncated axes, and it carries the count it was computed from.
 */

const W = 760;

/** Snowflake task states, grouped into the three outcomes worth telling apart. */
const STATE_TONE: Record<string, string> = {
  SUCCEEDED: "good",
  SKIPPED: "muted",
  FAILED: "bad",
  FAILED_AND_AUTO_SUSPENDED: "bad",
};

/**
 * When the unattended tasks actually ran, over the last 24 hours.
 *
 * One mark per run on a 24-hour axis. The claim being illustrated is "this happened without
 * anybody watching", and the shape of a scatter over time says that in a way three counters
 * cannot — the gaps between marks are the nights nobody was at a keyboard.
 */
export function TaskTimeline({
  runs,
  tasks,
  totalRuns,
}: {
  runs: { NAME: string; STATE: string; SCHEDULED_TIME: string }[];
  tasks: { name: string }[];
  totalRuns: number;
}) {
  const parsed = runs
    .map((r) => ({ ...r, at: new Date(r.SCHEDULED_TIME.replace(" ", "T") + "Z").getTime() }))
    .filter((r) => Number.isFinite(r.at));
  if (parsed.length === 0) return null;

  // Every registered task gets a lane, not just the ones with runs in this slice. The
  // procedure returns the most recent 40 runs, and one chatty task can fill all 40 — which
  // would silently drop the other task from a chart directly under a paragraph promising two.
  const names = [...new Set([...tasks.map((t) => t.name), ...parsed.map((r) => r.NAME)])].sort();
  const end = Math.max(...parsed.map((r) => r.at));
  const start = end - 24 * 3600 * 1000;
  const span = end - start || 1;

  const rowH = 30;
  const height = names.length * rowH + 26;

  return (
    <figure className="m-0 mt-5 rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5" data-glow>
      <figcaption className="mb-1 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
        When it ran, unattended &middot; last 24 hours
      </figcaption>
      <p className="mb-3 text-[0.82rem] leading-relaxed text-[var(--text-soft)]">
        One mark per task run. The gaps are the hours nobody was at a keyboard.
      </p>

      <svg
        viewBox={`0 0 ${W} ${height}`}
        className="h-auto w-full"
        role="img"
        aria-label={`Timeline of ${parsed.length} task runs across ${names.length} task${names.length === 1 ? "" : "s"} over 24 hours.`}
      >
        {names.map((name, row) => {
          const cy = row * rowH + 16;
          return (
            <g key={name}>
              <line x1={132} x2={W - 8} y1={cy} y2={cy} stroke="var(--line)" strokeWidth="1" />
              <text x={0} y={cy + 3.5} className="fill-[var(--text-soft)] text-[10px] font-bold">
                {name}
              </text>
              {parsed
                .filter((r) => r.NAME === name)
                .map((r, i) => (
                  <circle
                    key={i}
                    cx={132 + ((r.at - start) / span) * (W - 140)}
                    cy={cy}
                    r="4"
                    fill={`var(--${STATE_TONE[r.STATE] ?? "muted"})`}
                    fillOpacity="0.85"
                  >
                    <title>{`${r.NAME} — ${r.STATE} at ${r.SCHEDULED_TIME}`}</title>
                  </circle>
                ))}
            </g>
          );
        })}
        {[0, 6, 12, 18, 24].map((h) => (
          <text
            key={h}
            x={132 + (h / 24) * (W - 140)}
            y={height - 4}
            textAnchor="middle"
            className="fill-[var(--text-muted)] text-[9px]"
          >
            {h === 24 ? "now" : `-${24 - h}h`}
          </text>
        ))}
      </svg>

      <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-[0.75rem] text-[var(--text-muted)]">
        {[
          ["good", "succeeded"],
          ["muted", "nothing to do"],
          ["bad", "failed"],
        ].map(([tone, label]) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: `var(--${tone})` }}
            />
            {label}
          </span>
        ))}
        {totalRuns > parsed.length ? (
          <span>
            showing the most recent {parsed.length} of {totalRuns} runs
          </span>
        ) : null}
      </div>
    </figure>
  );
}
