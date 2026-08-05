-- Warrant :: 15 :: the unstructured corpus, parsed from real documents
--
-- Requires the PDFs and their manifest to be on @WARRANT.CORE.DOCS already.
-- ./scripts/setup.sh PUTs them from corpus/pdf/ before reaching here, and
-- refreshes the directory table, which PUT does not do on its own.
--
-- Why this file exists at all. It would be less work to hold the operating
-- procedures as VARCHAR literals in sql/10 — an earlier revision did exactly
-- that. But "combines structured and unstructured data" is then a claim resting
-- on a string column, and a reviewer is entitled to notice. These are documents:
-- laid out on a page, uploaded as files, and read back with a document parser
-- that has to recover the text. The thresholds the detectors implement are
-- clauses inside them.
--
-- Note the deliberate asymmetry between content and metadata. The parser's job
-- is to recover prose, so prose is what it supplies. doc_id, title and category
-- come from the manifest, because deriving a primary key by scraping rendered
-- output would make document layout load-bearing — reflow the PDF and the
-- corpus would silently re-key itself.
--
-- Idempotent. Safe to re-run.

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA DATA;

CREATE FILE FORMAT IF NOT EXISTS WARRANT.CORE.CORPUS_MANIFEST_JSON
  TYPE = JSON
  STRIP_OUTER_ARRAY = TRUE
  COMMENT = 'One row per document in corpus/pdf/manifest.json';

-- RUNBOOKS is derived, so CREATE OR REPLACE is correct here: re-running rebuilds
-- it from whatever is on the stage. It stays deliberately UNTAGGED — the
-- authority model has to keep exercising the untagged-is-not-cleared path, and
-- retrieval is a read, so grounding still works. See src/warrant/authority/tiers.py.
CREATE OR REPLACE TABLE RUNBOOKS AS
WITH manifest AS (
    SELECT $1:doc_id::STRING    AS doc_id,
           $1:title::STRING     AS title,
           $1:category::STRING  AS category,
           $1:revision::STRING  AS revision,
           $1:effective::DATE   AS effective_on,
           $1:owner::STRING     AS owner,
           $1:file::STRING      AS source_file
      FROM @WARRANT.CORE.DOCS/manifest.json
           (FILE_FORMAT => WARRANT.CORE.CORPUS_MANIFEST_JSON)
),
parsed AS (
    -- TO_FILE accepts a column reference, unlike SYSTEM$GET_TAG, which requires
    -- constant arguments. So one set-based statement parses the whole corpus
    -- rather than a statement per document.
    SELECT m.*,
           AI_PARSE_DOCUMENT(
               TO_FILE('@WARRANT.CORE.DOCS', m.source_file),
               {'mode': 'LAYOUT'}
           ) AS document
      FROM manifest m
)
SELECT doc_id,
       title,
       category,
       revision,
       effective_on,
       owner,
       source_file,
       document:content::STRING            AS body,
       document:metadata:pageCount::INT    AS page_count,
       LENGTH(document:content::STRING)    AS body_chars
  FROM parsed;

COMMENT ON TABLE RUNBOOKS IS
  $$Operating procedures, parsed from PDFs on @WARRANT.CORE.DOCS with AI_PARSE_DOCUMENT. Source of every detector threshold and the grounding corpus for RUNBOOK_SEARCH. Deliberately untagged.$$;

-- A corpus that silently parsed to nothing would degrade the agent to
-- unaided reasoning while still looking healthy — grounded_in would just be
-- empty, which the pipeline tolerates by design. So fail loudly here instead.
EXECUTE IMMEDIATE $$
DECLARE
  thin INTEGER;
  total INTEGER;
BEGIN
  SELECT COUNT(*) INTO :total FROM WARRANT.DATA.RUNBOOKS;
  SELECT COUNT(*) INTO :thin  FROM WARRANT.DATA.RUNBOOKS
   WHERE body IS NULL OR body_chars < 400;

  IF (total = 0) THEN
    RETURN 'FAILED: no documents parsed. Is the corpus on @WARRANT.CORE.DOCS?';
  END IF;
  IF (thin > 0) THEN
    RETURN 'FAILED: ' || thin || ' of ' || total || ' documents parsed to under 400 characters.';
  END IF;
  RETURN 'OK: ' || total || ' documents parsed.';
END;
$$;

SELECT 'Warrant :: 15_corpus complete' AS status,
       COUNT(*)          AS documents,
       SUM(page_count)   AS pages,
       MIN(body_chars)   AS smallest_body,
       SUM(body_chars)   AS total_chars
  FROM RUNBOOKS;
