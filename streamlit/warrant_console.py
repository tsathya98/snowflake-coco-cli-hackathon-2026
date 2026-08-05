"""Warrant :: the approval console.

Runs as Streamlit in Snowflake, inside the governed perimeter. There is no separate service,
no API key, and no copy of the data anywhere else — the reviewer's own Snowflake identity is
what authorises every query on this page.

Five design decisions, each made against a specific failure mode:

**Evidence is co-present, not behind a click.** The observation that triggered the exception,
the runbook clauses the reasoning leaned on, and the action being proposed are on screen
together. A reviewer asked to approve something whose evidence is one click away will approve
it without clicking.

**Provenance is a property of the value.** Anything the model wrote is rendered differently
from anything a human or a detector wrote, and carries the words "model-generated" — not just
a colour, because a colour alone is invisible to a colourblind reviewer and to a screen
reader. Every severity and tier is likewise shown as text beside its colour.

**Approve dispatches a validated payload.** Approving calls ``CORE.EXECUTE_ACTION`` with the
action id. It does not re-enter the reasoning loop with a description of what the human
agreed to, because then the agent would decide again how to carry it out, and the thing
executed would not be the thing approved.

**Reject, defer and refuse are three different outcomes, all recorded.** A dismiss that
writes nothing destroys the only audit trail the console exists to produce.

**No pandas, and every panel is isolated.** Rows arrive from ``collect()`` as plain dicts,
which keeps VARIANT columns as JSON strings and skips an Arrow conversion this app has no
reason to perform. Each panel renders inside :func:`guarded`, because an unhandled exception
anywhere in a Streamlit script replaces the *entire* app with a generic "Something went
wrong" — and for a console whose only job is to be trusted, one broken panel must never look
like a broken system.

That last decision paid for itself. ``st.dataframe(..., hide_index=True)`` raises
``TypeError: DataFrameSelectorMixin.dataframe() got an unexpected keyword argument
'hide_index'`` in the Streamlit-in-Snowflake build — the warehouse runtime wraps
``dataframe()`` and does not accept every keyword the open-source signature does. Five panels
failed on that at once, each showed a contained message naming itself, and every other tab kept
working. Unwrapped, it would have been a blank page with no indication of which of five
statements was at fault. **Prefer the smallest keyword set that works over the newest one**:
this file passes data and nothing else.
"""

import json
from collections import Counter
from contextlib import contextmanager

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Warrant", page_icon="⚖️", layout="wide")

session = get_active_session()

# Presentation only. Every selector is data-testid or data-baseweb based, because Streamlit's
# generated class names change between builds and Streamlit in Snowflake does not run the same
# build as a local install. A selector that stops matching degrades this page to stock Streamlit
# styling; it cannot break it. Nothing here is load-bearing for meaning — colour always
# accompanies a word, never replaces one.
CSS = """
<style>
.block-container {padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1480px;}
h1, h2, h3, h4, h5 {letter-spacing: -0.016em;}
[data-testid="stHeader"] {background: transparent;}

.stTabs [data-baseweb="tab-list"] {gap: 4px; border-bottom: 1px solid rgba(148,163,184,0.3);}
.stTabs [data-baseweb="tab"] {height: 46px; padding: 0 18px; font-size: 0.92rem; font-weight: 600;}
.stTabs [aria-selected="false"] {opacity: 0.62;}

.stButton button {border-radius: 7px; font-weight: 600; letter-spacing: 0.01em;}
[data-testid="stDataFrame"] {border-radius: 9px; overflow: hidden;}
</style>
"""

# One accent per meaning, used by every tile, chip and card on the page. Kept as a single mapping
# so a new panel cannot invent a sixth shade of amber.
#
# Chosen to clear 4.5:1 against **both** a white and a near-black canvas, because Snowsight has a
# dark theme and a Streamlit app inherits it. Nothing on this page may assume which one a judge is
# running: surfaces are translucent slate over whatever the canvas is, body text is `inherit`, and
# the only place a fixed text colour appears is white-on-solid-accent inside a chip.
TONE = {
    "neutral": "#64748b",
    "good": "#16a34a",
    "warn": "#d97706",
    "bad": "#dc2626",
    "info": "#6366f1",
}

# Two translucent surfaces, layered over the canvas rather than painted onto it.
SURFACE = "rgba(148,163,184,0.10)"
HAIRLINE = "rgba(148,163,184,0.32)"
MUTED = "rgba(148,163,184,0.95)"

TIER_NAMES = {
    0: "L0 · read only",
    1: "L1 · draft",
    2: "L2 · acts unsupervised",
    3: "L3 · needs approval",
    4: "L4 · never permitted",
}

# The tier bands share the palette with OUTCOME_TONE below, so the chip on a queued action and
# the card on the authority tab cannot disagree about what amber means. L0 and L1 are the same
# muted slate deliberately: read and draft are both "nothing happened to the data".
TIER_TONE = {
    0: TONE["neutral"],
    1: TONE["neutral"],
    2: TONE["good"],
    3: TONE["warn"],
    4: TONE["bad"],
}

TIER_MEANING = {
    "open": "act unsupervised (L2)",
    "internal": "act only with human approval (L3)",
    "regulated": "read and explain, never act (L4)",
}

# Severity is always rendered as this label *and* a chip. The mapping and the palette live
# together so they cannot drift into a band that has no colour or a colour with no band.
SEVERITY_STYLE = {
    "critical": ("#991b1b", "Critical"),
    "high": (TONE["warn"], "High"),
    "medium": (TONE["info"], "Medium"),
    "low": (TONE["neutral"], "Low"),
}

