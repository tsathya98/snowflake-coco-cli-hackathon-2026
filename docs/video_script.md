# Warrant demo video — natural five-minute script

This is the recording script, not submission copy. The portal asks for a 3–5 minute screen
recording of an end-to-end workflow executed through Cortex Code CLI, including input, processing,
output, and two or three modular skills. Read at a natural pace, the full script runs **5:20 —
which is over the limit**. Cutting one optional beat brings it to **4:53**. Decide which version
you are recording before you start; see *Spoken length* below.

The SAY blocks are written to be read **word for word, aloud** — contractions, pauses, and all.
Read from your phone, but look up during the three key lines listed in the delivery notes. If a
sentence trips your tongue twice, change the words, keep the fact.

## The story in one sentence

An operations lead starts Monday with three urgent exceptions; one governed workflow handles the
safe work, asks about the consequential work, and refuses the regulated work—even after approval.

**The mental model, if you only keep one line:** the agent can notice and recommend; the data's
live governance tag decides whether it may execute.

**The running order, so you never have to think about it mid-take:** public story → title card →
CoCo runs the loop → Streamlit reviewer view → tag change and refusal → adversarial tests →
public refusal proof.

## Spoken length

771 spoken words. At 155 wpm that is **4:58 of speech**, and about twenty seconds of the video is
action nobody talks over — the title card, the two-second pause after the refusal, the button
clicks. The section timings below therefore sum to **5:20**, which is past the portal's ceiling.

That is one beat too many, and no amount of talking faster fixes it. **Cut the adversarial section
and the video lands at 4:53**, with everything the portal actually asks for still in place: the
CLI end-to-end run, three named skills, and the approve-then-refuse climax. The adversarial story
survives on deck slide 6 and on the live page, where a judge can read it without a stopwatch.

The earlier, clipped version of this script fit in 4:58 — but it did not sound like a person. The
extra ninety-nine words are what conversational phrasing costs. Spending them here and cutting a
whole beat is the better trade.

Keep it only if a timed read-through comes in under **4:35 of speech**. Either way, paste the
prompts rather than typing them, and keep window switches to a single keystroke.

## What the judge should remember

1. The hard problem is not detection; it is authority.
2. CoCo CLI drives a real end-to-end run through modular Agent Skills and MCP tools.
3. The model proposes, but live Snowflake tags decide.
4. Authority is checked again at execution, so stale approval cannot override new policy.
5. The hostile-document tests assume the model was fooled and prove the boundary still holds.
6. Two surfaces, one boundary: the Streamlit console runs **inside Snowflake** and is the only
   surface that can act; the public Vercel viewer is outside and proves it cannot.

## Recording setup — MacBook (QuickTime plan)

- Use **QuickTime Player**. It is the best choice here: a clean 1080p screen recording, no
  meeting UI, no cloud upload, and no recording bot to distract from the proof. In QuickTime,
  choose **File → New Screen Recording**, Options → Microphone, then record the whole display.
  Record camera separately only if the portal explicitly requires a face camera; this demo is
  strongest as a calm narrated screen recording.
- Set the display to 1920×1080 before recording. Enable Do Not Disturb, hide the Dock, close
  Messages/Mail/Calendar, and turn off desktop notification previews. Keep one browser profile
  with no personal bookmarks or account tabs visible.
- Terminal: dark theme, 17–19 pt, already in the repository root.
- Keep four destinations ready:
  1. terminal with `cortex` and the repository;
  2. Streamlit in Snowflake, opened once so every tab is warm;
  3. Snowsight worksheet with the `ALTER TABLE` statement already typed;
  4. the public viewer: `https://snowflake-coco-cli-hackathon-2026.vercel.app/`.
- Export slide 1 of the final deck as a clean 16:9 still. Insert it for only 2–4 seconds at the
  product reveal; do not show PowerPoint, Canva, or the rest of the deck.
- Hide or crop the Snowsight address bar because it contains the account locator. The Vercel URL
  is safe and useful to show.
- Switch with Cmd+Tab. Clean jump cuts are fine.
- **Paste the prompts and the SQL; do not type them.** Keep all three CoCo prompts and the
  `ALTER TABLE` line in one scratch file, and paste each with a single keystroke. Typing a
  180-character prompt on camera costs twenty seconds the budget does not have, invites a typo
  that forces a retake, and proves nothing — the judge needs to read the prompt, not watch it
  appear. Paste, let it sit still for one beat so it is readable, then press Enter. Never show the
  scratch file itself; keep it on a second desktop or minimised.
- The reasoning calls take roughly two minutes. Start the run, explain what it is doing, then cut
  to the completed result. Do not pretend the cut is real time.

### Exact window order — arrange this before pressing Record

Keep these windows open, in this exact Cmd+Tab order. This prevents hunting for tabs while the
recording is running.

