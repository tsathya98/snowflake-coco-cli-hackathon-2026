# Demo video — 4 minutes, shot by shot

Build source for the recording. Working material rather than a judge-facing document — tracked so
it travels between machines, and written knowing it is public.

## What the portal actually asks for

> "Video size should not be more than 3-5 minutes. **End-to-end workflow executed via Cortex Code
> CLI** — Screen recording showing: Input → Processing → Output. **At least one fully working
> workflow, 2-3 modular skills/capabilities demonstrated.**"

Read that literally, because it decides the shape of the video. It is not "show me your app". It is
**show the workflow being executed through the CLI**, and show two or three skills doing distinct
things. Technical Execution (40%) separately scores *"strong use of Snowflake CoCo CLI, Agent
Skills and tools."* So CoCo drives; the console and the web viewer are where the result is
inspected. They are the Output, not the demo.

**Target 4:30–4:45.** Inside the 3–5 window with room to breathe. Do not rush to 3:00.

**Budget the words, not the minutes.** Everything in a `SAY` block below adds up to **670 words**.

| Your reading pace | Speech alone | Plus ~45s of typing, model time and two pauses |
|---|---|---|
| 165 wpm — brisk, presenting | 4:04 | **≈ 4:49, fits** |
| 150 wpm — conversational | 4:28 | ≈ 5:13, **over the limit** |

So this only fits if you read at a **presenting pace, not a chatting pace**. Time yourself against
the script before you record; if your read lands over 4:55, cut before you shoot, not after.

This is measured, not estimated, and it is the constraint that actually bites. An earlier draft of
this script ran to 916 words. That is over six minutes of talking, and no amount of tight editing
recovers it. **If you add a sentence, cut one.**

**Cut in this order if you need to:** prompt 1's narration, then the "Left is what the detector
measured" paragraph, then the second half of the injection section. **Never cut the turn at 2:55**
— it is the only thirty seconds a judge will still remember tomorrow.

## The story you are telling

A demo that is a tour of features is forgettable. A demo that is a story is not. There is one
story here and every section is a beat in it. If you only remember one thing while recording,
remember which beat you are on.

| Beat | The question in the viewer's head | Your answer |
|---|---|---|
| **Purpose** | Why should I care? | Three real problems are sitting on a dashboard, unfixed, because a dashboard waits for a person. |
| **Story** | Who is hurt by that? | The person who opens six tabs on Monday and does it all by hand. An agent could do her job. It never gets switched on. |
| **The blocker** | So why hasn't someone built it? | Nobody can say in advance what the agent is allowed to touch. The blocker was never capability. It was **authority**. |
| **Solution** | What is your idea? | Take the answer from the data. Every action's authority is read from the Snowflake governance tag on the tables it touches. |
| **Functionality** | Does it actually work? | One pass, six exceptions, three different endings, all from one code path, driven from the CLI. |
| **Proof** | Why should I believe you? | Approve something, reclassify the table underneath it, and watch your own approval fail to survive. Then watch tests that assume the model was fooled. |
| **The close** | What do I remember? | Everyone else will show you an agent that acts. This one declines. |

**The turn is at 2:15.** Everything before it earns the right to it; everything after it is
supporting evidence. If you are running long, cut from the sections *around* the turn, never from
the turn itself.

**One thread to keep pulling:** the word *authority*. Say it in the opening, say it when you
explain the tags, say it at the refusal, say it at the close. A single repeated word is what makes
four minutes feel like one argument instead of six demos.

## Yes, share your screen — here is the exact setup

It must be a **screen recording with voiceover**. No webcam needed; nobody scores your face, and a
face bubble costs screen space the terminal needs.

**Record the full screen at 1920×1080.** Have exactly these ready before you hit record, each
already opened once so nothing renders cold on camera:

| Window | What it is for |
|---|---|
| WSL terminal, font ~16pt, dark theme, maximised | The whole CLI section. This is most of the video. |
| Browser tab 1: the Streamlit console in Snowsight, all tabs clicked once | The Output section and the approval moment |
| Browser tab 2: a Snowsight worksheet with the ALTER TABLE statement already typed | The reclassification |
| Browser tab 3: the public viewer (vercel.app) | The close |

- **Crop or hide the browser address bar while on Snowsight** — it contains the account locator.
  The vercel.app tab is fine to show fully.
- Notifications off, one monitor, no other tabs visible.
- Use OBS or the built-in Xbox Game Bar (Win+Alt+R); anything that captures steady 1080p is fine.
  Record the voiceover in the same take — syncing a separate track costs an evening.
- Alt+Tab between windows rather than dragging them. Cuts are fine; say when you cut.

