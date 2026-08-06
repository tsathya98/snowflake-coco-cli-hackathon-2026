"use client";

/**
 * The governed console, for people who cannot open it.
 *
 * Approval happens in Streamlit in Snowflake, and Streamlit in Snowflake cannot be shared
 * with anyone who does not have an account on this Snowflake org. So the surface where the
 * governance actually bites — where a named human approves, and the refusal banner fires —
 * was the one surface a visitor could never see. Screenshots are a poor substitute for a
 * live app and a much better one than nothing.
 *
 * The files are copied from docs/images/ into public/console/ rather than referenced across
 * the repo, because Next serves only from public/. tools/check_doc_claims.py asserts the two
 * copies are byte-identical, so the pair cannot drift.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";

const SHOTS: [string, string, string][] = [
  [
    "console-headline",
    "The console, leading with refusals",
    "Six exceptions, five handled, one escalated — and the figure it leads with is what it refused, not what it got through.",
  ],
  [
    "evidence-and-reasoning",
    "Evidence beside the reasoning",
    "Left is what the detector measured. Right is what the model concluded, marked model-generated so a reviewer never has to guess which is which.",
  ],
  [
    "refusal-banner",
    "Approved by a human, refused anyway",
    "Between queueing and approval, INVENTORY was reclassified regulated. The approval is recorded. The action did not happen — the tag is read again before the write.",
  ],
  [
    "queue-already-decided",
    "The queue, after the decision",
    "An action already decided is shown as decided rather than removed. A reviewer should be able to see what they did.",
  ],
  [
    "authority-manifest",
    "What it may do, right now",
    "The full capability registry resolved against the tags in force, most restricted first.",
  ],
  [
    "whatif-revocation",
    "What a policy change would cost",
    "Reclassify an object hypothetically and see which capabilities it revokes, before touching governance.",
  ],
  [
    "replay",
    "Would today's policy still allow it?",
    "Every recorded action re-resolved against the classifications in force now — the question an auditor actually asks.",
  ],
  [
    "column-governance",
    "Masked at the column, not in the app",
    "A masking policy on QUALITY_HOLDS.lot_ref. The agent reads LOT-WITHHELD because Snowflake gives it that, not because the app hid it.",
  ],
];

export function ConsoleGallery() {
  const rail = useRef<HTMLDivElement>(null);
  const [at, setAt] = useState({ start: true, end: false });

  /**
   * Which ends we are against, so the buttons disable rather than dead-click.
   *
   * The tolerance is 24px, not 1 or 2. The rail has `px-1` padding and snaps to card edges, so
   * it rests at scrollLeft 4 rather than 0 and stops 10px short of its maximum — measured in a
   * real browser. A tight threshold meant neither end ever registered and both buttons stayed
   * enabled forever, which is the exact dead-click this state exists to prevent.
   */
  const measure = useCallback(() => {
    const el = rail.current;
    if (!el) return;
    const slack = 24;
    setAt({
      start: el.scrollLeft <= slack,
      end: el.scrollLeft >= el.scrollWidth - el.clientWidth - slack,
    });
  }, []);

  useEffect(() => {
    const el = rail.current;
    if (!el) return;
    measure();
    el.addEventListener("scroll", measure, { passive: true });
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      observer.disconnect();
    };
  }, [measure]);

  /**
   * Advance one card.
   *
   * The card width is read rather than assumed, so the step stays correct when the viewport
   * clamps it on a narrow screen.
   *
   * The animation is hand-rolled: suspend snap, drive scrollLeft frame by frame, restore snap on
   * the last frame — by which point the rail is already on a snap point, so nothing jumps.
   * Snapping still does its job for trackpad, touch and wheel, which is what it exists for.
   *
   * `scrollBy({behavior: "smooth"})` would be the obvious alternative and may well work; it is
   * avoided because a mandatory-snap container re-snapping mid-animation is a documented rough
   * edge, and driving the scroll directly removes the question. Doing it by frame also makes the
   * reduced-motion path above a plain assignment rather than a second code path.
   */
  const step = (direction: 1 | -1) => {
    const el = rail.current;
    if (!el) return;

    const card = el.querySelector("figure");
    const by = (card ? card.getBoundingClientRect().width + 16 : el.clientWidth * 0.8) * direction;
    const from = el.scrollLeft;
    const to = Math.max(0, Math.min(el.scrollWidth - el.clientWidth, from + by));
    if (to === from) return;

    // Respect the reader's preference: no animation, just arrive.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.scrollLeft = to;
      return;
    }

    el.style.scrollSnapType = "none";
    const started = performance.now();
    const DURATION = 380;

    const frame = (now: number) => {
      const t = Math.min(1, (now - started) / DURATION);
      const eased = 1 - Math.pow(1 - t, 3);
      el.scrollLeft = from + (to - from) * eased;
      if (t < 1) {
        requestAnimationFrame(frame);
      } else {
        el.style.scrollSnapType = "";
      }
    };
    requestAnimationFrame(frame);
  };

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <p className="m-0 text-[0.82rem] text-[var(--text-muted)]">
          Eight views of the governed console.{" "}
          <strong className="text-[var(--text-soft)]">Click any shot to open it full size.</strong>
        </p>

        {/* Buttons, because dragging a scrollbar is a bad way to page through anything.
         *  The rail still scrolls natively — this is an addition for people using a mouse, not a
         *  replacement for trackpad, touch or keyboard. */}
        <div className="flex shrink-0 gap-2">
          {([
            [-1, "Previous", "M15 18l-6-6 6-6", at.start],
            [1, "Next", "M9 18l6-6-6-6", at.end],
          ] as const).map(([direction, label, path, disabled]) => (
            <button
              key={label}
              type="button"
              onClick={() => step(direction)}
              disabled={disabled}
              aria-label={`${label} screenshot`}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--line-hi)] bg-[var(--surface-hi)] text-[var(--text-soft)] transition-colors hover:border-[var(--info)] hover:text-[var(--text)] disabled:cursor-default disabled:opacity-30 disabled:hover:border-[var(--line-hi)]"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <path d={path} />
              </svg>
            </button>
          ))}
        </div>
      </div>

      {/* A horizontal rail, not a vertical stack. Eight 1400px screenshots stacked two-up ran to
       *  about 2,400px of page — a quarter of the site spent on evidence most readers glance at
       *  once. A rail costs one viewport however many shots there are.
       *
       *  Scroll-snap and native overflow rather than a carousel library: it works before
       *  hydration, and with trackpad, touch, shift+wheel and keyboard alike. */}
      <div
        ref={rail}
        className="scroller table-wrap -mx-1 flex snap-x snap-mandatory gap-4 px-1 pb-3"
      >
        {SHOTS.map(([file, title, note]) => (
          <figure
            key={file}
            className="m-0 w-[min(86vw,620px)] shrink-0 snap-start overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface)]"
            data-glow
          >
            <a
              href={`/console/${file}.png`}
              target="_blank"
              rel="noreferrer"
              className="group relative block cursor-zoom-in"
              aria-label={`${title} — open full size`}
            >
              <Image
                src={`/console/${file}.png`}
                alt={title}
                width={1400}
                height={800}
                className="h-auto w-full border-b border-[var(--line)] transition-opacity group-hover:opacity-80"
                sizes="(max-width: 640px) 86vw, 620px"
              />
              <span className="pointer-events-none absolute bottom-2 right-2 rounded-md border border-[var(--line-hi)] bg-[var(--page-deep)] px-2 py-1 text-[0.66rem] font-bold uppercase tracking-[0.08em] text-[var(--text-soft)] opacity-0 transition-opacity group-hover:opacity-100">
                Open full size &#8599;
              </span>
            </a>
            <figcaption className="p-3.5 sm:p-4">
              <div className="text-[0.86rem] font-bold">{title}</div>
              <p className="mt-1 text-[0.79rem] leading-relaxed text-[var(--text-muted)]">{note}</p>
            </figcaption>
          </figure>
        ))}
      </div>
    </>
  );
}