| Order | Window | What must already be on screen | Why the judge sees it |
|---|---|---|---|
| 1 | Browser — Vercel viewer | Hero section with the three exceptions; later, the public refusal shortcut | Establishes the Monday scenario, then gives independent public proof. |
| 2 | Browser — Streamlit console | Overview / pending-action screen, already signed in | Shows the human review surface inside Snowflake. |
| 3 | Snowsight worksheet | Only the one-line `ALTER TABLE ... INVENTORY ... regulated` statement | Makes the live policy change legible without exposing the account locator. |
| 4 | Terminal | Repository root; no prior command output containing secrets | Shows Cortex Code CLI input, processing, output, and adversarial proof. |
| 5 | Finder / Preview | `docs/submission/warrant-video-title-card-1920x1080.png`, full-screen-ready | A 3–4 second product reveal only; never show the full deck. |

### What must be visible versus what can be cut

Visible proof is more important than continuous footage. Record these full moments: the CoCo
prompt, enough live processing to show it began, the completed CoCo answer, the tag-change SQL,
the reviewer approval, the refusal, the adversarial test pass, and the public refusal result.
Cut only waiting time, window switching, and long model processing. A hard cut is honest if the
spoken line says that the model calls take a couple of minutes.

## Pre-flight — do this before recording

```bash
# Return the workflow to a genuine pre-run state. Do not run the loop yet;
# the CoCo prompt in the recording must be the run that creates the output.
snow sql -c warrant -f sql/90_reset.sql

# Check the assumptions used in the video.
snow sql -c warrant -q "
SELECT (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS WHERE decision='pending') AS pending,
       (SELECT COUNT(*) FROM WARRANT.CORE.FINDINGS)                                 AS findings,
       (SELECT COUNT(*) FROM WARRANT.DATA.RUNBOOKS WHERE doc_id='RB-666')           AS attack_left,
       SYSTEM\$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.INVENTORY','TABLE')  AS inventory_tag;"

# Confirm that the MCP server is registered and both tasks are started.
cortex mcp list
snow sql -c warrant -q "SHOW TASKS IN SCHEMA WARRANT.CORE;"
```

Required state:

- `pending = 0`
- `findings = 0`
- `attack_left = 0`
- `inventory_tag = internal`
- `warrant` appears in `cortex mcp list`
- both Snowflake tasks show `started`

Start `SCAN_FOR_EXCEPTIONS` a few hours before recording if you want the public viewer's rolling
timeline to contain several marks. Do not quote its exact 24-hour run count; it changes naturally.

---

## 0:00–0:35 — Introduce the human problem

**DO:** Start on the public viewer hero, zoomed so the three operational examples are visible but
the counters below are outside the frame. The pipeline is intentionally reset; the CoCo run will
create those counts. Keep the cursor still.

**SAY:**

> Hi, I'm Sathya from Team Argmax, and I built this on my own. Let me start with the Monday
> morning it's for.
>
> An operations lead opens their queue, and there are three things sitting in it.
>
> A quality hold that's been open eighty-two days. A critical part down to five days of stock.
> And a supplier who's normally reliable, suddenly at twenty-six percent on-time.
>
> The dashboard knows about all three. What it doesn't know is what it's allowed to do about
> them.

**DELIVERY:** Do not open with “Hello everyone, today I am going to present.” Say the introduction
as though one judge has just sat beside you. Pause after “built this for” and after each
exception. On the last line, let the ellipsis breathe — that pause is the thesis landing.

## 0:35–1:04 — The real problem

**DO:** Stay on the same screen. Let the three cases remain visible.

**SAY:**

> And those aren't the same kind of decision. Get the supplier call wrong and I apologise. Get
> the stock order wrong and that's real money gone. And a quality record is regulated. Nobody's
> letting software near that.
>
> So you can't turn an agent loose on all three, and one that stops and asks every single time
> isn't worth deploying. The hard part was never finding the problem. It's working out who's
> allowed to act on it.

## 1:04–1:08 — Reveal Warrant

**DO:** Cut to the exported slide-1 title card. Show only the wordmark and tagline for 2–4 seconds.
Do not show PowerPoint or advance through the deck.

**SAY:**

> So that's why I built Warrant. No action without a warrant.

## 1:08–1:42 — The promise

**DO:** Return to the public viewer and point once across the three tag rows: `SHIPMENTS`,
`INVENTORY`, `QUALITY_HOLDS`.

**SAY:**

> Warrant runs one workflow, and it never writes its own permissions. It reads the governance
> tags that are already sitting on the data.
>
> So if the data's open, it goes ahead and does the work. If it's internal, it stops and puts it
> in front of a person. And if it's regulated, it refuses. Anything ambiguous, it assumes less
> authority, never more.
>
> Then it reads those tags again at the moment it executes. Hang on to that, because it matters
> in about a minute.

