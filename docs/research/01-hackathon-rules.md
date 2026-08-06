# Hackathon rules — verified reference

Authoritative source: **Terms & Conditions**
https://docs.google.com/document/d/e/2PACX-1vQ0RB2XJB3MuE_dZbroHkqlicLD2O_Y3FaGgj03JwkC6_dhUfRqi4az-Teb62S43km27dg9YlMarOD6/pub

Secondary: https://hack2skill.com/event/cococlihack/
Blocked (HTTP 403, could not verify): `coco-cli.yourstory.com`, the YourStory article.

> Where the T&C and the event page conflict, **the T&C governs**.

---

## Required submission artifacts

T&C §4.1 defines an "Entry" as:
> "(a) a complete profile, including name, email address, phone number, and country of the
> Participant and, for Team Entries, each Team member; (b) the Idea; (c) the Prototype, if
> applicable; and (d) presentation materials, link to source code (Github or other codeshare
> platforms) or source code files, if applicable."

T&C §4.5:
- **(a)** "Participants are required to submit a presentation deck (PPT or similar format)"
- **(b)** "Participants must provide complete access to the full source code of their Prototype
  via a GitHub repository (or similar code-sharing platform) for evaluation purposes. The
  repository should be accessible to the judges and include clear documentation for review."
- **(c)** Live demonstration at the Finals. **"Pre-recorded demos may not be accepted unless
  explicitly approved by the Sponsor."**
- **(d)** Participant is responsible for their own connectivity and technical setup.

| Artifact | Status |
|---|---|
| GitHub repo + full source | **REQUIRED** |
| Presentation deck (PPT or similar) | **REQUIRED** |
| "Clear documentation" in repo | **REQUIRED** |
| Working prototype | Required ("if applicable" hedge) |
| Profile data for every team member | **REQUIRED** |
| **Demo video** | **NOT required** — and pre-recorded demos are discouraged |
| Deployed / live public URL | **NOT SPECIFIED** — never mentioned anywhere |
| Architecture diagram | NOT SPECIFIED |
| Deck page limit / template | NOT SPECIFIED |

## Where to submit

T&C literally contains an unfilled placeholder: *"visit `<Microsite link to be added>`"*.
**Inference (high confidence):** the hack2skill participant dashboard. Not Devpost.
Confirm via the dashboard or support.

## Will judges run the code?

Verbatim: *"...for evaluation purposes. The repository should be accessible to the judges
and include clear documentation for **review**."*

The document says **review** — never *run*, *execute*, *build*, *install*, or *reproduce*.
There is no reproducibility clause, no README mandate, no setup-instructions requirement.

**Assessment:** screening (Aug 3–16) and final evaluation (Aug 17–22) happen without the team
present. The only guaranteed live proof is the **Grand Finale demo**. Realistic model is
**deck + code review**, with working-software proof deferred to the live finale.

**Implication:** optimize the repo to be *legible when skimmed*, and make sure the prototype
runs reliably **on your own machine** in September. Do not assume a judge will clone and debug.

## Mandatory technology (T&C §9 — these ARE the scoring criteria)

> "(1) Participant or Team defines an Idea and, if selected, creates a Prototype responsive to
> a designated theme, **including use of Cortex Code CLI**; (2) Participant or Team utilizes
> **programming languages Python, Java, and/or Scala**; (3) **use of Snowflake's platform by
> Participant or Team is required**; and (4) Participants or Teams can build any type of
> Prototype, but **special consideration will be given to Entries that incorporate Snowpark,
> Worksheets, Streamlit, and/or Snowflake Marketplace**"

- CoCo CLI: **mandatory**
- Snowflake platform: **mandatory**
- Python / Java / Scala: **scored criterion** — easy to miss
- Bonus surface: Snowpark, Worksheets, Streamlit, Snowflake Marketplace
- External services (AWS, Postgres, OpenAI/Anthropic APIs): **no prohibition**, but strategically
  unwise as a *substitute* for Snowflake-native features given criteria (3) and (4)

