"use server";

/**
 * The two things this page lets a visitor *do*. Neither writes anything, for different
 * reasons — and the difference is the point.
 *
 * `whatIf` writes nothing because it only computes. `attemptDecision` writes nothing
 * because Snowflake will not let it: it fires the real approval statements and hands back
 * the database's own refusal. One is safe by construction, the other is safe by
 * enforcement, and a visitor gets to watch the second kind happen.
 *
 * `AUTHORITY_MANIFEST(overrides)` resolves the real action registry against hypothetical
 * classifications. No `ALTER TABLE`, no row touched, nothing to undo: it answers "what
 * would this policy change cost me?" using the same resolver the executor uses, so it
 * cannot disagree with what would actually happen.
 *
 * That is why it is safe to expose publicly when approving is not. The distinction the
 * whole project argues for — reads and computations are not acts — is the same one that
 * decides what belongs on this surface.
 *
 * Note this file exports exactly one thing, and it is an async function. A `"use server"`
 * module may export nothing else — a constant array alongside the action fails at
 * *invocation* with "can only export async functions, found object", which the build does
 * not catch. The allowlist below therefore stays module-private and the component keeps
 * its own copy for rendering the dropdowns.
 */

import { callJson, query } from "@/lib/snowflake";
import {
  ATTEMPT_APPROVE,
  ATTEMPT_DECIDE,
  MANIFEST,
  MANIFEST_WHATIF,
  type ManifestPayload,
} from "@/lib/queries";

/**
 * Objects a visitor may ask about, and the classifications they may ask for.
 *
 * The statement already binds its argument as a parameter, so this is not what stops SQL
 * injection — `PARSE_JSON(?)` does that. This is a second, narrower question: a public
 * endpoint should not let an anonymous caller name arbitrary objects and learn from the
 * error message which ones exist. An allowlist answers only about the seven tables the
 * page already displays.
 */
const OBJECTS = [
  "WARRANT.DATA.SHIPMENTS",
  "WARRANT.DATA.SUPPLIERS",
  "WARRANT.DATA.SKUS",
  "WARRANT.DATA.INVENTORY",
  "WARRANT.DATA.QUALITY_HOLDS",
  "WARRANT.DATA.OPS_REQUESTS",
  "WARRANT.DATA.RUNBOOKS",
] as const;

const SENSITIVITIES = ["open", "internal", "regulated", "untagged"] as const;

export type WhatIfResult =
  | { ok: true; payload: ManifestPayload }
  | { ok: false; error: string };

/**
 * Resolve the capability manifest against a hypothetical classification.
 *
 * @param object Fully-qualified table name, which must be one of {@link OBJECTS}.
 * @param sensitivity One of {@link SENSITIVITIES}. `"untagged"` is sent as JSON `null`,
 *   which models *removing* the tag — deliberately distinct from tagging something
 *   `open`, because untagged is not treated as cleared.
 * @returns The manifest with a `changes` list, or a message safe to show a stranger.
 */
export async function whatIf(object: string, sensitivity: string): Promise<WhatIfResult> {
  if (object === "none") {
    try {
      return { ok: true, payload: await callJson<ManifestPayload>(MANIFEST) };
    } catch {
      return { ok: false, error: "Could not reach Snowflake. Try again in a moment." };
    }
  }

  if (!(OBJECTS as readonly string[]).includes(object)) {
    return { ok: false, error: "Unknown object." };
  }
  if (!(SENSITIVITIES as readonly string[]).includes(sensitivity)) {
    return { ok: false, error: "Unknown classification." };
  }

  const overrides = JSON.stringify({ [object]: sensitivity === "untagged" ? null : sensitivity });

  try {
    return { ok: true, payload: await callJson<ManifestPayload>(MANIFEST_WHATIF, [overrides]) };
  } catch {
    // Deliberately not the driver's message: it can name objects and roles, and this
    // endpoint is public.
    return { ok: false, error: "Could not resolve that hypothetical. Try again in a moment." };
  }
}

/**
 * What a visitor is told after trying to approve, reject or defer.
 *
 * `refused` is the expected outcome and the reason the control exists. `permitted` should
 * be unreachable — it means a grant was mis-applied and this surface is no longer
 * read-only — so it is modelled explicitly rather than folded into a success path, and
 * the component renders it as an alarm.
 */
export type DecisionAttempt =
  | { outcome: "refused"; statement: string; error: string }
  | { outcome: "permitted"; statement: string }
  | { outcome: "unavailable" };

const DECISIONS = ["approved", "rejected", "deferred"] as const;

/*
 * What a refusal looks like coming back from the driver. Both live forms are covered,
 * and they are refused in two different ways worth telling apart:
 *
 *   UPDATE  → "SQL access control error: Insufficient privileges to operate on table
 *              'PENDING_ACTIONS'." The role can see the table and is told no.
 *   CALL    → "Unknown user-defined function WARRANT.CORE.EXECUTE_ACTION." The role has
 *              no USAGE on the procedure, so Snowflake does not admit it exists. Denial
 *              by non-disclosure, which is the stronger of the two.
 *
 * Anything outside this set is treated as an unexpected fault rather than shown, since a
 * public endpoint should not narrate errors nobody predicted.
 */
const DENIAL =
  /access control|Insufficient privileges|not authorized|Unknown user-defined function|00300\d|002003/i;

/**
 * Attempt a real approval decision as `WARRANT_PUBLIC`, and report the refusal.
 *
 * Binds an `action_id` that cannot exist, so the statement is a no-op even in the
 * impossible case where the privilege check passes — see the note on {@link
 * ATTEMPT_APPROVE}. Nothing the caller supplies reaches the SQL as text: the decision is
 * checked against an allowlist and the id is generated here, not passed in.
 *
 * @param decision One of `approved`, `rejected` or `deferred`. Anything else is treated
 *   as `unavailable` rather than reported, since only this app's own UI calls it.
 * @returns The database's refusal with the statement that provoked it, or `permitted` if
 *   the boundary has failed, or `unavailable` if Snowflake could not be reached.
 */
export async function attemptDecision(decision: string): Promise<DecisionAttempt> {
  if (!(DECISIONS as readonly string[]).includes(decision)) return { outcome: "unavailable" };

  // Not a real queue entry, and deliberately unguessable so it cannot collide with one.
  const target = `public-attempt-${crypto.randomUUID()}`;
  const [statement, binds]: [string, string[]] =
    decision === "approved"
      ? [ATTEMPT_APPROVE, [target]]
      : [ATTEMPT_DECIDE, [decision, target]];

  try {
    await query(statement, binds);
    return { outcome: "permitted", statement: statement.trim() };
  } catch (refusal) {
    const message = refusal instanceof Error ? refusal.message : String(refusal);
    // The driver's text is shown verbatim here, unlike in `whatIf`. It names the role and
    // the procedure it refused — both of which this page already prints — and that naming
    // is the evidence. Anything that is not recognisably a denial could carry detail this
    // endpoint has no business disclosing, so it is replaced.
    return DENIAL.test(message)
      ? { outcome: "refused", statement: statement.trim(), error: message }
      : { outcome: "unavailable" };
  }
}
