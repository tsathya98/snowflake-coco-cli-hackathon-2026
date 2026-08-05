-- Warrant :: 10 :: synthetic operational data
--
-- Everything here is generated in-warehouse. No external files, no proprietary
-- data, no personal data. Deterministic where it matters so the demo is
-- reproducible: the planted anomalies always land in the same place.
--
-- Domain: a generic multi-site manufacturing supply chain. Three source tables,
-- deliberately tagged at three different sensitivity levels so the authority
-- model has something real to resolve against.

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA DATA;

-- ---------------------------------------------------------------------------
-- Reference: suppliers
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE SUPPLIERS (
    supplier_id     VARCHAR    PRIMARY KEY,
    supplier_name   VARCHAR    NOT NULL,
    country         VARCHAR    NOT NULL,
    tier            VARCHAR    NOT NULL,   -- 'strategic' | 'standard'
    onboarded_on    DATE       NOT NULL
);

INSERT INTO SUPPLIERS VALUES
    ('SUP-001', 'Northwind Components',   'Germany',   'strategic', '2019-03-14'),
    ('SUP-002', 'Ardent Materials',       'Vietnam',   'standard',  '2021-07-02'),
    ('SUP-003', 'Kestrel Polymers',       'India',     'strategic', '2018-11-20'),
    ('SUP-004', 'Halden Precision',       'Poland',    'standard',  '2022-01-09'),
    ('SUP-005', 'Meridian Glassworks',    'Japan',     'strategic', '2017-05-30'),
    ('SUP-006', 'Cortez Packaging',       'Mexico',    'standard',  '2023-02-17');

-- ---------------------------------------------------------------------------
-- Reference: SKUs
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE SKUS (
    sku             VARCHAR    PRIMARY KEY,
    description     VARCHAR    NOT NULL,
    site            VARCHAR    NOT NULL,
    unit_cost       NUMBER(10,2) NOT NULL,
    safety_stock    NUMBER(10,0) NOT NULL
);

INSERT INTO SKUS VALUES
    ('SKU-1001', 'Injection-moulded housing, 40mm', 'Rotterdam', 12.40,  4000),
    ('SKU-1002', 'Borosilicate vial, 10ml',         'Rotterdam',  0.85, 60000),
    ('SKU-1003', 'Aluminium seal, crimp',           'Singapore',  0.11, 90000),
    ('SKU-1004', 'Polymer stopper, bromobutyl',     'Singapore',  0.34, 75000),
    ('SKU-1005', 'Secondary carton, printed',       'Monterrey',  0.22, 50000),
    ('SKU-1006', 'Precision spindle assembly',      'Rotterdam', 84.00,   900);

-- ---------------------------------------------------------------------------
-- Fact: shipments  [sensitivity = open]
--
-- 180 days of inbound deliveries. Baseline on-time rate ~92%, with two planted
-- anomalies the agent is expected to find:
--   * SUP-002 collapses to ~35% on-time from day -13 onward
--   * SUP-006 drifts gradually late over the final 30 days
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE SHIPMENTS (
    shipment_id        VARCHAR      PRIMARY KEY,
    supplier_id        VARCHAR      NOT NULL,
    sku                VARCHAR      NOT NULL,
    site               VARCHAR      NOT NULL,
    quantity           NUMBER(10,0) NOT NULL,
    promised_date      DATE         NOT NULL,
    actual_date        DATE,
    days_late          NUMBER(5,0),
    status             VARCHAR      NOT NULL   -- 'delivered' | 'in_transit'
);

