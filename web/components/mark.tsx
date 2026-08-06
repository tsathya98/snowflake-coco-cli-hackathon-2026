/**
 * The Warrant mark.
 *
 * A warrant is a document that authorises, and it is recognisable by its seal. The mark
 * is that: a stamp ring, broken at the top-right the way a seal is broken when the
 * authority it carried is spent, with a governance tag inside it. The tag is doing the
 * work in this product — authority is derived from the tag on the data, so the tag is
 * what belongs at the centre of the seal rather than a gavel or a shield.
 *
 * Drawn as strokes on a 24-unit grid in `currentColor`, so it inherits the theme, works
 * on the nav at 18px and on a slide at 400px, and needs no dark and light variant. The
 * ring is deliberately the heaviest element: at favicon size the tag reduces to a
 * suggestion and the seal is what still reads.
 *
 * `spin` draws the ring once on mount. It is off by default and off entirely under
 * reduced motion, because a logo that animates on every render is a logo you notice
 * instead of read.
 */

export function Mark({
  size = 22,
  spin = false,
  gradient = false,
  id = "mark",
}: {
  size?: number;
  spin?: boolean;
  gradient?: boolean;
  id?: string;
}) {
  const stroke = gradient ? `url(#${id}-grad)` : "currentColor";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      role="img"
      aria-label="Warrant"
      className="shrink-0"
    >
      {gradient ? (
        <defs>
          <linearGradient id={`${id}-grad`} x1="0" y1="0" x2="24" y2="24">
            <stop offset="0%" stopColor="var(--info)" />
            <stop offset="100%" stopColor="var(--model)" />
          </linearGradient>
        </defs>
      ) : null}

      {/* The seal. Broken at the top-right — an unbroken ring reads as a clock face. */}
      <path
        d="M 20.4 7.2 A 9.6 9.6 0 1 0 21.6 12"
        stroke={stroke}
        strokeWidth="1.9"
        strokeLinecap="round"
        className={spin ? "mark-ring" : undefined}
      />

      {/* The tag whose classification decides what may be done. */}
      <path
        d="M 12.2 6.4 h 5.4 v 5.4 l -5.9 5.9 a 1.2 1.2 0 0 1 -1.7 0 l -3.7 -3.7 a 1.2 1.2 0 0 1 0 -1.7 z"
        stroke={stroke}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <circle cx="15.1" cy="8.9" r="1.15" fill={stroke} />
    </svg>
  );
}

/** Mark plus name, as it appears in the nav and above the fold. */
export function Wordmark({ size = 22, className = "" }: { size?: number; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <Mark size={size} spin />
      <span className="font-extrabold tracking-[-0.02em]">Warrant</span>
    </span>
  );
}