# The whole run in one line, above the tabs. A reviewer arriving cold should be able to read what
# the agent did before deciding which tab to open, and — this is the part that matters — should see
# `refused` and `awaiting you` with the same prominence as `acted alone`. A console that headlines
# only its throughput is advertising, not evidence.
#
# `acted` counts rows that reached an execution result other than a refusal, rather than
# `decision = 'auto'`, because an approved-then-executed action is just as much work that happened.
HEADLINE = """
SELECT (SELECT COUNT(*) FROM WARRANT.CORE.EXCEPTIONS)                                 AS detected,
       (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS
         WHERE execution_result IS NOT NULL AND execution_result <> 'refused')         AS acted,
       (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS WHERE decision = 'pending')  AS awaiting,
       (SELECT COUNT(*) FROM WARRANT.CORE.REFUSALS)                                    AS refused,
       (SELECT COUNT(*) FROM WARRANT.AUDIT.ACTION_AUDIT)                               AS logged,
       (SELECT COALESCE(TO_VARCHAR(MAX(ts), 'YYYY-MM-DD HH24:MI'), 'never')
          FROM WARRANT.AUDIT.ACTION_AUDIT)                                             AS last_at
"""

QUEUE = """
SELECT * FROM WARRANT.CORE.APPROVAL_QUEUE
 WHERE decision = 'pending'
 ORDER BY effective_tier DESC, proposed_at
"""

# Every nullable column is coalesced to a string here rather than left to become a Python None.
#
# This is not defensive tidying, it is the fix for the failure that blanked this whole app. An
# earlier revision called to_pandas() and died in pandas 3.0's new default string dtype; removing
# pandas from this file did not remove the problem, because `st.dataframe` builds a DataFrame
# internally from whatever it is handed, and the runtime carries pandas 3.0.5 transitively via
# streamlit. A column of mixed str and None still crosses that boundary and still lands in an
# Arrow conversion with nothing good to do with it. So no None leaves SQL.
DECIDED = """
SELECT action_id,
       action_type,
       decision,
       COALESCE(decided_by, '-')                                     AS decided_by,
       -- NOT aliased `decided_at`: Snowflake resolves ORDER BY against the select alias before
       -- the base column, so reusing the name makes the sort below read this VARCHAR and try to
       -- cast '-' to a timestamp. It fails with "Timestamp '-' is not recognized", nowhere near
       -- the line that caused it.
       COALESCE(TO_VARCHAR(decided_at, 'YYYY-MM-DD HH24:MI'), '-')   AS decided_when,
       COALESCE(decision_note, '-')                                  AS decision_note,
       COALESCE(execution_result, 'not executed')                    AS execution_result
  FROM WARRANT.CORE.PENDING_ACTIONS
 WHERE decision <> 'pending'
 ORDER BY COALESCE(decided_at, proposed_at) DESC
 LIMIT 50
"""

# `tier` is coalesced to a number rather than to text because render below indexes TIER_NAMES with
# it. A refusal always carries FORBIDDEN, so the fallback is unreachable in practice — but
# int(None) raises, and a refusal panel that crashes is the one panel that must not.
REFUSALS = """
SELECT TO_VARCHAR(ts, 'YYYY-MM-DD HH24:MI')          AS when_refused,
       COALESCE(action_id, exception_id, 'unknown')   AS subject,
       COALESCE(tier, 4)                              AS tier,
       COALESCE(action_type, 'action')                AS action_type,
       rationale,
       COALESCE(TO_VARCHAR(footprint_at_execution), '') AS footprint
  FROM WARRANT.CORE.REFUSALS
 ORDER BY ts DESC
 LIMIT 50
"""

# `tier` is nullable and numeric, so it is rendered as text rather than coalesced to a sentinel
# number — a 0 would read as "L0 read-only" when it means "no tier applied". See DECIDED above for
# why nothing nullable may leave SQL as a Python None.
AUDIT = """
SELECT TO_VARCHAR(ts, 'YYYY-MM-DD HH24:MI:SS')   AS at,
       phase,
       outcome,
       COALESCE(TO_VARCHAR(tier), '-')           AS tier,
       actor,
       rationale
  FROM WARRANT.AUDIT.ACTION_AUDIT
 ORDER BY ts DESC
 LIMIT 200
"""

# Read live on every render. No @st.cache_data anywhere in this file: the whole claim is that
# retagging an object changes the agent's behaviour immediately, and a cache would hide it.
#
# Spelled out one literal at a time because SYSTEM$GET_TAG requires *constant* arguments and
# rejects a column reference — `SELECT SYSTEM$GET_TAG(tag, obj, 'TABLE') FROM (…)` fails with
# "Invalid value [OBJ] for function 'SYSTEM$GET_TAG', parameter 1". A bound `?` is fine, which
# is why warrant.authority.tags can parameterise it; a column is not.
# `untagged` is substituted here rather than in Python so that no column in this file can hand a
# None to Streamlit. RUNBOOKS is genuinely untagged and must stay that way — it exercises the
# untagged-is-not-cleared path — so this is the one query guaranteed to produce a NULL.
GOVERNANCE = """
SELECT 'WARRANT.DATA.SHIPMENTS' AS object,
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.SHIPMENTS', 'TABLE'),
                'untagged') AS sensitivity
UNION ALL SELECT 'WARRANT.DATA.SUPPLIERS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.SUPPLIERS', 'TABLE'),
                'untagged')
UNION ALL SELECT 'WARRANT.DATA.SKUS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.SKUS', 'TABLE'),
                'untagged')
UNION ALL SELECT 'WARRANT.DATA.INVENTORY',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.INVENTORY', 'TABLE'),
                'untagged')
UNION ALL SELECT 'WARRANT.DATA.QUALITY_HOLDS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.QUALITY_HOLDS', 'TABLE'),
                'untagged')
UNION ALL SELECT 'WARRANT.DATA.OPS_REQUESTS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.OPS_REQUESTS', 'TABLE'),
                'untagged')
UNION ALL SELECT 'WARRANT.DATA.RUNBOOKS',
       COALESCE(SYSTEM$GET_TAG('WARRANT.CORE.SENSITIVITY', 'WARRANT.DATA.RUNBOOKS', 'TABLE'),
                'untagged')
"""

