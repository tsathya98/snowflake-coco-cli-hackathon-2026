# Datasets — what's free and usable

> **Hard constraint: synthetic or public data ONLY.** No Takeda data, real or derived.
> See `00-STATUS.md` §2.

## Built-in: `SNOWFLAKE_SAMPLE_DATA`

**Genuinely free** — verbatim from docs: *"The database and schemas do not use any data storage
so they do not incur storage charges for your account."* You pay warehouse credits only.

Schemas: `TPCH_SF1`, `TPCH_SF10`, `TPCH_SF100`, `TPCH_SF1000`, `TPCDS_SF10TCL`, `TPCDS_SF100TCL`,
plus a deprecated `WEATHER` schema (may be absent in some regions).

Restrictions: read-only, **no cloning, no Time Travel**.
Verify with `SHOW DATABASES LIKE '%sample%';` — the `origin` column should read `SFC_SAMPLES.SAMPLE_DATA`.

### Row counts
Snowflake publishes exactly one officially: `tpch_sf1.lineitem` = **6,001,215**.
The rest are TPC-H-spec-derived — run `COUNT(*)` if exactness matters.

| Table | SF1 | SF10 | SF100 |
|---|---|---|---|
| REGION / NATION | 5 / 25 | 5 / 25 | 5 / 25 (fixed, does not scale) |
| SUPPLIER | 10,000 | 100,000 | 1,000,000 |
| CUSTOMER | 150,000 | 1,500,000 | 15,000,000 |
| PART | 200,000 | 2,000,000 | 20,000,000 |
| PARTSUPP | 800,000 | 8,000,000 | 80,000,000 |
| ORDERS | 1,500,000 | 15,000,000 | 150,000,000 |
| LINEITEM | **6,001,215** ✓ | ~59,986,052 | ~600,037,902 |

⚠️ `TPCDS_SF10TCL.STORE_SALES` ≈ **29 billion rows** — ignore it on a $400 trial.

⚠️ **Tasty Bytes correction:** `SNOWFLAKE_LEARNING_DB` ships **empty of user tables**. The trial
page's "pre-loaded Tasty Bytes sample data" means the *worksheet* is pre-loaded — you still run
`COPY INTO` from `s3://sfquickstarts/tastybytes/` (a 100-row `menu` table).

---

## ⭐ Best starting point: existing Snowflake quickstarts

These generate their own synthetic data and ship a working schema. **Start from one of these
rather than from scratch** — it's faster and demonstrates Snowflake-native depth.

### 1. [Supply Chain Risk Intelligence: N-Tier Visibility](https://www.snowflake.com/en/developers/guides/supply-chain-risk-intelligence-with-snowflake/)
**Closest ready-made supply-chain schema.** Generates synthetic vendor masters, POs, **BOMs**,
trade data and regional risk via a `GENERATE_SYNTHETIC_DATA` stored proc, then builds a
Cortex Agent + Streamlit dashboard. → **Top candidate for PS1.**

### 2. [Golden Batch Process Optimization with Cortex AI](https://www.snowflake.com/en/developers/guides/golden-batch-process-optimization-with-cortex-ai/)
5-stage batch manufacturing with historian / MES / LIMS / ERP-style tables. **Explicitly names
pharmaceuticals as an applicable vertical** (worked example is confectionery). This gives
manufacturing-ops framing without touching any Takeda specifics.

### 3. [Intelligent Jidoka System for EV Manufacturing](https://www.snowflake.com/en/developers/guides/intelligent-jidoka-system-for-ev-manufacturing/)
Synthetic SAP + Siemens MES + IoT, medallion architecture, Cortex Analyst/Search/Agent.
Good *structural* template for an exception-detection system.

### 4. [Clinical Data Analysis with ADaM and SDTM](https://www.snowflake.com/en/developers/guides/clinical-data-analysis-with-adam-and-sdtm-in-snowflake/)
Real **CDISC** Pilot submission package, FDA/EMA workflows, adverse-event safety analysis.
Useful if you want genuine regulatory *documents* to run `AI_PARSE_DOCUMENT` against.

### 5. [Supply chain network optimization](https://www.snowflake.com/en/developers/guides/supply-chain-network-optimization-using-snowpark-and-cortex/)
Snowpark + PuLP.

> Note: `quickstarts.snowflake.com` now largely mirrors/redirects to
> `snowflake.com/en/developers/guides/`.

---

## Marketplace — free listings worth mounting

