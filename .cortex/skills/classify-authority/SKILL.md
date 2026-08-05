---
name: classify-authority
description: Resolve the authority tier a proposed action may execute at, derived from Snowflake object tags rather than a hardcoded rules list.
---

# classify-authority

The governance gate. This is what makes autonomous action defensible.

## Approach
1. For each object in `touched_objects[]`, read its `SENSITIVITY` tag with
   `SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', '<fully.qualified.name>', 'TABLE')`.
   Fully-qualified names are **required** — the tag lives in `CORE` while the tables live in
   `DATA`, so a bare tag name raises "Tag 'SENSITIVITY' does not exist or not authorized".
2. Map each tag to the scrutiny it demands: `open → L2`, `internal → L3`,
   `regulated → L4 (forbidden)`.
3. Untagged is **not** open — it demands `L3`, because unclassified is not the same as cleared.
4. The binding object is the one demanding the **most** scrutiny, and the effective tier is the
   **greater** of the requested tier and that demand. Reads and drafts (`≤ L1`) are exempt, so the
   agent can always investigate and explain even what it may never touch.

Implemented in `src/warrant/authority/tiers.py`, unit-tested in `tests/test_tiers.py`. The tag read
itself is `src/warrant/authority/tags.py`.

## Rules
- **Authority defaults down, never up.** Data can demote an action; it can never promote one.
- Ambiguity escalates. An empty `touched_objects[]` is treated as suspicious, not harmless.
- The rationale string is written verbatim to `ACTION_AUDIT`. Write it for an auditor.
- **Never read tags from `SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES`.** That view lags by up to two
  hours, so a governance change would not take effect until long after a reviewer had given up
  watching. It also omits inherited tags. `SYSTEM$GET_TAG` is real-time.
- **Never cache the tag read** — no module constant, no `lru_cache`, no `@st.cache_data`. Policy
  taking effect on the next loop iteration is the entire claim.
