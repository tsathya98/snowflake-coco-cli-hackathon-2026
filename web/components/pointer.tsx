"use client";

/**
 * Pointer-reactive lighting and scroll reveals.
 *
 * Three effects, none of which carries meaning:
 *   - an ambient glow that follows the cursor across the viewport
 *   - a spotlight local to whichever card is under it
 *   - a one-shot fade-and-rise as each section first enters view
 *
 * All of it is driven by CSS custom properties and attributes written directly to
 * the DOM inside a requestAnimationFrame, never by React state. A pointermove
 * handler that called setState would re-render the tree at pointer frequency;
 * here React renders once and the browser composites the rest. The listeners are
 * delegated at the window, so adding a card costs nothing.
 *
 * The hidden state for the reveal is applied *by this script*, not by the
 * stylesheet — so if the JS never runs, every section is simply visible. A CSS-only
 * `opacity: 0` would leave a reader with a blank page when it fails.
 *
 * Everything is skipped under `prefers-reduced-motion`, and the pointer effects are
 * additionally gated on a fine pointer: on a phone there is no cursor to follow and
 * the work would only cost battery.
 */

import { useEffect } from "react";

export function PointerGlow() {
  useEffect(() => {
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const cleanups: (() => void)[] = [];

    if (!calm) {
      const sections = Array.from(document.querySelectorAll<HTMLElement>("[data-reveal]"));
      sections.forEach((el) => el.setAttribute("data-reveal", "pending"));

      const observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            const el = entry.target as HTMLElement;
            // Stagger by position within its group so a row of tiles arrives as a
            // sweep rather than all at once.
            const delay = Number(el.dataset.revealDelay ?? 0);
            window.setTimeout(() => el.setAttribute("data-reveal", "shown"), delay);
            observer.unobserve(el);
          }
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.08 },
      );
      sections.forEach((el) => observer.observe(el));
      cleanups.push(() => observer.disconnect());
    }

    if (!calm && fine) {
      const root = document.documentElement;
      let frame = 0;
      let x = 0;
      let y = 0;
      let hovered: HTMLElement | null = null;

      const paint = () => {
        frame = 0;
        root.style.setProperty("--mx", `${x}px`);
        root.style.setProperty("--my", `${y}px`);
        if (hovered) {
          const box = hovered.getBoundingClientRect();
          hovered.style.setProperty("--gx", `${((x - box.left) / box.width) * 100}%`);
          hovered.style.setProperty("--gy", `${((y - box.top) / box.height) * 100}%`);
        }
      };

      const onMove = (event: PointerEvent) => {
        x = event.clientX;
        y = event.clientY;
        const over = (event.target as Element | null)?.closest?.(
          "[data-glow]",
        ) as HTMLElement | null;
        if (over !== hovered) {
          // Clear the outgoing card, or its spotlight freezes wherever the pointer left.
          hovered?.style.removeProperty("--gx");
          hovered?.style.removeProperty("--gy");
          hovered = over;
        }
        if (!frame) frame = requestAnimationFrame(paint);
      };

      // On the window rather than the document: leaving through browser chrome fires
      // no final move, and the glow would stay lit in the corner.
      const onLeave = () => {
        root.style.removeProperty("--mx");
        root.style.removeProperty("--my");
        hovered?.style.removeProperty("--gx");
        hovered?.style.removeProperty("--gy");
        hovered = null;
      };

      window.addEventListener("pointermove", onMove, { passive: true });
      window.addEventListener("pointerleave", onLeave);
      cleanups.push(() => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerleave", onLeave);
        if (frame) cancelAnimationFrame(frame);
      });
    }

    return () => cleanups.forEach((fn) => fn());
  }, []);

  return <div className="ambient" aria-hidden="true" />;
}