-- Pseudo-randomness comes from HASH(), not RANDOM(). RANDOM() requires a constant
-- seed, so RANDOM(<column>) is a compilation error; HASH() accepts columns and is
-- deterministic, which is what makes the planted anomalies reproducible. SEQ4() is
-- isolated in its own subquery because repeated SEQ4() calls in one SELECT are not
-- guaranteed to agree with each other.
INSERT INTO SHIPMENTS
WITH seq AS (
    SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 2400))
),
gen AS (
    SELECT
        n,
        DATEADD(day, -180 + (ABS(HASH(n, 'day')) % 181), CURRENT_DATE()) AS promised_date,
        'SUP-00' || (1 + MOD(n, 6))                                      AS supplier_id,
        'SKU-100' || (1 + MOD(n * 7, 6))                                 AS sku
    FROM seq
),
enriched AS (
    SELECT
        g.n,
        g.promised_date,
        g.supplier_id,
        g.sku,
        s.site,
        DATEDIFF(day, g.promised_date, CURRENT_DATE()) AS age_days,
        -- Planted degradation. Everything else stays near the 92% baseline.
        CASE
            WHEN g.supplier_id = 'SUP-002' AND DATEDIFF(day, g.promised_date, CURRENT_DATE()) <= 13
                THEN 65
            WHEN g.supplier_id = 'SUP-006' AND DATEDIFF(day, g.promised_date, CURRENT_DATE()) <= 30
                THEN 30
            ELSE 8
        END AS late_probability_pct
    FROM gen g
    JOIN SKUS s ON s.sku = g.sku
),
scored AS (
    SELECT
        e.*,
        (ABS(HASH(e.n, 'roll')) % 100) + 1     AS roll,
        1 + (ABS(HASH(e.n, 'late')) % 21)      AS lateness_days
    FROM enriched e
)
SELECT
    'SHP-' || LPAD(n::VARCHAR, 6, '0')                        AS shipment_id,
    supplier_id,
    sku,
    site,
    500 + (ABS(HASH(n, 'qty')) % 24501)                       AS quantity,
    promised_date,
    CASE WHEN age_days < 0 THEN NULL
         WHEN roll <= late_probability_pct
             THEN DATEADD(day, lateness_days, promised_date)
         ELSE promised_date
    END                                                       AS actual_date,
    CASE WHEN age_days < 0 THEN NULL
         WHEN roll <= late_probability_pct
             THEN lateness_days
         ELSE 0
    END                                                       AS days_late,
    CASE WHEN age_days < 0 THEN 'in_transit' ELSE 'delivered' END AS status
FROM scored;

-- ---------------------------------------------------------------------------
-- Fact: inventory positions  [sensitivity = internal]
--
-- Current stock against safety stock and consumption rate. SKU-1003 is planted
-- below safety stock with a short runway.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE INVENTORY (
    sku                 VARCHAR      PRIMARY KEY,
    site                VARCHAR      NOT NULL,
    on_hand             NUMBER(12,0) NOT NULL,
    safety_stock        NUMBER(12,0) NOT NULL,
    daily_consumption   NUMBER(10,0) NOT NULL,
    days_of_cover       NUMBER(6,1),
    as_of               TIMESTAMP_NTZ NOT NULL
);

INSERT INTO INVENTORY
SELECT
    s.sku,
    s.site,
    CASE s.sku
        WHEN 'SKU-1003' THEN 41000      -- planted: below safety stock of 90000
        WHEN 'SKU-1006' THEN 1150
        ELSE ROUND(s.safety_stock * (1.2 + (ABS(HASH(s.sku)) % 81) / 100.0))
    END                                                       AS on_hand,
    s.safety_stock,
    CASE s.sku
        WHEN 'SKU-1003' THEN 8200
        WHEN 'SKU-1002' THEN 5400
        WHEN 'SKU-1006' THEN 55
        ELSE GREATEST(ROUND(s.safety_stock / 12.0), 1)
    END                                                       AS daily_consumption,
    NULL                                                      AS days_of_cover,
    CURRENT_TIMESTAMP()                                       AS as_of
FROM SKUS s;

UPDATE INVENTORY
   SET days_of_cover = ROUND(on_hand / NULLIF(daily_consumption, 0), 1);

-- ---------------------------------------------------------------------------
-- Fact: quality holds  [sensitivity = regulated]
--
-- This table exists to be untouchable. The agent must be able to detect an
-- aging hold and explain it, and must refuse to act on it — not because a rule
-- in the code says so, but because the tag on this table says so.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE QUALITY_HOLDS (
    hold_id         VARCHAR      PRIMARY KEY,
    sku             VARCHAR      NOT NULL,
    lot_ref         VARCHAR      NOT NULL,
    site            VARCHAR      NOT NULL,
    raised_on       DATE         NOT NULL,
    age_days        NUMBER(5,0),
    disposition     VARCHAR      NOT NULL,   -- 'open' | 'released' | 'rejected'
    reason          VARCHAR      NOT NULL
);

