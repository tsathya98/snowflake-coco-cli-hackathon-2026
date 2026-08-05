-- Warrant :: 30 :: the AI surface — grounding corpus and governed query surface
--
-- Two objects, each doing one job the reasoning step depends on:
--
--   RUNBOOK_SEARCH  Cortex Search over the operating procedures. The agent's
--                   conclusions are grounded in these rather than in whatever the
--                   model remembers about supply chains, and the doc_ids it
--                   returns are recorded on the finding so a reviewer can check
--                   which clause the conclusion leaned on.
--
--   OPS_ANALYSIS    A semantic view. Gives the metrics stable names and
--                   definitions, so "on-time rate" means one thing everywhere
--                   rather than being re-derived per query.
--
-- Idempotent. Safe to re-run.

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA CORE;

-- ---------------------------------------------------------------------------
-- Grounding corpus.
--
-- ON takes a single text column, so title and category are searchable only as
-- attributes. The body carries the thresholds the detectors implement, which is
-- what makes a retrieved clause worth citing: the same document that sets the
-- threshold explains the response.
--
-- Indexed on WARRANT_SEARCH_WH rather than WARRANT_WH so a long index build
-- cannot stall the pipeline. Five documents is a one-second build, but the
-- separation is the point.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE CORTEX SEARCH SERVICE RUNBOOK_SEARCH
  ON body
  ATTRIBUTES doc_id, title, category
  WAREHOUSE = WARRANT_SEARCH_WH
  TARGET_LAG = '1 hour'
  COMMENT = 'Operating procedures the agent grounds its findings in'
AS (
  SELECT doc_id, title, category, body
  FROM WARRANT.DATA.RUNBOOKS
);

-- ---------------------------------------------------------------------------
-- Governed query surface.
--
-- Deliberately queried with the SEMANTIC_VIEW(...) construct rather than through
-- the Cortex Analyst REST API: the API is reachable from Streamlit in Snowflake
-- in principle, but external egress on a trial account is restricted in ways two
-- Snowflake docs describe differently. Direct SQL has no egress at all, so the
-- demo cannot fail on a network rule.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW OPS_ANALYSIS
  TABLES (
    shipments AS WARRANT.DATA.SHIPMENTS
      PRIMARY KEY (shipment_id)
      COMMENT = 'One row per inbound shipment',
    suppliers AS WARRANT.DATA.SUPPLIERS
      PRIMARY KEY (supplier_id)
      COMMENT = 'Supplier master',
    skus AS WARRANT.DATA.SKUS
      PRIMARY KEY (sku)
      COMMENT = 'Material master'
  )
  RELATIONSHIPS (
    shipments (supplier_id) REFERENCES suppliers,
    shipments (sku) REFERENCES skus
  )
  FACTS (
    shipments.is_on_time AS IFF(COALESCE(days_late, 0) <= 0, 1, 0)
      COMMENT = 'One when the shipment met its promised date',
    shipments.lateness AS COALESCE(days_late, 0)
      COMMENT = 'Days past the promised date, zero when on time'
  )
  DIMENSIONS (
    shipments.promised_on AS promised_date
      COMMENT = 'Date the shipment was promised',
    shipments.status AS status
      COMMENT = 'delivered, in_transit or expedited',
    shipments.destination AS site
      COMMENT = 'Receiving site',
    suppliers.supplier AS supplier_name
      COMMENT = 'Supplier of record',
    suppliers.supplier_tier AS tier
      COMMENT = 'strategic or standard; strategic escalates differently per RB-001',
    suppliers.country AS country
      COMMENT = 'Supplier country',
    skus.material AS description
      COMMENT = 'Material description'
  )
  METRICS (
    shipments.shipment_count AS COUNT(shipments.shipment_id)
      COMMENT = 'Number of shipments',
    shipments.on_time_rate AS AVG(shipments.is_on_time)
      COMMENT = 'Share of shipments meeting the promised date',
    shipments.avg_lateness_days AS AVG(shipments.lateness)
      COMMENT = 'Mean days late, counting on-time deliveries as zero',
    shipments.units AS SUM(shipments.quantity)
      COMMENT = 'Total units shipped'
  )
  COMMENT = 'Named, stable definitions for supplier delivery performance';

SELECT 'Warrant :: 30_ai complete' AS status;