## 1:42–3:10 — CoCo CLI takes the Monday queue

**DO:** Switch to the terminal and run:

```bash
cortex mcp list
cortex
```

**SAY:**

> Okay. This is Cortex Code CLI — CoCo — and Warrant's running as its MCP server. Thirteen
> tools, five resources, six skills. Eleven of those tools can only read. Two of them can act,
> and they declare that in their annotations.
>
> So, first question. What's it allowed to do right now?

**DO:** Enter this first prompt:

```text
Use the operate-warrant skill. Call governance_posture and authority_manifest, then tell me what Warrant may do right now and which Snowflake tags make that true.
```

**SAY while it responds:**

> And notice none of these tools takes an authority level as an argument. There's no parameter
> there for the model to reach for.

**DO:** Enter the end-to-end prompt:

```text
Using the orchestrate-loop skill, run one full AUTO pass against the live account. Summarise what detection, investigation, authority classification, routing, execution and audit did for each exception.
```

**SAY over the first few seconds:**

> Right. Now the real one. A single prompt, and it takes the whole Monday queue.
>
> The AI's doing the messy part here — reading the evidence, pulling the right procedure out of
> Cortex Search.
>
> These calls take a couple of minutes, so I'm cutting ahead to the result.

**DO:** Make an honest jump cut to the completed response. Keep the three outcomes visible. At
this point the same run has also created the pending SKU-1003 action used in the console section.

**SAY:**

> And there they are. The three from Monday.
>
> The supplier case went through on its own, because `SHIPMENTS` is open. The replenishment was
> prepared and then held, because `INVENTORY` is internal and a person signs that off. And the
> quality hold was escalated, but Warrant never tried to release it. That action isn't in its
> registry.
>
> Same code ran all three. The tags decided how each one ended.
>
> And it doesn't need me sitting here either. Two Snowflake Tasks run this same loop off a
> stream, whether anyone's watching or not.

**DO:** Enter the third, short prompt:

```text
Use the classify-authority skill to compare raise_replenishment with open_supplier_case. Show the touched object, live tag, and final tier for each.
```

**SAY:**

> The model recommends. Snowflake governance is what decides.

This section visibly demonstrates `operate-warrant`, `orchestrate-loop`, and
`classify-authority`, plus multiple MCP tools and the full CLI-driven workflow.

## 3:10–3:33 — The decision that comes back to a person

**DO:** Switch to the Streamlit console. Show the headline tiles, then the SKU-1003 pending card.
Point first to the detector evidence, then the model-generated reasoning and citation.

**SAY:**

> So the stockout's come back to a person, and this is where they'd decide. It's a Streamlit
> console running inside Snowflake, right next to the data, and it's the only surface that can
> actually act.
>
> Evidence on the left, the model's reasoning on the right. It's ready to go, and it hasn't
> happened.

## 3:33–4:18 — Change the policy underneath the decision

**DO:** Switch to the prepared Snowsight worksheet and run:

```sql
ALTER TABLE WARRANT.DATA.INVENTORY
  SET TAG WARRANT.CORE.SENSITIVITY = 'regulated';
```

**SAY:**

> But before the reviewer gets to decide, something changes underneath them. Governance
> reclassifies `INVENTORY` as regulated. That's one tag, and nothing's been redeployed.

**DO:** Return to the console, briefly show the regulated tag, then open the pending action. Use
this reviewer note:

```text
Checked in-transit is zero and SKU-1003 is not on quality hold. Quantity restores to safety-stock minimum.
```

Click **Approve and execute**.

**SAY immediately before clicking:**

> So this was queued under the old policy, and it's about to be approved under the new one.
> Watch.

**DO:** When the refusal appears, stop speaking for two full seconds.

**SAY:**

> Approved. And it still didn't happen.
>
> The executor read today's governance, not yesterday's approval. And the audit keeps both facts.
> A human said yes, and the action never ran.
>
> Because an approval is a decision somebody made at a moment in time. It isn't a permanent
> permission slip.

**IMPORTANT:** The order is queue while `internal` → reclassify to `regulated` → approve →
execution-time tag read → refuse. Never describe it as approve first and reclassify afterwards.

## 4:18–4:45 — What if the model is manipulated?  *(OPTIONAL — cut this first)*

> Dropping this whole beat is the single cleanest way under five minutes: it removes 66
> spoken words and 26 seconds of screen time, and it is the only section the portal's
> stated requirements do not ask for. If you cut it, the close begins at 4:05 and the
> video ends at 4:53.

**DO:** Switch to the terminal and run:

```bash
uv run pytest tests/test_adversarial.py -q
```

**SAY:**

