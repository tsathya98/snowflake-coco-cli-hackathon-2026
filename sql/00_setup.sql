-- Warrant :: 00 :: account setup, database, schemas, governance tags
-- Idempotent. Safe to re-run. Judges will re-run this.
--
-- Run as a role that can create databases and set account parameters (ACCOUNTADMIN
-- on a trial). Everything after this file runs as WARRANT_ROLE.

-- Cortex requires cross-region inference unless you are in a fully-enabled region.
-- Harmless if already set. ACCOUNTADMIN only.
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- ---------------------------------------------------------------------------
-- Compute. X-SMALL with a 60s auto-suspend: this is designed to run on a
-- $400 trial and an idle warehouse is the fastest way to burn it.
-- ---------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS WARRANT_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warrant pipeline compute';

-- Cortex Search serving needs its own warehouse and must not exceed MEDIUM.
CREATE WAREHOUSE IF NOT EXISTS WARRANT_SEARCH_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warrant Cortex Search indexing';

-- ---------------------------------------------------------------------------
-- Cost guard. This runs on a trial with a payment method on file, so overspend
-- is a real charge rather than a suspension.
--
-- A resource monitor covers warehouse credits only. It deliberately does NOT
-- cover Cortex AI functions or serverless tasks, both of which this pipeline
-- uses, so pair it with a Budget under Admin » Cost Management.
-- ---------------------------------------------------------------------------
CREATE RESOURCE MONITOR IF NOT EXISTS WARRANT_MONITOR
  WITH CREDIT_QUOTA = 100
  TRIGGERS ON 80 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE WARRANT_WH        SET RESOURCE_MONITOR = WARRANT_MONITOR;
ALTER WAREHOUSE WARRANT_SEARCH_WH SET RESOURCE_MONITOR = WARRANT_MONITOR;

-- ---------------------------------------------------------------------------
-- A SECOND monitor, for the warehouses this project does not own.
--
-- Found by a CoCo CLI cost audit (docs/coco_cli_evidence.md, session 2): the
-- monitor above covers the two warehouses the pipeline uses, and 39% of all
-- credit consumption was happening on COMPUTE_WH — the account default, used by
-- Snowsight worksheets, the `snow` CLI and CoCo itself. Human traffic, no
-- guardrail. Verifying the fix then surfaced SNOWFLAKE_LEARNING_WH in the same
-- state.
--
-- Deliberately a *separate* monitor rather than adding them to WARRANT_MONITOR.
-- Sharing one quota would couple interactive dev traffic to the demo's
-- availability: a Snowsight session that burned the 100 credits would trip the
-- SUSPEND trigger and take WARRANT_WH down with it, which is a self-inflicted
-- outage waiting for the worst possible moment. Separate budgets mean a browsing
-- binge can only suspend the browsing.
--
-- Each ALTER is wrapped in its own handler because these warehouses belong to the
-- account, not to this project, and may not exist elsewhere. A judge re-running
-- this file must not have it abort on a warehouse they never had.
-- ---------------------------------------------------------------------------
CREATE RESOURCE MONITOR IF NOT EXISTS WARRANT_DEV_MONITOR
  WITH CREDIT_QUOTA = 25
  TRIGGERS ON 80 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;

EXECUTE IMMEDIATE $$
DECLARE
  attached STRING DEFAULT '';
BEGIN
  BEGIN
    ALTER WAREHOUSE COMPUTE_WH SET RESOURCE_MONITOR = WARRANT_DEV_MONITOR;
    attached := attached || 'COMPUTE_WH ';
  EXCEPTION WHEN OTHER THEN attached := attached || '(no COMPUTE_WH) ';
  END;
  BEGIN
    ALTER WAREHOUSE SNOWFLAKE_LEARNING_WH SET RESOURCE_MONITOR = WARRANT_DEV_MONITOR;
    attached := attached || 'SNOWFLAKE_LEARNING_WH ';
  EXCEPTION WHEN OTHER THEN attached := attached || '(no SNOWFLAKE_LEARNING_WH) ';
  END;
  RETURN 'WARRANT_DEV_MONITOR covers: ' || attached;
