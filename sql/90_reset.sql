-- Warrant :: 90 :: reset the pipeline to a pre-run state
--
-- For re-running the demonstration. Clears what the loop produced and undoes
-- what it did, so the next run starts from the same place the first one did.
--
-- Deliberately does NOT touch WARRANT.AUDIT.ACTION_AUDIT. That table is
-- append-only and its whole value is that it cannot be tidied up: a decision log
-- you can erase is not a decision log. Use the run_id in the payload to tell one
-- run's rows from another's.
--
-- Also restores the SENSITIVITY tags, so a reclassification experiment does not
-- leak into the next run.

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA CORE;

-- What the loop produced.
TRUNCATE TABLE IF EXISTS PENDING_ACTIONS;
TRUNCATE TABLE IF EXISTS FINDINGS;
TRUNCATE TABLE IF EXISTS EXCEPTIONS;
TRUNCATE TABLE IF EXISTS APPROVAL_OFFSETS;

-- What the loop did. Only rows the agent itself raised — a human's rows survive.
DELETE FROM WARRANT.DATA.OPS_REQUESTS WHERE raised_by = 'warrant-agent';
UPDATE WARRANT.DATA.SHIPMENTS SET status = 'in_transit' WHERE status = 'expedited';

-- Rebuild the stream offsets so the next run does not replay this one's approvals.
CREATE OR REPLACE STREAM APPROVED_ACTIONS_STREAM ON TABLE PENDING_ACTIONS
  COMMENT = 'Fires the executor when a human approves a queued action';
CREATE OR REPLACE STREAM NEW_EXCEPTIONS_STREAM ON TABLE EXCEPTIONS
  COMMENT = 'Fires the investigator when a new exception is detected';

-- Restore the classifications, in case a reclassification demo was left in place.
ALTER TABLE WARRANT.DATA.SHIPMENTS     SET TAG CORE.SENSITIVITY = 'open';
ALTER TABLE WARRANT.DATA.SUPPLIERS     SET TAG CORE.SENSITIVITY = 'open';
ALTER TABLE WARRANT.DATA.SKUS          SET TAG CORE.SENSITIVITY = 'open';
ALTER TABLE WARRANT.DATA.OPS_REQUESTS  SET TAG CORE.SENSITIVITY = 'open';
ALTER TABLE WARRANT.DATA.INVENTORY     SET TAG CORE.SENSITIVITY = 'internal';
ALTER TABLE WARRANT.DATA.QUALITY_HOLDS SET TAG CORE.SENSITIVITY = 'regulated';
-- RUNBOOKS stays untagged on purpose: the untagged path must stay exercised.

SELECT 'Warrant :: 90_reset complete — ACTION_AUDIT deliberately preserved' AS status;
