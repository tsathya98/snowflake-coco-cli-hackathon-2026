"""The agent composing its own evidence pack.

The question this exists for is not "can we show a nice report" but the one that follows any
governed automation into its first audit: **produce everything you did, why, under whose authority,
and everything you declined.** Answering that by hand from four tables is the kind of task that
never gets done, and a control whose evidence is expensive to produce is a control nobody checks.

Three properties make the pack worth trusting rather than just reading:

**It is assembled from the record, not from narration.** Every figure is a row in
``ACTION_AUDIT``, ``PENDING_ACTIONS`` or ``FINDINGS``. No model writes any part of the structure,
so there is nothing here that can be fluent and wrong.

**Refusals get their own section, before the successes.** An evidence pack that leads with what
the automation achieved and buries what it declined is marketing. The declines are the control
working, and they are what a reviewer is actually checking.

**It carries the replay.** A pack that only described the past would answer "what happened".
Including the re-resolution against today's classifications answers "and would we allow it now",
which is the question that makes the rest of it meaningful.

Markdown, deliberately: it is generated inside Snowflake by the governed role, and rendering a PDF
would need a package the Snowflake Python environment does not carry, which would mean composing
the evidence outside the perimeter that produced it.
"""

from __future__ import annotations

from snowflake.snowpark import Session

from warrant.authority.replay import replay, summarise
from warrant.authority.tiers import Tier

TIER_LABELS = {
    int(Tier.READ_ONLY): "L0 read-only",
    int(Tier.DRAFT): "L1 draft",
    int(Tier.LOW_RISK_ACT): "L2 acts unsupervised",
    int(Tier.APPROVAL_REQUIRED): "L3 needs approval",
    int(Tier.FORBIDDEN): "L4 never permitted",
}

STAMP = """
SELECT TO_VARCHAR(CURRENT_TIMESTAMP(), 'YYYY-MM-DD HH24:MI:SS') AS at,
       CURRENT_ACCOUNT() AS account,
       CURRENT_ROLE()    AS role
"""

DECISION_COUNTS = """
SELECT phase, outcome, COUNT(*) AS n
  FROM WARRANT.AUDIT.ACTION_AUDIT
 GROUP BY phase, outcome
 ORDER BY phase, outcome
"""

REFUSALS = """
SELECT TO_VARCHAR(ts, 'YYYY-MM-DD HH24:MI') AS at,
       COALESCE(action_type, 'n/a')          AS action_type,
       COALESCE(tier, 4)                     AS tier,
       rationale
  FROM WARRANT.CORE.REFUSALS
 ORDER BY ts DESC
"""

EXECUTED = """
SELECT p.action_id,
       p.action_type,
       p.effective_tier,
       p.decision,
       COALESCE(p.decided_by, 'agent')        AS decided_by,
       COALESCE(p.binding_object, 'n/a')      AS binding_object,
       p.tier_rationale,
       f.severity,
       f.root_cause,
       ARRAY_TO_STRING(f.grounded_in, ', ')   AS grounded_in,
       f.model
  FROM WARRANT.CORE.PENDING_ACTIONS p
  JOIN WARRANT.CORE.FINDINGS f ON f.finding_id = p.finding_id
 WHERE p.execution_result = 'executed'
 ORDER BY p.effective_tier DESC, p.proposed_at
"""

CORPUS = """
SELECT doc_id, title, revision, TO_VARCHAR(effective_on) AS effective_on, owner, page_count
  FROM WARRANT.DATA.RUNBOOKS
 ORDER BY doc_id
"""


