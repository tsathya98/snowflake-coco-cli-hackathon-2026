---
name: propose-action
description: Convert a finding into a concrete, typed, reversible action with an explicit rollback path.
---

# propose-action

## Approach
1. Select an action type from the registry — no free-form SQL, ever.
2. Bind parameters from the finding's evidence, not from model free text.
3. Record the rollback procedure alongside the action. An action with no stated rollback is
   automatically treated as requiring approval.

## Rules
- Actions are data, not code. They are rows in `PENDING_ACTIONS`, executed by a typed dispatcher.
- Prefer the smallest reversible step over the complete fix.
- Never propose an action whose `touched_objects[]` you did not declare in the finding.
