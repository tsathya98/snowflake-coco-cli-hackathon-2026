/**
 * The public, read-only viewer.
 *
 * One scrolling page rather than tabs. A reviewer arriving from a submission form has a
 * minute and no idea what this is; asking them to hunt through tabs for the argument
 * loses more than the tidiness gains. The order is the order of the claim: what it did,
 * the one thing it would not decide alone, what it is allowed to do, what today's policy
 * says about yesterday's actions, what it refused, and what governs all of it.
 *
 * Server-rendered on every request. There is no cache anywhere in this app — the whole
 * point is that reclassifying a table changes the agent's authority immediately, and a
 * cached tag read would hide exactly that.
 */

import { callJson, query } from "@/lib/snowflake";
import {
  AUDIT,
  DECISIONS,
  GOVERNANCE,
  HEADLINE,
  MANIFEST,
  MASKED_HOLDS,
  METRICS,
  OUTCOME_TONE,
  REFUSALS,
  REPLAY,
  SEVERITY_TONE,
  TASK_ACTIVITY,
  TIER_NAMES,
  TIER_TONE,
  type ManifestPayload,
  type ReplayPayload,
  type TaskActivity,
} from "@/lib/queries";
import { PointerGlow } from "@/components/pointer";
import { Card, Chip, ModelText, Note, Reveal, Section, Tag, Tiles } from "@/components/ui";
import { DataTable } from "@/components/table";
import { ScrollSpy, ThemeToggle } from "@/components/theme";
import { WhatIf } from "@/components/whatif";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const REPO = "https://github.com/tsathya98/snowflake-coco-cli-hackathon-2026";

const TIER_MEANING: Record<string, string> = {
  open: "act unsupervised (L2)",
  internal: "act only with human approval (L3)",
  regulated: "read and explain, never act (L4)",
};

const NAV = [
  ["pass", "One pass"],
  ["evidence", "Evidence"],
  ["authority", "Authority"],
  ["replay", "Replay"],
  ["refusals", "Refusals"],
  ["governance", "Governance"],
  ["unattended", "Unattended"],
] as const;

const str = (v: unknown) => String(v ?? "");
const num = (v: unknown) => Number(v ?? 0);