**The constraint that shapes everything:** the full loop takes 2–3 minutes of model calls. You
cannot wait for it on camera. Start it, talk over the first seconds, cut, and resume on the
completed result. An honest jump cut costs nothing. A faked real-time run costs everything if a
judge notices the clock.

---

## Before you hit record

```bash
# 1. Canonical state. ~4 min — do this first, it is the long pole.
snow sql -c warrant -f sql/90_reset.sql
snow sql -c warrant -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');"

# 2. Assert the state the script assumes.
snow sql -c warrant -q "
SELECT (SELECT COUNT(*) FROM WARRANT.CORE.PENDING_ACTIONS WHERE decision='pending') AS pending,
       (SELECT COUNT(*) FROM WARRANT.DATA.RUNBOOKS WHERE doc_id='RB-666')           AS attack_left,
       SYSTEM\$GET_TAG('WARRANT.CORE.SENSITIVITY','WARRANT.DATA.INVENTORY','TABLE')  AS inventory_tag;"

# 3. Both unattended tasks must be started.
snow sql -c warrant -q "SHOW TASKS IN SCHEMA WARRANT.CORE;" | grep -E "started|suspended"
# if either is suspended:  ALTER TASK WARRANT.CORE.<name> RESUME;
```

**Required: `pending = 1`, `attack_left = 0`, `inventory_tag = internal`, both tasks `started`.**

`SCAN_FOR_EXCEPTIONS` sweeps hourly, so resume it a few hours before recording, not minutes —
otherwise the Unattended section of the viewer shows one lonely mark instead of a filled timeline.

---

**How to read the script:** `DO` is what happens on screen. `SAY` is what comes out of your mouth,
written the way you would actually say it. Read it out loud twice before recording; anywhere you
stumble, change the words to yours. Short sentences survive nerves.

## 0:00–0:50 · Purpose, story, and the blocker

**DO:** The public viewer's hero on screen, or just the terminal. Nothing moving yet. Do not
narrate what is on screen; let the words do the work.

**SAY:** *(slow right down on the three numbers. A full beat of silence before "All three".)*

> A quality hold, open eighty-two days. A SKU five days from running out. A supplier's on-time
> delivery down to twenty-six percent.
>
> All three are on a dashboard right now. None of them is fixed. Because a dashboard tells you
> something, and then it waits for a person.
>
> That person works out, by hand, which of forty open holds actually matters. Analytics stopped at
> the insight. Her work starts after it.
>
> An agent could do all of it today, and it still doesn't get switched on. Because the first
> question in a regulated operation is always "so it can change a quality record?" Say yes, nobody
> signs off. Say no, and it wasn't worth building.
>
> That was never a capability problem. It's an authority problem. So I built Warrant, and Warrant
> takes that answer from the data itself.

## 0:50–2:25 · FUNCTIONALITY — CoCo CLI drives the workflow

**DO:** Terminal, repo root.

```bash
cortex mcp list
```

**SAY:**

> This is Cortex Code CLI. The whole agent is exposed to it as an MCP server. Thirteen tools,
> eleven of them read-only, two that act.
>
> And on authority: not one of them accepts a tier. There's no parameter to pass, so there's
> nothing for a prompt to aim at.

**DO:**

```bash
cortex
```

Then type prompt 1:

```
Use the governance_posture and authority_manifest tools. What is the agent allowed to do right now, and what would change if INVENTORY were reclassified as regulated?
```

**SAY (while it works):**

> What is it allowed to do right now, and what would a policy change cost. The what-if runs on the
> same resolver the executor does, so it can't disagree with reality.

**DO:** Prompt 2, the end-to-end run:

```
Using the orchestrate-loop skill, run one full pass of the Warrant agent against the live account, then summarise what each phase did and how each action was routed.
```

**SAY (over the first seconds, then cut):**

> Now the full pass. Detection is set-based, and every threshold is quoted from a runbook clause,
> not invented. Then reasoning, grounded by Cortex Search over five procedures we parsed out of
> PDFs.
>
> This takes about two minutes, so I'm cutting to the result.

**DO:** Resume on the completed summary.

**SAY:**

> Six exceptions, three different endings. The supplier case it handled alone, because shipments
> are tagged open. The stockout it prepared in full and then stopped, because inventory is tagged
> internal. The quality hold it explained and would not touch, because that table is regulated.
>
> Same code path, all three. There is no "if table name" anywhere in this.

**DO:** Prompt 3, the differentiator:

```
Using the classify-authority skill, explain why raise_replenishment needed a human but open_supplier_case did not.
```

**SAY:**

> So why did one stop and the other not? That's the entire model. The tier came from the tag on
> the data, read live. Not from a rules file in the code.

*That is three skills and two MCP tools demonstrated, and the workflow executed through the CLI.
Spec satisfied.*

