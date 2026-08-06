"use server";

/**
 * The one thing this page lets a visitor *do* — and it still writes nothing.
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

import { callJson } from "@/lib/snowflake";
import { MANIFEST, MANIFEST_WHATIF, type ManifestPayload } from "@/lib/queries";

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
