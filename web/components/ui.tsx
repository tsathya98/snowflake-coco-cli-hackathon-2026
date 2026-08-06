/**
 * The shared visual vocabulary, matching streamlit/warrant_console.py.
 *
 * One chip renderer, one tile renderer, one accent mapping. Both surfaces of this
 * project use the same shapes and the same words, so a reader moving between them is
 * not asked to learn a second language for the same ideas.
 *
 * Colour never carries a meaning on its own. Every chip prints its label, every tile
 * its caption, and every accent is paired with text saying the same thing — a colour
 * alone is invisible to a colourblind reader and to a screen reader, and this page is
 * partly an argument about auditability.
 *
 * Responsive rules worth knowing: tables scroll horizontally inside `.scroller` rather
 * than crushing six columns into 360px, tile rows collapse 5 → 2 → 1, and every
 * interactive target keeps a 44px minimum height on touch.
 */

import type { CSSProperties, ReactNode } from "react";

/** A CSS accent token: good, warn, bad, info, model, muted. */
type Tone = string;

const tone = (name: Tone) => ({ ["--tone" as string]: `var(--${name})` }) as CSSProperties;

export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <div data-reveal data-reveal-delay={delay} className={className}>
      {children}
    </div>
  );
}

export function Tiles({ figures }: { figures: [string, ReactNode, Tone][] }) {
  return (
    <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-5">
      {figures.map(([label, value, name], i) => (
        <Reveal key={label} delay={i * 60}>
          <div
            data-glow
            style={tone(name)}
            className="h-full rounded-xl border border-[var(--line)] border-t-[3px] bg-[var(--surface)] px-4 py-3 transition-colors duration-300"
          >
            <div
              className="text-[1.7rem] font-extrabold leading-none tracking-[-0.03em]"
              style={{ color: `var(--${name})` }}
            >
              {value}
            </div>
            <div className="mt-1.5 text-[0.62rem] font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">
              {label}
            </div>
          </div>
        </Reveal>
      ))}
    </div>
  );
}

export function Chip({ children, tone: name }: { children: ReactNode; tone: Tone }) {
  return (
    <span
      className="mb-1 mr-1.5 inline-block rounded-full px-2.5 py-[3px] text-[0.68rem] font-bold tracking-wide"
      style={{ background: `var(--${name})`, color: "var(--chip-ink)" }}
    >
      {children}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="mb-1 mr-1.5 inline-block rounded-md border border-[var(--line)] bg-[var(--surface-hi)] px-1.5 py-0.5 font-mono text-[0.68rem] text-[var(--text-soft)]">
      {children}
    </span>
  );
}

export function Note({ tone: name, children }: { tone: Tone; children: ReactNode }) {
  return (
    <Reveal>
      <div
        data-glow
        style={{
          ...tone(name),
          borderColor: `color-mix(in srgb, var(--${name}) 45%, transparent)`,
          // The tint derives from the same token as the border, so a new tone cannot
          // half-apply — one name drives both.
          background: `color-mix(in srgb, var(--${name}) 10%, transparent)`,
        }}
        className="rounded-xl border p-4 text-[0.9rem] leading-relaxed sm:px-5"
      >
        {children}
      </div>
    </Reveal>
  );
}

export function ModelText({ children }: { children: ReactNode }) {
  return (
    <div
      className="rounded-r-xl border-l-[3px] p-3.5 text-[0.92rem] leading-relaxed sm:p-4"
      style={{
        borderColor: "var(--model)",
        background: "color-mix(in srgb, var(--model) 11%, transparent)",
      }}
    >
      <div
        className="mb-1.5 text-[0.63rem] font-extrabold uppercase tracking-[0.12em]"
        style={{ color: "var(--model)" }}
      >
        &#9670; model-generated
      </div>
      <div className="text-[var(--text)]">{children}</div>
    </div>
  );
}

export function Card({
  tone: name,
  children,
  className = "",
}: {
  tone: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      data-glow
      style={{ ...tone(name), borderLeftColor: `var(--${name})` }}
      className={`rounded-r-xl border border-l-[4px] border-[var(--line)] bg-[var(--surface)] p-4 transition-colors duration-300 ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Progressive disclosure for reference-grade material.
 *
 * The page had thirteen sections and ran to nineteen screens, which is a twenty-minute read
 * put in front of someone who has three minutes. The depth is the point and cutting it would
 * cost more than the length does, so the reference material folds instead.
 *
 * Two rules hold this honest. The summary states the claim, so a reader who never opens one
 * has still read what is being asserted and only the proof is a click away. And only static
 * material goes inside — nothing a reader can interact with should sit behind something they
 * have to discover first.
 *
 * Native `<details>`: it works before hydration, keyboard and screen readers already know it,
 * and the contents stay in the DOM, so this hides pixels rather than evidence.
 */
export function Details({
  summary,
  hint,
  children,
}: {
  summary: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <details className="group rounded-xl border border-[var(--line)] bg-[var(--surface)]" data-glow>
      <summary className="flex min-h-[44px] cursor-pointer list-none flex-wrap items-center gap-x-2.5 gap-y-0.5 px-4 py-3 text-[0.87rem] font-semibold transition-colors hover:text-[var(--info)] [&::-webkit-details-marker]:hidden">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          className="h-3.5 w-3.5 shrink-0 transition-transform duration-200 group-open:rotate-90"
          style={{ color: "var(--info)" }}
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
        <span>{summary}</span>
        {hint ? (
          <span className="text-[0.79rem] font-normal text-[var(--text-muted)]">{hint}</span>
        ) : null}
      </summary>
      <div className="border-t border-[var(--line)] p-4 sm:p-5">{children}</div>
    </details>
  );
}

export function Section({
  id,
  eyebrow,
  title,
  lede,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  lede: ReactNode;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 border-t border-[var(--line)] py-10 sm:py-14">
      <Reveal>
        <div className="mb-1.5 text-[0.65rem] font-bold uppercase tracking-[0.16em] text-[var(--info)]">
          {eyebrow}
        </div>
        <h2 className="text-[1.4rem] font-bold leading-tight tracking-[-0.02em] sm:text-[1.72rem]">
          {title}
        </h2>
        <p className="mt-2.5 max-w-[80ch] text-[0.92rem] leading-relaxed text-[var(--text-soft)]">
          {lede}
        </p>
      </Reveal>
      <div className="mt-5">{children}</div>
    </section>
  );
}