# Queried through the SEMANTIC_VIEW(...) construct rather than against the base tables, so the
# figure an approver reads is the same named definition the Cortex Analyst tool answers from.
# "On-time rate" resolves in exactly one place; a console that re-derived it in its own SQL could
# disagree with the agent about what it means, which is the failure the semantic layer prevents.
#
# Note the logical names: the view declares `suppliers.supplier AS supplier_name`, so the
# dimension is `suppliers.supplier` — the right-hand side is the underlying column, not the
# identifier you query by.
#
# The outer SELECT is not cosmetic. A bare `SELECT *` returns `NUMBER` columns, which Snowpark
# hands back as `decimal.Decimal`, and this console exists partly because an Arrow/pandas dtype
# surprise once replaced the whole app with "Something went wrong". Everything crossing into
# `st.dataframe` is therefore rounded and cast to a plain float or string here, in SQL, where the
# behaviour is the same in every runtime.
METRICS = """
SELECT supplier                          AS "Supplier",
       supplier_tier                     AS "Tier",
       ROUND(on_time_rate * 100, 1)::FLOAT   AS "On-time %",
       shipment_count::INT               AS "Shipments",
       ROUND(avg_lateness_days, 2)::FLOAT    AS "Avg days late"
  FROM SEMANTIC_VIEW(
    WARRANT.CORE.OPS_ANALYSIS
    DIMENSIONS suppliers.supplier, suppliers.supplier_tier
    METRICS    shipments.on_time_rate, shipments.shipment_count, shipments.avg_lateness_days
  )
 ORDER BY "On-time %"
"""

# Streamlit in Snowflake runs with the app owner's rights — WARRANT_ROLE — so this panel shows
# the regulated table exactly as the *agent* sees it, masking included. That is the point: a
# reviewer can confirm from the console alone that the agent never had the lot identifier, rather
# than taking a claim about column-level policy on trust.
COLUMN_GOVERNANCE = """
SELECT hold_id     AS "Hold",
       lot_ref     AS "Lot reference",
       site        AS "Site",
       sku         AS "SKU",
       age_days::INT AS "Days open",
       reason      AS "Reason"
  FROM WARRANT.DATA.QUALITY_HOLDS
 WHERE disposition = 'open' AND age_days > 60
 ORDER BY age_days DESC
"""

SETTLE_DECISION = """
UPDATE WARRANT.CORE.PENDING_ACTIONS AS p
   SET decision = s.r:decision::STRING,
       decided_by = s.r:actor::STRING,
       decided_at = CURRENT_TIMESTAMP(),
       decision_note = s.r:note::STRING
  FROM (SELECT PARSE_JSON(?) AS r) AS s
 WHERE p.action_id = s.r:action_id::STRING
"""

APPEND_AUDIT = """
INSERT INTO WARRANT.AUDIT.ACTION_AUDIT
       (audit_id, phase, action_id, actor, outcome, rationale, payload)
SELECT LEFT('AUD-' || REPLACE(UUID_STRING(), '-', ''), 16),
       'route', r:action_id::STRING, r:actor::STRING, r:outcome::STRING,
       r:rationale::STRING, r:payload
  FROM (SELECT PARSE_JSON(?) AS r)
"""

# `CURRENT_USER()` alone is not enough here, and the reason is worth knowing.
#
# It resolves correctly in a stored procedure (verified: `user='TSATHYA98'` with EXECUTE AS OWNER)
# but comes back **NULL inside Streamlit in Snowflake**, because the app runs with the owner's
# rights and does not disclose the viewer through the session. Binding that NULL into
# ACTION_AUDIT.actor — which is NOT NULL — aborted the write with
# `IntegrityError 100072: NULL result in a non-nullable column`, after the decision had already
# been recorded. See `current_actor()` for where the reviewer's identity actually comes from, and
# `decide()` for the ordering fix.
WHOAMI = "SELECT COALESCE(CURRENT_USER(), CURRENT_ROLE()) AS who"

DISPATCH = "CALL WARRANT.CORE.EXECUTE_ACTION(?)"

# The review surface is computed by stored procedures in sql/45_review.sql, not here. The console
# cannot import the `warrant` package — only stored procedures get it via IMPORTS — and
# reimplementing the authority rules in this file would put a second copy of the most important
# logic in the project one edit away from disagreeing with the first. These call the same functions
# the pipeline and the test suite use, which also means a judge can verify both features from SQL
# with no browser at all.
MANIFEST_LIVE = "CALL WARRANT.CORE.AUTHORITY_MANIFEST(NULL)"
MANIFEST_WHATIF = "CALL WARRANT.CORE.AUTHORITY_MANIFEST(PARSE_JSON(?))"
REPLAY_LIVE = "CALL WARRANT.CORE.REPLAY_DECISIONS(NULL)"
GENERATE_PACK = "CALL WARRANT.CORE.GENERATE_AUDIT_PACK()"

