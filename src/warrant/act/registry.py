"""The action registry: every action the agent is capable of, declared as data.

Two properties matter here, and both are governance properties rather than engineering
ones.

**Actions are data, not code.** The model never emits SQL. It selects an ``action_type``
from a closed enum and supplies named parameters, which are bound positionally as query
parameters. There is no path from model output to executed SQL text, so there is nothing
for a prompt injection to write into.

**Every action declares what it touches.** ``touched_objects`` is what
:func:`warrant.authority.tiers.resolve` reads to decide the action's authority tier. An
action that under-declares its footprint would under-declare its own risk, so the
registry — not the model — owns that list.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from warrant.authority.tiers import Tier

SHIPMENTS = "WARRANT.DATA.SHIPMENTS"
SUPPLIERS = "WARRANT.DATA.SUPPLIERS"
INVENTORY = "WARRANT.DATA.INVENTORY"
QUALITY_HOLDS = "WARRANT.DATA.QUALITY_HOLDS"
OPS_REQUESTS = "WARRANT.DATA.OPS_REQUESTS"


class ActionValidationError(ValueError):
    """Raised when proposed parameters do not match an action type's contract."""


@dataclass(frozen=True)
class ActionType:
    """One thing the agent can do, with its footprint and its undo path.

    ``parameters`` and ``rollback_parameters`` are in **placeholder order**, not
    declaration or alphabetical order: :meth:`bind` zips them positionally onto the ``?``
    placeholders. Getting that order wrong binds the right values to the wrong columns
    without raising anything, so ``tests/test_registry.py`` asserts the order against the
    column names in the SQL itself rather than merely counting placeholders.
    """

    name: str
    description: str
    requested_tier: Tier
    touched_objects: tuple[str, ...]
    parameters: tuple[str, ...]
    sql: str
    rollback_sql: str | None = None
    rollback_parameters: tuple[str, ...] = ()

    def bind(self, params: Mapping[str, Any], *, rollback: bool = False) -> tuple[str, list[Any]]:
        """Validate proposed parameters and order them for positional binding.

        Args:
            params: Parameter names to values, as proposed by the reasoning step. The
                same mapping serves both the action and its rollback; a rollback
                typically needs a subset.
            rollback: Bind :attr:`rollback_sql` instead of :attr:`sql`.

        Returns:
            A ``(sql, values)`` pair where ``values`` is ordered to match the ``?``
            placeholders in the chosen statement.

        Raises:
            ActionValidationError: If any required parameter is missing, if an
                unexpected parameter is present, or if a rollback was requested for an
                action that declares none. Unexpected parameters are rejected rather
                than ignored — a model that invented an extra argument has probably
                misunderstood the action, and silently dropping it hides that.
        """
        if rollback:
            if self.rollback_sql is None:
                raise ActionValidationError(f"action '{self.name}' declares no rollback")
            statement, expected = self.rollback_sql, self.rollback_parameters
        else:
            statement, expected = self.sql, self.parameters

        missing = [name for name in expected if name not in params]
        # A rollback binds a subset of the action's parameters, so surplus keys are only
        # an error on the forward path.
        unexpected = [] if rollback else [name for name in params if name not in expected]
        if missing or unexpected:
            problems = []
            if missing:
                problems.append(f"missing {', '.join(sorted(missing))}")
            if unexpected:
                problems.append(f"unexpected {', '.join(sorted(unexpected))}")
            raise ActionValidationError(f"action '{self.name}': {'; '.join(problems)}")
        return statement, [params[name] for name in expected]


