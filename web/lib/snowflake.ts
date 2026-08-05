/**
 * The only place this application talks to Snowflake.
 *
 * Authenticates as WARRANT_PUBLIC_SVC, a `TYPE = SERVICE` user holding the
 * WARRANT_PUBLIC role. That role has SELECT on a handful of views and USAGE on
 * the two procedures that only compute. It has no grant on EXECUTE_ACTION,
 * EXECUTE_APPROVED, RUN_LOOP or GENERATE_AUDIT_PACK — see sql/50_public_viewer.sql.
 *
 * So the read-only guarantee this app makes is not enforced here. It is enforced
 * by Snowflake, and a bug in this file cannot widen it. That ordering is
 * deliberate: a missing button is a UI decision a mistake can undo, a missing
 * grant is the database refusing the statement.
 */

import snowflake from "snowflake-sdk";

// The driver logs connection detail at INFO, including parameters. On a serverless
// platform that lands in logs a third party retains, so it is turned down before
// the first connection is created rather than after.
snowflake.configure({ logLevel: "ERROR", additionalLogToConsole: false });

/**
 * A single row, keyed by uppercase column name.
 *
 * Deliberately loose. Every query in `queries.ts` names its own columns and the
 * callers narrow at the point of use; a shared row interface here would have to
 * be the union of every shape and would stop describing any of them.
 */
export type Row = Record<string, unknown>;

/**
 * Reused across invocations of the same serverless instance.
 *
 * Establishing a Snowflake session costs a second or two, which on a cold lambda
 * is most of the response time. Vercel keeps an instance warm between nearby
 * requests, so holding the connection turns the second page view into a fast one.
 * The promise — not the connection — is cached, so two requests arriving during
 * the handshake wait on one attempt instead of opening two sessions.
 */
let pending: Promise<snowflake.Connection> | null = null;

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `${name} is not set. The public viewer needs SNOWFLAKE_ACCOUNT, ` +
        `SNOWFLAKE_USER and SNOWFLAKE_PRIVATE_KEY; see web/README.md.`,
    );
  }
  return value;
}

/**
 * Read the PKCS#8 private key from the environment.
 *
 * Deployment platforms differ in whether a multi-line secret survives with its
 * newlines intact — several store it with literal `\n` two-character sequences
 * instead. Both forms are accepted here, because the failure otherwise is an
 * opaque `ERR_OSSL_UNSUPPORTED` at connect time that reads like a broken key
 * rather than a mangled one.
 */
function privateKey(): string {
  const raw = required("SNOWFLAKE_PRIVATE_KEY");
  return raw.includes("\\n") ? raw.replace(/\\n/g, "\n") : raw;
}

function connect(): Promise<snowflake.Connection> {
  const connection = snowflake.createConnection({
    account: required("SNOWFLAKE_ACCOUNT"),
    username: required("SNOWFLAKE_USER"),
    authenticator: "SNOWFLAKE_JWT",
    privateKey: privateKey(),
    role: process.env.SNOWFLAKE_ROLE ?? "WARRANT_PUBLIC",
    warehouse: process.env.SNOWFLAKE_WAREHOUSE ?? "WARRANT_PUBLIC_WH",
    database: "WARRANT",
    schema: "CORE",
    clientSessionKeepAlive: false,
  });

  return new Promise((resolve, reject) => {
    connection.connect((error, conn) => {
      if (error) {
        // Drop the cached promise so the next request retries rather than
        // resolving forever against a session that never opened.
        pending = null;
        reject(error);
        return;
      }
      resolve(conn);
    });
  });
}

async function session(): Promise<snowflake.Connection> {
  if (!pending) pending = connect();
  const conn = await pending;
  // A warm lambda can outlive its Snowflake session. `isUp()` is a local check,
  // so this costs nothing on the happy path and avoids serving an error that
  // looks like a query fault when the session has simply expired.
  if (!conn.isUp()) {
    pending = connect();
    return pending;
  }
  return conn;
}

/**
 * Run one of the statements declared in `queries.ts`.
 *
 * @param statement A module-level constant. Never assembled from request data —
 *   the same boundary `tools/lint_sql_boundary.py` enforces on the Python side,
 *   extended to the web tier. Values bind; text does not.
 * @param binds Values for the `?` placeholders, if any.
 * @returns The rows, keyed by uppercase column name.
 */
export function query(statement: string, binds: unknown[] = []): Promise<Row[]> {
  return session().then(
    (conn) =>
      new Promise<Row[]>((resolve, reject) => {
        conn.execute({
          sqlText: statement,
          binds: binds as snowflake.Binds,
          complete: (error, _stmt, rows) => {
            if (error) reject(error);
            else resolve((rows ?? []) as Row[]);
          },
        });
      }),
  );
}

/**
 * Call one of the two procedures that return a JSON document and decode it.
 *
 * @param statement A `CALL` constant from `queries.ts`.
 * @param binds Values for the `?` placeholders, if any.
 * @returns The decoded payload.
 * @throws If the procedure returned nothing, which for these two means the call
 *   itself failed rather than that there was no data — both always return an
 *   object, even when it is empty.
 */
export async function callJson<T>(statement: string, binds: unknown[] = []): Promise<T> {
  const rows = await query(statement, binds);
  const first = rows[0];
  if (!first) throw new Error(`${statement} returned no rows`);
  return JSON.parse(String(Object.values(first)[0])) as T;
}
