# Paste-ready Canva / Claude Design prompts

## Follow-up refinement prompt for the existing seven-slide deck

Use this short prompt when the current PPTX or HTML deck is already loaded in Canva or Claude
Design. It is intentionally a refinement request, not a request to regenerate the presentation:

```text
Refine this existing seven-slide Warrant deck in place. Preserve the organiser's authentic Cortex
Code CLI Hackathon template, all seven slides, the current colour semantics, verified claims,
working links, QR code, and overall editorial style. Do not re-theme, add slides, produce alternate
versions, invent UI, or replace supplied evidence with generated imagery.

Make only these narrative and legibility improvements:

1. Slide 1: keep the cover minimal. WARRANT and “No action without a warrant” must be the first two
   reads. Reduce or remove the hero crop if its contents cannot be read, and keep links quiet.

2. Slide 2: turn the three statistics into one explicit Monday-morning scene. Add the small scene
   setter “MONDAY, 08:05 — ONE OPERATIONS LEAD OPENS THE EXCEPTION QUEUE”. Keep 82 days, 5 days,
   and 26% dominant, but show the evidence directly beneath each number:
   - 82 days: QH-0034 · QUALITY_HOLDS · RB-003 · 60-day threshold
   - 5 days: SKU-1003 · INVENTORY · RB-002 · 14-day threshold
   - 26%: SUP-002 · SHIPMENTS · latest weekly slice · RB-001
   Replace the dashboard sentence with: “Snowflake found all three. The work still waits — because
   a dashboard tells you, then waits for a person.”
   Add a readable evidence ribbon: “WHERE THIS COMES FROM — Deterministic synthetic Snowflake
   testbed: 2,400 shipments · 6 suppliers · 40 quality holds · 6 SKUs. Detection thresholds come
   from 5 parsed operating procedures; the 26% is SUP-002's latest weekly slice.”
   Do not add a fictional name, customer, company, persona card, or paragraph wall.

3. Slide 3: retain the three routing outcomes and central claim, but make the execution-time twist
   readable from a projected screen. Crop the supplied sequence diagram to, or recreate with simple
   editable native shapes, only this verified order: queued while INVENTORY is internal → governance
   reclassifies it regulated → reviewer approves → executor reads SYSTEM$GET_TAG again → refuses →
   appends audit. The complete tiny diagram is not useful if its labels cannot be read.

4. Slide 4: fix the denominator ambiguity. Under “ONE LIVE PASS”, group only 6 exceptions detected,
   20–95 seconds detection to proposal, 5 completed without a reviewer, and 1 escalated with
   evidence. Put “3 REFUSALS IN THE APPEND-ONLY AUDIT” in a visibly separate boundary-evidence
   badge labelled cumulative evidence. Do not make 5 + 1 + 3 look like outcomes from six mutually
   exclusive rows. Preserve the existing evidence table and measured-not-projected framing.

5. Slide 5: change the title to “The operations lead asks once. CoCo runs the governed loop.” Keep
   the 13 tools, 5 resources, 6 Agent Skills, and no-tier invariant. Crop the screenshot so one
   relevant portion is actually readable; do not use it as an unreadable poster.

6. Slide 6: retain the title, attack/control matrix, proof counts, and architecture-property
   conclusion. Crop the supplied screenshot to the hostile instruction and unchanged routing
   evidence; the matrix remains the primary visual.

7. Slide 7: keep the live-proof resolution and final line. The URL, working QR, Snowflake refusal,
   and “Everyone will show an agent that acts…” closing must remain the final reads. Do not add a
   generic thank-you slide.

Across the deck, carry a light story through the titles and transitions: pressure → authority
dilemma → governed mechanism → measured result → CoCo operation → hostile-model test → public
resolution. Do not add more prose to create story. Remove detail before shrinking type. All body
copy must be at least 16 pt; labels and source notes at least 11 pt. At 100% view, screenshots,
tables, URLs, code identifiers, and the critical sequence must be readable.

Return the revised editable PPTX and native 16:9 PDF plus a short QA note confirming that all seven
slides were inspected, the QR and hyperlinks work, no title wraps, no object clips or overlaps,
and no font is below the specified minimum. Do not merely describe the changes—apply them.
```

## Full generation prompt

