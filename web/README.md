# Warrant — public read-only viewer

The governed console lives in Snowflake, where a reviewer signs in as themselves and an approval
is attributable to a person. Streamlit in Snowflake [cannot be shared with anyone who does not
have a Snowflake account][sharing], so this exists: a public surface that can read what the agent
decided and why, and cannot decide anything.

That limit is not a UI convention. It is enforced in grants — see
[`sql/50_public_viewer.sql`](../sql/50_public_viewer.sql). `WARRANT_PUBLIC` holds `SELECT` on the
operational tables and `USAGE` on the three procedures that only compute. It has no grant on
`EXECUTE_ACTION`, `EXECUTE_APPROVED`, `RUN_LOOP` or `GENERATE_AUDIT_PACK`. A missing button is a
decision a bug can undo; a missing grant is Snowflake refusing the statement.

Approving is a governed act, so it belongs to the surface that has an identity. This is the same
reason the Cortex Agent is given no tool bound to the executor.

So the page keeps the buttons and lets you watch them fail. **Approve**, **Reject** and **Defer**
are wired to the statements the console really runs, and pressing one prints Snowflake's own
refusal with its error code. Leaving them out would have been easier and would have proved
nothing: an absent control is indistinguishable from a hidden one. The two refusals differ, and
the difference is worth reading —

| Control | What Snowflake says | Why |
|---|---|---|
| Reject / Defer | `SQL access control error: Insufficient privileges to operate on table 'PENDING_ACTIONS'` | the role can see the queue and is told no |
| Approve | `SQL compilation error: Unknown user-defined function WARRANT.CORE.EXECUTE_ACTION` | without `USAGE`, Snowflake will not concede the executor exists |

Both statements bind an `action_id` that cannot exist, so neither would do anything even if a
grant were one day mis-applied — the demonstration cannot become the incident it describes. If
one ever *is* permitted, the page says so as an alarm rather than a success, and `npm run probe`
fails.

[sharing]: https://docs.snowflake.com/en/developer-guide/streamlit/features/sharing-streamlit-apps

## What is on the page

One scrolling page rather than tabs — a reviewer arriving from a submission form has a minute and
no idea what this is, and asking them to hunt through tabs for the argument loses more than the
tidiness gains. The order is the order of the claim.

| Section | What it shows | Source |
|---|---|---|
| Hero | Three tables resolved live to L4 / L3 / L2. Not an illustration — the same `SYSTEM$GET_TAG` read that drives the agent, so retagging a table changes it | `components/resolution.tsx` |
| One pass | Weekly on-time delivery for six suppliers with the RB-001 threshold, then the routing table. Hover the chart to read every supplier at that week | `components/trend.tsx` |
| Evidence | The escalated action, detector measurement beside model reasoning, and the **live** approve / reject / defer controls | `components/decide.tsx` |
| Console | Eight screenshots of the Streamlit console, click-to-full-size, because that surface cannot be shared | `components/console.tsx` |
| Authority | The capability manifest, plus a what-if that prices a policy change without making it | `components/whatif.tsx` |
| Replay · Refusals · Governance | Every recorded action re-resolved against today's tags; the refusal ledger; the tags in force | `app/page.tsx` |
| Tested | The planted hostile runbook, and the six scored reasoning cases | `components/tested.tsx` |
| Unattended | One mark per task run over 24 hours, coloured by outcome | `components/charts.tsx` |
| CoCo CLI | The MCP tool surface, the resources, the six skills, and the no-tier invariant | `components/coco.tsx` |

The tool, skill and scorecard lists in the last two are transcriptions of things this app cannot
import, so `tools/check_doc_claims.py` walks the MCP server, the skills tree and
`eval/scorecard.json` and fails the gate if any of them drifts.

## Running it locally

```bash
cd web
npm install
npm run probe      # connectivity + the read-only boundary, before anything else
npm run dev
```

`npm run probe` is worth running first and worth reading. It proves four things cheapest-first, so
a failure names its own cause: the key is accepted, the session is the role and warehouse
intended, every object and procedure the page touches is readable, and **both write paths are
refused**. That last assertion is the point — a regression in the grants shows up here rather than
as an action nobody authorised, and now that the page invites visitors to test the boundary
themselves, a silent regression would turn a governance claim into a false one on a public URL.

## Configuration

Four variables. Nothing else is read.

| Variable | Value |
|---|---|
| `SNOWFLAKE_ACCOUNT` | `<org>-<account>`, the same identifier the `snow` CLI uses |
| `SNOWFLAKE_USER` | `WARRANT_PUBLIC_SVC` |
| `SNOWFLAKE_PRIVATE_KEY` | the PKCS#8 private key, PEM including header and footer |
| `SNOWFLAKE_ROLE` / `SNOWFLAKE_WAREHOUSE` | optional; default to `WARRANT_PUBLIC` / `WARRANT_PUBLIC_WH` |

Generate the pair and register the public half:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out warrant_public.p8 -nocrypt
openssl rsa -in warrant_public.p8 -pubout -out warrant_public.pub
snow sql -c <conn> -q "ALTER USER WARRANT_PUBLIC_SVC SET RSA_PUBLIC_KEY = '<key, header and footer stripped>';"
```

Keep the private key outside the repository — this repository is public, and `*.p8`, `*.pem` and
`.env*.local` are ignored so a stray copy cannot be committed by accident.

**Newlines are the one trap.** Some deployment platforms store a multi-line secret with literal
`\n` two-character sequences rather than real newlines. `lib/snowflake.ts` accepts both, because
the failure otherwise is an opaque `ERR_OSSL_UNSUPPORTED` at connect time that reads like a broken
key rather than a mangled one.

## Deploying to Vercel

Root directory `web`. Framework preset Next.js, everything else default. Add the four variables
above. The build needs no Snowflake access — every page is `force-dynamic` and queries at request
time.

## How it is built

- **Next.js 16, App Router, server components.** The page queries Snowflake directly during the
  render; there is no API layer to secure separately and no client-side credential.
- **No cache, anywhere.** `force-dynamic` and `revalidate = 0`. The central claim is that
  reclassifying a table changes the agent's authority immediately, and a cached tag read would
  hide precisely that. It costs a warehouse resume on a cold request and is worth it.
- **Statements are module constants** in `lib/queries.ts`, values bind with `?`. That is the same
  boundary `tools/lint_sql_boundary.py` enforces on the Python side, extended to the web tier.
- **One connection per serverless instance**, cached as a promise so two requests arriving during
  the handshake wait on one attempt rather than opening two sessions.
- **The visual vocabulary matches the Streamlit console** — same tier names, same outcome names,
  same chips and tiles — so a reader moving between the two surfaces is not asked to learn a
  second language for the same ideas.
- **Colour never carries meaning alone.** Every chip prints its label, every tile its caption. The
  pointer-reactive lighting is decorative and disabled under `prefers-reduced-motion`.
