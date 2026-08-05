-- Warrant :: 35 :: the conversational surface
--
-- A Cortex Agent as a real Snowflake object, so the decision record can be
-- interrogated in natural language. Requires RUNBOOK_SEARCH and OPS_ANALYSIS
-- from sql/30, hence 35.
--
-- ---------------------------------------------------------------------------
-- The one design decision here, and it is a governance decision.
--
-- This agent has NO authority to act. Not "authority it chooses not to use" —
-- none. Its tools are a search service and a semantic view, both read-only, and
-- it is not given a `generic` tool wired to RUN_LOOP or EXECUTE_ACTION.
--
-- That is deliberate rather than a limitation. The whole argument of this project
-- is that authority is derived from the classification of the data an action
-- touches and re-checked at execution time. A chat box that can invoke the
-- executor bypasses the console, the approval queue and the human — it would put
-- the most persuadable surface in the system on the far side of the gate. So the
-- conversational surface is L0/L1 by construction: it may look and speak, and it
-- may not touch. Actions are proposed by CORE.RUN_LOOP and approved in the
-- console, both of which resolve authority from the tags.
--
-- Ask it "why was this refused?" and it can answer. Ask it to un-refuse
-- something and it has no mechanism to.
-- ---------------------------------------------------------------------------
--
-- Idempotent. Safe to re-run.

USE ROLE WARRANT_ROLE;
USE WAREHOUSE WARRANT_WH;
USE DATABASE WARRANT;
USE SCHEMA CORE;

-- Verified by calling it, not by reading a docs page — two things here are not
-- obvious and both fail in ways worth knowing about:
--
--   1. An Analyst tool needs its own execution environment. Without the
--      `execution_environment` block below, creation succeeds and every run
--      fails with 399504 "The Analyst tool ... is missing an execution
--      environment" — a create-time success and a run-time failure.
--
--   2. Invoke a named agent with
--      SNOWFLAKE.CORTEX.DATA_AGENT_RUN('<fqn>', '<request body>').
--      SNOWFLAKE.CORTEX.AGENT_RUN('{"agent": "<fqn>", ...}') also *succeeds* —
--      but it silently ignores the agent name and answers from the account's
--      default assistant, which has none of these tools. It looks like a working
--      demo and proves nothing. Always check the returned model name and
--      tool_use blocks match the spec below.
CREATE OR REPLACE AGENT WARRANT_ANALYST
  COMMENT = 'Read-only conversational surface over the Warrant decision record. No authority to act.'
  PROFILE = '{"display_name": "Warrant"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-6

  orchestration:
    budget:
      seconds: 90
      tokens: 32000

  instructions:
    response: |
      You explain what the Warrant agent decided and why, for an operations or quality reviewer.

      Cite the doc_id of any procedure you rely on. Quote thresholds rather than paraphrasing
      them, because the detectors implement those exact numbers.

      You have no authority to act, and no tool that could. If you are asked to take an action,
      release a hold, approve a queued action or change a classification, say plainly that you
      cannot: actions are proposed by CORE.RUN_LOOP and approved by a human in the Warrant
      console, where authority is resolved from the object tags on the data the action touches.
      Do not offer to do it anyway.

      Never state a lot identifier. Lot references are withheld from automation by a masking
      policy, and if one appears to you it is 'LOT-WITHHELD'.
    orchestration: |
      Use procedures for anything about operating procedures, thresholds, or what automation is
      permitted to do. Use delivery_metrics for supplier delivery performance figures.
      Prefer procedures when a question is about permission or authority.
    sample_questions:
      - question: 'What does RB-003 permit automation to do with an aging quality hold?'
      - question: 'Which supplier has the worst on-time delivery rate?'
      - question: 'Why would the agent refuse to release a quality hold?'

  tools:
    - tool_spec:
        type: cortex_search
        name: procedures
        description: >
          The five operating procedures, parsed from PDF with AI_PARSE_DOCUMENT. The source of
          every threshold the detectors implement. Cite the doc_id.
    - tool_spec:
        type: cortex_analyst_text_to_sql
        name: delivery_metrics
        description: >
          Named, stable metric definitions for supplier delivery performance — on-time rate,
          shipment count, average lateness — over the governed semantic view.

  tool_resources:
    procedures:
      name: WARRANT.CORE.RUNBOOK_SEARCH
      max_results: '4'
      id_column: doc_id
      title_column: title
    delivery_metrics:
      semantic_view: WARRANT.CORE.OPS_ANALYSIS
      execution_environment:
        type: warehouse
        warehouse: WARRANT_WH
  $$;

SHOW AGENTS IN SCHEMA WARRANT.CORE;

SELECT 'Warrant :: 35_agent complete' AS status;