def audit_pack(session: Session) -> tuple[str, str]:
    """Compose the evidence pack.

    Args:
        session: An active Snowpark session.

    Returns:
        A ``(filename, markdown)`` pair. The filename carries the generation timestamp so a pack is
        never silently overwritten by a later one — an evidence file that can be replaced in place
        is not evidence.
    """
    stamp = session.sql(STAMP).collect()[0]
    generated_at, account, role = stamp["AT"], stamp["ACCOUNT"], stamp["ROLE"]
    replayed = replay(session)
    counts = summarise(replayed)

    out: list[str] = [
        "# Warrant — decision evidence pack",
        "",
        f"- **Generated** {generated_at}",
        f"- **Account** `{account}`",
        f"- **Composed by role** `{role}` — the same role the agent acts under, so this pack is "
        "subject to the same masking policies the agent is",
        "",
        "Assembled from the append-only decision record. No part of the structure below is "
        "model-generated; where model text appears it is quoted and labelled.",
        "",
        "## 1. Authority model in force",
        "",
        "An action's tier is resolved from the `SENSITIVITY` object tag on every table it touches, "
        "at proposal time **and again at execution time**. The most demanding object binds. "
        "Untagged is treated as unclassified, never as cleared.",
        "",
        "| Tier | Meaning |",
        "|---|---|",
    ]
    out += [f"| {value} | {label} |" for value, label in sorted(TIER_LABELS.items())]

    out += ["", "## 2. Declined actions", ""]
    refusals = session.sql(REFUSALS).collect()
    if not refusals:
        out += [
            "No actions were declined in the period covered. This is reported first regardless of "
            "whether it is empty, because the absence of refusals is itself a finding worth "
            "stating rather than an omission.",
        ]
    else:
        out += [
            f"**{len(refusals)} action(s) declined.** Listed before the completed work "
            "deliberately: the declines are the control operating.",
            "",
        ]
        for row in refusals:
            out += [
                f"### {row['ACTION_TYPE']} — declined {row['AT']}",
                "",
                f"- **Tier applied** {TIER_LABELS.get(int(row['TIER']), row['TIER'])}",
                f"- **Reason recorded** {row['RATIONALE']}",
                "",
            ]

    out += ["", "## 3. Completed actions, with the authority each ran under", ""]
    executed = session.sql(EXECUTED).collect()
    if not executed:
        out += ["No actions were executed in the period covered.", ""]
    for row in executed:
        out += [
            f"### {row['ACTION_TYPE']} — `{row['ACTION_ID']}`",
            "",
            f"- **Tier** {TIER_LABELS.get(int(row['EFFECTIVE_TIER']), row['EFFECTIVE_TIER'])}",
            f"- **Decision** {row['DECISION']} by `{row['DECIDED_BY']}`",
            f"- **Binding object** `{row['BINDING_OBJECT']}`",
            f"- **Why that tier** {row['TIER_RATIONALE']}",
            f"- **Grounded in** {row['GROUNDED_IN'] or 'no procedure retrieved'}",
            f"- **Severity** {row['SEVERITY']}",
            "",
            f"> Model-generated ({row['MODEL']}): {row['ROOT_CAUSE']}",
            "",
        ]

    out += [
        "",
        "## 4. Re-resolution against the classifications in force today",
        "",
        "Every recorded action re-resolved with the current tags. A divergence means the "
        "governance posture changed after the decision was taken.",
        "",
        f"- Actions replayed: **{counts['replayed']}**",
        f"- Would be decided differently today: **{counts['diverged']}**",
        f"- Would now be refused outright: **{counts['now_forbidden']}**",
        f"- **Executed work today's policy would no longer permit unsupervised: "
        f"{counts['needs_attention']}**",
        "",
    ]
    attention = [r for r in replayed if r.needs_attention]
    if attention:
        out += [
            "The final count is the only one that cannot be corrected going forward, because the "
            "work has already happened. Each is listed below.",
            "",
        ]
        for r in attention:
            out += [
                f"- `{r.action_id}` **{r.action_type}** ran at "
                f"{TIER_LABELS.get(int(r.tier_then or 0))} and would now resolve to "
                f"{TIER_LABELS.get(int(r.tier_now))}. {r.rationale_now}",
            ]
        out += [""]
    else:
        out += ["Nothing executed under a policy that has since tightened.", ""]

    out += [
        "",
        "## 5. Procedures the decisions were grounded in",
        "",
        "| Doc | Title | Rev | Effective | Owner | Pages |",
        "|---|---|---|---|---|---|",
    ]
    out += [
        f"| {r['DOC_ID']} | {r['TITLE']} | {r['REVISION']} | {r['EFFECTIVE_ON']} "
        f"| {r['OWNER']} | {r['PAGE_COUNT']} |"
        for r in session.sql(CORPUS).collect()
    ]

    out += [
        "",
        "",
        "## 6. Decision record totals",
        "",
        "| Phase | Outcome | Rows |",
        "|---|---|---|",
    ]
    out += [
        f"| {r['PHASE']} | {r['OUTCOME']} | {r['N']} |"
        for r in session.sql(DECISION_COUNTS).collect()
    ]
    out += [
        "",
        "",
        "`WARRANT.AUDIT.ACTION_AUDIT` is append-only and is deliberately spared by "
        "`sql/90_reset.sql`. A decision log that can be tidied up is not a decision log.",
        "",
    ]

    filename = f"warrant-audit-pack-{generated_at.replace(':', '').replace(' ', '-')}.md"
    return filename, "\n".join(out)
