"""Reading the ``SENSITIVITY`` tag off live Snowflake objects.

This module is the bridge between Snowflake's governance metadata and the policy in
:mod:`warrant.authority.tiers`. It is deliberately the only place that knows *how* a
sensitivity classification is stored, so changing the mechanism does not touch the policy.

Two decisions here are load-bearing, and both are easy to get wrong in a way that fails
silently rather than loudly.

**Real-time reads only.** ``SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES`` lags by up to two
hours and omits inherited tags. Warrant's central claim is that retagging an object changes
the agent's behaviour on the next iteration, so a stale read would not merely slow the demo
down — it would make the claim false. ``SYSTEM$GET_TAG`` is evaluated live.

**No caching, anywhere.** Not a module-level constant, not ``functools.lru_cache``, not
Streamlit's ``@st.cache_data``. Deduplication *within* a single call is fine, because one
action may name the same table twice; remembering anything *between* calls is not.
"""

from __future__ import annotations

from collections.abc import Iterable

from snowflake.snowpark import Session

from warrant.authority.tiers import TouchedObject

SENSITIVITY_TAG = "WARRANT.CORE.SENSITIVITY"
RETENTION_TAG = "WARRANT.CORE.RETENTION"
"""Fully-qualified names of the governance tags.

Qualification is mandatory rather than stylistic: the tags live in ``CORE`` while the
tables they classify live in ``DATA``, so a bare ``'SENSITIVITY'`` raises
``Tag 'SENSITIVITY' does not exist or not authorized`` no matter which schema is current.
"""

READ_TAGS = """
SELECT SYSTEM$GET_TAG(?, ?, 'TABLE') AS sensitivity,
       SYSTEM$GET_TAG(?, ?, 'TABLE') AS retention
"""
"""Every argument binds, so no object name is ever interpolated into SQL text.

Both tags are read in one statement rather than one per policy: the round trip dominates,
and reading them together means the two values are observed at the same instant. Two
sequential reads could straddle a governance change and produce a resolution that was never
true of the object at any single moment.
"""


def read_sensitivity(session: Session, fqns: Iterable[str]) -> list[TouchedObject]:
    """Read the live sensitivity classification of each object.

    Args:
        session: An active Snowpark session. Passed in rather than discovered so the policy
            path stays unit-testable without a warehouse.
        fqns: Fully-qualified table names, as declared by an action type's
            ``touched_objects``. Duplicates are read once; input order is preserved.

    Returns:
        One :class:`~warrant.authority.tiers.TouchedObject` per distinct name, ready to
        hand to :func:`~warrant.authority.tiers.resolve`. An object with no sensitivity tag
        yields ``sensitivity=None``, which ``resolve()`` treats as unclassified rather than
        as cleared — so a table nobody has classified cannot be acted on unsupervised. An
        object with no retention tag yields ``retention=None``, which demands nothing,
        because a legal hold is a state somebody adds rather than one whose absence is
        missing information.
    """
    touched: dict[str, TouchedObject] = {}
    for fqn in fqns:
        if fqn in touched:
            continue
        rows = session.sql(READ_TAGS, params=[SENSITIVITY_TAG, fqn, RETENTION_TAG, fqn]).collect()
        touched[fqn] = TouchedObject(
            fqn=fqn,
            sensitivity=rows[0][0] if rows else None,
            retention=rows[0][1] if rows else None,
        )
    return list(touched.values())