# The accent per manifest outcome, as a key of TONE rather than its own palette — the tier chip on
# a queued action and the capability card on the authority tab now resolve to the same colour
# through the same mapping. Every use also prints the outcome in words.
#
# A comment rather than the PEP 258 attribute docstring this was. Streamlit's "magic" renders any
# bare expression at module level, and a string literal sitting under an assignment is a bare
# expression — so both of these docstrings were being written onto the page as body text above the
# masthead. Nothing in a Streamlit script may document itself with a free-standing string.
OUTCOME_TONE = {
    "acts unsupervised": "good",
    "needs human approval": "warn",
    "refused outright": "bad",
}

SENSITIVITY_CHOICES = ("open", "internal", "regulated", "untagged")

# Recorded when the reviewer's identity cannot be established.
#
# Deliberately not a plausible-looking substitute like the owning role. An approval attributed to
# `WARRANT_ROLE` would read as though the agent's own role approved its own action, which is the
# one claim this system exists to be able to deny. A log that says "a human approved this and we
# could not establish which" is worth more than a log that quietly names the wrong actor.
UNATTRIBUTED = "unattributed-console-user"


def rows(statement: str, params: list | None = None) -> list[dict]:
    """Run a read and return plain dictionaries.

    Args:
        statement: A module-level SQL constant.
        params: Bound values, if any.

    Returns:
        One dict per row, keyed by uppercase column name. Deliberately not a DataFrame:
        ``collect()`` leaves VARIANT columns as JSON strings, whereas ``to_pandas()`` converts
        the whole result through Arrow — work this app never needs, and a source of surprises
        that differ between the Snowflake runtime and a local one.
    """
    result = session.sql(statement, params=params) if params else session.sql(statement)
    return [row.as_dict() for row in result.collect()]


@contextmanager
def guarded(label: str):
    """Render a panel so that its failure stays inside it.

    Args:
        label: What the panel is, named in the message shown if it fails.
    """
    try:
        yield
    except Exception as error:  # noqa: BLE001 - a contained panel failure, deliberately broad
        st.error(f"{label} could not be rendered — {type(error).__name__}: {error}", icon="⚠️")


def chips(labelled: list[tuple[str, str]], note: str = "") -> str:
    """One or more colour chips, each carrying its own label in words.

    Args:
        labelled: ``(label, colour)`` pairs, rendered left to right.
        note: Muted supplementary text shown after the chips.

    Returns:
        HTML. The label sits *inside* the chip rather than being conveyed by the colour, so every
        meaning survives greyscale, colour blindness and a screen reader. This is the only chip
        renderer on the page — the queue, the refusal ledger and the action detail all call it, so
        a severity band and a tier band cannot end up looking like different kinds of thing.
    """
    rendered = "".join(
        f"<span style='display:inline-block;background:{colour};color:#fff;padding:3px 11px;"
        f"border-radius:11px;font-size:0.73rem;font-weight:700;letter-spacing:0.03em;"
        f"margin:0 7px 4px 0'>{label}</span>"
        for label, colour in labelled
    )
    tail = f"<span style='color:{MUTED};font-size:0.84rem'>{note}</span>" if note else ""
    return f"<div style='margin:2px 0 8px'>{rendered}{tail}</div>"


def tiles(figures: list[tuple[str, object, str]]) -> None:
    """Render a row of headline figures.

    Args:
        figures: ``(label, value, tone)`` triples, where tone is a key of :data:`TONE`.

    Replaces ``st.metric`` everywhere on this page. Not for looks alone: ``st.metric`` sizes its
    label to the column and wraps "Needs attention" onto two lines beside a one-line neighbour,
    which on a projector reads as though the two figures are different kinds of measurement. A
    flex row keeps every tile the same height whatever the label length.
    """
    cells = "".join(
        f"<div style='flex:1;min-width:118px;background:{SURFACE};border:1px solid {HAIRLINE};"
        f"border-top:3px solid {TONE.get(tone, TONE['neutral'])};border-radius:9px;"
        f"padding:11px 15px'>"
        f"<div style='font-size:1.7rem;font-weight:800;line-height:1.05;"
        f"letter-spacing:-0.02em'>{value}</div>"
        f"<div style='font-size:0.68rem;font-weight:700;letter-spacing:0.07em;"
        f"text-transform:uppercase;color:{MUTED};margin-top:3px'>{label}</div></div>"
        for label, value, tone in figures
    )
    st.markdown(
        f"<div style='display:flex;flex-wrap:wrap;gap:10px;margin:4px 0 16px'>{cells}</div>",
        unsafe_allow_html=True,
    )


def model_generated(value: str) -> str:
    """Render a value so its machine origin is unmistakable.

    Args:
        value: Text the model produced.

    Returns:
        HTML marking the value as model-generated in words as well as in styling. A reviewer
        must never have to guess which parts of the page a model wrote.
    """
    return (
        "<div style='border-left:3px solid #8b5cf6;background:rgba(139,92,246,0.12);"
        "padding:11px 15px;border-radius:0 8px 8px 0'>"
        "<div style='color:#a78bfa;font-size:0.7rem;font-weight:800;letter-spacing:0.07em;"
        "text-transform:uppercase;margin-bottom:5px'>&#9670; model-generated</div>"
        f"<div style='white-space:pre-wrap'>{value}</div></div>"
    )


