/**
 * Connectivity probe. Run before building anything on top of it.
 *
 *   npm run probe
 *
 * Proves four things in order, cheapest first, so a failure names its own cause:
 *   1. the private key parses and Snowflake accepts the JWT
 *   2. the session is the role and warehouse we intended
 *   3. a real query returns real rows
 *   4. the read-only boundary holds — EXECUTE_ACTION must be refused
 *
 * Step 4 is the one that matters. A public endpoint is only read-only if the
 * database says so, and asserting it here means a regression shows up as a
 * failing probe rather than as an action nobody authorised.
 */

import snowflake from "snowflake-sdk";

snowflake.configure({ logLevel: "ERROR", additionalLogToConsole: false });

const key = process.env.SNOWFLAKE_PRIVATE_KEY ?? "";

const connection = snowflake.createConnection({
  account: process.env.SNOWFLAKE_ACCOUNT,
  username: process.env.SNOWFLAKE_USER,
  authenticator: "SNOWFLAKE_JWT",
  privateKey: key.includes("\\n") ? key.replace(/\\n/g, "\n") : key,
  role: process.env.SNOWFLAKE_ROLE ?? "WARRANT_PUBLIC",
  warehouse: process.env.SNOWFLAKE_WAREHOUSE ?? "WARRANT_PUBLIC_WH",
  database: "WARRANT",
  schema: "CORE",
});

const run = (sql) =>
  new Promise((resolve, reject) => {
    connection.execute({
      sqlText: sql,
      complete: (error, _s, rows) => (error ? reject(error) : resolve(rows ?? [])),
    });
  });

const started = Date.now();

connection.connect(async (error) => {
  if (error) {
    console.error("1. CONNECT  failed:", error.message);
    process.exit(1);
  }
  console.log(`1. CONNECT  ok (${Date.now() - started} ms)`);

  try {
    const [who] = await run(
      "SELECT CURRENT_USER() AS u, CURRENT_ROLE() AS r, CURRENT_WAREHOUSE() AS w",
    );
    console.log(`2. SESSION  ${who.U} as ${who.R} on ${who.W}`);

    const [counts] = await run(`
      SELECT (SELECT COUNT(*) FROM WARRANT.CORE.EXCEPTIONS)                            AS detected,
             (SELECT COUNT(*) FROM WARRANT.CORE.REFUSALS)                              AS refused,
             (SELECT COUNT(*) FROM WARRANT.AUDIT.ACTION_AUDIT)                         AS logged`);
    console.log(
      `3. READ     ${counts.DETECTED} exceptions, ${counts.REFUSED} refusals, ${counts.LOGGED} audit rows`,
    );

    // Every object the page reads, named individually.
    //
    // Not a nicety: CREATE OR REPLACE VIEW drops the grants on that view, so an
    // unrelated redeploy of sql/40_orchestration.sql silently revoked WARRANT_PUBLIC's
    // access to REFUSALS and APPROVAL_QUEUE and the deployed site 500'd. Nothing else
    // in this probe would have noticed — the counts above read tables, not views.
    for (const object of [
      "WARRANT.CORE.APPROVAL_QUEUE",
      "WARRANT.CORE.REFUSALS",
      "WARRANT.DATA.QUALITY_HOLDS",
      "WARRANT.CORE.EXCEPTIONS",
      "WARRANT.CORE.FINDINGS",
      "WARRANT.CORE.PENDING_ACTIONS",
      "WARRANT.AUDIT.ACTION_AUDIT",
    ]) {
      await run(`SELECT 1 FROM ${object} LIMIT 1`);
    }
    console.log("   GRANTS   all 7 objects the page reads are readable");

    for (const procedure of [
      "CALL WARRANT.CORE.REPLAY_DECISIONS(NULL)",
      "CALL WARRANT.CORE.TASK_ACTIVITY(1)",
    ]) {
      await run(procedure);
    }
    console.log("   PROCS    replay and task activity callable");

    const manifest = await run("CALL WARRANT.CORE.AUTHORITY_MANIFEST(NULL)");
    const payload = JSON.parse(String(Object.values(manifest[0])[0]));
    console.log(`   PROC     manifest returned ${payload.capabilities.length} capabilities`);

    // The boundary. This MUST fail.
    try {
      await run("CALL WARRANT.CORE.EXECUTE_ACTION('probe-should-never-run')");
      console.error("4. BOUNDARY  *** FAILED *** EXECUTE_ACTION was permitted to this role");
      process.exit(1);
    } catch (refused) {
      console.log(`4. BOUNDARY ok — EXECUTE_ACTION refused: ${refused.message.slice(0, 72)}`);
    }

    console.log(`\nprobe green in ${Date.now() - started} ms`);
    process.exit(0);
  } catch (failure) {
    console.error("failed:", failure.message);
    process.exit(1);
  }
});
