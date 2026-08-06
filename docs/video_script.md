# Warrant demo video — natural five-minute script

This is the recording script, not submission copy. The portal asks for a 3–5 minute screen
recording of an end-to-end workflow executed through Cortex Code CLI, including input, processing,
output, and two or three modular skills. Timed at the rate a person actually reads aloud while
driving five windows, it runs **4:49**, and a trim block takes it to **4:29** if your read is
slower. Read *Spoken length* before you record anything.

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

## Spoken length — read this before you record

**458 spoken words. At 125 wpm that is 3:39 of speech, plus 70 seconds of action nobody can talk
over, so the video lands at 4:49.**

125 wpm is the honest rate for reading a written script aloud, with feeling, while driving five
windows. The earlier draft assumed 155 wpm and lumped all action into twenty seconds. That is why
every slot overran in practice: a slot marked 1:05–1:42 really took past 2:00, and the error
compounded down the whole timeline.

Action time is now counted per beat, because it is nowhere near evenly spread — the console beat
alone costs more than the old estimate for the entire video:

| Beat | Words | Speech | Action | Slot |
| --- | --- | --- | --- | --- |
| The gap, and the Monday morning | 96 | 46s | 0s | 46s |
| Reveal | 11 | 5s | 3s | 8s |
| The promise | 49 | 24s | 0s | 24s |
| CoCo runs the queue | 147 | 71s | 28s | 99s |
| Console, tag change, refusal | 98 | 47s | 24s | 71s |
| Close | 57 | 27s | 15s | 42s |

**Do one timed read of the SAY blocks alone, out loud, at the pace you will actually record.** Do
not skip this. If your speech-only time exceeds **3:35**, you read slower than 125 wpm and the
untrimmed script breaches five minutes. Apply the trim block below and you land at **4:29**.

For reference: at 115 wpm the untrimmed script runs 5:08, and at 110 wpm it runs 5:19. That is the
whole reason the trim block exists. Do not try to win the time back by speaking faster on camera —
that is what makes a demo sound rushed, and it is the one failure the judges hear immediately.

The adversarial pytest beat is gone from the running order. It cost 66 words plus an eight-second
test run, and it is the only section the portal's stated requirements do not ask for. The full
story lives on deck slide 6 and on the public page, where a judge can read it without a stopwatch.

## What the judge should remember

1. The hard problem is not detection; it is authority.
2. CoCo CLI drives a real end-to-end run through modular Agent Skills and MCP tools.
3. The model proposes, but live Snowflake tags decide.
4. Authority is checked again at execution, so stale approval cannot override new policy.
5. The hostile-document tests assume the model was fooled and prove the boundary still
   holds. Mentioned in the close; demonstrated in the repository and on the public page.
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
- **Paste the prompts and the SQL; do not type them.** Typing a 180-character prompt on camera
  costs twenty seconds the budget does not have, invites a typo that forces a retake, and proves
  nothing — the judge needs to read the prompt, not watch it appear. Paste, let it sit still for one
  beat so it is readable, then press Enter.
- **Two separate files, and only one of them goes on camera.** Saying "let me grab my prompts out
  of notepad" out loud is better than pretending they materialise, so the notepad is in the script
  on purpose. But it must contain *only* the three CoCo prompts and the `ALTER TABLE` line —
  `docs/private/on-camera-prompts.txt`, which is git-ignored. Keep `docs/paste-buffer.txt` with its
  reset commands and pre-flight checklist on a second desktop, minimised, never visible. A viewer
  who reads "Required before you press Record" over your shoulder learns the demo was staged.
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

