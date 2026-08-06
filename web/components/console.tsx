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
  return (
    <>
      <p className="mb-4 text-[0.82rem] text-[var(--text-muted)]">
        A console is dense, and a thumbnail of one is unreadable.{" "}
        <strong className="text-[var(--text-soft)]">Click any shot to open it full size.</strong>
      </p>
      {/* Two-up only from lg. These are 1400px-wide screenshots of a data-dense app: at the sm
          breakpoint a half-width column is ~300px, which is a picture of a console rather than
          a console you can read. */}
      <div className="grid gap-5 lg:grid-cols-2">
        {SHOTS.map(([file, title, note]) => (
          <figure
            key={file}
            className="m-0 overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--surface)]"
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
                sizes="(max-width: 1024px) 100vw, 50vw"
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