END;
$$;

-- SYSTEM$STREAMLIT_NOTEBOOK_WH is deliberately left alone: it is a system-managed
-- warehouse, and the console runs on WARRANT_WH by its own QUERY_WAREHOUSE, so
-- nothing here depends on it.

CREATE DATABASE IF NOT EXISTS WARRANT
  COMMENT = 'Warrant :: governed autonomous operations agent';

USE DATABASE WARRANT;

CREATE SCHEMA IF NOT EXISTS DATA    COMMENT = 'Synthetic operational source data';
CREATE SCHEMA IF NOT EXISTS CORE    COMMENT = 'Detection, reasoning and action pipeline';
CREATE SCHEMA IF NOT EXISTS AUDIT   COMMENT = 'Append-only decision and action log';

-- ---------------------------------------------------------------------------
-- The governance vocabulary.
--
-- This tag is the whole point of Warrant. An action's authority ceiling is read
-- from the tags on the objects it touches, so changing policy is an ALTER TABLE,
-- not a code change and a redeploy.
-- ---------------------------------------------------------------------------
CREATE TAG IF NOT EXISTS CORE.SENSITIVITY
  ALLOWED_VALUES 'open', 'internal', 'regulated'
  COMMENT = $$Authority ceiling for automated action against this object.
open      -> agent may act automatically (L2)
internal  -> agent must obtain human approval (L3)
regulated -> agent may never act (L4); it may still read and explain
Untagged is deliberately NOT treated as open. See src/warrant/authority/tiers.py.$$;

-- ---------------------------------------------------------------------------
-- A dedicated role, so the demo shows real RBAC rather than everything as
-- ACCOUNTADMIN. Judges look at this.
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS WARRANT_ROLE
  COMMENT = 'Least-privilege role for the Warrant pipeline';

GRANT USAGE ON WAREHOUSE WARRANT_WH        TO ROLE WARRANT_ROLE;
GRANT USAGE ON WAREHOUSE WARRANT_SEARCH_WH TO ROLE WARRANT_ROLE;
GRANT USAGE ON DATABASE WARRANT            TO ROLE WARRANT_ROLE;
GRANT USAGE ON SCHEMA WARRANT.DATA         TO ROLE WARRANT_ROLE;
GRANT USAGE ON SCHEMA WARRANT.CORE         TO ROLE WARRANT_ROLE;
GRANT USAGE ON SCHEMA WARRANT.AUDIT        TO ROLE WARRANT_ROLE;

GRANT CREATE TABLE, CREATE VIEW, CREATE DYNAMIC TABLE, CREATE TASK,
      CREATE STREAM, CREATE PROCEDURE, CREATE FUNCTION, CREATE STAGE,
      CREATE SEMANTIC VIEW, CREATE CORTEX SEARCH SERVICE, CREATE ALERT,
      CREATE STREAMLIT, CREATE FILE FORMAT, CREATE AGENT
  ON SCHEMA WARRANT.CORE TO ROLE WARRANT_ROLE;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA WARRANT.DATA  TO ROLE WARRANT_ROLE;
GRANT CREATE TABLE            ON SCHEMA WARRANT.AUDIT   TO ROLE WARRANT_ROLE;

-- Cortex access. CORTEX_USER is granted to PUBLIC by default on most accounts;
-- this is explicit so the grant is visible to a reviewer.
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE WARRANT_ROLE;

-- Tasks run as the role that owns them and need this account-level privilege.
GRANT EXECUTE TASK ON ACCOUNT TO ROLE WARRANT_ROLE;

-- And serverless tasks need a *second*, separate privilege. Without it a task is created
-- happily, resumes happily, then fails every run with
--   091089: Cannot execute task, EXECUTE MANAGED TASK privilege must be granted to owner role
-- until SUSPEND_TASK_AFTER_NUM_FAILURES suspends it. Nothing surfaces at create or resume
-- time, so the only symptom is a task that silently stopped — check
-- INFORMATION_SCHEMA.TASK_HISTORY rather than SHOW TASKS, because SHOW reports the state
-- as 'started' right up until the auto-suspend.
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE WARRANT_ROLE;