-- One SEQ4() in a subquery, then referenced as a column. Deliberately not repeated
-- SEQ4() calls in one SELECT: those are not guaranteed to return the same value.
INSERT INTO QUALITY_HOLDS
WITH seq AS (
    SELECT SEQ4() AS n FROM TABLE(GENERATOR(ROWCOUNT => 40))
)
SELECT
    'QH-' || LPAD(n::VARCHAR, 4, '0')                         AS hold_id,
    'SKU-100' || (1 + MOD(n * 3, 6))                          AS sku,
    'LOT-' || LPAD((80000 + n * 7)::VARCHAR, 6, '0')          AS lot_ref,
    CASE MOD(n, 3) WHEN 0 THEN 'Rotterdam'
                   WHEN 1 THEN 'Singapore'
                   ELSE 'Monterrey' END                       AS site,
    DATEADD(day, -(2 + (ABS(HASH(n, 'age')) % 94)), CURRENT_DATE()) AS raised_on,
    NULL                                                      AS age_days,
    CASE WHEN (ABS(HASH(n, 'disp')) % 100) + 1 <= 30 THEN 'open' ELSE 'released' END
                                                              AS disposition,
    ARRAY_CONSTRUCT(
        'Out-of-specification assay result pending investigation',
        'Visual inspection defect above AQL threshold',
        'Environmental monitoring excursion during fill',
        'Supplier certificate of analysis discrepancy',
        'Deviation raised during batch record review'
    )[MOD(n, 5)]::VARCHAR                                     AS reason
FROM seq;

UPDATE QUALITY_HOLDS
   SET age_days = DATEDIFF(day, raised_on, CURRENT_DATE());

-- The unstructured half of the corpus is NOT here. The operating procedures live
-- in corpus/*.md, are rendered to PDFs, uploaded to @WARRANT.CORE.DOCS, and read
-- back with AI_PARSE_DOCUMENT in sql/15_corpus.sql — which is what builds
-- DATA.RUNBOOKS. They were VARCHAR literals in this file until it became clear
-- that "structured plus unstructured" resting on a string column is a claim a
-- reviewer can see through.

-- ---------------------------------------------------------------------------
-- Action target: operational requests raised by the agent  [sensitivity = open]
--
-- Every action in src/warrant/act/registry.py that creates work writes here
-- rather than mutating a source fact. Starts empty; the demo fills it.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE OPS_REQUESTS (
    request_id      VARCHAR       PRIMARY KEY,
    raised_at       TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    request_type    VARCHAR       NOT NULL,  -- supplier_case|replenishment|quality_notification
    subject_id      VARCHAR       NOT NULL,
    quantity        NUMBER(12,0),
    detail          VARCHAR       NOT NULL,
    raised_by       VARCHAR       NOT NULL
);

-- ---------------------------------------------------------------------------
-- Apply the governance tags. This is the policy surface. Changing a value here
-- changes what the agent is permitted to do — with no code change.
-- ---------------------------------------------------------------------------
ALTER TABLE OPS_REQUESTS  SET TAG WARRANT.CORE.SENSITIVITY = 'open';
ALTER TABLE SHIPMENTS     SET TAG WARRANT.CORE.SENSITIVITY = 'open';
ALTER TABLE INVENTORY     SET TAG WARRANT.CORE.SENSITIVITY = 'internal';
ALTER TABLE QUALITY_HOLDS SET TAG WARRANT.CORE.SENSITIVITY = 'regulated';
ALTER TABLE SUPPLIERS     SET TAG WARRANT.CORE.SENSITIVITY = 'open';
ALTER TABLE SKUS          SET TAG WARRANT.CORE.SENSITIVITY = 'open';
-- RUNBOOKS is deliberately left untagged, to exercise the untagged-is-not-open path.

-- ---------------------------------------------------------------------------
-- Column-level governance on the regulated table.
--
-- Attached here rather than in sql/00 for the same reason the tags are: the
-- CREATE OR REPLACE TABLE above drops every policy and tag attached to the old
-- table, silently. A masking policy applied at setup time and never re-applied
-- would be gone the first time anyone regenerated the data — and a control that
-- disappears without complaint is worse than no control.
--
-- FORCE so re-running this file over a table that already carries the policy
-- replaces it instead of raising.
--
-- The tag decides what the agent may DO; this decides what it may SEE. The
-- quality-hold detector reads hold_id, age_days, site, sku, reason and
-- disposition, so surfacing and drafting still work exactly as before — the
-- agent just cannot name the lot. Policy definition and rationale: sql/00.
-- ---------------------------------------------------------------------------
ALTER TABLE QUALITY_HOLDS MODIFY COLUMN lot_ref
  SET MASKING POLICY WARRANT.CORE.LOT_REF_MASK FORCE;

GRANT SELECT ON TABLE QUALITY_HOLDS TO ROLE WARRANT_QUALITY_OWNER;

SELECT 'Warrant :: 10_synthetic_data complete' AS status,
       (SELECT COUNT(*) FROM SHIPMENTS)     AS shipments,
       (SELECT COUNT(*) FROM QUALITY_HOLDS) AS quality_holds,
       (SELECT COUNT(*) FROM INVENTORY)     AS inventory_positions;
