"use client";

/**
 * The detection chart, made interactive.
 *
 * Still no chart library, and still server-rendered on first paint: a client component in the
 * App Router ships its HTML with the document, so a reader with JavaScript disabled — or one
 * looking at it before hydration — sees the same picture the static version drew. Interactivity
 * is added on top of a correct chart rather than being the thing that produces one.
 *
 * Three interactions, each answering a question the static version left open:
 *
 *   hover the plot  → "what were the others doing that week?"  A crosshair reads every series
 *                     at the nearest week and ranks them, so the pack is a number, not a smudge.
 *   hover a legend  → "which grey line is which?"  Focus one series, dim the rest.
 *   click a legend  → the same, but pinned, because on a touch screen hover does not exist and
 *                     on a laptop you want to read the tooltip without holding the mouse still.
 *
 * The crosshair deliberately reads *all* series rather than the nearest point. Nearest-point
 * tooltips are easier to build and answer the wrong question here: the claim is comparative —
 * one supplier left the pack — so the pack has to be in the tooltip.
 */

import { useCallback, useMemo, useRef, useState } from "react";
import type { Row } from "@/lib/snowflake";
import { OTD_SUBJECT, OTD_THRESHOLD } from "@/lib/queries";

const W = 760;
const H = 240;
const PAD = { top: 14, right: 54, bottom: 26, left: 34 };