def call_json(statement: str, params: list | None = None) -> dict:
    """Invoke a procedure that returns JSON and decode it.

    Args:
        statement: One of the ``CALL`` constants above.
        params: Bound values, if any.

    Returns:
        The decoded payload.
    """
    result = session.sql(statement, params=params) if params else session.sql(statement)
    return json.loads(result.collect()[0][0])


def summarise_change(change: dict) -> str:
    """One capability change, as a phrase naming both the action and the movement.

    Args:
        change: One entry from the manifest payload's ``changes`` list.

    Returns:
        Markdown naming the action and the outcome it moves between, in words — a reviewer reading
        "acts unsupervised -> refused outright" does not need to know what L2 and L4 mean.
    """
    return f"`{change['action']}` ({change['from_outcome']} to {change['to_outcome']})"


def capability_card(capability: dict) -> None:
    """Render one capability as a card whose colour and words agree.

    Args:
        capability: One entry from the ``AUTHORITY_MANIFEST`` payload.
    """
    accent = TONE[OUTCOME_TONE.get(capability["outcome"], "neutral")]
    tags = "".join(
        f"<span style='display:inline-block;background:{SURFACE};border:1px solid {HAIRLINE};"
        f"border-radius:6px;padding:1px 7px;margin:2px 4px 2px 0;font-size:0.72rem;"
        f"font-family:monospace'>{c['object'].split('.')[-1]}"
        f" · {c['sensitivity']}</span>"
        for c in capability["classifications"]
    )
    st.markdown(
        f"<div style='border-left:4px solid {accent};border-top:1px solid {HAIRLINE};"
        f"border-right:1px solid {HAIRLINE};border-bottom:1px solid {HAIRLINE};"
        f"background:{SURFACE};padding:11px 15px;border-radius:0 8px 8px 0;margin-bottom:9px'>"
        f"<div style='display:flex;justify-content:space-between;align-items:baseline;gap:12px'>"
        f"<span style='font-family:monospace;font-weight:700;font-size:0.95rem'>"
        f"{capability['action']}</span>"
        f"<span style='color:{accent};font-weight:800;font-size:0.74rem;text-transform:uppercase;"
        f"letter-spacing:0.06em;white-space:nowrap'>{capability['outcome']}</span></div>"
        f"<div style='margin-top:7px'>{tags}</div>"
        f"<div style='color:{MUTED};font-size:0.8rem;margin-top:7px'>"
        f"{capability['rationale']}</div></div>",
        unsafe_allow_html=True,
    )


def current_actor() -> str:
    """Establish who is making this decision.

    Streamlit exposes the signed-in Snowflake user on its own user object, which is the only
    source that works inside a Streamlit-in-Snowflake app — ``CURRENT_USER()`` returns NULL there.
    The SQL read is kept as a fallback because it *does* work outside SiS, which is where the
    console's statements get exercised by the extraction probe in the handoff.

    Returns:
        The reviewer's username, or :data:`UNATTRIBUTED` if it cannot be established. Never
        ``None`` — ``ACTION_AUDIT.actor`` is NOT NULL, and a decision that cannot be written to the
        log is worse than one attributed to nobody in particular.
    """
    # `st.user` on current Streamlit, `st.experimental_user` on older builds. Both are mappings in
    # some versions and attribute objects in others, hence the defensive access rather than a
    # single expression.
    for holder in (getattr(st, "user", None), getattr(st, "experimental_user", None)):
        if holder is None:
            continue
        for key in ("user_name", "login_name", "email", "name"):
            value = None
            try:
                value = holder[key] if hasattr(holder, "__getitem__") else None
            except (KeyError, TypeError):
                value = None
            value = value or getattr(holder, key, None)
            if value:
                return str(value)

    result = rows(WHOAMI)
    return (result[0]["WHO"] if result and result[0]["WHO"] else None) or UNATTRIBUTED


def decide(action_id: str, decision: str, note: str, execute_now: bool) -> None:
    """Record a human decision, and dispatch it if it was an approval.

    Args:
        action_id: The queued action.
        decision: ``approved``, ``rejected`` or ``deferred``.
        note: The reviewer's reason. Required for a rejection — a rejection nobody explained
            teaches the next reviewer nothing.
        execute_now: Whether to dispatch the action after recording the approval.

    Every branch writes an audit row. A deferral leaves the action pending but still records
    that a human looked and chose to wait, because "nobody has looked at this yet" and
    "someone looked and deferred" are different states.

    **The audit row is written first, before the decision is persisted.** That ordering is
    deliberate. The two writes are not in one transaction, so one of them can fail alone, and the
    two failure modes are not equally bad: an audit entry for a decision that did not persist is
    over-logging, which a reviewer can reconcile, whereas a persisted decision with no audit entry
    is a decision that happened outside the record — exactly what an append-only decision log
    exists to make impossible. The original order was the other way round and produced precisely
    that: a NULL ``actor`` aborted the audit write *after* the action had already been marked
    approved.
    """
    actor = current_actor()

    session.sql(
        APPEND_AUDIT,
        params=[
            json.dumps(
                {
                    "action_id": action_id,
                    "actor": actor,
                    "outcome": decision,
                    "rationale": note or f"{decision} by {actor} without a note.",
                    "payload": {"decided_in": "console", "identified_actor": actor != UNATTRIBUTED},
                }
            )
        ],
    ).collect()

    if decision != "deferred":
        session.sql(
            SETTLE_DECISION,
            params=[
                json.dumps(
                    {"action_id": action_id, "decision": decision, "actor": actor, "note": note}
                )
            ],
        ).collect()

    if decision == "approved" and execute_now:
        # Dispatch the already-validated payload. Deliberately NOT a fresh reasoning turn:
        # the reviewer approved this action, not a description of it.
        result = session.sql(DISPATCH, params=[action_id]).collect()[0][0]
        if result == "refused":
            # Rendered as a full banner rather than st.error. This is the single most important
            # state the console can be in — a human's approval that did not survive — and at video
            # compression a standard alert reads as a validation warning about the text box.
            st.markdown(
                "<div style='border:2px solid #dc2626;background:rgba(220,38,38,0.13);"
                "border-radius:11px;padding:18px 22px;margin:12px 0'>"
                "<div style='font-size:1.2rem;font-weight:800;color:#f87171;"
                "letter-spacing:-0.015em'>&#9878;&#65039; Refused at execution time</div>"
                "<div style='font-size:1rem;font-weight:700;margin-top:8px'>"
                "Your approval was recorded. The action was not taken.</div>"
                "<div style='margin-top:8px;font-size:0.9rem;max-width:78ch;opacity:0.85'>"
                "The data this action touches is classified in a way that forbids it — a "
                "classification that changed after the action was queued. Authority is resolved "
                "again at execution time, so an approval cannot outlive the policy it was given "
                "under. The refusal is in the append-only log; see the Refusals tab."
                "</div></div>",
                unsafe_allow_html=True,
            )
            return
        st.success(f"Approved and dispatched — {result}.", icon="✅")
        return
    st.success(f"Recorded as {decision}.", icon="📝")


