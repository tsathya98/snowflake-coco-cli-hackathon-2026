-- ---------------------------------------------------------------------------
-- Warrant :: 50_public_viewer
--
-- The identity behind the public, read-only web console at web/.
--
-- The governed console — Streamlit in Snowflake — runs on the reviewer's own
-- Snowflake login, which is what makes an approval in ACTION_AUDIT attributable
-- to a person. A public web app has no such identity: every visitor would share
-- one service account. So it does not get one. WARRANT_PUBLIC can read what the
-- agent decided and why; it cannot decide anything.
--
-- That is not a limitation apologised for in the UI. It is the tier model applied
-- to the surface itself, and it is the same reason WARRANT_ANALYST is given no
-- generic tool bound to the executor: a surface with no established identity has
-- no authority, however persuasive the request.
--
-- The constraint is enforced HERE, in grants, not in the web tier. A missing
-- button is a UI decision that a bug can undo. A missing grant is Snowflake
-- refusing the statement.
--
-- Run once, after 45_review.sql. Requires ACCOUNTADMIN (creating a role and a
-- user is an account-level act).
-- ---------------------------------------------------------------------------

USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- A warehouse of its own.
--
-- Public traffic is unpredictable and this account is a trial. Giving the web
-- app its own X-SMALL warehouse means a crawler cannot contend with the agent's
-- own runs, and its spend is separately attributable in WAREHOUSE_METERING.
-- AUTO_SUSPEND is deliberately the floor: a page view should not keep compute
-- warm for a minute after the reader has gone.
-- ---------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS WARRANT_PUBLIC_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Serves the public read-only web console. Separately metered on purpose.';

ALTER WAREHOUSE WARRANT_PUBLIC_WH SET RESOURCE_MONITOR = WARRANT_MONITOR;

CREATE ROLE IF NOT EXISTS WARRANT_PUBLIC
  COMMENT = 'Read-only. Serves the public web console. Holds no privilege that can change anything.';

GRANT USAGE ON WAREHOUSE WARRANT_PUBLIC_WH TO ROLE WARRANT_PUBLIC;
GRANT USAGE ON DATABASE WARRANT              TO ROLE WARRANT_PUBLIC;
GRANT USAGE ON SCHEMA WARRANT.CORE           TO ROLE WARRANT_PUBLIC;
GRANT USAGE ON SCHEMA WARRANT.DATA           TO ROLE WARRANT_PUBLIC;
GRANT USAGE ON SCHEMA WARRANT.AUDIT          TO ROLE WARRANT_PUBLIC;

-- ---------------------------------------------------------------------------
-- Reads, enumerated one at a time.
--
-- Deliberately not `GRANT SELECT ON ALL TABLES`, and deliberately not `ON FUTURE`.
-- A blanket grant would silently extend to whatever gets created next, which is
-- exactly the drift this project exists to argue against. A table added later
-- must be granted deliberately or the public app cannot see it — and the app
-- failing loudly on a missing grant is the correct outcome.
-- ---------------------------------------------------------------------------
GRANT SELECT ON VIEW  WARRANT.CORE.APPROVAL_QUEUE   TO ROLE WARRANT_PUBLIC;
GRANT SELECT ON VIEW  WARRANT.CORE.REFUSALS         TO ROLE WARRANT_PUBLIC;
GRANT SELECT ON TABLE WARRANT.CORE.EXCEPTIONS       TO ROLE WARRANT_PUBLIC;
GRANT SELECT ON TABLE WARRANT.CORE.FINDINGS         TO ROLE WARRANT_PUBLIC;
GRANT SELECT ON TABLE WARRANT.CORE.PENDING_ACTIONS  TO ROLE WARRANT_PUBLIC;
GRANT SELECT ON TABLE WARRANT.AUDIT.ACTION_AUDIT    TO ROLE WARRANT_PUBLIC;
GRANT SELECT ON TABLE WARRANT.DATA.QUALITY_HOLDS    TO ROLE WARRANT_PUBLIC;

-- The semantic view, so the public app reads the same metric definitions the
-- agent answers from rather than re-deriving on-time rate in its own SQL.
GRANT SELECT ON SEMANTIC VIEW WARRANT.CORE.OPS_ANALYSIS TO ROLE WARRANT_PUBLIC;

-- ---------------------------------------------------------------------------
-- The two procedures that only compute.
--
-- AUTHORITY_MANIFEST and REPLAY_DECISIONS resolve the real registry against the
-- real tags and return JSON. They write nothing.
--
-- GENERATE_AUDIT_PACK is NOT granted: it writes a file to a stage, and a public
-- endpoint that can create objects on request is a denial-of-service surface
-- however read-only its intent.
--
-- EXECUTE_ACTION, EXECUTE_APPROVED and RUN_LOOP are NOT granted, which is the
-- whole point of this file. If the web tier were ever coaxed into calling one,
-- Snowflake refuses it.
-- ---------------------------------------------------------------------------
GRANT USAGE ON PROCEDURE WARRANT.CORE.AUTHORITY_MANIFEST(OBJECT) TO ROLE WARRANT_PUBLIC;
GRANT USAGE ON PROCEDURE WARRANT.CORE.REPLAY_DECISIONS(OBJECT)   TO ROLE WARRANT_PUBLIC;

-- ---------------------------------------------------------------------------
-- The service user.
--
-- Key-pair only: TYPE = SERVICE cannot hold a password and cannot sign in to
-- Snowsight, so a leaked deployment secret cannot become an interactive session.
-- The public key is set by the operator after generating a key pair locally —
-- it is not in this file and must never be committed.
--
--   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out warrant_public.p8 -nocrypt
--   openssl rsa -in warrant_public.p8 -pubout -out warrant_public.pub
--   ALTER USER WARRANT_PUBLIC_SVC SET RSA_PUBLIC_KEY = '<contents, header/footer stripped>';
--
-- Note the masking policy still applies: this role is not WARRANT_QUALITY_OWNER,
-- so lot references read LOT-WITHHELD in the public app exactly as they do to the
-- agent. The governance demo survives leaving the perimeter, because the policy
-- is attached to the column and follows the role, not the client.
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS WARRANT_PUBLIC_SVC
  TYPE = SERVICE
  DEFAULT_ROLE = WARRANT_PUBLIC
  DEFAULT_WAREHOUSE = WARRANT_PUBLIC_WH
  COMMENT = 'Read-only service identity for the public web console. Key-pair auth only.';

GRANT ROLE WARRANT_PUBLIC TO USER WARRANT_PUBLIC_SVC;

-- ---------------------------------------------------------------------------
-- Prove the boundary rather than assert it.
--
-- Lists what the role can do. A reviewer should see reads and two procedures,
-- and should not find EXECUTE_ACTION, EXECUTE_APPROVED or RUN_LOOP anywhere in
-- the output.
-- ---------------------------------------------------------------------------
SHOW GRANTS TO ROLE WARRANT_PUBLIC;

SELECT 'Warrant :: 50_public_viewer complete — set RSA_PUBLIC_KEY on WARRANT_PUBLIC_SVC next'
       AS status;
