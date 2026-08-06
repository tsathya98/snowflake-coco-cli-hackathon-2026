/**
 * Every statement this application can run, declared once at module scope.
 *
 * Nothing here is assembled from request data. That is the same rule
 * `tools/lint_sql_boundary.py` enforces across the Python package — statements
 * are constants and values bind — extended to the web tier, so the guarantee
 * does not stop at the edge of the warehouse.
 *
 * The queries mirror `streamlit/warrant_console.py` on purpose. Two surfaces
 * reading the same figures through different SQL is how they start quietly
 * disagreeing about what "handled" means.
 */

/** Tier numbers to the words used everywhere else in the project. */
export const TIER_NAMES: Record<number, string> = {
  0: "L0 · read only",
  1: "L1 · draft",
  2: "L2 · acts unsupervised",
  3: "L3 · needs approval",
  4: "L4 · never permitted",
};

/** Tier to a CSS accent token. Kept beside the names so a tier cannot gain one without the other. */
export const TIER_TONE: Record<number, string> = {
  0: "muted",
  1: "muted",
  2: "good",
  3: "warn",
  4: "bad",
};

export const OUTCOME_TONE: Record<string, string> = {
  "acts unsupervised": "good",
  "needs human approval": "warn",
  "refused outright": "bad",
};

export const SEVERITY_TONE: Record<string, string> = {
  critical: "bad",
  high: "warn",
  medium: "info",
  low: "muted",
};

/**
 * The run in one line. `acted` counts anything that reached an execution result
 * other than a refusal, rather than `decision = 'auto'`, because an
 * approved-then-executed action is just as much work that happened.
 */
export const HEADLINE = `
SELECT (SELECT COUNT(*) FROM WARRANT.CORE.EXCEPTIONS)                                 AS detected,
       (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS
         WHERE execution_result IS NOT NULL AND execution_result <> 'refused')         AS acted,
       (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS WHERE decision = 'pending')  AS awaiting,
       (SELECT COUNT(*) FROM WARRANT.CORE.REFUSALS)                                    AS refused,
       (SELECT COUNT(*) FROM WARRANT.AUDIT.ACTION_AUDIT)                               AS logged,
       (SELECT COALESCE(TO_VARCHAR(MAX(ts), 'YYYY-MM-DD HH24:MI'), 'never')
          FROM WARRANT.AUDIT.ACTION_AUDIT)                                             AS last_at`;

/**
 * What one pass produced, joined back to the tag that decided each routing.
 *
 * The public viewer shows the *outcome* of the queue rather than an approval
 * form, because this surface has no authority to approve. See sql/50_public_viewer.sql.
 */
export const DECISIONS = `
SELECT f.action_type                                            AS action_type,
       e.entity                                                 AS entity,
       e.metric                                                 AS metric,
       f.severity                                               AS severity,
       p.effective_tier                                         AS tier,
       COALESCE(p.binding_object, 'none declared')              AS binding_object,
       p.tier_rationale                                         AS tier_rationale,
       p.decision                                               AS decision,
       COALESCE(p.execution_result, 'not executed')             AS execution_result,
       f.root_cause                                             AS root_cause,
       e.observed                                               AS observed,
       e.expected                                               AS expected,
       e.deviation                                              AS deviation,
       e.detection_method                                       AS detection_method,
       COALESCE(TO_VARCHAR(f.grounded_in), '[]')                AS grounded_in,
       f.model                                                  AS model
  FROM WARRANT.CORE.EXCEPTIONS e
  JOIN WARRANT.CORE.FINDINGS f  ON f.exception_id = e.exception_id
  LEFT JOIN WARRANT.CORE.PENDING_ACTIONS p ON p.finding_id = f.finding_id
 ORDER BY p.effective_tier DESC NULLS LAST, e.entity`;

export const REFUSALS = `
SELECT TO_VARCHAR(ts, 'YYYY-MM-DD HH24:MI')            AS when_refused,
       COALESCE(action_id, exception_id, 'unknown')     AS subject,
       COALESCE(tier, 4)                                AS tier,
       COALESCE(action_type, 'action')                  AS action_type,
       rationale                                        AS rationale,
       COALESCE(TO_VARCHAR(footprint_at_execution), '') AS footprint
  FROM WARRANT.CORE.REFUSALS
 ORDER BY ts DESC
 LIMIT 25`;

/**
 * Read live on every render with SYSTEM$GET_TAG, never from ACCOUNT_USAGE, which
 * lags by up to two hours. Spelled out one literal at a time because the function
 * requires constant arguments and rejects a column reference.
 *
 * RUNBOOKS is genuinely untagged and must stay that way — it is what exercises
 * the untagged-is-not-cleared path — so `untagged` is substituted here in SQL.
 */
