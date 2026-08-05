"""Shared test doubles.

Every function that talks to Snowflake takes its ``Session`` as the first argument rather
than discovering one, which is what makes the whole pipeline unit-testable without a
warehouse. :class:`FakeSession` is the other half of that bargain.

It deliberately implements only the Snowpark surface this codebase is sanctioned to use —
``session.sql(...)`` returning something with ``collect()`` and ``count()``. If production
code reaches for anything else it raises ``AttributeError``, which is a useful signal in
its own right: it means the code took a dependency on Snowpark that the design did not
sanction, and that no unit test can cover.

Rows are real :class:`snowflake.snowpark.Row` objects, not dictionaries, so tests exercise
the same positional-and-named access production code uses.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any, NamedTuple

import pytest
from snowflake.snowpark import Row

Answer = Sequence[Row] | Callable[[tuple[Any, ...]], Sequence[Row]]
"""Canned rows, or a function of the bound parameters that produces them.

The callable form exists because statements are matched on their SQL text, and several
distinct reads share identical text while differing only in what they bind — every tag read
is ``SELECT SYSTEM$GET_TAG(?, ?, 'TABLE')``. Keying on text alone cannot tell them apart.
"""


class RecordedCall(NamedTuple):
    """One statement a fake session was asked to run."""

    sql: str
    params: tuple[Any, ...]


class FakeDataFrame:
    """The result of :meth:`FakeSession.sql`."""

    def __init__(self, rows: Sequence[Row]) -> None:
        self._rows = list(rows)

    def collect(self) -> list[Row]:
        """Return the canned rows."""
        return list(self._rows)

    def count(self) -> int:
        """Return how many rows the statement would have produced."""
        return len(self._rows)


class FakeSession:
    """Records every statement and answers with rows keyed by a SQL substring."""

    def __init__(
        self,
        responses: Mapping[str, Answer] | None = None,
        failures: Mapping[str, Exception] | None = None,
    ) -> None:
        """Build a session double.

        Args:
            responses: Maps a distinctive substring of a statement to the rows it should
                return, or to a callable taking the bound parameters. The first matching
                entry wins; an unmatched statement returns no rows, which is the honest
                analogue of a query that found nothing.
            failures: Maps a substring to an exception to raise instead, for testing the
                paths that matter most — the ones where Snowflake says no.
        """
        self._responses = dict(responses or {})
        self._failures = dict(failures or {})
        self.calls: list[RecordedCall] = []

    def sql(self, statement: str, params: Sequence[Any] | None = None) -> FakeDataFrame:
        """Record a statement and return its canned result.

        Args:
            statement: The SQL text.
            params: Bound parameter values, recorded so tests can assert that values were
                *bound* rather than interpolated.

        Returns:
            A :class:`FakeDataFrame` over the matching canned rows.

        Raises:
            Exception: Whatever ``failures`` associates with a matching substring.
        """
        bound = tuple(params or ())
        self.calls.append(RecordedCall(statement, bound))
        for needle, error in self._failures.items():
            if needle in statement:
                raise error
        for needle, answer in self._responses.items():
            if needle in statement:
                rows = answer(bound) if callable(answer) else answer
                return FakeDataFrame(rows)
        return FakeDataFrame([])


def bound(call: RecordedCall) -> dict[str, Any]:
    """Decode the single JSON object a write statement binds.

    Args:
        call: A recorded statement whose only parameter is a JSON object.

    Returns:
        The decoded object. Writes bind one JSON blob rather than positional parameters
        because a bound ``None`` becomes the string ``'None'`` inside a stored procedure —
        see :mod:`warrant.common.audit`.
    """
    return json.loads(call.params[0])


DEMO_TAGS = {
    "WARRANT.DATA.SHIPMENTS": "open",
    "WARRANT.DATA.SUPPLIERS": "open",
    "WARRANT.DATA.SKUS": "open",
    "WARRANT.DATA.OPS_REQUESTS": "open",
    "WARRANT.DATA.INVENTORY": "internal",
    "WARRANT.DATA.QUALITY_HOLDS": "regulated",
    # RUNBOOKS is deliberately absent: it is untagged in the account too, and the untagged
    # path is the one most likely to be wrong.
}
"""The sensitivity classifications actually applied in the demo account.

Verified against ``SYSTEM$GET_TAG`` rather than transcribed from ``sql/10_synthetic_data.sql``,
so a drift between the DDL and the account shows up as a failing test.
"""


@pytest.fixture
def tagged_session() -> FakeSession:
    """A session whose tag reads mirror the demo account, keyed on the bound object name."""
    return FakeSession(
        responses={
            "SYSTEM$GET_TAG": lambda params: [Row(SENSITIVITY=DEMO_TAGS.get(params[1]))],
        }
    )