# Five action types spanning every branch of the authority model, so the demo exercises
# all of them against real tags rather than describing them:
#   open_supplier_case   → open data          → executes unsupervised
#   expedite_shipment    → open data          → executes unsupervised
#   raise_replenishment  → internal data      → queued for human approval
#   notify_quality_owner → regulated, drafts  → permitted, because it acts on nothing
#   release_quality_hold → regulated, acts    → refused outright
ACTION_TYPES: dict[str, ActionType] = {
    "open_supplier_case": ActionType(
        name="open_supplier_case",
        description=(
            "Open a supplier performance review case and notify the category buyer. "
            "The standard response to sustained on-time delivery degradation (RB-001)."
        ),
        requested_tier=Tier.LOW_RISK_ACT,
        touched_objects=(SHIPMENTS, SUPPLIERS, OPS_REQUESTS),
        parameters=("supplier_id", "justification"),
        sql=(
            "INSERT INTO WARRANT.DATA.OPS_REQUESTS "
            "(request_id, request_type, subject_id, detail, raised_by) "
            "SELECT UUID_STRING(), 'supplier_case', ?, ?, 'warrant-agent'"
        ),
        rollback_sql=(
            "DELETE FROM WARRANT.DATA.OPS_REQUESTS "
            "WHERE request_type = 'supplier_case' AND subject_id = ?"
        ),
        rollback_parameters=("supplier_id",),
    ),
    "expedite_shipment": ActionType(
        name="expedite_shipment",
        description=(
            "Flag an in-transit shipment for expedited freight. Permitted unsupervised "
            "only below the cost threshold in RB-004."
        ),
        requested_tier=Tier.LOW_RISK_ACT,
        touched_objects=(SHIPMENTS,),
        parameters=("shipment_id",),
        sql=(
            "UPDATE WARRANT.DATA.SHIPMENTS SET status = 'expedited' "
            "WHERE shipment_id = ? AND status = 'in_transit'"
        ),
        rollback_sql=(
            "UPDATE WARRANT.DATA.SHIPMENTS SET status = 'in_transit' "
            "WHERE shipment_id = ? AND status = 'expedited'"
        ),
        rollback_parameters=("shipment_id",),
    ),
    "raise_replenishment": ActionType(
        name="raise_replenishment",
        description=(
            "Raise a replenishment request for a SKU at stockout risk (RB-002). Reads "
            "inventory positions, which are internal, so this always needs a human."
        ),
        requested_tier=Tier.LOW_RISK_ACT,
        touched_objects=(INVENTORY, OPS_REQUESTS),
        parameters=("sku", "quantity", "justification"),
        sql=(
            "INSERT INTO WARRANT.DATA.OPS_REQUESTS "
            "(request_id, request_type, subject_id, quantity, detail, raised_by) "
            "SELECT UUID_STRING(), 'replenishment', ?, ?, ?, 'warrant-agent'"
        ),
        rollback_sql=(
            "DELETE FROM WARRANT.DATA.OPS_REQUESTS "
            "WHERE request_type = 'replenishment' AND subject_id = ?"
        ),
        rollback_parameters=("sku",),
    ),
    "notify_quality_owner": ActionType(
        name="notify_quality_owner",
        description=(
            "Draft a notification to the quality owner about an aging hold. RB-003 "
            "permits automation to surface a hold and nothing further, so this drafts "
            "rather than acts and is allowed against regulated data."
        ),
        requested_tier=Tier.DRAFT,
        # OPS_REQUESTS is declared because the notification is written there. Omitting the
        # table an action writes to would under-declare its footprint, and footprint is
        # precisely what authority is resolved from.
        touched_objects=(QUALITY_HOLDS, OPS_REQUESTS),
        parameters=("hold_id", "message"),
        sql=(
            "INSERT INTO WARRANT.DATA.OPS_REQUESTS "
            "(request_id, request_type, subject_id, detail, raised_by) "
            "SELECT UUID_STRING(), 'quality_notification', ?, ?, 'warrant-agent'"
        ),
        rollback_sql=None,
    ),
    "release_quality_hold": ActionType(
        name="release_quality_hold",
        description=(
            "Change a quality hold's disposition. Registered deliberately so the "
            "refusal is demonstrable: RB-003 reserves this for a qualified person, and "
            "the regulated tag on QUALITY_HOLDS enforces it without a rule in the code."
        ),
        requested_tier=Tier.LOW_RISK_ACT,
        touched_objects=(QUALITY_HOLDS,),
        # Placeholder order, not logical order: SET precedes WHERE.
        parameters=("disposition", "hold_id"),
        sql="UPDATE WARRANT.DATA.QUALITY_HOLDS SET disposition = ? WHERE hold_id = ?",
        rollback_sql=None,
    ),
}


def get_action_type(name: str) -> ActionType:
    """Look up a registered action type.

    Args:
        name: The ``action_type`` value proposed by the reasoning step.

    Returns:
        The matching :class:`ActionType`.

    Raises:
        ActionValidationError: If the name is not registered. The reasoning call is
            schema-constrained to this same set of names, so reaching this is a signal
            that the schema and the registry have drifted apart.
    """
    try:
        return ACTION_TYPES[name]
    except KeyError:
        raise ActionValidationError(
            f"unknown action type '{name}'; registered: {', '.join(sorted(ACTION_TYPES))}"
        ) from None
