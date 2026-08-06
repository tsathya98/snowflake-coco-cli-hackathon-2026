/**
 * Two charts, drawn as SVG from live rows. No chart library.
 *
 * Not asceticism: a charting library would ship a client bundle to render two static pictures
 * that the server already has all the numbers for. These render on the server, cost nothing on
 * the wire beyond their own markup, and inherit the theme because every colour is a CSS
 * variable — which a canvas-based library could not do without re-rendering on theme change.
 *
 * Both are deliberately plain. A page arguing that you should not have to trust it is a bad
 * place for a chart that flatters: no truncated axes, partial buckets are labelled rather than
 * dropped, and each one carries the count it was computed from.
 */

import type { Row } from "@/lib/snowflake";
import { OTD_SUBJECT, OTD_THRESHOLD } from "@/lib/queries";

const W = 760;
const H = 240;
const PAD = { top: 14, right: 54, bottom: 26, left: 34 };

/**
 * Weekly on-time delivery per supplier, with the detection threshold.
 *
 * The point of the picture is that one line leaves the pack. Five suppliers are drawn in a
 * muted stroke and the subject in the alert colour, because a chart where every series
 * competes for attention is a chart that has not been asked what it is for.
 */
export function OnTimeTrend({ rows }: { rows: Row[] }) {
  const weeks = [...new Set(rows.map((r) => String(r.WEEK)))].sort();
  const suppliers = [...new Set(rows.map((r) => String(r.SUPPLIER)))].sort();
  if (weeks.length < 2 || suppliers.length === 0) return null;

  const x = (i: number) => PAD.left + (i * (W - PAD.left - PAD.right)) / (weeks.length - 1);
  const y = (pct: number) => PAD.top + ((100 - pct) * (H - PAD.top - PAD.bottom)) / 100;

  const series = suppliers.map((supplier) => {
    const points = weeks.map((week) => {
      const row = rows.find((r) => String(r.SUPPLIER) === supplier && String(r.WEEK) === week);
      return row ? Number(row.ON_TIME_PCT) : null;
    });
    return { supplier, points };
  });

  const path = (points: (number | null)[]) =>
    points
      .map((p, i) => (p === null ? "" : `${i === 0 || points[i - 1] === null ? "M" : "L"}${x(i)},${y(p)}`))
      .join(" ");

  const subject = series.find((s) => s.supplier === OTD_SUBJECT);
  const last = subject?.points.filter((p) => p !== null).at(-1);
  const shipments = rows.reduce((n, r) => n + Number(r.SHIPMENTS ?? 0), 0);

  return (
    <figure className="m-0 rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5" data-glow>
      <figcaption className="mb-1 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
        On-time delivery by week &middot; the signal the detector fired on
      </figcaption>
      <p className="mb-3 text-[0.82rem] leading-relaxed text-[var(--text-soft)]">
        {shipments.toLocaleString()} of the 2,400 shipments were delivered inside the last 13
        weeks; those are the ones plotted, across {suppliers.length} suppliers. Five hold their
        baseline.{" "}
        <strong style={{ color: "var(--bad)" }}>{OTD_SUBJECT}</strong> does not — and that
        divergence, not a dashboard, is what started the run.
      </p>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label={`Weekly on-time delivery. ${OTD_SUBJECT} falls to ${last}% against a detection threshold of ${OTD_THRESHOLD}%, while the other suppliers stay above it.`}
      >
        {[0, 25, 50, 75, 100].map((pct) => (
          <g key={pct}>
            <line
              x1={PAD.left}
              x2={W - PAD.right}
              y1={y(pct)}
              y2={y(pct)}
              stroke="var(--line)"
              strokeWidth="1"
            />
            <text
              x={PAD.left - 7}
              y={y(pct) + 3.5}
              textAnchor="end"
              className="fill-[var(--text-muted)] text-[9px]"
            >
              {pct}
            </text>
          </g>
        ))}

        {/* RB-001 §1. Drawn under the series so a line crossing it stays legible. */}
        <line
          x1={PAD.left}
          x2={W - PAD.right}
          y1={y(OTD_THRESHOLD)}
          y2={y(OTD_THRESHOLD)}
          stroke="var(--warn)"
          strokeWidth="1.5"
          strokeDasharray="5 4"
        />
        <text
          x={W - PAD.right + 5}
          y={y(OTD_THRESHOLD) + 3.5}
          className="fill-[var(--warn)] text-[9px] font-bold"
        >
          RB-001
        </text>

        {series
          .filter((s) => s.supplier !== OTD_SUBJECT)
          .map((s) => (
            <path
              key={s.supplier}
              d={path(s.points)}
              fill="none"
              stroke="var(--text-muted)"
              strokeWidth="1.25"
              strokeOpacity="0.5"
              strokeLinejoin="round"
            />
          ))}

        {subject ? (
          <>
            <path
              d={path(subject.points)}
              fill="none"
              stroke="var(--bad)"
              strokeWidth="2.6"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {subject.points.map((p, i) =>
              p === null ? null : <circle key={i} cx={x(i)} cy={y(p)} r="2.6" fill="var(--bad)" />,
            )}
            <text
              x={W - PAD.right + 5}
              y={y(last ?? 0) + 3.5}
              className="fill-[var(--bad)] text-[9.5px] font-bold"
            >
              {OTD_SUBJECT}
            </text>
          </>
        ) : null}

        {weeks.map((week, i) =>
          i % 2 === 0 ? (
            <text
              key={week}
              x={x(i)}
              y={H - 8}
              textAnchor="middle"
              className="fill-[var(--text-muted)] text-[9px]"
            >
              {week}
            </text>
          ) : null,
        )}
      </svg>

      <p className="mt-2 text-[0.75rem] leading-relaxed text-[var(--text-muted)]">
        Percent on time, bucketed by promised week. The dashed line is RB-001 §1 — 20 points
        below {OTD_SUBJECT}&rsquo;s 90-day baseline of 90.8%. The first and last buckets are
        partial weeks and are shown rather than trimmed, because dropping the last one would hide
        the most recent point.
      </p>
    </figure>
  );
}

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