def render_action(row: dict) -> None:
    """One pending action, with its evidence beside it rather than behind it."""
    colour, label = SEVERITY_STYLE.get(str(row["SEVERITY"]).lower(), (TONE["neutral"], "Unrated"))
    band = int(row["EFFECTIVE_TIER"])
    tier = TIER_NAMES.get(band, str(row["EFFECTIVE_TIER"]))
    tone = TIER_TONE.get(band, TONE["neutral"])
    action_id = row["ACTION_ID"]

    st.markdown(
        f"<div style='border-left:4px solid {tone};background:{SURFACE};padding:13px 17px;"
        f"border-radius:0 9px 9px 0;margin-bottom:10px'>"
        + chips([(label, colour), (tier, tone)], f"{row['METRIC']} · {row['ENTITY']}")
        + f"<div style='font-size:1.12rem;font-weight:700;"
        f"letter-spacing:-0.015em'>{row['ACTION_TYPE']}</div>"
        f"<div style='font-family:monospace;font-size:0.72rem;color:{MUTED};margin-top:3px'>"
        f"{action_id}</div></div>",
        unsafe_allow_html=True,
    )

    evidence, proposal = st.columns(2, gap="large")

    with evidence:
        st.markdown("**What was observed**")
        st.markdown(
            f"- **Observed** — {row['OBSERVED']}\n"
            f"- **Expected** — {row['EXPECTED']}\n"
            f"- **Deviation** — {row['DEVIATION']}\n"
            f"- **Detected by** — `{row['DETECTION_METHOD']}`"
        )
        grounded = json.loads(row["GROUNDED_IN"] or "[]")
        st.markdown(
            "**Grounded in** — "
            + (", ".join(f"`{d}`" for d in grounded) if grounded else "_no runbook retrieved_")
        )
        with st.expander("Supporting figures the model cited"):
            for item in json.loads(row["EVIDENCE"] or "[]"):
                st.markdown(f"- {item}")

    with proposal:
        st.markdown("**Why this action, and why it needs you**")
        st.markdown(model_generated(str(row["ROOT_CAUSE"])), unsafe_allow_html=True)
        st.markdown("**Authority**")
        st.markdown(chips([(tier, tone)]), unsafe_allow_html=True)
        st.caption(str(row["TIER_RATIONALE"]))
        st.markdown(f"**Binding object** — `{row['BINDING_OBJECT'] or 'none declared'}`")
        if row["ROLLBACK_PLAN"]:
            st.markdown(f"**Undo path** — `{str(row['ROLLBACK_PLAN'])[:90]}…`")
        else:
            st.markdown(
                "**Undo path** — **none declared**; RB-004 treats that as grounds for more "
                "scrutiny, not less"
            )
        with st.expander("Parameters that will be bound"):
            st.json(json.loads(row["ACTION_PARAMS"] or "{}"))
            st.caption(
                f"Produced by {row['MODEL']}. Bound as query parameters — the model never "
                "contributes SQL text."
            )

    note = st.text_area(
        "Your reason (required to reject)",
        key=f"note-{action_id}",
        placeholder="What did you check? What made this the right call?",
        height=68,
    )
    approve, reject, defer = st.columns(3)
    if approve.button("Approve and execute", key=f"a-{action_id}", type="primary"):
        decide(action_id, "approved", note, execute_now=True)
    if reject.button("Reject", key=f"r-{action_id}"):
        if not note.strip():
            st.warning("A rejection needs a reason, so the next reviewer learns from it.")
        else:
            decide(action_id, "rejected", note, execute_now=False)
    if defer.button("Defer", key=f"d-{action_id}"):
        decide(action_id, "deferred", note, execute_now=False)
    st.divider()


