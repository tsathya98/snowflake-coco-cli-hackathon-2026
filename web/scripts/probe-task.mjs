/**
 * Can WARRANT_PUBLIC call TASK_ACTIVITY, and with a bound parameter?
 *
 * Split out from probe.mjs because a grant on a *new* procedure is exactly the thing
 * that gets forgotten, and the failure mode is a 500 on the deployed page rather than
 * anything visible locally.
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

const run = (sql, binds = []) =>
  new Promise((resolve, reject) => {
    connection.execute({
      sqlText: sql,
      binds,
      complete: (error, _s, rows) => (error ? reject(error) : resolve(rows ?? [])),
    });
  });

connection.connect(async (error) => {
  if (error) {
    console.error("connect failed:", error.message);
    process.exit(1);
  }
  try {
    const rows = await run("CALL WARRANT.CORE.TASK_ACTIVITY(?)", [24]);
    const payload = JSON.parse(String(Object.values(rows[0])[0]));
    console.log("TASK_ACTIVITY ok as WARRANT_PUBLIC");
    console.log("  tasks:  ", payload.tasks.map((t) => `${t.name}=${t.state}`).join(", "));
    console.log("  summary:", JSON.stringify(payload.summary));
    process.exit(0);
  } catch (failure) {
    console.error("TASK_ACTIVITY FAILED:", failure.message);
    process.exit(1);
  }
});
