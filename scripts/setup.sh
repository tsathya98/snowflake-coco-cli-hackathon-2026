#!/usr/bin/env bash
#
# Provision Warrant into a Snowflake account, end to end, from nothing.
#
#   ./scripts/setup.sh [connection-name]
#
# Idempotent: safe to re-run. Everything it creates uses IF NOT EXISTS or
# OR REPLACE, and the pipeline tables are MERGEd rather than inserted into.
#
# Requires: snow (Snowflake CLI) with a configured connection, and zip.

set -euo pipefail

CONNECTION="${1:-warrant}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v snow >/dev/null; then
  echo "snow (Snowflake CLI) is not on PATH. See https://docs.snowflake.com/en/developer-guide/snowflake-cli/index" >&2
  exit 1
fi

echo "==> Warrant :: provisioning into connection '${CONNECTION}'"

# 00 creates every stage the later steps upload into, so it must run first.
echo "==> sql/00_setup.sql"
snow sql --connection "$CONNECTION" --filename sql/00_setup.sql >/dev/null

# The operating procedures are real documents, so they must exist as files before
# sql/15 can parse them. They are committed under corpus/pdf/ deliberately, so
# provisioning needs no PDF toolchain — rendering is byte-deterministic and CI
# proves the PDFs match corpus/*.md. See tools/build_corpus.py.
echo "==> uploading the document corpus"
snow sql --connection "$CONNECTION" \
  --query "PUT file://${ROOT}/corpus/pdf/*.pdf @WARRANT.CORE.DOCS
             AUTO_COMPRESS = FALSE OVERWRITE = TRUE" >/dev/null
snow sql --connection "$CONNECTION" \
  --query "PUT file://${ROOT}/corpus/pdf/manifest.json @WARRANT.CORE.DOCS
             AUTO_COMPRESS = FALSE OVERWRITE = TRUE" >/dev/null
# The directory table is not refreshed by PUT, and sql/15 reads through it.
snow sql --connection "$CONNECTION" \
  --query "ALTER STAGE WARRANT.CORE.DOCS REFRESH" >/dev/null

# 15 parses the corpus and builds DATA.RUNBOOKS, so it must precede 30, which
# indexes that table with Cortex Search.
# The console is staged and created in SQL rather than with `snow streamlit deploy`. The CLI
# produces an app that fails to load with an unattributable "Python Interpreter Error"; sql/36
# documents the diagnosis and the four object properties that differ.
echo "==> uploading the approval console"
snow sql --connection "$CONNECTION" \
  --query "PUT file://${ROOT}/streamlit/warrant_console.py @WARRANT.CORE.STREAMLIT/console
             AUTO_COMPRESS = FALSE OVERWRITE = TRUE" >/dev/null

for step in sql/10_synthetic_data.sql sql/15_corpus.sql sql/20_pipeline.sql \
            sql/30_ai.sql sql/35_agent.sql sql/36_console.sql; do
  echo "==> ${step}"
  snow sql --connection "$CONNECTION" --filename "$step" >/dev/null
done

# Package the real module rather than inlining it into the procedure, so the code
# that runs in Snowflake is the same code the test suite covers.
echo "==> packaging src/warrant"
rm -rf build/pkg && mkdir -p build/pkg
cp -r src/warrant build/pkg/warrant
find build/pkg -name '__pycache__' -type d -prune -exec rm -rf {} +
( cd build/pkg && zip -qr ../warrant.zip warrant )

echo "==> uploading warrant.zip"
snow sql --connection "$CONNECTION" \
  --query "PUT file://${ROOT}/build/warrant.zip @WARRANT.CORE.CODE
             AUTO_COMPRESS = FALSE OVERWRITE = TRUE" >/dev/null

# 40 and 45 both import the packaged python, so they run after the upload above.
for step in sql/40_orchestration.sql sql/45_review.sql; do
  echo "==> ${step}"
  snow sql --connection "$CONNECTION" --filename "$step" >/dev/null
done

cat <<'DONE'

==> Warrant is provisioned.

Run one full pass of the loop:

  snow sql -c warrant -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');"

Then see every decision it made, including the ones where it declined:

  snow sql -c warrant -q "SELECT phase, outcome, tier, rationale
                            FROM WARRANT.AUDIT.ACTION_AUDIT ORDER BY ts;"

See docs/judges_walkthrough.md for the governance demonstration.
DONE