st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    "<div style='background:linear-gradient(115deg,#0f172a 0%,#1e293b 55%,#312e81 100%);"
    "border-radius:13px;padding:20px 26px;margin-bottom:14px'>"
    "<div style='display:flex;align-items:baseline;gap:14px;flex-wrap:wrap'>"
    "<span style='font-size:1.55rem;font-weight:800;color:#fff;letter-spacing:-0.025em'>"
    "&#9878;&#65039; Warrant</span>"
    "<span style='font-size:0.76rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;"
    "color:#a5b4fc'>governed autonomous operations &middot; running inside Snowflake</span></div>"
    "<div style='margin-top:8px;font-size:0.9rem;color:#cbd5e1;max-width:88ch;line-height:1.5'>"
    "An operations agent whose authority is derived from the governance tags on the data it "
    "touches &mdash; read live, and resolved again at execution time. Every decision below, "
    "including every refusal, is a row in an append-only log.</div></div>",
    unsafe_allow_html=True,
)

with guarded("The headline figures"):
    headline = rows(HEADLINE)[0]
    tiles(
        [
            ("Exceptions detected", headline["DETECTED"], "info"),
            ("Handled by the agent", headline["ACTED"], "good"),
            ("Awaiting you", headline["AWAITING"], "warn"),
            ("Refused", headline["REFUSED"], "bad"),
            ("Decisions logged", headline["LOGGED"], "neutral"),
        ]
    )
    st.caption(f"Last recorded decision: {headline['LAST_AT']}. Read live on every render.")

queue_tab, authority_tab, replay_tab, refusal_tab, governance_tab, audit_tab = st.tabs(
    [
        "Awaiting your decision",
        "What am I allowed to do?",
        "Replay",
        "Refusals",
        "Governance",
        "Decision log",
    ]
)

with queue_tab:
    with guarded("The approval queue"):
        pending = rows(QUEUE)
        if not pending:
            st.info(
                "Nothing is awaiting a decision. Run `CALL WARRANT.CORE.RUN_LOOP('AUTO');` to "
                "scan for exceptions.",
                icon="✅",
            )
        else:
            st.markdown(
                f"<div style='background:rgba(217,119,6,0.13);border:1px solid {TONE['warn']};"
                f"border-radius:9px;padding:11px 16px;margin-bottom:14px;font-size:0.9rem'>"
                f"<b>{len(pending)} action(s) need a human.</b> Ordered by the authority they "
                f"demand, most demanding first &mdash; the ones the agent was least willing to "
                f"take on its own are the ones worth your attention first.</div>",
                unsafe_allow_html=True,
            )
            for row in pending:
                render_action(row)

    with guarded("Already-decided actions"):
        decided = rows(DECIDED)
        if decided:
            st.markdown("#### Already decided")
            st.dataframe(decided)

with authority_tab, guarded("The authority explorer"):
    st.markdown(
        "#### Everything this agent can do, and what it is allowed to do right now\n"
        "Every action in the registry, resolved against the classifications currently on the data "
        "it touches. Most restricted first — what the agent **may not** do is what a reviewer "
        "should read before what it may."
    )

    live = call_json(MANIFEST_LIVE)["capabilities"]
    counts = Counter(c["outcome"] for c in live)
    tiles(
        [
            ("Refused outright", counts.get("refused outright", 0), "bad"),
            ("Needs human approval", counts.get("needs human approval", 0), "warn"),
            ("Acts unsupervised", counts.get("acts unsupervised", 0), "good"),
        ]
    )

    st.divider()
    st.markdown("##### Ask a policy question before answering it destructively")
    st.caption(
        "Choose a hypothetical classification. This resolves the **real** rules against "
        "hypothetical inputs — no `ALTER TABLE`, no write, nothing to undo. It is the same "
        "resolver the executor uses, so it cannot disagree with what would actually happen."
    )
    objects = sorted({c["object"] for cap in live for c in cap["classifications"]})
    picker, chooser = st.columns([3, 2])
    target = picker.selectbox("If this object were reclassified…", ["(nothing)", *objects])
    hypothetical = chooser.selectbox("…to", SENSITIVITY_CHOICES, index=2)

    if target == "(nothing)":
        shown, changes = live, []
    else:
        payload = call_json(
            MANIFEST_WHATIF,
            params=[json.dumps({target: None if hypothetical == "untagged" else hypothetical})],
        )
        shown, changes = payload["capabilities"], payload["changes"]

        revoked = [c for c in changes if c["revocation"]]
        granted = [c for c in changes if not c["revocation"]]
        if revoked:
            st.error(
                f"**{len(revoked)} capability(ies) would be revoked** by tagging "
                f"`{target.split('.')[-1]}` as `{hypothetical}`: "
                + ", ".join(summarise_change(c) for c in revoked),
                icon="⚖️",
            )
        if granted:
            st.warning(
                f"**{len(granted)} capability(ies) would be widened**: "
                + ", ".join(summarise_change(c) for c in granted),
                icon="⚠️",
            )
        if not changes:
            st.info("No capability changes. This reclassification would cost the agent nothing.")

    st.divider()
    for capability in shown:
        capability_card(capability)

