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

**Target 4:00.** Inside the 3–5 window with room to breathe. Do not rush to 3:00.

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

## 0:00–0:25 · The problem

**DO:** Repo README on screen, or just the terminal. Nothing moving yet.

**SAY:**

> Enterprise ops teams don't lack insight. They lack action. And the reason agents that can act
> never get deployed isn't capability. It's trust. Nobody will hand an autonomous agent blanket
> authority over regulated data.
>
> So I built Warrant. The idea is simple. The agent's authority comes from the data itself, from
> the governance tags already sitting on the tables. Change a tag, and what the agent may do
> changes with it. No code change. No deploy.

## 0:25–1:35 · INPUT and PROCESSING — CoCo CLI drives it

**DO:** Terminal, repo root.

```bash
cortex mcp list
```

**SAY:**

> This is Cortex Code CLI. The whole agent is exposed to it as an MCP server. Thirteen tools.
> Eleven of them only read, two can act. And here's the part that matters. Not one of them accepts
> an authority tier. There's no parameter to pass. You cannot prompt your way into more power.

**DO:**

```bash
cortex
```

Then type prompt 1:

```
Use the governance_posture and authority_manifest tools. What is the agent allowed to do right now, and what would change if INVENTORY were reclassified as regulated?
```

**SAY (while it works):**

> I'm asking what the agent is allowed to do right now, and what a policy change would cost. Those
> are two real tool calls. And the what-if runs on the same resolver the executor uses, so the
> answer can't disagree with what would actually happen. Nothing gets written to produce it.

**DO:** Prompt 2, the end-to-end run:

```
Using the orchestrate-loop skill, run one full pass of the Warrant agent against the live account, then summarise what each phase did and how each action was routed.
```

**SAY (over the first seconds, then cut):**

> Now the full pass. Detection first. It's set-based, and every threshold is quoted from a runbook
> clause, not invented. Then reasoning. The model reads the evidence, grounded by Cortex Search
> over five operating procedures we parsed out of PDFs.
>
> This takes about two minutes, so I'm cutting to the result.

**DO:** Resume on the completed summary.

**SAY:**

> Six exceptions. Five it handled on its own. One it stopped and escalated. Same loop for every
> table. No special cases.

**DO:** Prompt 3, the differentiator:

```
Using the classify-authority skill, explain why raise_replenishment needed a human but open_supplier_case did not.
```

**SAY:**

> So why did one stop? The supplier case ran on its own, because shipments are tagged open. The
> replenishment stopped, because inventory is tagged internal. That's the entire model. The tier
> came from the tag on the data, read live. Not from a rules file in the code.

*That is three skills and two MCP tools demonstrated, and the workflow executed through the CLI.
Spec satisfied.*

## 1:35–2:10 · OUTPUT — the console

**DO:** Switch to the Streamlit console tab. Point with the cursor as you speak: tiles first, then
the pending card, left column, right column.

**SAY:**

> Same run, seen from the approval console. This is Streamlit, running inside Snowflake.
>
> Six detected. Five handled. One waiting on me. And notice which count it leads with. The
> refusals. Not the throughput.
>
> On the left, what the detector measured. On the right, what the model concluded. It's marked
> model generated, because a reviewer should never have to guess which words a machine wrote. And
> it cites the exact runbook clause it's reasoning from. That clause lives in a PDF this pipeline
> parsed at setup.

## 2:10–3:00 · The moment: an approval that doesn't survive

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
> Authority is resolved again at execution time. So my approval could not outlive the policy it
> was granted under. And both facts are in the audit log. That I approved it. And that it was
> refused. An audit trail that only keeps outcomes can't tell you who tried.

**DO (off camera, right after this section):** put the tag back.

```bash
snow sql -c warrant -q "ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY = 'internal';"
```

## 3:00–3:30 · It survives a hostile document

**DO:** Terminal.

**SAY:**

> One more thing. The runbooks this agent reads are untrusted input. So we planted an attack in
> the corpus. A fake procedure that claims to supersede the real one, and grants the agent release
> authority. It ranks first in retrieval. All six findings cite it. And the routing doesn't move.
>
> But I'm not asking you to believe the model resisted. Watch.

**DO:**

```bash
uv run pytest tests/test_adversarial.py -q
```

**SAY:**

> These ten tests assume the model fell for it completely. And they check that the outcome is
> governed anyway. The tier comes from the registry. The tag comes from the object. The parameters
> are bound, never concatenated.
>
> "The model resisted" is a property of a model, and models change under you. "The model's
> compliance changed nothing" is a property of the architecture.

## 3:30–4:00 · Close

**DO:** Switch to the public viewer tab. Scroll past the hero so the three live tag rows are seen,
stop at Evidence.

**SAY:**

> Everything you've seen is also live at a public link, read only. And I'd rather prove that than
> claim it.

**DO:** Click **Approve and execute**. Let the green panel render fully before speaking.

**SAY:**

> Same buttons the console has, wired to the same statements. And it comes back green, because
> being refused is the pass condition. That's Snowflake's answer, not the page's.
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