# SHOW TASKS returns 27 columns and wraps illegibly, so narrow it to what matters.
snow sql -c warrant -q "SHOW TASKS IN SCHEMA WARRANT.CORE;
SELECT \"name\", \"state\", \"schedule\" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));"
```

Required state, and where each value comes from:

| Check | Read it from |
| --- | --- |
| `pending = 0` | the four-counter query, `PENDING` column |
| `findings = 0` | the same query, `FINDINGS` column |
| `attack_left = 0` | the same query, `ATTACK_LEFT` column |
| `inventory_tag = internal` | the same query, `INVENTORY_TAG` column |
| `warrant` appears in `cortex mcp list` | `cortex mcp list`, run inside WSL |
| both tasks show `started` | the narrowed `SHOW TASKS`, `state` column |

Start `SCAN_FOR_EXCEPTIONS` a few hours before recording if you want the public viewer's rolling
timeline to contain several marks. Do not quote its exact 24-hour run count; it changes naturally.

---

## 0:00–0:46 — The gap, and the Monday morning

**DO:** Start on the public viewer hero, zoomed so the three operational examples are visible and
the counters below are outside the frame. The pipeline is intentionally reset; the CoCo run will
create those counts. Keep the cursor still.

**SAY:**

> Every operations dashboard can tell you what's wrong. Not one of them can tell you what you're
> allowed to do about it.
>
> I'm Sathya, Team Argmax, solo developer. Here's the Monday morning I built this for.
>
> An operations lead opens their queue. A quality hold, open eighty-two days. A critical part down
> to five days of stock. A supplier suddenly at twenty-six percent on-time.
>
> Get the supplier call wrong and I apologise. Get the stock order wrong and that's real money
> gone.
>
> The hard part isn't finding the problem. It's who's allowed to act on it.

**DELIVERY:** The first two sentences are the whole pitch — say them slowly, then pause before
your name. Do not open with "Hello everyone, today I am going to present." Pause after each of the
three exceptions. Look up from the phone on the last line.

## 0:46–0:54 — Reveal Warrant

**DO:** Cut to the exported slide-1 title card. Wordmark and tagline only, 3 seconds. Do not show
PowerPoint or advance through the deck.

**SAY:**

> So that's why I built Warrant. No action without a warrant.

## 0:54–1:17 — The promise

**DO:** Return to the public viewer and point once across the three tag rows: `SHIPMENTS`,
`INVENTORY`, `QUALITY_HOLDS`.

**SAY:**

> Warrant never writes its own permissions. It reads the governance tags that are already sitting
> on the data.
>
> If the data's open, it just does the work. If it's internal, a person decides. If it's regulated,
> it refuses.
>
> And it reads those tags again at the moment it executes.

## 1:17–2:56 — CoCo CLI takes the Monday queue

**DO:** Switch to the terminal and run:

```bash
cortex mcp list
cortex
```

**SAY:**

> This is Cortex Code CLI — CoCo — running here on WSL, with Warrant registered as its MCP server.
> Thirteen tools, five resources, six skills. Two of them can act, and they say so in their
> annotations.

**DO:** Bring up the notepad holding the three prompts, then paste the first one.

**SAY while you open it:**

> Let me grab my prompts out of notepad.

```text
Use the operate-warrant skill. Call governance_posture and authority_manifest, then tell me what Warrant may do right now and which Snowflake tags make that true.
```

**SAY while it responds:**

> And notice, none of these tools takes an authority level as an argument.

**DO:** Paste the end-to-end prompt:

```text
Using the orchestrate-loop skill, run one full AUTO pass against the live account. Summarise what detection, investigation, authority classification, routing, execution and audit did for each exception.
```

**SAY over the first few seconds:**

> Now one prompt takes the whole Monday queue. The AI pulls the right procedure out of Cortex
> Search. This takes a couple of minutes, so I'm cutting ahead.

**DO:** Make an honest jump cut to the completed response. Keep the three outcomes visible. The
same run also creates the pending SKU-1003 action used in the console section.

**SAY:**

> There they are. The supplier case ran on its own, because `SHIPMENTS` is open. The replenishment
> was prepared and then held, because `INVENTORY` is internal and a person signs that off. The
> quality hold was escalated, and Warrant never tried to release it.
>
> And it doesn't need me. Two Snowflake Tasks run this loop off a stream.

**DO:** Paste the third, short prompt:

```text
Use the classify-authority skill to compare raise_replenishment with open_supplier_case. Show the touched object, live tag, and final tier for each.
```

**SAY:**

> The model recommends. The tags decide.

This section visibly demonstrates `operate-warrant`, `orchestrate-loop`, and `classify-authority`,
plus multiple MCP tools and the full CLI-driven workflow.

## 2:56–4:07 — Back to a person, then the policy moves

**DO:** Switch to the Streamlit console. Show the headline tiles, then the SKU-1003 pending card
with its evidence and model reasoning.

**SAY:**

> So the stockout comes back to a person. This is a Streamlit console running inside Snowflake,
> right next to the data, and it's the only surface that can actually act.

**DO:** Switch to the prepared Snowsight worksheet and run:

```sql
ALTER TABLE WARRANT.DATA.INVENTORY
  SET TAG WARRANT.CORE.SENSITIVITY = 'regulated';
