/**
 * The shared visual vocabulary, matching streamlit/warrant_console.py.
 *
 * One chip renderer, one tile renderer, one accent mapping. Both surfaces of this
 * project use the same shapes and the same words so a reader moving between them
 * is not asked to learn a second language for the same ideas.
 *
 * Colour never carries a meaning on its own here. Every chip prints its label,
 * every tile prints its caption, and every accent is paired with text that says
 * the same thing — a colour alone is invisible to a colourblind reader and to a
 * screen reader, and this page is partly an argument about auditability.
 */

import type { ReactNode } from "react";

/** A CSS accent token: one of good, warn, bad, info, model, muted. */
type Tone = string;

const accent = (tone: Tone) => ({ ["--accent" as string]: `var(--${tone})` }) as React.CSSProperties;

export function Tiles({ figures }: { figures: [string, ReactNode, Tone][] }) {
  return (
    <div className="tiles">
      {figures.map(([label, value, tone]) => (
        <div className="tile" data-glow key={label} style={accent(tone)}>
          <div className="value">{value}</div>
          <div className="label">{label}</div>
        </div>
      ))}
    </div>
  );
}

export function Chip({ children, tone }: { children: ReactNode; tone: Tone }) {
  return (
    <span className="chip" style={accent(tone)}>
      {children}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return <span className="tag">{children}</span>;
}

/** A callout whose border and tint take the accent, and whose text says why. */
export function Note({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <div className="note" data-glow style={accent(tone)}>
      {children}
    </div>
  );
}

export function ModelText({ children }: { children: ReactNode }) {
  return (
    <div className="model">
      <div className="stamp">&#9670; model-generated</div>
      <div>{children}</div>
    </div>
  );
}

/**
 * A table from plain rows.
 *
 * @param columns `[key, heading, numeric?]`. `numeric` right-aligns and sets the
 *   monospace face so figures line up down the column.
 */
export function Table({
  columns,
  rows,
}: {
  columns: [string, string, boolean?][];
  rows: Record<string, unknown>[];
}) {
  return (
    <table>
      <thead>
        <tr>
          {columns.map(([key, heading]) => (
            <th key={key}>{heading}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={index}>
            {columns.map(([key, , numeric]) => (
              <td key={key} className={numeric ? "num" : undefined}>
                {String(row[key] ?? "-")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function Section({
  id,
  title,
  lede,
  children,
}: {
  id: string;
  title: string;
  lede: ReactNode;
  children: ReactNode;
}) {
  return (
    <section id={id}>
      <h2>{title}</h2>
      <p>{lede}</p>
      {children}
    </section>
  );
}