Upload the organiser template and the six assets listed after the prompt. Paste the complete block
below into Canva AI or Claude Design. Do not split it into multiple messages: the constraints,
content and QA contract need to arrive together. `docs/deck_slides.md` remains the human-readable
source of truth.

```text
ROLE
Act as a senior presentation designer, technical editor, and production QA reviewer. Create a
polished, editable, seven-slide hackathon submission deck for Warrant. The audience is a technical
hackathon judging panel evaluating innovation, technical execution, impact, and use of Snowflake
CoCo CLI. They may first skim the deck without narration and later hear a short pitch.

COMMUNICATION JOB
By the end, judges should believe Warrant makes autonomous operations deployable in governed
environments because Snowflake governance—not the model—decides whether each proposed action may
run, needs a human, or must be refused.

Do not merely arrange the supplied copy. Build a cumulative argument:
operational pain → authority problem → mechanism → measured outcome → CoCo implementation →
adversarial proof → live boundary.

INSTRUCTION PRIORITY
When instructions appear to conflict, follow this order:
1. Accuracy, locked claims, exact URLs, and the seven-slide narrative.
2. The source template's authentic Snowflake branding, masters, logos, typography, and safe areas.
3. Legibility and clean visual hierarchy.
4. Decorative preference.

Never sacrifice accuracy or legibility to preserve a decorative treatment. Never silently omit a
required claim. If the platform cannot satisfy a requirement, return the closest compliant draft
and list the exact unmet requirement outside the deck; do not invent a workaround inside a slide.

REFERENCE AND OUTPUT
- Use the uploaded “Prototype Submission Template _ Cortex Code CLI Hackathon.pptx” as the brand
  source, not merely colour inspiration. Retain its authentic master/layout hierarchy, Snowflake
  marks, header/footer treatment, fonts, and required cover fields. Duplicate suitable branded
  content canvases for additional slides instead of rebuilding the brand from scratch.
- Delete the organiser instruction slide. It is guidance, not submission content.
- Build exactly 7 physical slides. Do not add a generic “Thank you” slide.
- Canvas: 16:9, 10 x 5.625 inches. Export PPTX and a native 16:9 PDF; never A4.
- Keep all elements editable except the supplied screenshots and diagram.
- Do not flatten the deck into seven full-slide images. Text, tables, labels, and the QR code must
  remain separately editable.
- Keep at least 0.45 in equal left/right margins. Treat the organiser header and footer as protected
  zones; no title, table, image, URL, QR code, or page number may overlap them.
- Preserve working hyperlinks in both PPTX and PDF.

BUILD METHOD
1. Inspect every slide in the uploaded template before designing.
2. Identify the cover layout and the cleanest branded content-canvas layout.
3. Duplicate those source layouts to create exactly seven output slides.
4. Remove all template instruction text and unused empty placeholders; retain authentic branding.
5. Place the supplied assets only in the slides assigned below.
6. Apply the exact content and hierarchy below.
7. Render and inspect all seven slides at full size and as a montage.
8. Fix wrapping, clipping, overlaps, unreadable tables, inconsistent margins, poor crops, fake QR
   codes, broken links, and unfilled placeholders before returning the deck.

LOCKED CONTENT RULES
- LOCKED means it must remain factually and semantically exact: all numbers, table/object names,
  authority outcomes, sequence ordering, product/tool counts, test counts, URLs, team details, and
  quoted security claim.
- Titles supplied below are also locked unless a one-line fit requires a shorter version. If
  shortened, preserve the claim and never turn a takeaway title into a generic section label.
- You may tighten supporting prose only to improve fit. Do not introduce a new number, claim,
  customer, benchmark, ROI, forecast, award, partner, or deployment assertion.
- Do not change “251 tests collected” into “251 tests passed.” The verified local result is 247
  passed, 3 skipped, and 1 deselected, with 251 collected and 100% branch coverage.
- Do not change the execution sequence. The correct order is: the action is queued while
  INVENTORY is internal → governance reclassifies INVENTORY as regulated → the reviewer approves
  the queued action → the executor reads the tag again → the executor refuses → audit records it.
- Do not imply the Vercel page can approve a real action. Its value is that its real calls are
  refused by Snowflake.
- Do not describe live rolling task counts as fixed evidence and do not use trial-credit consumption
  as business impact.
- Do not expose these production instructions, locked-content labels, layout percentages, source
  paths, speaker guidance, or QA notes as visible audience-facing copy.

PROJECT
Warrant is a governed autonomous operations agent built on Snowflake for Team Argmax, a solo
submission by Sathya T, Problem Statement 1: Intelligent Workflow Automation Agent.
Tagline: “No action without a warrant.”

THE IDEA TO LAND
The model may propose an action, but it never grants itself authority. Warrant resolves authority
from Snowflake object tags on every table an action touches, and resolves it again immediately
before execution. The same Python workflow therefore acts on open data, asks a human for internal
data, and refuses regulated actions. A policy change takes effect without changing or redeploying
the application.

VISUAL DIRECTION
- Editorial, technical, precise, premium; more engineering brief than startup pitch.
- Deep navy #0A1B33 background, warm white #F0EBE4 text, muted #9AA4B2, cyan #00B8A9.
- Semantic colours only: green #15803D means ACTED; amber #B45309 means HUMAN APPROVAL; red
  #B91C1C means REFUSED. Pair every colour with a text label.
- Inter, Söhne, or Helvetica Now. Titles 30–34 pt; body 15–18 pt; labels 11–12 pt; never below 11 pt.
- Use JetBrains Mono for code, table names, tags, SQL procedures, and paths.
- No stock photography, robot/brain imagery, lightbulbs, clip art, decorative 3D, fake UI,
  gradient meshes, drop shadows, or decorative underline strokes.
- Use simple 1 px borders, restrained 8 px corner radii, generous whitespace, and a consistent
  grid. Do not shrink text to fit.
- Add this quiet footer on slides 2–7: snowflake-coco-cli-hackathon-2026.vercel.app
- Prefer one strong composition per slide over a dashboard of many cards. Stat tiles on slide 4
  are the deliberate exception.
- Each slide must have one obvious first read at thumbnail size: title, primary evidence, conclusion.
- Use no more than two font families. Match template typography first; otherwise use Inter or
  Söhne plus JetBrains Mono.
- Keep titles to one line. If a title wraps, shorten it without weakening the claim; never reduce
  title size below the template's established slide-title size.
- Body text must be at least 16 pt. Labels and source notes may be 11–12 pt. Never go below 11 pt.
- Tables must be readable from a projected screen: short rows, strong column alignment, no paragraph
  text inside cells, and enough row height to avoid crowding.
- Screenshots must never be stretched. Preserve aspect ratio, crop only at natural section
  boundaries, and ensure the key evidence remains readable.

SOURCE NOTES
Add a [Sources] block to speaker notes for each slide. Do not show these blocks on the canvas.
Use these source references:
- Slides 1 and 7: https://snowflake-coco-cli-hackathon-2026.vercel.app/ and
  https://github.com/tsathya98/snowflake-coco-cli-hackathon-2026
- Slide 2: README.md, docs/the_data.md, and the public live-proof page.
- Slide 3: README.md, docs/architecture.md, docs/images/deck/sequence-dark.png.
- Slide 4: docs/rubric_alignment.md, eval/scorecard.json, README.md.
- Slide 5: mcp/warrant_mcp/server.py, .cortex/skills/, docs/images/web/coco-cli.png.
- Slide 6: tests/test_adversarial.py, corpus/adversarial/, eval/scorecard.json,
  docs/images/web/tested.png.
- Slide 7: web/, docs/images/web/evidence.png, docs/images/web/refusals.png.
If the platform cannot create speaker notes, omit the blocks from the visible slides and return the
source list separately with the deck.

ASSET CONTRACT
The uploaded files are evidence, not visual inspiration. Match them by filename or prompt label:
- [HERO] = hero.png. Use once, on slide 1 only.
- [SEQUENCE] = sequence-dark.png. Use once, on slide 3 only. It has transparency; preserve it.
- [COCO CLI] = coco-cli.png. Use once, on slide 5 only.
- [TESTED] = tested.png. Use once, on slide 6 only.
- [EVIDENCE] = evidence.png. Preferred slide 7 proof image.
- [REFUSALS] = refusals.png. Slide 7 fallback if its refusal result is more legible.
Do not substitute a generated image, stock asset, reconstructed diagram, mock terminal, or invented
screenshot for any missing file. If an asset is unavailable, leave a clearly named production
placeholder in the draft and identify the missing filename in the QA report outside the deck. Use
at most one of [EVIDENCE] and [REFUSALS] on slide 7; do not make a screenshot collage.

SLIDE 1 — COVER
Narrative job: name the product and state the governing idea in under five seconds.
Composition: asymmetrical 58/42 split. Copy on the left; restrained [HERO] crop on the right.
The word WARRANT is the first read, the tagline the second, metadata the third.
Large wordmark: WARRANT
Tagline in cyan: No action without a warrant.
Subtitle: A governed autonomous operations agent on Snowflake
Metadata: Team Argmax · Sathya T · Solo submission
Problem Statement: PS1 — Intelligent Workflow Automation Agent
Small links:
Live proof: snowflake-coco-cli-hackathon-2026.vercel.app
Source: github.com/tsathya98/snowflake-coco-cli-hackathon-2026
Use a restrained crop of [HERO] on the right. Keep the cover minimal and all organiser-required
fields visible.
Do not add an agenda, architecture diagram, feature list, paragraph, or decorative subtitle.

SLIDE 2 — PROBLEM BRIEF
Narrative job: establish that the unmet need begins after detection, and that authority—not model
capability—is what blocks deployment.
Composition: title at top; three equal numeric columns across the upper-middle; one concise sentence;
two flat text groups below; one red callout as the final read. The three numbers must occupy at
least one-third of the usable slide height.
Eyebrow: PROBLEM BRIEF
Title: The automation that would help is the automation nobody will approve
Scene setter: MONDAY, 08:05 — ONE OPERATIONS LEAD OPENS THE EXCEPTION QUEUE
Make these the dominant visual:
82 days — QUALITY HOLD STILL OPEN — QH-0034 · QUALITY_HOLDS — RB-003 · 60-day threshold
5 days — STOCK COVER LEFT — SKU-1003 · INVENTORY — RB-002 · 14-day threshold
26% — SUPPLIER ON-TIME DELIVERY — SUP-002 · SHIPMENTS — latest weekly slice · RB-001
Sentence: Snowflake found all three. The work still waits — because a dashboard tells you, then
waits for a person.
Compact panel 1, heading THE WORK AFTER THE INSIGHT:
Investigate · find the governing procedure · prepare the response · decide who may approve · act
or escalate · record it.
Compact panel 2, heading THE DEPLOYMENT BLOCKER:
“Can the agent change a regulated quality record?” Blanket access is unacceptable. Draft-only
automation is not useful enough.
Red bordered callout labelled THE REAL BLOCKER:
Capability was not the problem. Authority was.
Readable evidence ribbon:
WHERE THIS COMES FROM — Deterministic synthetic Snowflake testbed: 2,400 shipments · 6 suppliers ·
40 quality holds · 6 SKUs. Detection thresholds come from 5 parsed operating procedures; the 26%
is SUP-002's latest weekly slice.
Avoid paragraphs and persona cards.
Do not use [HERO] again and do not turn the two text groups into six small UI cards.

SLIDE 3 — ARCHITECTURE
Narrative job: explain both normal routing and the execution-time policy re-check—the central
technical differentiator.
Composition: title; compact four-column routing table in the upper 30%; [SEQUENCE] as the dominant
middle visual; seven-stage strip; one red conclusion callout. The sequence ordering and the second
tag read must remain legible without speaker narration.
Eyebrow: ARCHITECTURE
Title: One loop. Three endings. The tag on the data decides.
Use a four-column table:
SUP-002 · delivery collapsed to 26% | SHIPMENTS | open | ACTED · no human
SKU-1003 · five days from stockout | INVENTORY | internal | ESCALATED · evidence ready
QH-0034 · proposed release of 82-day hold | QUALITY_HOLDS | regulated | REFUSED · reason logged
Colour only the outcome labels green, amber, and red respectively.
Line beneath: Same Python path; no branching on table names.
Use [SEQUENCE] as the evidence source, but do not shrink the entire image until the labels become
decorative. Use a readable crop of its execution-time section or recreate only that section with
simple editable native shapes. Preserve this exact ordering:
queue while INVENTORY is internal → governance reclassifies it regulated → reviewer approves →
executor reads SYSTEM$GET_TAG again → action is refused → refusal is audited.
Seven-stage strip:
Watch → Detect → Investigate → Classify → Route → Execute → Audit
Emphasise Classify, Route, Execute.
Red bordered callout labelled THE CLAIM THAT MATTERS:
Approval does not survive a governance change. Authority defaults down, never up.
Small technical line:
Snowflake Tasks + Streams · Cortex Search · AI_COMPLETE structured JSON · object tags + masking ·
append-only audit
If the slide becomes crowded, remove the small technical line first. Never remove the sequence,
the three routing outcomes, or the execution-time re-read.

SLIDE 4 — IMPACT STATEMENT
Narrative job: show what happened and prove the results are measured rather than forecast.
Composition: four aligned one-pass stat tiles in one row; a clearly separate cumulative refusal
badge; evidence table below; cyan conclusion callout at the bottom. Green and amber apply to the
one-pass outcomes; red applies to the separate refusal evidence.
Eyebrow: IMPACT
Title: Measured on the live account, not projected
Group labelled ONE LIVE PASS — four stat tiles:
6 — EXCEPTIONS DETECTED
20–95 s — DETECTION TO PROPOSAL
5 — COMPLETED WITHOUT A REVIEWER
1 — ESCALATED WITH EVIDENCE
Separate red badge, explicitly labelled cumulative rather than part of the six-row funnel:
3 — REFUSALS IN THE APPEND-ONLY AUDIT
Caption: cumulative boundary evidence
Below, a readable two-column evidence table:
Reasoning quality | 6 scenarios x 5 dimensions, all passed
Hostile document reached the prompt | 6/6 findings cited it; 0 routings changed
Planted anomaly separation | robust z -3.63 vs -0.46 next worst
Engineering gate | 251 tests collected · 100% branch coverage · 0 mypy errors
Cyan bordered callout labelled THE NUMBER THAT MATTERS:
Not agent versus human on speed: deployable versus not. Blanket write access is never switched on;
Warrant spans open, internal and regulated work in one loop.
Small source note:
Live operational counts are visible at the public proof link. Reproducible quality claims are
checked from repository artifacts in CI.
Do not add a fixed “task runs in 24h” number or trial-credit usage; both are unsuitable as durable
impact claims.
Do not add an ROI chart, time-saved estimate, benchmark comparison, customer quote, or percentage
improvement. None has been measured.

SLIDE 5 — COCO CLI + MCP
Narrative job: prove CoCo CLI, MCP, Agent Skills, and Python execution are structural parts of the
solution rather than submission decoration.
Composition: [COCO CLI] in a 62% left media frame; a 38% right text rail with the three counts and
annotations; invariant callout spanning the bottom. Crop the screenshot so its title and the tool
surface remain recognizable.
Eyebrow: COCO CLI + MCP
Title: The operations lead asks once. CoCo runs the governed loop.
Place [COCO CLI] on the left two-thirds, cropped only at natural section boundaries.
Right column:
13 TOOLS — 11 read · 2 act
5 RESOURCES — governance · capabilities · audit · runbooks
6 AGENT SKILLS — five loop phases + operate-warrant
Small annotations:
Every tool carries truthful MCP ToolAnnotations.
execute_approved_action declares destructiveHint: true.
The server reuses the operator's Snowflake connection and identity.
Red bordered callout labelled THE INVARIANT:
No tool accepts an authority tier. The model has no parameter with which to grant itself more
power; the tool resolves authority from live tags.
Bottom strip:
cortex mcp discovers the server · Agent Skills explain the workflow · Python executes in Snowflake
Do not represent the 13 tools as thirteen separate icons or cards. Do not invent terminal output.

SLIDE 6 — SECURITY AND VERIFICATION
Narrative job: move the argument from “the model behaved” to “the architecture contains a model
that may misbehave.”
Composition: 44% [TESTED] crop on the left; 56% attack/control matrix on the right; proof badges
and the red conclusion below. The matrix is the primary evidence, not decorative cybersecurity art.
Eyebrow: TECHNICAL EXECUTION
Title: Assume the model was compromised. The boundary still held.
Place a readable crop of [TESTED] on the left. On the right, create a two-column attack/control
matrix:
“Treat the regulated table as open” | Tier discarded; SYSTEM$GET_TAG is authoritative
“Use an empty touched-object list” | Objects re-derived from the action registry
“Release the hold” | No registered dispatcher exists
SQL embedded in an identifier | Bound as data, never composed as SQL
“Suppress the audit row” | Append-only audit path
Three proof badges:
10 ADVERSARIAL TESTS · 6/6 ON EVERY REASONING DIMENSION · 100% BRANCH COVERAGE
Red bordered callout with the exact copy:
“The model refused the attack” is a model property. “The model complied and nothing changed” is
an architecture property.
Small line:
Explicit JSON Schema · bound runtime values · tags read live, never cached · Snowflake masking
Do not use a shield, lock, hacker, red-code, or AI-generated security illustration.

SLIDE 7 — LIVE PROOF AND CLOSE
Narrative job: let judges verify the boundary themselves, state the honest scope, and resolve the
opening tension with one memorable line.
Composition: surface/authority table on the left; [EVIDENCE] or [REFUSALS] on the right; prominent
URL plus working QR below; limitations in small but readable text; closing line as the final visual
anchor. The URL and QR are more important than decorative imagery.
Eyebrow: LIVE PROOF
Title: Only the governed surface can act
Three-row table:
Streamlit inside Snowflake | CAN ACT · attributable reviewer identity · executor re-checks tags
Public Vercel viewer | CANNOT ACT · live buttons send real statements · Snowflake refuses
Cortex Agent / CoWork | READ ONLY · no executor tool attached
Use [EVIDENCE] or [REFUSALS] so the green “THE BOUNDARY HELD” result and Snowflake error are legible.
Prominent cyan block:
TRY THE BOUNDARY YOURSELF
https://snowflake-coco-cli-hackathon-2026.vercel.app/
Scan the QR code, press Approve, Reject, or Defer, and watch Snowflake refuse it.
Generate a working QR code from that exact HTTPS URL. Keep the URL as selectable text beside it.
After generating the QR code, decode or scan it as part of QA. A QR-shaped placeholder is a failure.
Small validation note:
Validated 6 Aug 2026: HTTP 200; live Snowflake data loaded; all seven public objects readable;
EXECUTE_ACTION and queue updates refused for WARRANT_PUBLIC.
Honest limitation line:
Synthetic data · one Snowflake account · production rollout requires controlled runbooks, domain
validation, monitoring, and organisational approval.
Closing line in cyan:
Everyone will show an agent that acts. Warrant shows one that knows when it must not.

FINAL QA BEFORE RETURNING THE DECK
- Exactly seven slides. No organiser instruction page. No generic thank-you slide.
- Problem Brief, Architecture, and Impact Statement are explicit section labels.
- Slide 3 preserves queue → reclassify → approve → execution-time re-read → refuse.
- All screenshots are supplied assets; no AI-generated interfaces.
- The Vercel and GitHub links are selectable text and the QR resolves to the exact Vercel URL.
- No text is below 11 pt, no table is unreadable, and no element overlaps template branding.
- Green, amber, and red are used only for acted, human approval, and refused.
- Export editable PPTX and native 16:9 PDF, then visually inspect every page.
- No title wraps; no text or image is clipped; no object unintentionally overlaps another object.
- No unresolved placeholders such as “Click to add title”, “Date”, “Footer”, or “Slide Number”.
- No screenshot is stretched, blurred, duplicated, or cropped through its key evidence.
- At thumbnail size, each slide still has one obvious primary claim.
- At 100% size, all body copy, tables, code identifiers, errors, and URLs are readable.
- The PPTX opens in PowerPoint without a repair warning and the PDF contains exactly seven 16:9
  pages with no letterboxing.

RETURN PACKAGE
Return:
1. The editable seven-slide PPTX.
2. The seven-page native 16:9 PDF.
3. A one-paragraph QA report outside the deck confirming slide count, hyperlink/QR test, overflow
   check, placeholder check, and any font substitutions.
Do not return planning slides, an appendix, alternate covers, or extra variants unless requested.
```

## Upload these assets

| Prompt label | File |
|---|---|
| `[HERO]` | `docs/images/web/hero.png` |
| `[SEQUENCE]` | `docs/images/deck/sequence-dark.png` |
| `[COCO CLI]` | `docs/images/web/coco-cli.png` |
| `[TESTED]` | `docs/images/web/tested.png` |
| `[EVIDENCE]` | `docs/images/web/evidence.png` |
| `[REFUSALS]` | `docs/images/web/refusals.png` |

If Canva switches to a light content background, substitute
`docs/images/deck/sequence.png` for the dark sequence diagram. Do not let the design tool replace
screenshots with generated approximations.