## Two conflicting rubrics

| Source | Rubric |
|---|---|
| hack2skill page | Technical Execution 40% · Real-World Relevance 30% · Solution Completeness 30% |
| **T&C §9** | The four unweighted criteria above. **The 40/30/30 split does not appear in the T&C at all.** |

No sub-rubric, no per-criterion points, no tie-breaker published. Treat both as live: satisfy
the T&C's hard requirements *and* optimize for the 40/30/30 weighting.

**Judges:** "employees of the Sponsor, employees of the Administrator, and/or external industry
specialists." Decisions are "final, non-appealable, binding."

## Round structure

1. Initial Screening — Aug 3–16, 2026
2. Final Evaluation — Aug 17–22, 2026
3. Finalists announced — Aug 24, 2026
4. **Induction — Aug 26, 2026** ("presentation guidelines, judging expectations, logistics")
5. **Grand Finale — Sept 1–4, 2026** — virtual, live presentation before the judging panel

Finale presentation length: **NOT SPECIFIED** — issued at the Aug 26 induction.

## Pre-existing code

- **No "must be created during the contest" clause exists.** Searched explicitly.
- No repo-creation-date rule. No prohibition on prior work.
- Originality warranty is satisfied by your own prior work ("original to the Participant").
- **BUT §4.4(e) blocks proprietary/employer code.** See `00-STATUS.md` §2 — this is the binding
  constraint here.
- Open-source libraries permitted (§4.4(c)) if their terms don't "restrict Sponsor's ability to
  evaluate, display, promote, or otherwise use the Entry" — avoid strong copyleft.

## IP

You keep ownership:
> "any applicable intellectual property rights to an Entry will be owned by and remain with the
> applicable Participant or Team members."

But you grant:
> "a royalty-free, non-exclusive, worldwide, **irrevocable**, sublicensable license to use, host,
> reproduce, modify, distribute, display, perform, create derivative works from, and otherwise
> exploit the Entry"

Governing law: **Delaware**.

## Team rules

- 1–4 members, individual or team
- **One entry per person** — cannot be on multiple teams
- Multiple submissions: only the final one counts (resubmission tolerated)
- A Team Lead submits on behalf of the team
- Changing team composition after registration: NOT SPECIFIED

## Data rules

- Participant is responsible for having rights to all data used
- Public datasets and Sponsor-recommended APIs permitted
- Non-Snowflake-identified datasets require a license link or copy
- §4.4(e) prohibits proprietary/confidential datasets
- **Synthetic vs real: NOT SPECIFIED. PII: NOT SPECIFIED beyond generic "data privacy laws."
  No healthcare/HIPAA carve-out exists.**
- → Given the Takeda context: **synthetic data only, no exceptions.**

## Disqualification grounds

- Tampering with the entry process or contest operation
- Robotic/macro/automated entry methods
- Violating the Official Rules
- "unethical, inappropriate or disruptive action or conduct"
- Plagiarism / unauthorized proprietary code or data (§4.4(e))
- Sponsor may cancel, terminate, modify, or suspend the contest at any time

## Eligibility

Legal residents of India, ASEAN (Indonesia, Philippines, Malaysia, Singapore, Thailand, Vietnam),
ANZ, Republic of Korea, Japan, Sri Lanka, Bangladesh, Nepal. Age 18+.

Excluded: Snowflake employees, Administrator employees, judges, employees of Snowflake portfolio
companies, and their immediate family/household members.

*(Note: the Eventopia listing's "college students" eligibility claim is wrong — contradicted by
both primary sources.)*

## Prizes

$10,000 pool — Winner $4,300 · 1st RU $2,200 · 2nd RU $1,590 · up to 5 consolation @ $530.
Subject to eligibility verification, identity verification and compliance checks. Winners bear
all personal taxes, duties, and FX fees.