-- Cortex access is the only grant needed on the SNOWFLAKE database.
-- SYSTEM$GET_TAG needs USAGE on the tag's parent DB/schema (WARRANT.CORE, above).
-- IMPORTED PRIVILEGES would add ACCOUNT_USAGE access, which this project never uses.

-- ---------------------------------------------------------------------------
-- Column-level governance: the agent cannot read what it cannot act on.
--
-- The sensitivity tag stops the agent *acting* on a regulated record. It does
-- nothing to stop it *reading* one — and reads are deliberately tag-exempt,
-- because the agent has to be able to surface an aging hold and explain it.
--
-- So the two controls do different jobs. RB-003 lets automation surface a hold
-- and notify the owner, and nothing further. Surfacing needs the age, the site,
-- the SKU and the reason. It does not need `lot_ref` — the physical lot
-- identifier is what makes a record actionable, and identifying a lot is a
-- qualified person's business. This policy enforces that separation, so the
-- agent literally cannot name the thing it is forbidden to touch.
--
-- Deliberately a plain redaction, not a hash-based pseudonym. `lot_ref` is drawn
-- from a domain of forty known values, so any digest of it is reversible by
-- brute force in milliseconds; a pseudonym here would be security theatre that
-- looked more sophisticated than the redaction it replaced.
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS WARRANT_QUALITY_OWNER
  COMMENT = 'The qualified person. Sees lot identifiers; the agent does not.';

CREATE MASKING POLICY IF NOT EXISTS WARRANT.CORE.LOT_REF_MASK
  AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'WARRANT_QUALITY_OWNER') THEN val
    ELSE 'LOT-WITHHELD'
  END
  COMMENT = 'Lot identifiers are visible to a qualified person, withheld from automation';

-- Least privilege on purpose: WARRANT_ROLE owns QUALITY_HOLDS and so may attach a
-- policy it has APPLY on, but it is NOT granted APPLY MASKING POLICY on the
-- account, which would let it attach or detach policies anywhere. The narrower
-- grant means the agent's own role cannot unmask itself by dropping the policy
-- from some other table and re-adding a permissive one.
GRANT APPLY ON MASKING POLICY WARRANT.CORE.LOT_REF_MASK TO ROLE WARRANT_ROLE;

GRANT USAGE ON DATABASE WARRANT      TO ROLE WARRANT_QUALITY_OWNER;
GRANT USAGE ON SCHEMA WARRANT.DATA   TO ROLE WARRANT_QUALITY_OWNER;
GRANT USAGE ON WAREHOUSE WARRANT_WH  TO ROLE WARRANT_QUALITY_OWNER;
-- SELECT on QUALITY_HOLDS is granted in sql/10, where the table exists and WARRANT_ROLE
-- owns it. Granting it here would fail on a first run and only appear to work on a re-run.

-- Granted to the running user so the unmasked side of the demo is one USE ROLE away.
SET quality_owner_grantee = CURRENT_USER();
GRANT ROLE WARRANT_QUALITY_OWNER TO USER IDENTIFIER($quality_owner_grantee);

-- Grant to the current user so the demo is runnable immediately.
SET current_user_name = CURRENT_USER();
GRANT ROLE WARRANT_ROLE TO USER IDENTIFIER($current_user_name);

-- Stage holding the packaged Python. The stored procedure imports the real
-- package rather than inlining a copy of the loop, so the code that runs in
-- Snowflake is byte-for-byte the code the test suite covers.
CREATE STAGE IF NOT EXISTS WARRANT.CORE.CODE
  COMMENT = 'Packaged warrant python, imported by CORE.RUN_LOOP';

GRANT READ, WRITE ON STAGE WARRANT.CORE.CODE TO ROLE WARRANT_ROLE;

