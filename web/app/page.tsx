/**
 * The public, read-only viewer.
 *
 * One scrolling page rather than tabs. A reviewer arriving from a submission form
 * has a minute and no idea what this is; asking them to hunt through tabs for the
 * argument loses more than the tidiness gains. The order is the order of the
 * claim: what it did, what it is allowed to do, what it refused, what governs it.
 *
 * Server-rendered on every request. There is no cache anywhere in this app —
 * the whole point is that reclassifying a table changes the agent's authority
 * immediately, and a cached tag read would hide exactly that.
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
  TIER_NAMES,
  TIER_TONE,
  type ManifestPayload,
  type ReplayPayload,
} from "@/lib/queries";
import { PointerGlow } from "@/components/pointer";
import { Chip, ModelText, Note, Section, Table, Tag, Tiles } from "@/components/ui";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const TIER_MEANING: Record<string, string> = {
  open: "act unsupervised (L2)",
  internal: "act only with human approval (L3)",
  regulated: "read and explain, never act (L4)",
};

const str = (value: unknown) => String(value ?? "");
const num = (value: unknown) => Number(value ?? 0);

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
  const [manifest, replay] = await Promise.all([
    callJson<ManifestPayload>(MANIFEST),
    callJson<ReplayPayload>(REPLAY),
  ]);

  const escalated = decisions.find((d) => str(d.DECISION) === "pending") ?? decisions[0];
  const counts = manifest.capabilities.reduce<Record<string, number>>((acc, c) => {
    acc[c.outcome] = (acc[c.outcome] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      <PointerGlow />
      <main>
        <header className="hero" data-glow>
          <h1>
            <span>&#9878;&#65039; Warrant</span>
            <span className="kicker">governed autonomous operations &middot; on Snowflake</span>
          </h1>
          <p>
            An operations agent that closes the loop from detection to action, and whose permission
            to take each action is read from the Snowflake object tags on the data that action
            touches &mdash; live, and again at execution time, so a human&rsquo;s approval cannot
            outlive the policy it was granted under.
          </p>
          <p style={{ marginTop: 10, fontSize: "0.86rem", color: "var(--muted)" }}>
            Team Argmax &middot; CoCo CLI Hackathon 2026, Problem Statement 1 &middot;{" "}
            <a href="https://github.com/tsathya98/snowflake-coco-cli-hackathon-2026">source</a>
          </p>
        </header>

        <Tiles
          figures={[
            ["Exceptions detected", num(headline?.DETECTED), "info"],
            ["Handled by the agent", num(headline?.ACTED), "good"],
            ["Awaiting a human", num(headline?.AWAITING), "warn"],
            ["Refused", num(headline?.REFUSED), "bad"],
            ["Decisions logged", num(headline?.LOGGED), "muted"],
          ]}
        />

        <Note tone="info">
          <strong>This page is read-only, and not by convention.</strong> It authenticates as{" "}
          <code>WARRANT_PUBLIC</code>, a role holding <code>SELECT</code> on a handful of objects
          and <code>USAGE</code> on the two procedures that only compute. It has no grant on{" "}
          <code>EXECUTE_ACTION</code>. Approving is a governed act and belongs to the console
          inside Snowflake, where the reviewer has an identity of their own &mdash; the same reason
          the conversational agent is given no tool bound to the executor.
        </Note>

        <Section
          id="pass"
          title="What one pass did"
          lede={
            <>
              One <code>CALL WARRANT.CORE.RUN_LOOP(&apos;AUTO&apos;)</code> over 2,400 shipments, 40
              quality holds and 6 SKUs. Three different outcomes, from one loop with no branching on
              table names &mdash; the tag on the data decided each one.
            </>
          }
        >
          <Table
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
                str(d.DECISION) === "pending"
                  ? "awaiting a human"
                  : str(d.EXECUTION_RESULT),
            }))}
          />
        </Section>

        {escalated ? (
          <Section
            id="evidence"
            title="The one it would not decide alone"
            lede="Evidence beside the reasoning, not behind a click. A reviewer asked to approve something whose evidence is one click away approves it without clicking."
          >
            <div className="split">
              <div>
                <div className="label">What was observed</div>
                <ul style={{ margin: "0 0 14px", paddingLeft: 18, color: "var(--bone-soft)" }}>
                  <li>
                    <strong>Observed</strong> &mdash; {str(escalated.OBSERVED)}
                  </li>
                  <li>
                    <strong>Expected</strong> &mdash; {str(escalated.EXPECTED)}
                  </li>
                  <li>
                    <strong>Deviation</strong> &mdash; {str(escalated.DEVIATION)}
                  </li>
                  <li>
                    <strong>Detected by</strong> &mdash;{" "}
                    <code>{str(escalated.DETECTION_METHOD)}</code>
                  </li>
                </ul>
                <div className="label">Grounded in</div>
                <div>
                  {(JSON.parse(str(escalated.GROUNDED_IN) || "[]") as string[]).map((doc) => (
                    <Tag key={doc}>{doc}</Tag>
                  ))}
                </div>
              </div>
              <div>
                <div className="label">Why this action, and why it needs a human</div>
                <ModelText>{str(escalated.ROOT_CAUSE)}</ModelText>
                <div style={{ marginTop: 14 }}>
                  <Chip tone={SEVERITY_TONE[str(escalated.SEVERITY).toLowerCase()] ?? "muted"}>
                    {str(escalated.SEVERITY)}
                  </Chip>
                  <Chip tone={TIER_TONE[num(escalated.TIER)] ?? "muted"}>
                    {TIER_NAMES[num(escalated.TIER)]}
                  </Chip>
                </div>
                <p style={{ fontSize: "0.84rem", color: "var(--muted)", marginTop: 6 }}>
                  {str(escalated.TIER_RATIONALE)}
                </p>
                <p style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  Produced by <code>{str(escalated.MODEL)}</code>. Bound as query parameters &mdash;
                  the model never contributes SQL text.
                </p>
              </div>
            </div>
          </Section>
        ) : null}

        <Section
          id="authority"
          title="What is it allowed to do, right now?"
          lede="Every action in the registry resolved against the classifications currently on the data it touches. Most restricted first — what the agent may not do is what a reviewer should read before what it may. Computed by the same resolver the executor uses."
        >
          <Tiles
            figures={[
              ["Refused outright", counts["refused outright"] ?? 0, "bad"],
              ["Needs human approval", counts["needs human approval"] ?? 0, "warn"],
              ["Acts unsupervised", counts["acts unsupervised"] ?? 0, "good"],
            ]}
          />
          {manifest.capabilities.map((capability) => (
            <div
              className="card"
              data-glow
              key={capability.action}
              style={
                {
                  ["--accent" as string]: `var(--${OUTCOME_TONE[capability.outcome] ?? "muted"})`,
                } as React.CSSProperties
              }
            >
              <div className="head">
                <span className="name">{capability.action}</span>
                <span className="outcome">{capability.outcome}</span>
              </div>
              <div style={{ marginTop: 8 }}>
                {capability.classifications.map((c) => (
                  <Tag key={c.object}>
                    {c.object.split(".").pop()} &middot; {c.sensitivity ?? "untagged"}
                  </Tag>
                ))}
              </div>
              <div className="why">{capability.rationale}</div>
            </div>
          ))}
        </Section>

        <Section
          id="replay"
          title="Would today's policy still allow what already happened?"
          lede="Every recorded action re-resolved against the classifications in force now — not a report over stored tiers, but the real resolver over the real registry with current tags. The question an auditor actually asks, and the one nobody can usually answer."
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
          <Table
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
        </Section>

        <Section
          id="refusals"
          title="Every action it declined to take"
          lede="A refusal is a result, not an error, so it is recorded with the same care as an action. This is the question most agents cannot answer about themselves."
        >
          {refusals.length === 0 ? (
            <Note tone="muted">No refusals recorded in the current run.</Note>
          ) : (
            refusals.map((row, index) => (
              <div
                className="card"
                data-glow
                key={index}
                style={{ ["--accent" as string]: "var(--bad)" } as React.CSSProperties}
              >
                <div>
                  <Chip tone="bad">Refused</Chip>
                  <Chip tone="bad">{TIER_NAMES[num(row.TIER)] ?? str(row.TIER)}</Chip>
                  <span style={{ color: "var(--muted)", fontSize: "0.84rem" }}>
                    {str(row.WHEN_REFUSED)} &middot; {str(row.SUBJECT)}
                  </span>
                </div>
                <div style={{ marginTop: 6 }}>
                  <strong>{str(row.ACTION_TYPE)}</strong> &mdash; {str(row.RATIONALE)}
                </div>
                {row.FOOTPRINT ? (
                  <div className="why">Classifications at execution time: {str(row.FOOTPRINT)}</div>
                ) : null}
              </div>
            ))
          )}
        </Section>

        <Section
          id="governance"
          title="The classifications in force, read live"
          lede={
            <>
              Read with <code>SYSTEM$GET_TAG</code> on every request &mdash; never from{" "}
              <code>ACCOUNT_USAGE</code>, which lags by up to two hours, and never cached. Change a
              tag and the agent&rsquo;s next decision changes with it, with no code change and no
              redeploy.
            </>
          }
        >
          <Table
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
          <p style={{ fontSize: "0.82rem", color: "var(--muted)", marginTop: 8 }}>
            Untagged is deliberately not treated as open: an object nobody has classified is not the
            same as an object someone classified as safe.
          </p>
        </Section>

        <Section
          id="masking"
          title="What it may see, as opposed to what it may do"
          lede={
            <>
              The sensitivity tag stops the agent <strong>acting</strong> on a regulated record. It
              does not stop it <strong>reading</strong> one, deliberately, or it could never surface
              an aging hold and explain it. Those are two controls, so there is a second: a masking
              policy on <code>QUALITY_HOLDS.lot_ref</code>.
            </>
          }
        >
          <Table
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
          <p style={{ fontSize: "0.82rem", color: "var(--muted)", marginTop: 8 }}>
            The policy is attached to the column and follows the <em>role</em>, not the client
            &mdash; so it holds even here, outside Snowflake. This page reads as{" "}
            <code>WARRANT_PUBLIC</code>, which is not the quality owner, and sees exactly what the
            agent sees. A qualified person reads the real values from the same query.
          </p>
        </Section>

        <Section
          id="metrics"
          title="The governed metric layer"
          lede={
            <>
              Read through <code>SEMANTIC_VIEW(...)</code> against{" "}
              <code>CORE.OPS_ANALYSIS</code>, not the base tables. Classification governs what the
              agent may <em>do</em>; the semantic view governs what the numbers <em>mean</em>, so
              this page and the agent cannot quietly disagree about on-time rate.
            </>
          }
        >
          <Table
            columns={[
              ["SUPPLIER", "Supplier"],
              ["TIER", "Tier"],
              ["ON_TIME_PCT", "On-time %", true],
              ["SHIPMENTS", "Shipments", true],
              ["AVG_DAYS_LATE", "Avg days late", true],
            ]}
            rows={metrics}
          />
        </Section>

        <Section
          id="log"
          title="The append-only decision log"
          lede="Every phase of every run, including every refusal, written once and never updated. The most recent 40."
        >
          <Table
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
        </Section>

        <div className="foot">
          Read live from Snowflake on every request &mdash; nothing on this page is cached, because
          the claim is that a governance change takes effect immediately. Data is synthetic and
          generated in-warehouse. The governed console, where actions are actually approved, runs
          as Streamlit in Snowflake on the reviewer&rsquo;s own identity.
        </div>
      </main>
    </>
  );
}
