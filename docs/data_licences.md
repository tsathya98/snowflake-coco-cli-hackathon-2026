# Data provenance and licences

All data in this project is **synthetic**, generated in-warehouse by
`sql/10_synthetic_data.sql`. No proprietary, personal, or employer data is used anywhere, and
no third-party dataset is mounted.

| Dataset | Source | Licence | Used for |
|---|---|---|---|
| Suppliers, SKUs, shipments, inventory, quality holds | Generated in-warehouse by `sql/10_synthetic_data.sql` | n/a — original | Every metric and exception |
| Operating procedures (RB-001…RB-005) | Written for this project. Markdown in `corpus/`, rendered to PDFs in `corpus/pdf/` by `tools/build_corpus.py` | n/a — original | The unstructured half of the corpus: parsed with `AI_PARSE_DOCUMENT`, indexed by Cortex Search, and the source of every detector threshold |

## The document corpus

The five procedures are genuine documents rather than text columns — laid out on a page,
uploaded to `@WARRANT.CORE.DOCS`, and read back with `AI_PARSE_DOCUMENT`. They are original
prose written for this project; no real standard operating procedure, from any organisation, was
consulted or adapted.

The PDFs are **generated and committed**, which is a deliberate trade. Committing them means
provisioning needs no PDF toolchain. The cost is that a generated binary can drift from its
source, so rendering is pinned to a fixed creation date and producer string to make it
byte-deterministic, and `tools/build_corpus.py --check` re-renders in memory and compares bytes.
CI runs that check, so a Markdown edit that was never re-rendered fails the build rather than
shipping a document whose text no longer matches the source a reviewer reads.

**No Snowflake Marketplace listing is used.** That is a deliberate choice rather than an
omission: a Marketplace dataset would not be synthetic, and keeping the data provenance
trivially verifiable matters more than an extra service on the inventory. The README's service
table says the same, so the two cannot drift.

## Reproducibility

The generator is deterministic. It uses `ABS(HASH(...))` rather than `RANDOM()` — partly
because `RANDOM()` in Snowflake requires a *constant* seed and rejects a column reference, and
partly because a fixed hash means the planted anomalies land in the same place on every run.
Anyone re-running `sql/10_synthetic_data.sql` gets the same three problems:

- **SUP-002** — on-time delivery collapses to 40.5% over 14 days against a 90.8% baseline
- **SKU-1003** — 41,000 on hand against 90,000 safety stock, 5.0 days of cover
- **Six quality holds** open beyond the review window, four of them past 60 days

Each sits on a table with a different `SENSITIVITY` classification, which is what lets one loop
demonstrate three different governance outcomes.