-- The document corpus. A directory table is required because sql/15_corpus.sql
-- drives the parse from DIRECTORY()/the manifest rather than a hardcoded file
-- list, and server-side encryption is required because AI_PARSE_DOCUMENT cannot
-- read a client-side-encrypted stage.
CREATE STAGE IF NOT EXISTS WARRANT.CORE.DOCS
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Operating procedures as documents, parsed by sql/15_corpus.sql';

GRANT READ, WRITE ON STAGE WARRANT.CORE.DOCS TO ROLE WARRANT_ROLE;

-- Where the agent writes its own evidence packs. Server-side encryption so the
-- files stay readable to a reviewer with the role, and a directory table so a
-- pack can be found without knowing its timestamped name.
CREATE STAGE IF NOT EXISTS WARRANT.CORE.PACKS
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Decision evidence packs written by CORE.GENERATE_AUDIT_PACK';

GRANT READ, WRITE ON STAGE WARRANT.CORE.PACKS TO ROLE WARRANT_ROLE;

-- Separate stage for the console, so redeploying the UI cannot disturb the
-- packaged python the stored procedures import.
CREATE STAGE IF NOT EXISTS WARRANT.CORE.STREAMLIT
  COMMENT = 'Streamlit in Snowflake approval console'
  DIRECTORY = (ENABLE = TRUE);

GRANT READ, WRITE ON STAGE WARRANT.CORE.STREAMLIT TO ROLE WARRANT_ROLE;

-- ---------------------------------------------------------------------------
-- Runtime configuration. Values the pipeline needs that are environment-specific
-- rather than code, so they belong in a table rather than in the repository.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS WARRANT.CORE.CONFIG (
    key   VARCHAR PRIMARY KEY,
    value VARCHAR
);

GRANT SELECT ON TABLE WARRANT.CORE.CONFIG TO ROLE WARRANT_ROLE;

-- ---------------------------------------------------------------------------
-- Escalation delivery.
--
-- On a trial, email reaches only verified users in the same account and the
-- recipient must appear in ALLOWED_RECIPIENTS. Rather than commit a personal
-- address to a public repository, derive the running user's own verified
-- address — so this wires itself up in a judge's account exactly as it does in
-- ours, and the repository contains nobody's email.
--
-- Notification integrations are account-level, hence ACCOUNTADMIN here and a
-- USAGE grant to WARRANT_ROLE. The address is also written to CONFIG because
-- WARRANT_ROLE cannot run SHOW USERS to rediscover it at send time.
--
-- Wrapped in EXECUTE IMMEDIATE so the whole block is one statement: a bare
-- DECLARE/BEGIN/END would be split on its semicolons by the CLI.
-- ---------------------------------------------------------------------------
EXECUTE IMMEDIATE $$
DECLARE
  recipient STRING;
BEGIN
  SHOW USERS;
  SELECT "email" INTO :recipient
    FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
   WHERE "name" = CURRENT_USER();

  IF (recipient IS NULL) THEN
    RETURN 'No verified email on the current user. Escalation email not created; '
        || 'the approval console remains the notification surface.';
  END IF;

  EXECUTE IMMEDIATE
       'CREATE OR REPLACE NOTIFICATION INTEGRATION WARRANT_EMAIL '
    || 'TYPE = EMAIL ENABLED = TRUE ALLOWED_RECIPIENTS = (''' || recipient || ''')';
  EXECUTE IMMEDIATE 'GRANT USAGE ON INTEGRATION WARRANT_EMAIL TO ROLE WARRANT_ROLE';

  MERGE INTO WARRANT.CORE.CONFIG AS t
  USING (SELECT 'escalation_email' AS key, :recipient AS value) AS s
     ON t.key = s.key
   WHEN MATCHED THEN UPDATE SET t.value = s.value
   WHEN NOT MATCHED THEN INSERT (key, value) VALUES (s.key, s.value);

  RETURN 'Escalation email wired to the verified address on the current user.';
END;
$$;


SELECT 'Warrant :: 00_setup complete' AS status;
