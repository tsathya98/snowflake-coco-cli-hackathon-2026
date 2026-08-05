-- Warrant :: 20 :: pipeline tables, baselines, streams
--
-- The pipeline is: METRIC_BASELINE (dynamic) -> EXCEPTIONS -> FINDINGS
--                  -> PENDING_ACTIONS -> ACTION_AUDIT
--
-- Every stage is idempotent and every stage is auditable.

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA CORE;

-- ---------------------------------------------------------------------------
-- Baselines. A Dynamic Table rather than a scheduled INSERT: Snowflake keeps it
-- fresh within TARGET_LAG and we do not maintain refresh logic ourselves.
--
-- TARGET_LAG is one hour, matching SCAN_FOR_EXCEPTIONS' hourly cron: there is no
-- point refreshing a baseline more often than anything reads it. An earlier
-- '1 minute' lag meant both tables re-ran every sixty seconds around the clock,
-- which on a trial is a real and entirely wasted charge. Detection reads these
-- tables, so this bound is also the pipeline's freshness guarantee -- lower it if
-- you want a tighter one and are willing to pay for it.
--
-- Rolling supplier on-time performance, 14-day window against 90-day baseline.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE SUPPLIER_OTD_BASELINE
  TARGET_LAG = '60 minutes'
  WAREHOUSE = WARRANT_WH
  REFRESH_MODE = AUTO
  COMMENT = 'Rolling on-time-delivery rate per supplier: recent window vs baseline'
AS
WITH delivered AS (
    SELECT
        supplier_id,
        promised_date,
        IFF(COALESCE(days_late, 0) <= 0, 1, 0) AS on_time
    FROM WARRANT.DATA.SHIPMENTS
    WHERE status = 'delivered'
),
windowed AS (
    SELECT
        supplier_id,
        AVG(IFF(promised_date >= DATEADD(day, -14, CURRENT_DATE()), on_time, NULL))  AS recent_otd,
        AVG(IFF(promised_date <  DATEADD(day, -14, CURRENT_DATE()), on_time, NULL))  AS baseline_otd,
        COUNT_IF(promised_date >= DATEADD(day, -14, CURRENT_DATE()))                 AS recent_n,
        COUNT_IF(promised_date <  DATEADD(day, -14, CURRENT_DATE()))                 AS baseline_n
    FROM delivered
    GROUP BY supplier_id
)
SELECT
    w.supplier_id,
    s.supplier_name,
    s.tier,
    ROUND(w.recent_otd   * 100, 1) AS recent_otd_pct,
    ROUND(w.baseline_otd * 100, 1) AS baseline_otd_pct,
    ROUND((w.recent_otd - w.baseline_otd) * 100, 1) AS delta_pct_points,
    w.recent_n,
    w.baseline_n
FROM windowed w
JOIN WARRANT.DATA.SUPPLIERS s ON s.supplier_id = w.supplier_id;

-- Inventory runway. Trivial arithmetic, but materialising it makes the
-- detection query readable and gives the semantic view something to bind to.
CREATE OR REPLACE DYNAMIC TABLE INVENTORY_RUNWAY
  TARGET_LAG = '60 minutes'
  WAREHOUSE = WARRANT_WH
  REFRESH_MODE = AUTO
  COMMENT = 'Stock position against safety stock, with projected days of cover'
AS
SELECT
    i.sku,
    k.description,
    i.site,
    i.on_hand,
    i.safety_stock,
    i.daily_consumption,
    i.days_of_cover,
    i.on_hand - i.safety_stock                          AS headroom,
    IFF(i.on_hand < i.safety_stock, TRUE, FALSE)        AS below_safety_stock,
    -- In-transit cover matters: the runbook calls duplicate replenishment the
    -- most common error in this workflow.
    COALESCE((
        SELECT SUM(sh.quantity)
        FROM WARRANT.DATA.SHIPMENTS sh
        WHERE sh.sku = i.sku AND sh.status = 'in_transit'
    ), 0)                                               AS in_transit_qty
FROM WARRANT.DATA.INVENTORY i
JOIN WARRANT.DATA.SKUS k ON k.sku = i.sku;

