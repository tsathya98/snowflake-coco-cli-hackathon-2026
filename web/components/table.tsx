"use client";

/**
 * A table that admits when it is scrollable.
 *
 * Six columns do not fit a phone and wrapping each cell to three lines is worse than
 * scrolling, so the wrapper scrolls. But a scroll region nobody can see is a scroll
 * region nobody uses, so this measures its own overflow and says so three ways: a
 * permanently visible scrollbar (in CSS), an edge fade on whichever side has more
 * content, and a one-line hint that appears only when there is genuinely something
 * off-screen.
 *
 * The measurement is a ResizeObserver plus a scroll listener rather than a media query,
 * because whether six columns overflow depends on the content, not on the viewport —
 * the same table fits on a laptop and does not on a phone, and a long supplier name can
 * flip it either way.
 */

import { useCallback, useEffect, useRef, useState } from "react";

export function DataTable({
  columns,
  rows,
  caption,
}: {
  columns: [string, string, boolean?][];
  rows: Record<string, unknown>[];
  caption?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [edges, setEdges] = useState("");
  const [scrollable, setScrollable] = useState(false);

  const measure = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const overflowing = el.scrollWidth - el.clientWidth > 2;
    setScrollable(overflowing);
    if (!overflowing) {
      setEdges("");
      return;
    }
    const atStart = el.scrollLeft <= 1;
    const atEnd = el.scrollLeft >= el.scrollWidth - el.clientWidth - 1;
    setEdges(`${atStart ? "" : "left"} ${atEnd ? "" : "right"}`.trim());
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    // The table itself resizes independently of the wrapper when fonts load.
    const table = el.querySelector("table");
    if (table) observer.observe(table);
    el.addEventListener("scroll", measure, { passive: true });
    return () => {
      observer.disconnect();
      el.removeEventListener("scroll", measure);
    };
  }, [measure]);

  return (
    <figure className="m-0">
      {scrollable ? (
        <figcaption className="mb-1.5 flex items-center gap-1.5 text-[0.72rem] text-[var(--text-muted)]">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3.5 w-3.5"
            aria-hidden="true"
          >
            <path d="M8 7 4 12l4 5M16 7l4 5-4 5" />
          </svg>
          {caption ?? "Scroll sideways for the remaining columns"}
        </figcaption>
      ) : null}

      <div className="table-wrap" data-overflow={edges}>
        <div ref={ref} className="scroller" tabIndex={0} role="region" aria-label={caption}>
          <table className="w-full min-w-[660px] border-separate border-spacing-0 text-[0.84rem]">
            <thead>
              <tr>
                {columns.map(([key, heading]) => (
                  <th
                    key={key}
                    scope="col"
                    className="sticky top-0 border-b border-[var(--line)] bg-[var(--surface-hi)] px-3 py-2.5 text-left text-[0.62rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)] first:rounded-tl-xl last:rounded-tr-xl"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index} className="group transition-colors hover:bg-[var(--surface-hi)]">
                  {columns.map(([key, , numeric]) => (
                    <td
                      key={key}
                      className={`border-b border-[var(--line)] px-3 py-2.5 align-top text-[var(--text-soft)] group-last:border-b-0 ${
                        numeric ? "text-right font-mono tabular-nums" : ""
                      }`}
                    >
                      {String(row[key] ?? "-")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </figure>
  );
}
