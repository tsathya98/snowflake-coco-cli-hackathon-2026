# The deck-generation prompt

`deck_slides.md` is the build source: what goes on each slide and why, written for a person. This
file is the **prompt** — one block to paste into Canva AI, Claude with artifacts, Gamma, or
Beautiful.ai to get a first draft you then correct.

**How to use it.** Copy everything inside the fence and paste it as a single message. Then upload
the five images named at the end; most tools cannot fetch them and will leave a placeholder box
otherwise. Expect to fix two things by hand every time: tables come back too small, and callouts
come back as plain paragraphs. Both are faster to fix than to prompt around.

**What to do after.** Delete the organiser's slide 2 (their instructions, not your content), drop
your six slides onto their template so the navy header and gradient footer are theirs rather than a
copy, then export to PDF. Check the PDF on a phone before submitting: if the three-lane table on
slide 3 is unreadable there, it will be unreadable from the back of a room.

---

```
You are designing a 6-slide submission deck for a hackathon. Output a complete deck, one slide at
a time, with every word of copy written out. Do not summarise, do not use lorem ipsum, and do not
invent any number that is not given below.

PROJECT
Warrant — a governed autonomous operations agent built on Snowflake.
Team Argmax, solo, team leader Sathya T. Snowflake CoCo CLI Hackathon 2026,
Problem Statement 1: Intelligent Workflow Automation Agent.
Tagline: "No action without a warrant."

THE ONE IDEA THE DECK MUST LAND
An AI agent that can act does not get deployed in a regulated operation, because nobody can say in
advance what it is allowed to touch. Warrant answers that from the data itself: every action's
authority is read live from the Snowflake governance tag on the tables it touches, and read again
at execution time. So the same code path handles one exception unsupervised, escalates a second to
a human, and refuses a third outright — and which one happens is decided by the tag, not by code.

FORMAT
- 16:9, exactly 10 x 5.625 inches. Not 13.33 inches.
- Leave the top 0.6in and bottom 0.45in of every slide empty. An organiser-branded header bar and
  gradient footer get layered in afterwards and must not collide with content.
- One idea per slide. If a slide needs a paragraph of body text, it is two slides — tell me instead
  of shrinking the type.

VISUAL SYSTEM
- Background: deep navy #0A1B33. Body text near-white #F0EBE4. Muted text #9AA4B2.
- Accent for links and structure: cyan #00B8A9.
- Three semantic colours, used ONLY with their meaning, never decoratively:
    green  #15803D = the agent acted unsupervised
    amber  #B45309 = a human had to approve
    red    #B91C1C = refused
- Type: one clean grotesque (Inter, Söhne, or Helvetica Now). Titles 30-34pt, bold, tight tracking.
  Body 14-16pt. Table text no smaller than 12pt. Never below 11pt anywhere.
- Every coloured element also carries a text label. Colour alone is invisible to a colourblind
  reviewer, and this project is partly an argument about auditability.
- Monospace (JetBrains Mono or similar) for anything that is a real identifier: table names, tags,
  function names, file paths.
- NO stock photography. NO clip art. NO robot or brain or lightbulb icons. NO gradient meshes, no
  drop shadows, no 3D. NO decorative underline strokes below titles. Flat, dense, editorial.
- "Callout" means a real box: 1px border in the stated colour, background the same colour at 10%
  opacity, an uppercase label in that colour, then the sentence. Not a coloured paragraph.

────────────────────────────────────────────────────────────────
SLIDE 1 — COVER

Centred. Large wordmark "Warrant", then the tagline in cyan:
    No action without a warrant.
Then a single line of body:
    A governed autonomous operations agent on Snowflake.

Bottom-left, small, four labelled fields on two lines:
    Team Name: Argmax        Team Leader: Sathya T
    Team Size: 1             Problem Statement: PS1, Intelligent Workflow Automation Agent

────────────────────────────────────────────────────────────────
SLIDE 2 — PROBLEM BRIEF
Eyebrow: PROBLEM BRIEF
Title: The automation that would actually help is the one that never ships

Three huge figures across the top, equal width, the number at 54pt and the caption at 11pt
uppercase beneath it:
    82 days   A QUALITY HOLD, STILL OPEN
    5 days    OF STOCK COVER LEFT ON ONE SKU
    26%       ON-TIME DELIVERY AT ONE SUPPLIER

One line under them, in muted text:
    All three are on a dashboard right now. None of them is fixed.

Then two short body paragraphs:
    Someone opens six tabs on Monday morning, works out which of the forty open holds actually
    matters, writes the supplier email, raises the replenishment, files the note. Analytics stopped
    at the insight. The work starts after it.

    An agent could do all of it. It does not get deployed, because in a regulated operation the
    first question is always the same: "so it can change a quality record?" If the answer is yes,
    nobody signs off. If the answer is no, it only drafts emails, it was not worth building.

Red callout, labelled THE REAL BLOCKER:
    The blocker was never capability. It was authority. Nobody could say, in advance and in
    writing, what the agent was allowed to touch.

Three small personas along the bottom in one row, name in bold then one line each:
    Operations analyst — owns the exception queue, wants routine responses to stop reaching them.
    Quality and compliance owner — needs a defensible answer to "what is this allowed to do, and
    who decided?"
    Data platform owner — refuses to maintain a second copy of the access policy inside an app.

Footer line, small and muted:
    Supply chain and manufacturing operations. 100% synthetic data: 2,400 shipments, 6 suppliers,
    40 quality holds, 6 SKUs, 5 operating procedures.

────────────────────────────────────────────────────────────────
SLIDE 3 — ARCHITECTURE
Eyebrow: ARCHITECTURE
Title: One loop, three endings, decided by the tag on the data

This is the most important slide. Give the table the top half and the diagram the bottom half.

A four-column table, each row colour-coded in the Ending column only:
    THE EXCEPTION                      | TABLE IT TOUCHES | TAG        | ENDING
    SUP-002 on-time collapsed to 26%   | SHIPMENTS        | open       | Handled, nobody asked        (green)
    SKU-1003 five days from stockout   | INVENTORY        | internal   | Escalated, prepared then stopped  (amber)
    QH-0034 on hold 82 days            | QUALITY_HOLDS    | regulated  | Refused, and it says why     (red)

One line directly beneath, italic:
    Same code path, three endings. There is no "if table_name" anywhere in this.

Below that, full width: place the supplied image [SEQUENCE DIAGRAM]. Do not redraw it, do not
put a white box behind it, it is transparent on purpose.

A single horizontal strip of seven stages, stages 4, 5 and 6 in amber and the rest in muted grey:
    01 Watch  02 Detect  03 Investigate  04 Classify  05 Route  06 Execute  07 Audit
Caption under it, small:
    Stages 1 to 3 are a pipeline any competent team would build. Stages 4 to 6 are the submission.

Red callout, labelled THE CLAIM THAT MATTERS:
    Authority is resolved again at execution time. Approve an action, reclassify the table it
    touches, run the executor: it refuses, and records why. A human's own approval does not
    survive a governance change, and nothing was deployed in between.

────────────────────────────────────────────────────────────────
SLIDE 4 — IMPACT
Eyebrow: IMPACT
Title: Measured on the live account, not projected

Five stat tiles across the top. Number at 40pt, caption 10pt uppercase. First two in near-white,
then green, amber, red:
    6        EXCEPTIONS FROM 2,400 SHIPMENTS
    20-95s   DETECTION TO PROPOSED ACTION
    5        HANDLED WITH NO HUMAN TOUCH
    1        ESCALATED WITH EVIDENCE
    3        REFUSED, WITH A REASON

A two-column table below:
    WHAT WAS MEASURED                                                          | RESULT
    Reasoning evaluation, scenarios x scoring dimensions passed                | 6 x 5, all
    Hostile document planted in the corpus: findings citing it / routings changed | 6 of 6  /  0
    Statistical separation of the planted anomaly (robust z)                   | -3.63 vs -0.46 next-worst
    Tests / branch coverage / mypy-strict errors                               | 251 / 100% / 0
    Unattended task runs in 24h / failed                                       | 34 / 0
    Credits to build the entire project                                        | 8.39 of 400

One line, not a table:
    Every number on this slide is a CI gate. Clone the repository, run one command, and a checker
    executes the project's own tools and fails if any figure here disagrees with the code.

Navy or cyan callout, labelled THE NUMBER THAT MATTERS:
    Not agent-versus-human on speed. Deployable versus not. An agent with blanket write access is
    not 10x faster than a review meeting, it is never switched on. The same loop safely spans
    open, internal and regulated data in one pass.

────────────────────────────────────────────────────────────────
SLIDE 5 — COCO CLI AND MCP
Eyebrow: COCO CLI + MCP
Title: The whole agent is an MCP server, and CoCo operates it

Left two-thirds: place the supplied image [COCO CLI SCREENSHOT].

Right third, three stacked facts, the number large and the text small:
    13 tools     11 annotated readOnlyHint, 2 that act. execute_approved_action declares
                 destructiveHint: true, because it is.
    5 resources  Each with a tool twin, because not every client supports resources.
    6 skills     The five loop phases, plus operate-warrant to drive them from a terminal.

Red callout across the full width, labelled THE INVARIANT:
    No tool on this server accepts an authority tier. A tool taking "tier" as a parameter would
    hand the model the one decision the design exists to keep away from it. Every tool resolves
    the tier itself from the live tag, so prompt-engineering the model into higher authority has
    no parameter to aim at. Asserted by a test that walks every registered tool's live schema.

Small line at the bottom:
    The server holds no credential of its own. It reads the same connections.toml that snow and
    cortex do, so it inherits the operator's identity rather than acquiring one.

────────────────────────────────────────────────────────────────
SLIDE 6 — THE BOUNDARY, AND WHAT IS NOT PROVEN
Eyebrow: SOLUTION COMPLETENESS
Title: Three surfaces, and only one of them can act

Two-column table, the answer column colour-coded:
    SURFACE                              | CAN IT ACT?
    Streamlit console, inside Snowflake  | Yes, through the governed path. The reviewer's own
                                           identity, so an approval is attributable to a person.  (amber)
    Public web viewer, Next.js on Vercel | No, and you can prove it yourself. The approve, reject
                                           and defer buttons are live and send the real statements.
                                           Snowflake refuses them in front of you.                (green)
    Cortex Agent in CoWork               | No. Two read-only tools, nothing bound to the executor. (green)

Right side or below: place the supplied image [EVIDENCE SCREENSHOT].

Then, in smaller type, a short honest-limitations block with the heading WHAT THIS DOES NOT PROVE:
    Synthetic data, one account. The mechanism is domain-agnostic; the demonstration is not a
    deployment.
    SNOWFLAKE.ML.ANOMALY_DETECTION is a documented seam, not an implementation.
    Thresholds come from a corpus written for this project; a real deployment needs the live
    controlled documents.

Closing line across the bottom, larger, in cyan:
    Everyone in this track will show you an agent that acts. This is one that declines, and whose
    declining does not depend on the model choosing to.

Bottom edge, small and muted:
    snowflake-coco-cli-hackathon-2026.vercel.app  ·  github.com/tsathya98/snowflake-coco-cli-hackathon-2026

────────────────────────────────────────────────────────────────
IMAGES I WILL UPLOAD, AND WHERE THEY GO
[SEQUENCE DIAGRAM]     -> slide 3, full width, transparent background, do not put a card behind it
[COCO CLI SCREENSHOT]  -> slide 5, left two-thirds
[EVIDENCE SCREENSHOT]  -> slide 6
Optionally also: a hero shot for slide 1 or 2, and the seven-stage workflow shot for slide 3 if
you prefer it to the sequence diagram.
Give every image a thin 1px border in #1E2D45 and 8px rounded corners. Never crop a screenshot
through a heading or a number.

FINAL CHECK BEFORE YOU RETURN THE DECK
- Six slides, no more.
- No number appears that is not in this prompt.
- No slide has more than one idea.
- Nothing sits in the top 0.6in or bottom 0.45in.
- Green, amber and red each appear only with their stated meaning.
- Every table cell is at least 12pt.
```

---

## The five files to upload

| Placeholder | File |
|---|---|
| `[SEQUENCE DIAGRAM]` | `docs/images/deck/sequence.png` (4434 × 2880, transparent) |
| `[COCO CLI SCREENSHOT]` | `docs/images/web/coco-cli.png` |
| `[EVIDENCE SCREENSHOT]` | `docs/images/web/evidence.png` |
| optional hero | `docs/images/web/hero.png` |
| optional workflow | `docs/images/web/story-workflow.png` |

If a tool refuses transparent PNGs, use `docs/images/deck/sequence-dark.png` instead — same
diagram, drawn for a dark background.
