"use client";

/**
 * Pointer-reactive lighting.
 *
 * Two effects, both driven by CSS custom properties rather than by React state:
 * an ambient glow that follows the cursor across the page, and a spotlight local
 * to whichever card is under it.
 *
 * Written as direct style writes inside a requestAnimationFrame, never as
 * `setState`. A pointermove handler that re-renders would re-render the whole
 * tree at pointer frequency; here React renders once and the browser composites
 * the rest. One listener is delegated at the document rather than one per card,
 * so adding a card costs nothing.
 *
 * Disabled entirely under `prefers-reduced-motion`. Nothing here carries meaning —
 * it is lighting — so removing it costs a reader nothing, and motion that tracks
 * the cursor is exactly the kind that provokes symptoms in people who set that
 * preference.
 */

import { useEffect } from "react";

export function PointerGlow() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

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

      const over = (event.target as Element | null)?.closest?.("[data-glow]") as HTMLElement | null;
      if (over !== hovered) {
        // Clear the outgoing card's spotlight, or it freezes mid-fade where the
        // pointer happened to leave.
        hovered?.style.removeProperty("--gx");
        hovered?.style.removeProperty("--gy");
        hovered = over;
      }

      if (!frame) frame = requestAnimationFrame(paint);
    };

    // `pointerleave` on the window, not the document: leaving through a browser
    // chrome edge does not fire a final move, and the glow would stay lit.
    const onLeave = () => {
      root.style.removeProperty("--mx");
      root.style.removeProperty("--my");
      hovered?.style.removeProperty("--gx");
      hovered?.style.removeProperty("--gy");
      hovered = null;
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);

  return <div className="ambient" aria-hidden="true" />;
}