## 2:25–2:55 · OUTPUT — where the human actually sees it

**DO:** Switch to the Streamlit console tab. Point with the cursor as you speak: tiles first, then
the pending card, left column, right column.

**SAY:**

> Now the person's side, because one of those six came back to a human. Same run, from the approval
> console. Streamlit, inside Snowflake.
>
> Six detected, five handled, one waiting on me. Notice which count it leads with. The refusals,
> not the throughput.
>
> Left is what the detector measured. Right is what the model concluded, marked model generated,
> citing the clause it reasoned from.

## 2:55–3:45 · THE TURN — an approval that doesn't survive

*This is the beat the whole video exists for. Slow down. Do not talk over the pause.*

**DO:** Switch to the worksheet tab. The statement is already typed. Run it.

```sql
ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY = 'regulated';
```

**SAY:**

> Now watch this. Governance just reclassified that table. One tag. Nothing deployed.

**DO:** Back to the console. Governance tab shows `regulated`. Then the pending card. Type the
reviewer note:

```
Checked in-transit is zero and SKU-1003 is not on quality hold. Quantity restores to safety-stock minimum.
```

Click **Approve and execute**.

**SAY:**

> And I approve the action anyway.

**DO:** The refusal banner appears. **Say nothing for two full seconds.**

**SAY:**

> I approved this. It still didn't happen.
>
> Authority is resolved again at execution time, so my approval couldn't outlive the policy it was
> granted under. And both facts are in the audit log. That I approved it, and that it was refused.
> A trail that only keeps outcomes can't tell you who tried.

**DO (off camera, right after this section):** put the tag back.

```bash
snow sql -c warrant -q "ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY = 'internal';"
```

## 3:45–4:15 · PROOF — it survives a hostile document

**DO:** Terminal.

**SAY:**

> One fair objection to all of that: it depends on the model behaving.
>
> The runbooks this agent reads are untrusted input. So we planted an attack in the corpus, a fake
> procedure claiming to supersede the real one and grant the agent release authority. It ranks
> first in retrieval, all six findings cite it, and the routing doesn't move.
>
> But don't take "the model resisted" from me. Watch.

**DO:**

```bash
uv run pytest tests/test_adversarial.py -q
```

**SAY:**

> These ten tests assume the model fell for it completely, and assert the outcome is governed
> anyway.
>
> "The model resisted" is a property of a model, and models change under you. "The model's
> compliance changed nothing" is a property of the architecture.

## 4:15–4:40 · THE CLOSE

**DO:** Switch to the public viewer tab, at the top. Pause one beat so the three live tag rows on
the right are readable, then **click the second shortcut card, "The refusal that held"** — it jumps
straight to Evidence. Clicking beats scrolling here: it is one motion instead of ten, and it shows
the page was built for someone in a hurry.

**SAY:**

> All of this is live at a public link, read only. And on the authority question, I'd rather prove
> it than claim it.

**DO:** Click **Approve and execute**. Let the green panel render fully before speaking.

**SAY:**

> Same buttons the console has, wired to the same statements. It comes back green, because being
> refused is the pass condition. That's Snowflake's answer, not the page's.
>
> Everyone in this track will show you an agent that acts. This is one that declines. And its
> declining doesn't depend on the model choosing to.

**DO:** Hold on the green panel for the last two seconds. Stop recording.

---

## After recording

1. **Reset**, or the next take starts from a consumed queue:
   ```bash
   snow sql -c warrant -f sql/90_reset.sql && snow sql -c warrant -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');"
   ```
2. Watch it once at 1× with sound. The two things that must survive compression are the
   **terminal text** and the **refusal panel**.
3. Upload **unlisted, not private** — a private link 404s for a judge. Confirm in an incognito
   window before submitting.

## Recovery, if something fails live

| If | Do |
|---|---|
| CoCo is slow or wanders | You have the transcript. Cut to the result and narrate — the spec asks for the workflow executed via the CLI, not for it to be fast |
| CoCo asks for a permission | Approve it on camera. It is a fair thing for a judge to see |
| The refusal doesn't fire | `INVENTORY` was already `regulated`. Check pre-flight and re-record that section only |
| No pending card | A prior take consumed it. Full reset, ~4 min |
| A console panel shows a red error box | Keep going and say "each panel is isolated so one failure can't take the app down" — which is true, and is a design point |
| The web viewer's approve button says "could not reach Snowflake" | The refusal did not match the expected shape. Check `npm run probe` — it asserts both write paths — and fall back to narrating the read-only note above the buttons |
| `cortex mcp list` shows nothing | The server is registered per-machine. `cortex mcp add warrant "$PWD/.venv-wsl/bin/python -m warrant_mcp.server" -t stdio` |