export default async function Page() {
  const [headline] = await query(HEADLINE);
  const [decisions, refusals, governance, holds, metrics, audit] = await Promise.all([
    query(DECISIONS),
    query(REFUSALS),
    query(GOVERNANCE),
    query(MASKED_HOLDS),
    query(METRICS),
    query(AUDIT),
  ]);
  const [manifest, replay, schedule] = await Promise.all([
    callJson<ManifestPayload>(MANIFEST),
    callJson<ReplayPayload>(REPLAY),
    callJson<TaskActivity>(TASK_ACTIVITY, [24]),
  ]);

  const escalated = decisions.find((d) => str(d.DECISION) === "pending") ?? decisions[0];
  const counts = manifest.capabilities.reduce<Record<string, number>>((acc, c) => {
    acc[c.outcome] = (acc[c.outcome] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      <PointerGlow />
      <ScrollSpy ids={NAV.map(([id]) => id)} />

      <nav className="sticky top-0 z-30 border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--page)_88%,transparent)] backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2.5 sm:px-6">
          <span className="shrink-0 text-[0.95rem] font-extrabold tracking-[-0.02em]">
            &#9878;&#65039; Warrant
          </span>
          <div className="scroller flex min-w-0 flex-1 gap-1">
            {NAV.map(([id, label]) => (
              <a
                key={id}
                href={`#${id}`}
                className="whitespace-nowrap rounded-lg px-2.5 py-1.5 text-[0.78rem] text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-hi)] hover:text-[var(--text)]"
              >
                {label}
              </a>
            ))}
          </div>
          <ThemeToggle />
          <a
            href={REPO}
            className="hidden shrink-0 rounded-lg border border-[var(--line)] px-3 py-1.5 text-[0.78rem] font-semibold transition-colors hover:border-[var(--line-hi)] sm:block"
            style={{ color: "var(--info)" }}
          >
            Source
          </a>
        </div>
      </nav>

      <main className="relative z-10 mx-auto max-w-6xl px-4 pb-24 sm:px-6">
        <header className="pt-10 sm:pt-16">
          <Reveal>
            <div
              className="mb-3 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[0.66rem] font-bold uppercase tracking-[0.14em]"
              style={{
                borderColor: "color-mix(in srgb, var(--info) 40%, transparent)",
                background: "color-mix(in srgb, var(--info) 10%, transparent)",
                color: "var(--info)",
              }}
            >
              <span className="animate-sheen">&#9679;</span> live from Snowflake, uncached
            </div>
            <h1 className="max-w-[19ch] text-[2rem] font-extrabold leading-[1.05] tracking-[-0.035em] sm:text-[3.1rem]">
              No action without a{" "}
              <span
                style={{
                  background: "linear-gradient(100deg, var(--info), var(--model))",
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                warrant
              </span>
              .
            </h1>
            <p className="mt-4 max-w-[68ch] text-[1rem] leading-relaxed text-[var(--text-soft)] sm:text-[1.08rem]">
              An operations agent that closes the loop from detection to action, and whose
              permission to take each action is read from the Snowflake object tags on the data
              that action touches — live, and again at execution time, so a human&rsquo;s approval
              cannot outlive the policy it was granted under.
            </p>
            <p className="mt-4 text-[0.82rem] text-[var(--text-muted)]">
              Team Argmax &middot; CoCo CLI Hackathon 2026, Problem Statement 1 &middot;{" "}
              <a href={REPO} className="underline underline-offset-2" style={{ color: "var(--info)" }}>
                source on GitHub
              </a>
            </p>
          </Reveal>
        </header>

        <div className="mt-9">
          <Tiles
            figures={[
              ["Exceptions detected", num(headline?.DETECTED), "info"],
              ["Handled by the agent", num(headline?.ACTED), "good"],
              ["Awaiting a human", num(headline?.AWAITING), "warn"],
              ["Refused", num(headline?.REFUSED), "bad"],
              ["Decisions logged", num(headline?.LOGGED), "muted"],
            ]}
          />
          <p className="mt-2.5 text-[0.76rem] text-[var(--text-muted)]">
            Last recorded decision: {str(headline?.LAST_AT)}. Read on every request.
          </p>
        </div>

        <div className="mt-7">
          <Note tone="info">
            <strong>This page is read-only, and not by convention.</strong> It authenticates as{" "}
            <code className="font-mono text-[0.85em]">WARRANT_PUBLIC</code>, a role holding{" "}
            <code className="font-mono text-[0.85em]">SELECT</code> on a handful of objects and{" "}
            <code className="font-mono text-[0.85em]">USAGE</code> on the two procedures that only
            compute. It has no grant on{" "}
            <code className="font-mono text-[0.85em]">EXECUTE_ACTION</code>. Approving is a
            governed act and belongs to the console inside Snowflake, where the reviewer has an
            identity of their own — the same reason the conversational agent is given no tool bound
            to the executor.
          </Note>
        </div>

        <Section
          id="pass"
          eyebrow="What one pass did"
          title="Three outcomes, one loop, no branching on table names"
          lede={
            <>
              One <code className="font-mono text-[0.88em]">CALL WARRANT.CORE.RUN_LOOP(&apos;AUTO&apos;)</code>{" "}
              over 2,400 shipments, 40 quality holds and 6 SKUs. The tag on the data decided every
              routing below.
            </>
          }
        >
          <Reveal>
            <DataTable
              columns={[
                ["ENTITY", "Entity"],
                ["ACTION_TYPE", "Action proposed"],
                ["TIER_LABEL", "Authority"],
                ["BINDING_OBJECT", "Bound by"],
                ["OUTCOME", "Outcome"],
              ]}
              rows={decisions.map((d) => ({
                ...d,
                TIER_LABEL: TIER_NAMES[num(d.TIER)] ?? "-",
                BINDING_OBJECT: str(d.BINDING_OBJECT).split(".").pop(),
                OUTCOME:
                  str(d.DECISION) === "pending" ? "awaiting a human" : str(d.EXECUTION_RESULT),
              }))}
            />
          </Reveal>
        </Section>

        {escalated ? (
          <Section
            id="evidence"
            eyebrow="The one it would not decide alone"
            title="Evidence beside the reasoning, not behind a click"
            lede="A reviewer asked to approve something whose evidence is one click away approves it without clicking."
          >
            <div className="grid gap-5 lg:grid-cols-2">
              <Reveal>
                <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5" data-glow>
                  <div className="mb-3 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
                    What was observed
                  </div>
                  <dl className="space-y-2 text-[0.88rem]">
                    {[
                      ["Observed", str(escalated.OBSERVED)],
                      ["Expected", str(escalated.EXPECTED)],
                      ["Deviation", str(escalated.DEVIATION)],
                      ["Detected by", str(escalated.DETECTION_METHOD)],
                    ].map(([k, v]) => (
                      <div key={k} className="flex flex-col gap-0.5 sm:flex-row sm:gap-2">
                        <dt className="shrink-0 font-semibold sm:w-28">{k}</dt>
                        <dd className="m-0 text-[var(--text-soft)]">{v}</dd>
                      </div>
                    ))}
                  </dl>
                  <div className="mt-4 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
                    Grounded in
                  </div>
                  <div className="mt-1.5">
                    {(JSON.parse(str(escalated.GROUNDED_IN) || "[]") as string[]).map((doc) => (
                      <Tag key={doc}>{doc}</Tag>
                    ))}
                  </div>
                </div>
              </Reveal>

              <Reveal delay={90}>
                <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4 sm:p-5" data-glow>
                  <div className="mb-3 text-[0.62rem] font-bold uppercase tracking-[0.11em] text-[var(--text-muted)]">
                    Why this action, and why it needs a human
                  </div>
                  <ModelText>{str(escalated.ROOT_CAUSE)}</ModelText>
                  <div className="mt-4">
                    <Chip tone={SEVERITY_TONE[str(escalated.SEVERITY).toLowerCase()] ?? "muted"}>
                      {str(escalated.SEVERITY)}
                    </Chip>
                    <Chip tone={TIER_TONE[num(escalated.TIER)] ?? "muted"}>
                      {TIER_NAMES[num(escalated.TIER)]}
                    </Chip>
                  </div>
                  <p className="mt-2 text-[0.83rem] leading-relaxed text-[var(--text-muted)]">
                    {str(escalated.TIER_RATIONALE)}
                  </p>
                  <p className="mt-2 text-[0.78rem] text-[var(--text-muted)]">
                    Produced by <code className="font-mono">{str(escalated.MODEL)}</code>. Bound as
                    query parameters — the model never contributes SQL text.
                  </p>
                </div>
              </Reveal>
            </div>
          </Section>
        ) : null}

        <Section
          id="authority"
          eyebrow="What is it allowed to do, right now?"
          title="Every action, resolved against the tags in force — and what a policy change would cost"
          lede="Most restricted first — what the agent may not do is what a reviewer should read before what it may. Computed by the same resolver the executor uses."
        >
          <Tiles
            figures={[
              ["Refused outright", counts["refused outright"] ?? 0, "bad"],
              ["Needs human approval", counts["needs human approval"] ?? 0, "warn"],
              ["Acts unsupervised", counts["acts unsupervised"] ?? 0, "good"],
            ]}
          />
          <div className="mt-6">
            <WhatIf initial={manifest} />
          </div>
        </Section>

        <Section
          id="replay"
          eyebrow="Decision replay"
          title="Would today's policy still allow what already happened?"
          lede="Every recorded action re-resolved against the classifications in force now — not a report over stored tiers, but the real resolver over the real registry with current tags. The question an auditor actually asks."
        >
          <Tiles
            figures={[
              ["Replayed", replay.summary.replayed, "muted"],
              ["Would differ today", replay.summary.diverged, "info"],
              ["Now forbidden", replay.summary.now_forbidden, "warn"],
              [
                "Needs attention",
                replay.summary.needs_attention,
                replay.summary.needs_attention ? "bad" : "good",
              ],
            ]}
          />
          <div className="mt-4">
            <Reveal>
              <DataTable
                columns={[
                  ["action_type", "Action"],
                  ["execution_result", "Ran as"],
                  ["then", "Tier then"],
                  ["now", "Tier now"],
                  ["attention", "Needs attention"],
                ]}
                rows={replay.decisions.map((d) => ({
                  ...d,
                  then: TIER_NAMES[d.tier_then] ?? "-",
                  now: TIER_NAMES[d.tier_now] ?? "-",
                  attention: d.needs_attention ? "YES" : "no",
                }))}
              />
            </Reveal>
          </div>
        </Section>

        <Section
          id="refusals"
          eyebrow="The refusal ledger"
          title="Every action the agent declined to take"
          lede="A refusal is a result, not an error, so it is recorded with the same care as an action. This is the question most agents cannot answer about themselves."
        >
          {refusals.length === 0 ? (
            <Note tone="muted">No refusals recorded in the current run.</Note>
          ) : (
            <div className="space-y-2.5">
              {refusals.map((row, index) => (
                <Reveal key={index} delay={index * 55}>
                  <Card tone="bad">
                    <div className="flex flex-wrap items-center gap-x-1 gap-y-1">
                      <Chip tone="bad">Refused</Chip>
                      <Chip tone="bad">{TIER_NAMES[num(row.TIER)] ?? str(row.TIER)}</Chip>
                      <span className="text-[0.8rem] text-[var(--text-muted)]">
                        {str(row.WHEN_REFUSED)} &middot; {str(row.SUBJECT)}
                      </span>
                    </div>
                    <div className="mt-1.5 text-[0.88rem] leading-relaxed">
                      <strong>{str(row.ACTION_TYPE)}</strong> &mdash; {str(row.RATIONALE)}
                    </div>
                    {row.FOOTPRINT ? (
                      <div className="mt-1.5 break-all font-mono text-[0.72rem] text-[var(--text-muted)]">
                        {str(row.FOOTPRINT)}
                      </div>
                    ) : null}
                  </Card>
                </Reveal>
              ))}
            </div>
          )}
        </Section>

        <Section
          id="governance"
          eyebrow="Governance"
          title="The classifications in force, read live"
          lede={
            <>
              Read with <code className="font-mono text-[0.88em]">SYSTEM$GET_TAG</code> on every
              request — never from <code className="font-mono text-[0.88em]">ACCOUNT_USAGE</code>,
              which lags by up to two hours, and never cached. Change a tag and the agent&rsquo;s
              next decision changes with it, with no code change and no redeploy.
            </>
          }
        >
          <Reveal>
            <DataTable
              columns={[
                ["OBJECT", "Object"],
                ["SENSITIVITY", "Sensitivity"],
                ["MAY", "The agent may"],
              ]}
              rows={governance.map((row) => ({
                ...row,
                MAY: TIER_MEANING[str(row.SENSITIVITY)] ?? "act only with human approval (L3)",
              }))}
            />
          </Reveal>
          <p className="mt-2.5 text-[0.8rem] text-[var(--text-muted)]">
            Untagged is deliberately not treated as open: an object nobody has classified is not the
            same as an object someone classified as safe.
          </p>

          <h3 className="mt-9 text-[1.05rem] font-bold tracking-[-0.015em]">
            What it may <em>see</em>, as opposed to what it may <em>do</em>
          </h3>
          <p className="mt-2 max-w-[80ch] text-[0.9rem] leading-relaxed text-[var(--text-soft)]">
            The sensitivity tag stops the agent <strong>acting</strong> on a regulated record. It
            does not stop it <strong>reading</strong> one, deliberately, or it could never surface
            an aging hold and explain it. Those are two controls, so there is a second: a masking
            policy on <code className="font-mono text-[0.88em]">QUALITY_HOLDS.lot_ref</code>.
          </p>
          <div className="mt-4">
            <Reveal>
              <DataTable
                columns={[
                  ["HOLD", "Hold"],
                  ["LOT_REFERENCE", "Lot reference"],
                  ["SITE", "Site"],
                  ["SKU", "SKU"],
                  ["DAYS_OPEN", "Days open", true],
                  ["REASON", "Reason"],
                ]}
                rows={holds}
              />
            </Reveal>
          </div>
          <p className="mt-2.5 max-w-[80ch] text-[0.8rem] leading-relaxed text-[var(--text-muted)]">
            The policy is attached to the column and follows the <em>role</em>, not the client — so
            it holds even here, outside Snowflake. This page reads as{" "}
            <code className="font-mono">WARRANT_PUBLIC</code>, which is not the quality owner, and
            sees exactly what the agent sees.
          </p>

          <h3 className="mt-9 text-[1.05rem] font-bold tracking-[-0.015em]">
            The governed metric layer
          </h3>
          <p className="mt-2 max-w-[80ch] text-[0.9rem] leading-relaxed text-[var(--text-soft)]">
            Read through <code className="font-mono text-[0.88em]">SEMANTIC_VIEW(...)</code>, not
            the base tables. Classification governs what the agent may <em>do</em>; the semantic
            view governs what the numbers <em>mean</em>.
          </p>
          <div className="mt-4">
            <Reveal>
              <DataTable
                columns={[
                  ["SUPPLIER", "Supplier"],
                  ["TIER", "Tier"],
                  ["ON_TIME_PCT", "On-time %", true],
                  ["SHIPMENTS", "Shipments", true],
                  ["AVG_DAYS_LATE", "Avg days late", true],
                ]}
                rows={metrics}
              />
            </Reveal>
          </div>
        </Section>

        <Section
          id="unattended"
          eyebrow="Minimal manual intervention"
          title="What ran without anybody present"
          lede={
            <>
              Two Snowflake tasks operate this pipeline unattended:{" "}
              <code className="font-mono text-[0.88em]">EXECUTE_ON_APPROVAL</code>, triggered on the
              approval stream, and <code className="font-mono text-[0.88em]">SCAN_FOR_EXCEPTIONS</code>,
              an hourly sweep. Both serverless, so an idle schedule costs nothing.
            </>
          }
        >
          <Tiles
            figures={[
              ["Runs in 24h", schedule.summary.runs, "info"],
              ["Succeeded", schedule.summary.succeeded, "good"],
              ["Nothing to do", schedule.summary.skipped_nothing_to_do, "muted"],
              ["Failed", schedule.summary.failed, schedule.summary.failed ? "bad" : "good"],
            ]}
          />
          <div className="mt-4 space-y-2.5">
            {schedule.tasks.map((task) => (
              <Reveal key={task.name}>
                <Card tone={task.state === "started" ? "good" : "muted"}>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                    <span className="font-mono text-[0.9rem] font-bold">{task.name}</span>
                    <span
                      className="text-[0.66rem] font-extrabold uppercase tracking-[0.11em]"
                      style={{ color: `var(--${task.state === "started" ? "good" : "muted"})` }}
                    >
                      {task.state}
                    </span>
                  </div>
                  <div className="mt-1.5 text-[0.82rem] text-[var(--text-muted)]">{task.role}</div>
                </Card>
              </Reveal>
            ))}
          </div>
          <p className="mt-3 max-w-[80ch] text-[0.8rem] leading-relaxed text-[var(--text-muted)]">
            <strong>&ldquo;Nothing to do&rdquo; is counted separately from a failure, on purpose.</strong>{" "}
            A triggered task that finds its stream empty and spends nothing is working correctly —
            folding those into either column would misreport a healthy pipeline. The failures shown,
            if any, are real: they predate an <code className="font-mono">EXECUTE MANAGED TASK</code>{" "}
            grant that serverless tasks require, and the task auto-suspended itself after three of
            them rather than failing quietly.
          </p>
        </Section>

        <Section
          id="log"
          eyebrow="The append-only log"
          title="Every phase of every run, written once"
          lede="Including every refusal. Never updated, never deleted. The most recent 40."
        >
          <Reveal>
            <DataTable
              columns={[
                ["AT", "At"],
                ["PHASE", "Phase"],
                ["OUTCOME", "Outcome"],
                ["TIER", "Tier"],
                ["ACTOR", "Actor"],
                ["RATIONALE", "Rationale"],
              ]}
              rows={audit}
            />
          </Reveal>
        </Section>

        <footer className="mt-6 border-t border-[var(--line)] pt-6 text-[0.8rem] leading-relaxed text-[var(--text-muted)]">
          Read live from Snowflake on every request — nothing here is cached, because the claim is
          that a governance change takes effect immediately. Data is synthetic and generated
          in-warehouse. The governed console, where actions are actually approved, runs as Streamlit
          in Snowflake on the reviewer&rsquo;s own identity.{" "}
          <a href={REPO} className="underline underline-offset-2" style={{ color: "var(--info)" }}>
            Source, tests and reproduction steps
          </a>
          .
        </footer>
      </main>
    </>
  );
}
