-- Warrant :: 36 :: the approval console
--
-- Requires streamlit/warrant_console.py to be on @WARRANT.CORE.STREAMLIT/console
-- already. ./scripts/setup.sh PUTs it before reaching here.
--
-- ---------------------------------------------------------------------------
-- Why the console is created here in SQL rather than with `snow streamlit deploy`.
--
-- It was deployed with the CLI first, and the app failed to load every single
-- time with:
--
--     Python Interpreter Error:
--     TypeError: bad argument type for built-in operation
--
-- and nothing else. No traceback, and — the part that took longest to notice —
-- no rows in the account event table and *no queries in QUERY_HISTORY from the
-- app at all*, even with LOG_LEVEL = 'DEBUG' and TRACE_LEVEL = 'ALWAYS' set on
-- the object. That absence is the whole diagnosis: the interpreter never reached
-- line one of the script, so every theory about pandas, dtypes, emoji or
-- st.dataframe was aimed at a stage that was never executing.
--
-- The app file is byte-for-byte identical under both deployment methods. What
-- differs is the object the CLI produces:
--
--   | property   | snow streamlit deploy                | here                |
--   |------------|--------------------------------------|---------------------|
--   | owner      | ACCOUNTADMIN (the connection's role) | WARRANT_ROLE        |
--   | root       | snow://streamlit/.../versions/live   | a plain stage       |
--   | main_file  | streamlit/warrant_console.py (nested)| warrant_console.py  |
--   | title      | contained an em dash                 | ASCII               |
--
-- Created this way it loads. Note that Streamlit in Snowflake runs with the
-- *owner's* rights, so WARRANT_ROLE ownership is not incidental tidying: it is
-- what makes the console see the regulated table through the same masking policy
-- the agent does, rather than reading around it as ACCOUNTADMIN.
--
-- Idempotent. Safe to re-run.
-- ---------------------------------------------------------------------------

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA CORE;

CREATE OR REPLACE STREAMLIT WARRANT_CONSOLE
  ROOT_LOCATION = '@WARRANT.CORE.STREAMLIT/console'
  MAIN_FILE = 'warrant_console.py'
  QUERY_WAREHOUSE = WARRANT_WH
  TITLE = 'Warrant - approval console'
  COMMENT = 'Human-in-the-loop review for the Warrant operations agent';

-- No environment.yml is staged, deliberately. The console imports only stdlib,
-- streamlit and snowflake.snowpark, all present in the default warehouse
-- runtime; shipping a manifest forces a conda resolution on every cold start and
-- buys nothing. pandas arrives transitively via streamlit, which is why nothing
-- in the console hands it a Python None -- see the comments in the file.

SHOW STREAMLITS LIKE 'WARRANT_CONSOLE' IN SCHEMA CORE;

SELECT 'Warrant :: 36_console complete' AS status;