> There's one harder question. What if a document attacks the model itself?
>
> So we planted one. A fake runbook that claims it can override policy. And these tests assume
> the model believed every word of it, then check that nothing could happen anyway.
>
> A model that refuses an attack is encouraging. One that falls for it and still can't do any
> damage — that's a boundary.

## 4:45–5:20 — Resolve the Monday morning

**DO:** Switch to the public viewer. Keep the Vercel URL visible. Click the shortcut **The refusal
that held**, then click **Approve and execute**. Wait until the green “THE BOUNDARY HELD” result is
fully visible.

**SAY:**

> So Monday's queue has an answer. The supplier was handled, the replenishment went back to a
> person with its evidence, and the regulated record was protected.
>
> And this page is public. It's on Vercel, outside Snowflake, but these buttons are real. They
> send the actual statements using a role that can't act. A refusal you can watch is the only
> proof that counts.

**DO:** Click. Pause while the response loads.

**SAY:**

> Green. Snowflake itself refused it, and that's the pass condition.
>
> Warrant knows which work was never its decision to make.
>
> No action without a warrant.

**DO:** Hold on the green refusal panel and visible URL for two seconds, then stop recording.

---

## Delivery notes that make it sound human

- Speak to one judge, not “the audience.” Imagine you are showing the project to a technical
  colleague sitting beside you.
- Use contractions. “It doesn't” sounds natural; “it does not” sounds like documentation.
- Do not narrate every click. Say what the result means.
- Let the refusal breathe. The two-second silence after approval is part of the story.
- Look away from the script during the three key lines:
  - “So blanket autonomy is reckless — but an agent that always stops and asks is useless.”
  - “Approved… and it still didn't happen.”
  - “A model falling for it, and nothing changing — that's a boundary.”
- If a sentence does not sound like you after two read-throughs, rewrite it in your own words while
  keeping the fact and meaning intact.
- Aim for calm confidence, not trailer voice. The product is interesting enough without hype.

### If someone asks what it is, off-script

Not spoken in the video, but have it ready for the description field and for any live question:

> I built Warrant for the moment after an operations dashboard finds a problem. It uses Snowflake
> procedures and AI reasoning to prepare a response, but it reads the live governance tag on the
> affected data before doing anything. So supplier outreach can run, replenishment goes to a
> person, and a regulated quality change is refused—even if someone approved it before the policy
> changed.

## Cut list if the first take runs long

Cut in this order:

1. “Remember that — it matters in a minute.” in the promise. The climax still lands without the
   setup; it just loses a little foreshadowing.
2. “Evidence on the left, the model's reasoning on the right.” in the reviewer section — you are
   pointing at it anyway.
3. “These tests assume the model believed every word, then check that nothing could happen
   anyway.” in the adversarial section.
4. “A refusal you can watch is the only proof that counts.” in the close; keep the Monday
   resolution and final lines.
5. “Eleven of those tools only read; two can act, and they say so in their annotations.” — the
   thirteen-five-six count survives on its own.

Do not cut “no tool here takes an authority level as input” to save four seconds. It is the only
spoken statement of the invariant the deck gives a whole panel to.

Never cut:

- the visible end-to-end CoCo prompt and result;
- the three routed outcomes;
- queue → reclassify → approve → re-read → refuse;
- the two-second pause after the refusal;
- the final public boundary proof.

## Immediately after recording

Restore `INVENTORY` and reset the demo state:

```bash
snow sql -c warrant -q \
  "ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY = 'internal';"

snow sql -c warrant -f sql/90_reset.sql
snow sql -c warrant -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');"
```

Then:

1. Watch the video once at 1× with sound.
2. Confirm terminal text, the governance change, and both refusal panels remain readable after
   compression.
3. Confirm no Snowflake account locator, credentials, notification, or personal information is
   visible.
4. Upload the video as **unlisted**, not private.
5. Open the submitted URL in a signed-out/incognito window.

## Recovery table

| If | Do |
|---|---|
| CoCo takes too long | Keep the start and completed result, then make an honest jump cut. |
| CoCo starts wandering | Stop it, use the exact prompt again, and re-record only that terminal section. |
| CoCo requests permission | Approve it on camera; the operator boundary is relevant evidence. |
| No pending action appears | A prior take consumed it. Run the full pre-flight again. |
| The execution is not refused | Stop. Check that `INVENTORY` is `regulated`; do not narrate around a failed control. |
| A Streamlit panel fails | Re-record after checking query history. Do not turn an unrelated error into a design claim. |
| The public button cannot reach Snowflake | Run `npm run probe` from `web/`. Use a previous verified take only if the probe is green. |
| `warrant` is absent from `cortex mcp list` | Run `cortex mcp add warrant "$PWD/.venv-mcp/bin/python -m warrant_mcp.server" -t stdio`. |