export function OnTimeTrend({ rows }: { rows: Row[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [at, setAt] = useState<number | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);

  const { weeks, suppliers, series, shipments } = useMemo(() => {
    const weeks = [...new Set(rows.map((r) => String(r.WEEK)))].sort();
    const suppliers = [...new Set(rows.map((r) => String(r.SUPPLIER)))].sort();
    const series = suppliers.map((supplier) => ({
      supplier,
      points: weeks.map((week) => {
        const row = rows.find((r) => String(r.SUPPLIER) === supplier && String(r.WEEK) === week);
        return row ? Number(row.ON_TIME_PCT) : null;
      }),
    }));
    return {
      weeks,
      suppliers,
      series,
      shipments: rows.reduce((n, r) => n + Number(r.SHIPMENTS ?? 0), 0),
    };
  }, [rows]);

  const x = useCallback(
    (i: number) => PAD.left + (i * (W - PAD.left - PAD.right)) / Math.max(1, weeks.length - 1),
    [weeks.length],
  );
  const y = (pct: number) => PAD.top + ((100 - pct) * (H - PAD.top - PAD.bottom)) / 100;

  /** Map a client x-coordinate to the nearest week index, through the viewBox scale. */
  const track = useCallback(
    (clientX: number) => {
      const box = svgRef.current?.getBoundingClientRect();
      if (!box) return;
      const local = ((clientX - box.left) / box.width) * W;
      const step = (W - PAD.left - PAD.right) / Math.max(1, weeks.length - 1);
      const i = Math.round((local - PAD.left) / step);
      setAt(Math.min(weeks.length - 1, Math.max(0, i)));
    },
    [weeks.length],
  );

  if (weeks.length < 2 || suppliers.length === 0) return null;

  const focus = pinned ?? hovered;
  const subject = series.find((s) => s.supplier === OTD_SUBJECT);
  const last = subject?.points.filter((p) => p !== null).at(-1);

  const path = (points: (number | null)[]) =>
    points
      .map((p, i) =>
        p === null ? "" : `${i === 0 || points[i - 1] === null ? "M" : "L"}${x(i)},${y(p)}`,
      )
      .join(" ");

  const tone = (supplier: string) => (supplier === OTD_SUBJECT ? "var(--bad)" : "var(--text-muted)");

  /** Everyone's value at the tracked week, worst first — the ranking is the comparison. */
  const reading =
    at === null
      ? []
      : series
          .map((s) => ({ supplier: s.supplier, value: s.points[at] }))
          .filter((r): r is { supplier: string; value: number } => r.value !== null)
          .sort((a, b) => a.value - b.value);

  return (
    <figure
      className="m-0 rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5"
      data-glow
    >
      <figcaption className="mb-1 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
        On-time delivery by week &middot; the signal the detector fired on
      </figcaption>
      <p className="mb-3 text-[0.82rem] leading-relaxed text-[var(--text-soft)]">
        {shipments.toLocaleString()} of the 2,400 shipments were delivered inside the last{" "}
        {weeks.length} weeks; those are the ones plotted, across {suppliers.length} suppliers. Five
        hold their baseline. <strong style={{ color: "var(--bad)" }}>{OTD_SUBJECT}</strong> does not
        — and that divergence, not a dashboard, is what started the run.
      </p>

      <div className="relative">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          className="h-auto w-full touch-pan-y"
          role="img"
          aria-label={`Weekly on-time delivery. ${OTD_SUBJECT} falls to ${last}% against a detection threshold of ${OTD_THRESHOLD}%, while the other suppliers stay above it.`}
          onMouseMove={(e) => track(e.clientX)}
          onMouseLeave={() => setAt(null)}
          onTouchStart={(e) => track(e.touches[0].clientX)}
          onTouchMove={(e) => track(e.touches[0].clientX)}
          onTouchEnd={() => setAt(null)}
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

          {/* RB-001 §1. Under the series, so a line crossing it stays legible. */}
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

          {at !== null ? (
            <line
              x1={x(at)}
              x2={x(at)}
              y1={PAD.top}
              y2={H - PAD.bottom}
              stroke="var(--line-hi)"
              strokeWidth="1"
            />
          ) : null}

          {series.map((s) => {
            const isSubject = s.supplier === OTD_SUBJECT;
            const dimmed = focus !== null && focus !== s.supplier;
            return (
              <g key={s.supplier}>
                <path
                  d={path(s.points)}
                  fill="none"
                  stroke={tone(s.supplier)}
                  strokeWidth={focus === s.supplier ? 2.8 : isSubject ? 2.6 : 1.25}
                  strokeOpacity={dimmed ? 0.15 : isSubject || focus === s.supplier ? 1 : 0.5}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  className="transition-[stroke-opacity,stroke-width] duration-150"
                />
                {/* A dot at the tracked week, so the tooltip's numbers have a position. */}
                {at !== null && s.points[at] !== null && !dimmed ? (
                  <circle
                    cx={x(at)}
                    cy={y(s.points[at])}
                    r={isSubject ? 4 : 3}
                    fill={tone(s.supplier)}
                  />
                ) : null}
              </g>
            );
          })}

          {subject && at === null ? (
            <>
              {subject.points.map((p, i) =>
                p === null ? null : (
                  <circle key={i} cx={x(i)} cy={y(p)} r="2.6" fill="var(--bad)" />
                ),
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
                className={
                  at === i
                    ? "fill-[var(--text)] text-[9px] font-bold"
                    : "fill-[var(--text-muted)] text-[9px]"
                }
              >
                {week}
              </text>
            ) : null,
          )}
        </svg>

        {at !== null && reading.length > 0 ? (
          <div
            className="pointer-events-none absolute top-0 z-10 w-[13.5rem] -translate-x-1/2 rounded-lg border border-[var(--line-hi)] bg-[var(--page-deep)] p-2.5 shadow-lg"
            style={{
              // Clamped so the card never hangs off either edge of the figure.
              left: `${Math.min(84, Math.max(16, (x(at) / W) * 100))}%`,
            }}
          >
            <div className="mb-1.5 text-[0.64rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">
              week of {weeks[at]}
            </div>
            {reading.map((r) => (
              <div
                key={r.supplier}
                className="flex items-baseline justify-between gap-3 text-[0.74rem] leading-relaxed"
                style={{
                  color: r.supplier === OTD_SUBJECT ? "var(--bad)" : "var(--text-soft)",
                  fontWeight: r.supplier === OTD_SUBJECT ? 800 : 400,
                }}
              >
                <span className="font-mono">{r.supplier}</span>
                <span>{r.value}%</span>
              </div>
            ))}
            <div className="mt-1.5 border-t border-[var(--line)] pt-1.5 text-[0.68rem] text-[var(--warn)]">
              RB-001 fires below {OTD_THRESHOLD}%
            </div>
          </div>
        ) : null}
      </div>

      {/* Legend doubles as the control. Buttons, not divs, so it is reachable by keyboard. */}
      <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1.5">
        {series.map((s) => (
          <button
            key={s.supplier}
            type="button"
            onMouseEnter={() => setHovered(s.supplier)}
            onMouseLeave={() => setHovered(null)}
            onFocus={() => setHovered(s.supplier)}
            onBlur={() => setHovered(null)}
            onClick={() => setPinned(pinned === s.supplier ? null : s.supplier)}
            aria-pressed={pinned === s.supplier}
            className={`inline-flex items-center gap-1.5 rounded-md px-1.5 py-1 font-mono text-[0.72rem] transition-colors ${
              focus === s.supplier
                ? "bg-[var(--surface-hi)] text-[var(--text)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-soft)]"
            }`}
          >
            <span
              className="inline-block h-0.5 w-3.5 rounded-full"
              style={{ background: tone(s.supplier) }}
            />
            {s.supplier}
            {pinned === s.supplier ? " ·" : ""}
          </button>
        ))}
      </div>

      {/* Capped, not full-bleed. At the chart's width this ran to 174 characters a line, which is
       *  more than twice a comfortable measure — the eye loses the start of the next line. */}
      <p className="mt-2 max-w-[92ch] text-[0.75rem] leading-relaxed text-[var(--text-muted)]">
        Percent on time, bucketed by promised week. Hover the chart to read every supplier at that
        week; hover or tap a name to pick its line out of the pack. The dashed line is RB-001 §1 —
        20 points below {OTD_SUBJECT}&rsquo;s 90-day baseline of 90.8%. The first and last buckets
        are partial weeks and are shown rather than trimmed, because dropping the last one would
        hide the most recent point.
      </p>
    </figure>
  );
}