-- ---------------------------------------------------------------------------
-- EXCEPTIONS :: what the detector found.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS EXCEPTIONS (
    exception_id     VARCHAR       PRIMARY KEY,
    detected_at      TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    metric           VARCHAR       NOT NULL,
    entity           VARCHAR       NOT NULL,
    observed         VARCHAR       NOT NULL,
    expected         VARCHAR       NOT NULL,
    deviation        VARCHAR       NOT NULL,
    detection_method VARCHAR       NOT NULL,
    source_objects   ARRAY         NOT NULL,
    state            VARCHAR       NOT NULL DEFAULT 'open',  -- open|investigated|closed
    CONSTRAINT uq_open_exception UNIQUE (metric, entity, state)
);

COMMENT ON TABLE EXCEPTIONS IS
  $$One row per detected operational exception. Deduplicated on (metric, entity) while open, per runbook RB-005.$$;

-- ---------------------------------------------------------------------------
-- FINDINGS :: what the agent concluded. One per exception.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS FINDINGS (
    finding_id        VARCHAR       PRIMARY KEY,
    exception_id      VARCHAR       NOT NULL,
    created_at        TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    severity          VARCHAR       NOT NULL,   -- low|medium|high|critical
    root_cause        VARCHAR       NOT NULL,
    evidence          ARRAY         NOT NULL,
    grounded_in       ARRAY,                    -- runbook doc_ids from Cortex Search
    recommended_action VARCHAR      NOT NULL,
    action_type       VARCHAR       NOT NULL,
    action_params     OBJECT        NOT NULL,
    requested_tier    NUMBER(1,0)   NOT NULL,
    touched_objects   ARRAY         NOT NULL,
    model             VARCHAR       NOT NULL
);

-- ---------------------------------------------------------------------------
-- PENDING_ACTIONS :: the approval queue. This table is the human-in-the-loop.
--
-- Snowflake cannot receive an inbound webhook, so Slack buttons are impossible.
-- The approval console writes here instead, and a stream on this table triggers
-- execution. Everything stays inside the governed perimeter.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PENDING_ACTIONS (
    action_id        VARCHAR       PRIMARY KEY,
    finding_id       VARCHAR       NOT NULL,
    proposed_at      TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    action_type      VARCHAR       NOT NULL,
    action_params    OBJECT        NOT NULL,
    effective_tier   NUMBER(1,0)   NOT NULL,
    binding_object   VARCHAR,
    tier_rationale   VARCHAR       NOT NULL,
    rollback_plan    VARCHAR,
    decision         VARCHAR       NOT NULL DEFAULT 'pending',  -- pending|approved|rejected|auto
    decided_by       VARCHAR,
    decided_at       TIMESTAMP_NTZ,
    decision_note    VARCHAR,
    executed_at      TIMESTAMP_NTZ,
    execution_result VARCHAR
);

-- Consumed with DML by the executor task. A bare SELECT does not advance the
-- offset, which is the single most common Streams bug.
CREATE OR REPLACE STREAM APPROVED_ACTIONS_STREAM
  ON TABLE PENDING_ACTIONS
  COMMENT = 'Fires the executor when a human approves a queued action';

CREATE OR REPLACE STREAM NEW_EXCEPTIONS_STREAM
  ON TABLE EXCEPTIONS
  COMMENT = 'Fires the investigator when a new exception is detected';

-- ---------------------------------------------------------------------------
-- ACTION_AUDIT :: append-only. Never UPDATE, never DELETE.
--
-- Every decision the agent makes lands here, including the ones where it
-- refused to act. A refusal is as important to record as an action.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS WARRANT.AUDIT.ACTION_AUDIT (
    audit_id       VARCHAR       PRIMARY KEY,
    ts             TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    phase          VARCHAR       NOT NULL,   -- detect|reason|classify|route|execute|refuse
    exception_id   VARCHAR,
    finding_id     VARCHAR,
    action_id      VARCHAR,
    actor          VARCHAR       NOT NULL,   -- 'agent' or a username
    tier           NUMBER(1,0),
    outcome        VARCHAR       NOT NULL,
    rationale      VARCHAR       NOT NULL,
    payload        OBJECT
);

COMMENT ON TABLE WARRANT.AUDIT.ACTION_AUDIT IS
  'Append-only decision log. Includes refusals. Never updated or deleted.';

SELECT 'Warrant :: 20_pipeline complete' AS status;