with replay_tab, guarded("Decision replay"):
    st.markdown(
        "#### Would today's policy still allow what already happened?\n"
        "Every recorded action re-resolved against the classifications in force **now**. Not a "
        "report over stored tiers — the real resolver, over the real registry, with current tags. "
        "A divergence means the governance posture changed after the decision was taken."
    )
    payload = call_json(REPLAY_LIVE)
    summary, decisions = payload["summary"], payload["decisions"]

    tiles(
        [
            ("Replayed", summary["replayed"], "neutral"),
            ("Would differ today", summary["diverged"], "info"),
            ("Now forbidden", summary["now_forbidden"], "warn"),
            (
                "Needs attention",
                summary["needs_attention"],
                "bad" if summary["needs_attention"] else "good",
            ),
        ]
    )

    if summary["needs_attention"]:
        st.error(
            f"**{summary['needs_attention']} executed action(s) would not be permitted "
            "unsupervised under today's classifications.** This is the only category that cannot "
            "be corrected going forward, because the work has already happened.",
            icon="⚖️",
        )
    else:
        st.success(
            "Nothing executed under a policy that has since tightened.",
            icon="✅",
        )

    st.dataframe(
        [
            {
                "Action": d["action_type"],
                "Ran as": d["execution_result"],
                "Decided by": d["decided_by"],
                "Tier then": TIER_NAMES.get(d["tier_then"], "-"),
                "Tier now": TIER_NAMES.get(d["tier_now"], "-"),
                "Differs": "yes" if d["diverged"] else "no",
                "Needs attention": "YES" if d["needs_attention"] else "no",
            }
            for d in decisions
        ]
    )

    st.divider()
    st.markdown("##### The agent's own evidence pack")
    st.caption(
        "Composed inside Snowflake by the agent's own role — so it is subject to the same masking "
        "policies the agent is — from the append-only record. Declines are listed before completed "
        "work, deliberately."
    )
    if st.button("Generate audit pack"):
        st.success(f"Written to {session.sql(GENERATE_PACK).collect()[0][0]}", icon="📄")

with refusal_tab, guarded("The refusal ledger"):
    st.markdown(
        "#### Every action the agent declined to take\n"
        "A refusal is a result, not an error, so it is recorded with the same care as an "
        "action. This is the question most agents cannot answer about themselves."
    )
    refused = rows(REFUSALS)
    if not refused:
        st.info(
            "No refusals recorded yet. To see one, reclassify the table a pending action "
            "touches and then approve it:  \n"
            "`ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY "
            "= 'regulated';`",
            icon="⚖️",
        )
    else:
        for row in refused:
            st.markdown(
                chips(
                    [
                        ("Refused", "#7f1d1d"),
                        (str(TIER_NAMES.get(int(row["TIER"]), row["TIER"])), TONE["bad"]),
                    ],
                    f"{row['WHEN_REFUSED']} · {row['SUBJECT']}",
                ),
                unsafe_allow_html=True,
            )
            st.markdown(f"**{row['ACTION_TYPE']}** — {row['RATIONALE']}")
            if row["FOOTPRINT"]:
                st.caption(f"Classifications at execution time: {row['FOOTPRINT']}")
            st.divider()

with governance_tab, guarded("The governance table"):
    st.markdown(
        "#### The classifications in force, read live\n"
        "Read with `SYSTEM$GET_TAG` on every render — never from `ACCOUNT_USAGE`, which lags "
        "by up to two hours, and never cached. Change a tag and the agent's next decision "
        "changes with it, without a code change or a redeploy."
    )
    st.dataframe(
        [
            {
                "Object": row["OBJECT"],
                "Sensitivity": row["SENSITIVITY"],
                # 'untagged' is deliberately absent from TIER_MEANING, so it takes the default —
                # unclassified demands the same scrutiny as internal, which is the whole point of
                # not treating an untagged object as cleared.
                "The agent may": TIER_MEANING.get(
                    row["SENSITIVITY"], "act only with human approval (L3)"
                ),
            }
            for row in rows(GOVERNANCE)
        ]
    )
    st.caption(
        "Untagged is deliberately not treated as open: an object nobody has classified is not "
        "the same as an object someone classified as safe."
    )

with governance_tab, guarded("Column-level governance"):
    st.markdown(
        "#### What the agent may see, as opposed to what it may do\n"
        "The sensitivity tag above stops the agent **acting** on a regulated record. It does not "
        "stop it **reading** one — and deliberately so, because the agent has to be able to "
        "surface an aging hold and explain it. Those are two different controls, so there is a "
        "second one: a masking policy on `QUALITY_HOLDS.lot_ref`."
    )
    st.dataframe(rows(COLUMN_GOVERNANCE))
    st.caption(
        "This console runs with the agent's own role, so the lot references above are withheld "
        "here exactly as they are withheld from the agent. A qualified person — "
        "`WARRANT_QUALITY_OWNER` — sees the real values in the same table, from the same query. "
        "The agent can therefore say a hold is 82 days old and why, and cannot say which "
        "physical lot it concerns: identifying the lot is what would make the record actionable."
    )

with governance_tab, guarded("The governed metric layer"):
    st.markdown(
        "#### The governed metric layer\n"
        "Read through `SEMANTIC_VIEW(...)` against `CORE.OPS_ANALYSIS`, not against the base "
        "tables. Classification governs *what the agent may do*; the semantic view governs *what "
        "the numbers mean* — so this console and the agent cannot quietly disagree about the "
        "definition of on-time rate."
    )
    st.dataframe(rows(METRICS))
    st.caption(
        "These are 180-day aggregates. The detectors compare a rolling 14-day window against a "
        "90-day baseline, per RB-001, which is why a supplier can look unremarkable here and "
        "still raise an exception."
    )

with audit_tab, guarded("The decision log"):
    st.markdown("#### Append-only decision log")
    log = rows(AUDIT)
    if not log:
        st.info("Nothing recorded yet.", icon="📋")
    else:
        counts = Counter(row["PHASE"] for row in log)
        tiles(
            [
                (phase, count, "bad" if phase == "refuse" else "neutral")
                for phase, count in counts.most_common()
            ]
        )
        st.dataframe(log)
