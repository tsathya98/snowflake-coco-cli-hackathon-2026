"use client";

/**
 * Theme control: system, light, dark.
 *
 * The resolved theme is always written to `<html data-theme>`, never left implicit.
 * That means the stylesheet needs exactly two states rather than three — an explicit
 * value and a media query that has to be excluded when the explicit value disagrees.
 * The inline script in `layout.tsx` does the same resolution before first paint, so a
 * reader who prefers light never sees a dark flash.
 *
 * "System" is a real third choice, not a synonym for the current OS setting: it keeps
 * tracking `prefers-color-scheme` if the OS flips while the page is open. Only an
 * explicit light or dark pick is persisted.
 */

import { useEffect, useState } from "react";

type Choice = "system" | "light" | "dark";

const KEY = "warrant-theme";

function systemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function apply(choice: Choice) {
  const resolved = choice === "system" ? systemTheme() : choice;
  document.documentElement.setAttribute("data-theme", resolved);
  document.documentElement.style.colorScheme = resolved;
}

const OPTIONS: [Choice, string, string][] = [
  ["light", "Light", "M12 3v2m0 14v2m9-9h-2M5 12H3m14.7-6.7-1.4 1.4M7.7 16.3l-1.4 1.4m12 0-1.4-1.4M7.7 7.7 6.3 6.3"],
  ["system", "System", "M3 5h18v11H3zM8 20h8m-4-4v4"],
  ["dark", "Dark", "M20 13a8 8 0 1 1-9-9 6.5 6.5 0 0 0 9 9Z"],
];

export function ThemeToggle() {
  const [choice, setChoice] = useState<Choice>("system");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(KEY) as Choice | null;
    const initial: Choice = stored === "light" || stored === "dark" ? stored : "system";
    setChoice(initial);
    setReady(true);

    // Keep following the OS while "system" is selected.
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if ((localStorage.getItem(KEY) as Choice | null) === null) apply("system");
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const pick = (next: Choice) => {
    setChoice(next);
    if (next === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, next);
    apply(next);
  };

  return (
    <div
      role="radiogroup"
      aria-label="Colour theme"
      // Hidden until the stored choice is known, so the highlight never renders on the
      // wrong segment and then jump. `invisible` rather than `hidden` keeps the layout.
      className={`flex shrink-0 items-center gap-0.5 rounded-lg border border-[var(--line)] bg-[var(--surface)] p-0.5 ${
        ready ? "" : "invisible"
      }`}
    >
      {OPTIONS.map(([value, label, path]) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={choice === value}
          aria-label={label}
          title={label}
          onClick={() => pick(value)}
          className={`flex h-7 w-7 items-center justify-center rounded-md transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--info)] ${
            choice === value
              ? "bg-[var(--surface-hi)] text-[var(--text)]"
              : "text-[var(--text-muted)] hover:text-[var(--text)]"
          }`}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-[15px] w-[15px]"
            aria-hidden="true"
          >
            {value === "light" ? <circle cx="12" cy="12" r="4" /> : null}
            <path d={path} />
          </svg>
        </button>
      ))}
    </div>
  );
}

/**
 * Highlights the nav link for whichever section is currently in view.
 *
 * This is what a tab bar would have given — orientation — without a tab bar's cost,
 * which is hiding five sixths of the page behind a click a reviewer will not make.
 *
 * Uses the *topmost* intersecting section rather than the most visible one: while
 * scrolling through a long table two sections overlap, and picking by ratio makes the
 * highlight flicker between them.
 */
export function ScrollSpy({ ids }: { ids: string[] }) {
  useEffect(() => {
    const links = new Map<string, HTMLAnchorElement>();
    ids.forEach((id) => {
      const link = document.querySelector<HTMLAnchorElement>(`a[href="#${id}"]`);
      if (link) links.set(id, link);
    });

    const mark = (active: string | null) => {
      links.forEach((link, id) => {
        link.setAttribute("data-active", String(id === active));
      });
    };

    const sections = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => el !== null);

    const onScroll = () => {
      let current: string | null = null;
      for (const section of sections) {
        if (section.getBoundingClientRect().top <= 120) current = section.id;
      }
      mark(current);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [ids]);

  return null;
}
