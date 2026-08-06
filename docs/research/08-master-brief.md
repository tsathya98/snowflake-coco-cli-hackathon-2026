# Master brief — everything about this hackathon

_Compiled 2026-08-04. Primary sources re-verified on this date unless marked otherwise._

**Purpose:** the single consolidated answer to *what to build, how, where, what to submit, what's
expected, and what it costs.* Where a topic has a dedicated deep-dive doc, this brief states the
conclusion and links out rather than duplicating.

**Source hierarchy** — used consistently below:

| Tier | Source | Weight |
|---|---|---|
| **P1** | [Terms & Conditions](https://docs.google.com/document/d/e/2PACX-1vQ0RB2XJB3MuE_dZbroHkqlicLD2O_Y3FaGgj03JwkC6_dhUfRqi4az-Teb62S43km27dg9YlMarOD6/pub) | **Governs.** Contractual. |
| **P1** | `docs/submission_template/*.pptx` (the actual file, in-repo) | Official artifact |
| **P2** | [hack2skill event page](https://hack2skill.com/event/cococlihack/) | Marketing; conflicts with P1 |
| **P3** | Organizer statements in the video sessions | Reveals scoring intent, not binding |
| **P4** | Competitor repos, community posts | Inference only |

`coco-cli.yourstory.com` returns **HTTP 403** and could not be read.

---

## 1. 🔴 The one genuinely urgent thing: the deadline is contradictory

**Today is Aug 4, 2026 — between the two candidate deadlines.**

| Source | What it says |
|---|---|
| **T&C (P1)** | *"The 'Submission Period' begins on June 15, 2026 at 12:00 AM IST and ends on **August 02, 2026 at 11:59 PM IST**."* And critically: *"During the Submission Period, eligible individuals may register as Registrants **and Participants or Teams may submit an Idea and Prototype**"* — so Aug 2 covers submission, not just registration. Judging Period then *"begins on August 03, 2026"*. |
| **Event page (P2)** | Registration Closes **2 August** · Prototype Submissions Close **6 August** · Prototype Evaluations **7–22 August** |

The tempting reconciliation — "Aug 2 is registration, Aug 6 is the prototype" — **is refuted by the
T&C's own wording**, which puts prototype submission inside the Aug 2 window. The event page's
separate Aug 6 date and Aug 7 evaluation start are genuinely inconsistent with the T&C's Aug 3
judging start. No published extension notice was found.

**This cannot be resolved from public sources.** Do all three, now:
1. Open the submission form on the dashboard — if it accepts a submission, that settles it empirically:
   `https://hack2skill.com/event/cococlihack/dashboard/interactions`
2. Email `support+cococlihack@hack2skill.com` (9 AM–5 PM IST)
3. Ask on Discord: `https://discord.gg/KMKtbxBJpW`

**Regardless of the answer — submit something immediately.** Hack2skill's participant guide states
you may re-upload and *"the latest submission before the deadline is recorded"*. A rough draft
uploaded now costs nothing, protects against portal failure, and reveals the true required-field list.

### Full official timeline (event page, P2)

| Date (2026) | Milestone |
|---|---|
| Jun 15 | Registration opens · Contest Period begins (T&C) |
| Jun 25 | Problem Statement Explainer session |
| Jul 2 | Workshop 1 — CoCo CLI Starter |
| Jul 9 | Workshop 2 — CoCo CLI hands-on *(the public recording is dated Jul 17)* |
| Jul 13 | **Prototype submissions open** |
| Jul 23 | AMA session |
| **Aug 2** | Registration closes · **T&C: Submission Period ends, 11:59 PM IST** |
| **Aug 6** | **Event page: prototype submissions close** ⚠️ conflict |
| Aug 3–22 | T&C Judging Period · *event page says evaluations Aug 7–22* |
| Aug 24 | Finalists announced (*"on or around"*) |
| Aug 26 | **Induction session** — presentation guidelines and judging expectations are issued here |
| Sep 1–4 | **Grand Finale** — virtual, **live** demo to the judging panel |
| Sep 4 | Contest Period ends, 11:59 PM IST |

Timezone is **IST** wherever the T&C specifies one; the event page specifies none.

### There is a second edition running ~6 weeks behind, and it is still open

`hack2skill.com/event/cococlihack-gccedition/` — the **GCC Edition**: registrations 15 Jul → **1 Sep
2026**, prototype submissions close **1 Sep 2026**, shortlist 23 Sep, **Grand Finale 1–4 Oct 2026**.
Same "Age 18+" and "1–4 members" framing; **different problem statements** and a more explicit
four-axis rubric.

Two reasons this matters:
1. **It is a fallback if the APJ deadline has genuinely passed** — but only if you're eligible. GCC =
   Gulf Cooperation Council; its residency requirements were **not verified** and almost certainly
   differ from the APJ list in §3. **Check eligibility before counting on it.**
2. **It is the most likely source of date errors** in any notes — blending the two editions' schedules
   produces plausible-looking but wrong dates. Every date in this brief is the **main/APJ** edition.

---

## 2. Does it cost money? No — and this is now contractually confirmed

**Verbatim from the T&C (P1):**

> "NO PURCHASE OR PAYMENT NECESSARY."

> "Sponsor will provide a free Trial Account to Registrants for purposes of the Contest" with
> "a **$400 USD credit**."

Event page (P2), verbatim: *"No, participation is completely free."*

So: **no registration fee, and the $400 Snowflake trial credit is a sponsor commitment**, not merely
the generic public trial. That is a stronger guarantee than this repo previously assumed.

### Snowflake runs TWO different trials — do not confuse them

This resolves the $400-vs-$40 ambiguity that ran through earlier notes. Verbatim from
[snowflake.com/en/snowflake-trial](https://www.snowflake.com/en/snowflake-trial/):

> "Get started your way with two Snowflake trial options: Unlock the full Snowflake AI Data Cloud
> with **$400 in free credits**, or try Cortex Code CLI subscription with **$40 in free inferences**.
> Both are built for a 30-day experience."

| | **General AI Data Cloud trial** | **CoCo/Cortex Code CLI trial** |
|---|---|---|
| Signup | `signup.snowflake.com` | `signup.snowflake.com/cortex-code` |
| Allowance | **$400 in credits** | **$40 in inferences** |
| Credit card | Not required | **Required** |
| At expiry | Account **suspended** | 🚨 **Auto-converts to ~$20/month** |
| Covers platform compute/storage? | Yes (from the $400) | **No** — billed separately |

→ **Use the $400 path.** The T&C's sponsor-provided Trial Account matches it ($400, no card).

**Duration is a ceiling, not a guarantee:** *"The trial continues for 30 days (from the sign-up date)
**or until you've depleted your free usage balance, whichever occurs first**."* Unused balance
expires. A team that burns $400 in week two loses the account in week two.

**CoCo itself is metered:** *"CoCo is billed based on token consumption."* There is no free unlimited
tier. Precision matters here — the standalone CoCo signup draws down a *bundled fixed allowance*,
whereas an existing on-demand account is *true per-token pay-as-you-go*. Admins can cap it per user
per surface over a rolling 24-hour window (`CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER`).

⚠️ **Source-strength caveat:** "30 days" is confirmed in both docs and marketing, but **`$40`, `$20`
and `$400` appear only on snowflake.com marketing/product pages — `docs.snowflake.com` contains no
dollar figures at all**, saying merely "a fixed amount of CoCo CLI usage."

### But there are real ways to spend money by accident

| Risk | Detail | Mitigation |
|---|---|---|
| 🚨 **The CoCo-CLI-specific trial auto-converts to PAID** | `signup.snowflake.com/cortex-code` gives $40 of inference for 30 days and then **bills you** unless cancelled. Trial accounts can't be cancelled in the UI — you must contact support. | Prefer the standard $400 trial. If you must use the CoCo trial, **diarise the cancellation date**. |
| Idle warehouse burn | An XS warehouse running 24/7 for 30 days consumes ~720 credits; $400 ≈ 130–200 credits. | X-Small everywhere, `AUTO_SUSPEND = 60`. |
| Streamlit-in-Snowflake tab left open | The WebSocket keeps the warehouse hot ~15 min after last activity, and **mouse movement counts as activity**. | Set `streamlitSleepTimeoutMinutes`. |
| Resource monitors don't cover AI | Verbatim: *"You can't use a resource monitor to track spending associated with serverless features and AI services."* | Use **Budgets** too — but they only notify, never suspend. Watch Admin » Billing. |
| Cortex AI credits | Billed in a separate **AI Credit** currency at ~$2.00–2.20/credit. | Trial accounts without a payment method are capped ~10 credits/day of Cortex AI. |

Full detail: [`04-snowflake-setup.md`](04-snowflake-setup.md).

---

## 3. Eligibility

**Age (T&C, P1):** *"eighteen (18) years of age or older as of the beginning of the Submission
Period."* — The "20+" figure in earlier drafts of this repo was wrong.

**Countries (T&C, P1, verbatim):** *"legal residents of (i) India; (ii) member states of the
Association of Southeast Asian Nations (ASEAN) (specifically Indonesia, Philippines, Malaysia,
Singapore, Thailand, Vietnam); (iii) Australia and New Zealand (ANZ); (iv) the Republic of Korea;
(v) Japan, (vi) Sri Lanka, (vii) Bangladesh, and (viii) Nepal."*

There is no catch-all "other APJ regions" category. Cross-border teams are fine provided every
member resides in an eligible country.

**Teams:** 1–4 members · one entry per person, cannot join multiple teams · a Team Lead submits on
behalf of the team · only the final submission counts.

**Excluded:** Snowflake employees, Administrator (YourStory) employees, judges, employees of
Snowflake portfolio companies, and their immediate family/household members.

Note there is a **separate GCC edition** (`hack2skill.com/event/cococlihack-gccedition/`) with
different problem statements and a more explicit four-axis rubric. We are on **Standard/APJ**.

---

## 4. What to develop

Pick **one** of four tracks. Full per-track organizer guidance, including verbatim "strong vs weak"
quotes, is in [`notes_from_video_sessions.md` §3](../notes_from_video_sessions.md).

| # | Track | One-line test of success | Fatal weak version |
|---|---|---|---|
| **1** | **Intelligent Workflow Automation Agent** ← *our track* | Does it **take action**, not just surface insight? | A dashboard with alerts; a chatbot over a database |
| 2 | Unstructured Data Intelligence System | Does it *understand* how documents relate, not just retrieve? | "A basic RAG demo" |
| 3 | AI-Native Data Application | Would someone want to use it tomorrow? | A technical proof-of-concept |
| 4 | Domain-Specific AI Copilot | Does it behave like a *junior expert* in one field? | A generic LLM wrapper with industry branding |

**Official wording of our track, verbatim from the event page (P1-grade, exact):**

> "Build an AI-driven system that can understand enterprise data and autonomously execute multi-step
> workflows **using Snowflake CoCo CLI**."

All four problem statements carry that same "…using Snowflake CoCo CLI" suffix — which is the event
page's own evidence that the tool is central, independent of the T&C's mandate. The exact wording of
tracks 2–4 was **not** captured verbatim; the "strong vs weak" framing for every track comes from the
video session (P3), not from published text.

Our choice and the reasoning against the other three:
[`03-problem-statement-decision.md`](03-problem-statement-decision.md).

---

## 5. How to develop — the mandatory stack

**T&C §9 — these four clauses *are* the scoring criteria:**

1. Create a Prototype responsive to a designated theme, **including use of Cortex Code CLI** → CoCo
   CLI is **mandatory**
2. **Python, Java, and/or Scala** → a scored criterion, and the easiest one to fail by accident
   (not TypeScript, not Go)
3. **Use of Snowflake's platform is required**
4. **"Special consideration"** for **Snowpark, Worksheets, Streamlit, and/or Snowflake Marketplace**

**Beyond the T&C, the organizers stated on camera (P3):**

> "The expectation is for you to utilise as many Snowflake services as possible and **you will be
> positively rewarded for it** while we are evaluating the submissions."

> "…your evaluation is going to be very Snowflake-product-heavy… it is mandatory to include
> Snowflake as solution."

→ **Breadth of native Snowflake usage is stated policy, and the portal has a dedicated field where
you declare it.** External services aren't prohibited, but using them as a *substitute* for a
Snowflake-native capability works against criteria (3) and (4).

Naming: the product launched as **Cortex Code** (Nov 2025), the CLI hit GA (Feb 2026), and was
renamed **CoCo** (Jun 2, 2026). The T&C still says "Cortex Code CLI", the docs URLs still say
`cortex-code`, and **the binary is still `cortex`**. Same product.

Install, auth, command surface, skills, MCP, pricing and security gotchas:
[`02-coco-cli-reference.md`](02-coco-cli-reference.md).

---

## 6. Where to develop — and why the trial dictates the architecture

**Account:** standard trial (`signup.snowflake.com`), **Enterprise** edition, **AWS us-west-2**.

Enterprise is needed for row-access/masking policies and object tagging — which is what *our*
governance story is built on. **It is not a CoCo requirement:** the docs state no minimum edition and
publish no supported cloud/region list. CoCo CLI is **GA — not preview — since Feb 2, 2026** (Snowsight
surface GA Mar 9, 2026), "available to all Commercial (non-Gov, VPS, Sovereign) accounts with
cross-region inference enabled."

us-west-2 is chosen because it is the only region with the full Cortex surface; **Mumbai and Singapore
lack Cortex Analyst and Cortex AI functions**. Viable APJ alternatives are Tokyo and Sydney. You
cannot move an existing account between regions, so treat the choice as fixed at signup.

**Cross-region inference** is `ACCOUNTADMIN`-only:
`ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';`
Two refinements over earlier notes:
- It may already be set — *"For new accounts created in new organizations within commercial regions
  after March 9, 2026, ANY_REGION is the default."* Check before assuming you must run it.
- **Set it to `ANY_REGION` or `AWS_US`, not `AWS_APJ`.** `AWS_APJ` is documented as possibly limited
  to Claude Sonnet 4.0, while `AWS_US` is *"recommended for the best experience with Claude Opus 4.x"*.
  So `auto` on an APJ-scoped account will **not** necessarily give you a top-tier model.

### ⚠️ Windows: the prerequisites and the installer disagree

The native PowerShell installer is real (`irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex`,
"Windows Native on Intel" is a supported platform), **but the documented prerequisites also require
"local terminal access to the bash, zsh, or fish shell."** Those two statements are in tension. Budget
time for this, and be ready to run the interactive session under **WSL or Git Bash** even though the
installer targets PowerShell. Also required: **Snowflake CLI (`snow`) installed** — CoCo reads the same
`~/.snowflake/connections.toml` — plus the `SNOWFLAKE.CORTEX_USER` role, which is granted via `PUBLIC`
by default. (`CORTEX_AGENT_USER` is *not* — it must be granted explicitly.)

**Three trial limits that shaped the whole design:**

1. **External network access is restricted** on trial accounts → Snowflake cannot reliably call out to
   your own endpoint. ⚠️ Two official pages disagree on *how* restricted: one says external access is
   simply not enabled for trials, another says it is "limited to 10 credits daily until you add
   payment." **Unresolved — test it rather than trusting either.**
2. **Snowpark Container Services is unavailable** on trial → no containers, no GPU
3. **Snowflake cannot receive inbound webhooks**, and only **5 outbound webhook providers** are
   allowlisted (Slack, Teams, PagerDuty, Jira, ServiceNow). Email works but **only to verified users
   in the same account**.

**This is good news strategically:** it forces the agent to live *inside* Snowflake on native
primitives, which is exactly what the T&C rewards. It also means human-in-the-loop approval must be
**Streamlit console → table → stream → triggered task**, since Slack interactive buttons are
impossible without a public endpoint.

**Deployment for the "live link" field:** Streamlit in Snowflake is the right answer (governed
identity, zero infra) but is **not publicly viewable** — viewers need an account in yours. Snowflake
CoWork (`ai.snowflake.com`) is a free second demo surface. If a genuinely public clickable URL is
needed, Streamlit Community Cloud is the only free option — note the leading competitor solved this
by shipping a **no-login web prototype as the judge's entry point**.

Detail: [`04-snowflake-setup.md`](04-snowflake-setup.md) · [`07-notifications.md`](07-notifications.md).

---

## 7. What and where to submit

**Where:** the Hack2skill participant dashboard. (The T&C contains an unfilled placeholder —
*"visit `<Microsite link to be added>`"* — so this is inference, but high confidence. Not Devpost.)

**The T&C (P1) §4.5 requires:** a presentation deck (PPT or similar) · complete access to full source
code via GitHub with *"clear documentation"* · a **live demonstration at the Finals**, where
*"pre-recorded demos may not be accepted unless explicitly approved by the Sponsor"* · your own
connectivity.

**The portal (P3, organizer verbatim) collects six things:**

> "…one is your **GitHub and your deployment link**… The other is where you have to add your **video
> link**. You have to add your **presentation**… And which is the **problem statement**? … **What all
> are the services that you have included specifically that you need to mention right there.**"

⚠️ **The T&C and the portal disagree about the video.** The T&C never requires one and discourages
pre-recorded demos; the portal has a video field, and T&C §7.2 grants Snowflake rights to publish the
*"video URL"* — which confirms a video is part of an Entry. **Treat both as required.** The length cap
is **unverified** — the "3 minutes" figure came from a different Hack2skill event; on *this* event one
competitor logged 4:40 as compliant. Confirm on the dashboard.

### The official deck template — verified from the actual file in this repo

`docs/submission_template/Prototype Submission Template _ Cortex Code CLI Hackathon.pptx`, 6 slides.
Slide 1 cover: **Team Name · Problem Statement · Team Leader Name · Team Size**. Slide 2 mandates
three sections, verbatim:

1. **Problem Brief** — "What real business problem does this solve? / Who is the target
   user/persona? / What is the current pain point and how does this improve it? / Industry/domain
   context"
2. **Architecture Diagram** — "System design showing data flow / **Which Cortex Code CLI skills are
   used and how they connect** / Data sources (structured/unstructured) / How modular components plug
   together"
3. **Impact Statement** — "**Measurable** outcomes (time saved, accuracy improvement, etc.) /
   Scalability potential / How this extends beyond the demo"

Slides 3–4 are blank working slides, slide 5 is "Additional Slide", slide 6 blank.

> **Two scored expectations hide here.** The architecture slide *explicitly asks which CoCo Agent
> Skills you used* — so ship named skills. And the Impact Statement demands **measurable** outcomes —
> so lead with a number, even a clearly-labelled simulated one.

---

## 8. What's expected — how you'll actually be judged

**Two rubrics are live simultaneously. Satisfy both.**

| Source | Rubric |
|---|---|
| Event page + sessions (P2/P3) | **Technical Execution 40% · Real-World Relevance 30% · Solution Completeness 30%** |
| **T&C §9 (P1)** | The four unweighted criteria in §5 above. **The 40/30/30 split appears nowhere in the T&C.** |

Sub-criteria found identically worded in two independent competitor repos (P4 — probably from the
dashboard, unverified): Technical Execution → multi-step orchestration, error handling, decision
branches, strong use of CoCo CLI + Agent Skills. Real-World Relevance → defined business problem,
realistic context, **measurable impact**. Solution Completeness → end-to-end ingestion → reasoning →
actionable output with **minimal manual intervention**.

Technical Execution 40% was described on camera as: does it logically work, is it architecturally
sound, **is anything hard-coded versus genuinely fetching from an API**, how much works in a real
scenario.

### 🔴 Your repo will be statically analysed — this is the least-known rule

Organizer, verbatim (P3):

> "…**the GitHub repository that you'll be submitting will also be statically analysed for its code
> quality, security, efficiency, testing and accessibility.**"

The stated rationale is that CoCo CLI makes generating plausible code trivial, so functionality alone
no longer discriminates. **Tests, linting, CI, and zero committed secrets are effectively scored line
items** — not hygiene.

**Judges (T&C):** *"employees of the Sponsor, employees of the Administrator, and/or external
industry specialists."* Decisions are *"final, non-appealable, binding."* No named panel is published.
Note the T&C says the repo is for *"review"* — never *run*, *execute*, or *reproduce*. Screening and
evaluation happen without you present; the only guaranteed live proof is the **Sept 1–4 finale**.
→ Optimise the repo to be **legible when skimmed**, and make sure the demo runs reliably on **your own
machine** in September.

Competitor intelligence and the two things the leaders both did:
[`06-competitive-landscape.md`](06-competitive-landscape.md).

---

## 9. Prizes — and the "$10,000 pool" is not what the T&C actually says

**T&C §10.1, verbatim (P1):**

> "1st Prize — USD 4,300 per winning Entry · 2nd Prize — USD 2,200 per winning Entry · 3rd Prize —
> USD 1,590 per winning Entry · Consolation Prizes — USD 530 per winning Entry, **up to five (5)
> winners**"

Those line items sum to a **maximum of $10,740** — not the **$10,000** the event page advertises as a
"Prize Pool". This is a genuine discrepancy, not a transcription error:

- A raw-string audit of the 199,116-byte T&C found **`"10,000"` = 0 occurrences, `"pool"` = 0, `"INR"`
  = 0, `"lakh"` = 0, ₹ = 0.** The T&C never frames the prizes as a pool and never mentions rupees.
- The event page's INR line items sum to exactly ₹10,00,000, implying the prize table was denominated
  in INR and converted at ~₹92–94/USD. But the literal string "₹10,00,000" appears **0 times** on the
  event page either.
- **So both "$10,740" and "₹10,00,000" are derived figures that no official source prints.**
- Consolation prizes are capped at five but **not guaranteed**, so no total is officially committed.

**Cite the four USD line items, never a pool total.** Payment is made "in the winner's local currency
in an amount equivalent to the applicable USD prize amount", and winners are "solely responsible for
all personal taxes, duties, foreign exchange fees". Awards are subject to eligibility and identity
verification.

Non-cash: visibility in the APJ Snowflake developer community and presentation to the judging panel.
(Earlier drafts claimed exposure to "venture capital experts" — embellishment, in no primary source.)
The payment mechanism and timeline are **unverified**.

**IP:** you keep ownership, but you grant Snowflake a *"royalty-free, non-exclusive, worldwide,
**irrevocable**, sublicensable licence"*. Because it is irrevocable, **any employer-IP contamination
is unrecoverable after submission** — hence the clean-room rule in
[`00-STATUS.md`](00-STATUS.md) §2. Governing law: Delaware.

---

## 10. Still unverified — do not build load-bearing assumptions on these

| # | Unknown | Why it matters | How to settle it |
|---|---|---|---|
| 1 | **The real submission deadline** | Existential | Dashboard / support / Discord — §1 |
| 2 | Video length cap; public vs unlisted | Could invalidate the submission | Dashboard |
| 3 | Whether a deployment link is strictly required | T&C never mentions one | Dashboard |
| 4 | **Whether CoCo CLI runs on the standard $400 trial, and whether CoCo tokens debit those $400 credits** | **The single most consequential cost unknown.** The docs enumerate only two billing models — the standalone CoCo subscription, and pay-as-you-go for existing on-demand/capacity accounts — and a $400 trial is slotted into *neither*. Indirect argument for "yes": CoCo is GA to all Commercial accounts with cross-region inference on, `ANY_REGION` is default for new accounts, and trials are on-demand. That is inference, not a citation. | Test `cortex` in the first hour |
| 5 | Whether `CREATE NOTIFICATION INTEGRATION … TYPE = WEBHOOK` works on trial | Decides if the action stage is real or in-app only | Test it |
| 6 | Whether the CoCo trial provisions a *full* account (DBs, warehouses, Streamlit) | We need all of it | Test `CREATE DATABASE` |
| 7 | Finale presentation length/format | Affects the deck | Issued at the **Aug 26 induction** |
| 8 | The dashboard sub-rubric (P4 above) | Only competitor-sourced | Dashboard |

| 9 | Whether external network access on trial is *off* or *capped at 10 credits/day* | Two official pages disagree — §6 | Test `CREATE EXTERNAL ACCESS INTEGRATION` |
| 10 | Exact wording of tracks 2–4 | Only track 1 was captured verbatim | Event page / dashboard |

Two gated workshop recordings remain unwatched on the dashboard and are the most likely source of
undocumented submission mechanics.

### What a 99-agent research sweep could *not* independently corroborate

Worth knowing, because it changes how much weight these carry. A deep multi-source verification pass
(16 sources fetched, 75 claims extracted, 25 adversarially verified 3-vote) confirmed the Snowflake
product facts to a high standard but **could not corroborate the hackathon-operational facts** from
public primary sources:

- **The 40/30/30 rubric** — it does appear on the event page (independently fetched and confirmed here
  on 2026-08-04), but it is **absent from the T&C**, so it remains marketing-tier. Unchanged from §8.
- **The static GitHub code-quality analysis, and any H2O.ai role in it** — rests *entirely* on the
  organizer's spoken statement in the Jun 25 session (P3). **No tool is named, and no published page
  mentions it.** Four separate attempts to extract that video's transcript failed, so it cannot be
  re-verified from the source; the quotes in this repo came from an earlier `yt-dlp` caption pull.
  Treat it as credible-but-single-sourced: cheap to satisfy, so satisfy it anyway.
- **Round 1/2/3 structure, judge identities, submission deliverables, video length cap, whether the
  repo must be public, the support email, and any official Discord** — none verified against a primary
  source. Everything this brief says about them is dashboard-tier or organizer-spoken.

Two corrections the sweep produced, already applied above: the prize total (§9) and the two-trial cost
model (§2). One draft-note claim was affirmatively **refuted** (age 20+ → 18+) and one affirmatively
**confirmed** (the Jun 25, 2026 session date, via the YouTube oEmbed API and the event timeline; a
competing "first session was Jul 2" claim from a Facebook post was refuted 3–0).

---

## 11. Where the repo's own docs overstate reality

Filesystem ground truth as of 2026-08-04, because two docs describe an aspirational end state:

- `README.md` and `judges_walkthrough.md` both invoke **`./scripts/setup.sh` — `scripts/` does not
  exist**
- `README.md` lists **`streamlit/` — does not exist**
- `src/warrant/` is skeletal: only `authority/tiers.py` has substance; `act/`, `detect/`, `reason/`
  and `common/` are `__init__.py` only
- `tests/` contains only `test_tiers.py`; `sql/` has 3 files
- All 5 `.cortex/skills/*/SKILL.md` **do** exist

Treat those two docs as **specification, not status**. The live checklist is
[`00-STATUS.md`](00-STATUS.md); the go-public checklist is [`../../PRE_SUBMISSION.md`](../../PRE_SUBMISSION.md).