```

**SAY:**

> But before the reviewer decides, something changes underneath them. Governance reclassifies
> `INVENTORY` as regulated. Nothing's been redeployed.

**DO:** Return to the console, briefly show the regulated tag, open the pending action, paste this
reviewer note, then click **Approve and execute**.

```text
Checked in-transit is zero and SKU-1003 is not on quality hold. Quantity restores to safety-stock minimum.
```

**SAY immediately before clicking:**

> Queued under the old policy, about to be approved under the new one. Watch.

**DO:** When the refusal appears, stop speaking for two full seconds.

**SAY:**

> Approved. And it still didn't happen.
>
> The executor read today's governance, not yesterday's approval. A human said yes, the action
> never ran, and the audit keeps both.
>
> An approval is a decision, not a permanent permission slip.

**IMPORTANT:** The order is queue while `internal` → reclassify to `regulated` → approve →
execution-time tag read → refuse. Never describe it as approve first and reclassify afterwards.

## 4:07–4:49 — Resolve the Monday morning

**DO:** Switch to the public viewer. Keep the Vercel URL visible. Click the shortcut **The refusal
that held**, then click **Approve and execute**. Wait until the green "THE BOUNDARY HELD" result is
fully visible.

**SAY:**

> So Monday's queue has an answer. The supplier was handled, the replenishment went to a person,
> and the regulated record was protected.
>
> This page is public. It's on Vercel, outside Snowflake, but these buttons are real — they send
> the actual statements with a role that can't act.

**DO:** Click. Pause while the response loads.

**SAY:**

> Green. Snowflake itself refused it.
>
> No action without a warrant.

**DO:** Hold on the green refusal panel and visible URL for two seconds, then stop recording.

---

## Delivery notes that make it sound human

- Speak to one judge, not "the audience." Imagine you are showing this to a technical colleague
  sitting beside you.
- Use contractions. "It doesn't" sounds natural; "it does not" sounds like documentation.
- Say your own asides out loud rather than editing around them. "Running here on WSL" and "let me
  grab my prompts out of notepad" are in the script on purpose — they sound like a person working,
  and they explain the paste instead of hiding it. Keep the notepad to the three prompts only, so
  nothing else is legible when it appears.
- Do not narrate every click. Say what the result means.
- Let the refusal breathe. The two-second silence after approval is part of the story.
- Look away from the script on these three lines:
  - "Not one of them can tell you what you're allowed to do about it."
  - "Approved. And it still didn't happen."
  - "No action without a warrant."
- If a sentence does not sound like you after two read-throughs, rewrite it in your own words and
  keep the fact.
- Aim for calm confidence, not trailer voice. The product is interesting enough without hype.

### If someone asks what it is, off-script

Not spoken in the video, but have it ready for the description field and for any live question:

> I built Warrant for the moment after an operations dashboard finds a problem. It uses Snowflake
> procedures and AI reasoning to prepare a response, but it reads the live governance tag on the
> affected data before doing anything. So supplier outreach can run, replenishment goes to a
> person, and a regulated quality change is refused—even if someone approved it before the policy
> changed.

## Trim block — apply if your timed read exceeds 3:35 of speech

Six whole sentences. Together they remove 42 words and about 20 seconds, taking the video from
**4:49 to 4:29**. Cut them entirely; do not half-say them.

1. `Let me grab my prompts out of notepad.` — just open it silently.
2. `And it reads those tags again at the moment it executes.` — the climax still lands, it just
   arrives as a surprise rather than a payoff.
3. `There they are.`
4. `An approval is a decision, not a permanent permission slip.` — the sentence before it already
   says the same thing with evidence attached.
5. `So Monday's queue has an answer.`
6. `This page is public.` — fold it into the next sentence, which names Vercel anyway.

Do not cut `And notice, none of these tools takes an authority level as an argument.` Thirteen
words, and it is the only spoken statement of the invariant the deck gives a whole panel to.

If a timed read still exceeds **4:00 of speech** after all six, drop the third CoCo prompt
(`classify-authority`) and its one line. That costs a named skill but keeps you at two, which still
satisfies the portal's "2-3 modular skills", and it buys eight seconds of action time as well.

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
| `warrant` is absent from `cortex mcp list` | From the repo root, run `cortex mcp add warrant "$PWD/.venv-wsl/bin/python" -m warrant_mcp.server -t stdio -e PYTHONPATH="$PWD/mcp"`. |