export const GOVERNANCE = `
SELECT 'WARRANT.DATA.SHIPMENTS' AS object,
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.SHIPMENTS','TABLE'),
                'untagged') AS sensitivity
UNION ALL SELECT 'WARRANT.DATA.SUPPLIERS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.SUPPLIERS','TABLE'),'untagged')
UNION ALL SELECT 'WARRANT.DATA.SKUS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.SKUS','TABLE'),'untagged')
UNION ALL SELECT 'WARRANT.DATA.INVENTORY',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.INVENTORY','TABLE'),'untagged')
UNION ALL SELECT 'WARRANT.DATA.QUALITY_HOLDS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.QUALITY_HOLDS','TABLE'),'untagged')
UNION ALL SELECT 'WARRANT.DATA.OPS_REQUESTS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.OPS_REQUESTS','TABLE'),'untagged')
UNION ALL SELECT 'WARRANT.DATA.RUNBOOKS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.RUNBOOKS','TABLE'),'untagged')`;

/**
 * The masking demonstration, and the reason it survives leaving Snowflake: the
 * policy is attached to the column and follows the *role*, not the client. This
 * app authenticates as WARRANT_PUBLIC, which is not the quality owner, so the lot
 * references read LOT-WITHHELD here exactly as they do to the agent.
 */
export const MASKED_HOLDS = `
SELECT hold_id AS hold, lot_ref AS lot_reference, site, sku,
       age_days::INT AS days_open, reason
  FROM WARRANT.DATA.QUALITY_HOLDS
 WHERE disposition = 'open' AND age_days > 60
 ORDER BY age_days DESC`;

/** Through SEMANTIC_VIEW, so this page and the agent cannot disagree on a definition. */
export const METRICS = `
SELECT supplier                            AS supplier,
       supplier_tier                       AS tier,
       ROUND(on_time_rate * 100, 1)::FLOAT AS on_time_pct,
       shipment_count::INT                 AS shipments,
       ROUND(avg_lateness_days, 2)::FLOAT  AS avg_days_late
  FROM SEMANTIC_VIEW(
    WARRANT.CORE.OPS_ANALYSIS
    DIMENSIONS suppliers.supplier, suppliers.supplier_tier
    METRICS    shipments.on_time_rate, shipments.shipment_count, shipments.avg_lateness_days
  )
 ORDER BY on_time_pct`;

export const AUDIT = `
SELECT TO_VARCHAR(ts, 'YYYY-MM-DD HH24:MI:SS') AS at,
       phase, outcome,
       COALESCE(TO_VARCHAR(tier), '-')         AS tier,
       actor, rationale
  FROM WARRANT.AUDIT.ACTION_AUDIT
 ORDER BY ts DESC
 LIMIT 40`;

/** The procedures WARRANT_PUBLIC may call. Every one of them only computes. */
export const MANIFEST = "CALL WARRANT.CORE.AUTHORITY_MANIFEST(NULL)";
export const MANIFEST_WHATIF = "CALL WARRANT.CORE.AUTHORITY_MANIFEST(PARSE_JSON(?))";
export const REPLAY = "CALL WARRANT.CORE.REPLAY_DECISIONS(NULL)";
export const TASK_ACTIVITY = "CALL WARRANT.CORE.TASK_ACTIVITY(?)";

/*
 * The three statements a visitor is invited to *try*, and which Snowflake refuses.
 *
 * These are the real statements the governed console runs — not lookalikes written to
 * fail. A demo that proves a boundary has to cross it, or it proves nothing; a disabled
 * button only shows that this page chose not to ask.
 *
 * They are safe to fire at a live production account because they are inert twice over.
 * First, WARRANT_PUBLIC holds no grant on EXECUTE_ACTION and no INSERT/UPDATE anywhere,
 * so authorisation fails before execution. Second — for the case where that grant is one
 * day mis-applied — the caller binds an action_id that cannot exist, so EXECUTE_ACTION
 * finds nothing to run and the UPDATE matches no row. The demo cannot become the incident
 * it is describing.
 */
export const ATTEMPT_APPROVE = "CALL WARRANT.CORE.EXECUTE_ACTION(?)";
export const ATTEMPT_DECIDE = `
  UPDATE WARRANT.CORE.PENDING_ACTIONS
     SET decision = ?, decided_by = CURRENT_USER(), decided_at = CURRENT_TIMESTAMP()
   WHERE action_id = ?`;

export type Capability = {
  action: string;
  outcome: string;
  tier: number;
  rationale: string;
  classifications: { object: string; sensitivity: string | null }[];
};

export type ManifestPayload = {
  capabilities: Capability[];
  changes?: { action: string; from_outcome: string; to_outcome: string; revocation: boolean }[];
};

export type TaskActivity = {
  window_hours: number;
  tasks: { name: string; state: string; role: string }[];
  runs: { NAME: string; STATE: string; SCHEDULED_TIME: string; COMPLETED_TIME: string }[];
  summary: {
    runs: number;
    succeeded: number;
    skipped_nothing_to_do: number;
    failed: number;
    pending: number;
  };
};

export type ReplayPayload = {
  summary: { replayed: number; diverged: number; now_forbidden: number; needs_attention: number };
  decisions: {
    action_type: string;
    execution_result: string;
    decided_by: string;
    tier_then: number;
    tier_now: number;
    diverged: boolean;
    needs_attention: boolean;
  }[];
};