**Cost mechanics** (from [data-sharing-intro](https://docs.snowflake.com/en/user-guide/data-sharing-intro)):
> "no actual data is copied or transferred between accounts... **Shared data does not take up any
> storage in a consumer account... The only charges to consumers are for the compute resources
> (i.e. virtual warehouses) used to query the imported data.**"

So you can mount dozens of free listings on a trial for free. **Flip side:** because it's a share,
you cannot enable Search Optimization or clustering on it — you'd need `CREATE TABLE AS SELECT`
into your own schema, and *that* copy does incur storage.

**Trial accounts can consume free listings — confirmed** (official quickstarts instruct exactly
this). The trial restriction is on the *provider* side: trial accounts cannot publish.

SQL alternative to the UI: `CREATE DATABASE ... FROM LISTING ...`
([docs](https://docs.snowflake.com/en/collaboration/consumer-listings-sql))

### Highest-value free grab
**`GZTSZ290BV255` — "Snowflake Public Data (Free)"** (provider: Snowflake Public Data Products,
formerly Cybersyn). Free, unlimited. Creates `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`.
Catalog: https://data-docs.snowflake.com/sources — **66 sources**.

> ⚠️ **~3-month (one-quarter) data lag** on the free tier. Paid tier (`GZTSZ290BUXPL`) removes it.

Supply-chain-relevant sources within it: **WTO** (bilateral imports, tariffs), **ITA** (US
export/import + Consolidated Screening List of restricted export entities), **USDA** commodity
supply/distribution, **UNIDO** industrial statistics, **BLS** Producer Price Index, **US DOT**,
**NOAA/NWS**, **FEMA** disaster declarations (supplier-site risk), **EPA** facility emissions,
**USPTO**, **SAM.gov/USASpending**.

### Supply chain / manufacturing
| Listing | Provider | Notes |
|---|---|---|
| **FactSet Supply Chain Relationships (sample)** `GZT0ZGCQ51RQ` | FactSet | `SCR_RELATIONSHIPS`, `SCR_TIER_2_SUPPLIERS`. **An actual supplier/customer graph between global companies — best free supply-chain-topology dataset on the Marketplace.** |
| D&B Shipping Insights Sample `GZT0ZPWB4J7` | D&B | 54M shipments/month |
| CEIC Shipping / Commodities / Automotive `GZTSZRC7HRC` / `HQ3` / `HPM` | CEIC | port activity, commodity prices |
| item+s Scope 3 Emission Factors (Sample) `GZSYZFMOPO` | item+s | used by Bayer/Siemens/Bosch |
| ICIS Chemical Price Assessments `GZSVZ9FU7N` | ICIS | |
| Pelmorex Weather Source frostbyte `GZSOZ1LLEL` + SafeGraph frostbyte | | required by Tasty Bytes quickstart |

### Pharma / clinical
| Listing | Provider | Notes |
|---|---|---|
| **Synthetic Healthcare Data – Clinical and Claims** `GZSTZL7M0Q6` | Snowflake VHOL | Synthea patients/encounters/claims/medications. **Best pick for a safe pharma demo.** |
| AACT (Aggregate Analysis of ClinicalTrials.gov) `GZSTZ45DPJ59F` | Element Data | Free, unlimited. `V_STUDIES`, `V_SPONSORS`, ~45 views. **The relational option.** |
| Clinical Trials Research Database `GZSTZ67BY9ORD` | Snowflake | 400k+ studies, daily refresh. ⚠️ **A Cortex Knowledge Extension (shared Cortex Search Service), not a relational warehouse** — query via Cortex Agent/Search, not SQL joins. |
| PubMed Biomedical Research Corpus `GZSTZ67BY9OQW` | Snowflake | Also a CKE |
| Drug Vocabulary `GZTYZJ6Q7UU` | DrugBank | ⚠️ **Not** the FDA NDC Directory |

⚠️ **Pattern:** most "free" commercial supply-chain listings (FactSet, D&B, Definitive Healthcare)
are **samples/subsets**; full products are paid.

---

## Confirmed NOT available (saves searching)

- 🚨 **No FDA FAERS / adverse-events listing on Snowflake Marketplace at all** (it's on AWS and
  Databricks marketplaces, not Snowflake)
- No free FDA NDC Directory or recalls listing
- **No FDA, no FAERS, no NDC, no ClinicalTrials.gov, no CMS claims inside Snowflake Public Data.**
  Its health coverage is provider-registry (CMS NPPES), taxonomy (NUCC), and social determinants only.
- Komodo Health: "By request" enterprise pricing. Truveta and HealthVerity: no Snowflake listing.
- Sonra's OpenStreetMap listings appear in search indexes but pages no longer resolve — likely
  retired; use CARTO or Overture instead.
- 🚨 **Industry "solution" bundles are not GA.** `data-docs.snowflake.com/solutions/healthcare`
  and `/industrial-manufacturing` describe curated bundles with semantic models and pre-built
  Cortex agents, but **every one carries `"status": "waitlist"`. Don't plan around them.**

## Unverified / open

- TPC-H row counts above SF1 (spec-derived, not Snowflake-published)
- TPC-DS table names are nowhere enumerated in Snowflake docs
- Which of the 66 Public Data sources are excluded from the free tier — no authoritative
  per-source free/paid table exists
- Rearc listings (CMS-NPPES, RxNorm, GeoHealth SDoH, CTTI-AACT) appear only in Rearc's GitHub
  docs, never on a live listing page — **do not treat as confirmed**

## Sources

[Sample data](https://docs.snowflake.com/en/user-guide/sample-data) ·
[Using sample data](https://docs.snowflake.com/en/user-guide/sample-data-using) ·
[TPC-H](https://docs.snowflake.com/en/user-guide/sample-data-tpch) ·
[TPC-DS](https://docs.snowflake.com/en/user-guide/sample-data-tpcds) ·
[Data sharing intro](https://docs.snowflake.com/en/user-guide/data-sharing-intro) ·
[Consumer listings via SQL](https://docs.snowflake.com/en/collaboration/consumer-listings-sql) ·
[Public Data catalog](https://data-docs.snowflake.com/sources)
