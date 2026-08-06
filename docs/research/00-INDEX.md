# Snowflake CoCo CLI Hackathon 2026 — planning & research

> ⚠️ **This repository is private and must stay private.** It contains competitor analysis and
> internal notes that do not belong in the public submission repo.
> The submission repo is separate: **https://github.com/tsathya98/warrant**

## Picking up on a new machine

```bash
git clone https://github.com/tsathya98/coco-hackathon-planning.git
git clone https://github.com/tsathya98/warrant.git
```

Read **[`00-STATUS.md`](00-STATUS.md)** first — it carries the current state, urgent
items, and the ordered next-actions checklist.

## Docs

Research notes (this folder, `docs/research/`):

| Doc | Contents |
|---|---|
| **[00-STATUS](00-STATUS.md)** | Current state, urgent items, ordered checklist. **Start here.** |
| **[08-master-brief](08-master-brief.md)** | Consolidated: what/how/where to build, what to submit, judging, cost. **The brief.** |
| [01-hackathon-rules](01-hackathon-rules.md) | T&C verified — artifacts, deadlines, mandatory tech, IP, eligibility |
| [02-coco-cli-reference](02-coco-cli-reference.md) | What CoCo CLI is, install, auth, commands, pricing, gotchas |
| [03-problem-statement-decision](03-problem-statement-decision.md) | Why PS1, why not the others, clean-room constraint |
| [04-snowflake-setup](04-snowflake-setup.md) | Account setup, services, the confirmed architecture |
| [05-datasets](05-datasets.md) | Free/synthetic data, quickstart schemas, Marketplace listings |
| [06-competitive-landscape](06-competitive-landscape.md) | Competitor repos, judging intel, deck template, prior winners |
| [07-notifications](07-notifications.md) | Why not IFTTT; Slack/Telegram/email channel comparison |

Project docs (`docs/`):

| Doc | Contents |
|---|---|
| [agent_onboarding_prompt](../agent_onboarding_prompt.md) | Paste-in prompt to bring a fresh agent session up to speed |
| [notes_from_video_sessions](../notes_from_video_sessions.md) | Organizer quotes from the official sessions; **secondary source** |
| [architecture](../architecture.md) | Why everything runs inside Snowflake *(stub)* |
| [judges_walkthrough](../judges_walkthrough.md) | Reproduction steps for judges *(aspirational — `scripts/` not built yet)* |
| [data_licences](../data_licences.md) | Data provenance statement for submission |

## The 60-second version

Building **PS1 — Intelligent Workflow Automation Agent** as **Warrant**: a governed autonomous
operations agent on Snowflake. An action's authority tier is derived from **Snowflake object tags
on the data it touches**, not a hardcoded rules list — so governance policy and agent behaviour
stay in sync by construction. Domain is generic supply-chain / manufacturing ops on synthetic data.

Must be built **with CoCo CLI**, in **Python**, **on Snowflake** — all three are explicit T&C
scoring criteria.

## Hard constraints

1. **Clean-room build.** No employer code, data, or business logic. Ideas and professional
   judgment carry over; source does not.
2. **Python/Java/Scala only** — scored criterion, easy to miss.
3. **Synthetic data only.**
4. **Repo is statically analysed** for code quality, security, testing — organizer stated this
   explicitly. Tests and CI are not optional.

## Open questions only the dashboard can answer

- The real deadline (T&C says Aug 2; event page says Aug 6)
- Exact required submission fields — a video and deployment link both appear required
- Whether CoCo CLI runs on a standard trial, or needs the separate CoCo trial

## Deliverables

| Artifact | Status |
|---|---|
| GitHub repo + clear documentation | **REQUIRED** — [warrant](https://github.com/tsathya98/warrant) |
| Presentation deck (PPT) | **REQUIRED** — template structure in `06-competitive-landscape` |
| Deployment link | Appears required (portal field) |
| Demo video | Appears required (portal field); length cap unverified |
| Live demo at Grand Finale | Sept 1–4 — pre-recorded explicitly discouraged |
