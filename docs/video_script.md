# Demo video — 4 minutes, shot by shot

**Gitignored working material.** Build source for the recording, not a judge-facing document.

## What the portal actually asks for

> "Video size should not be more than 3-5 minutes. **End-to-end workflow executed via Cortex Code
> CLI** — Screen recording showing: Input → Processing → Output. **At least one fully working
> workflow, 2-3 modular skills/capabilities demonstrated.**"

Read that literally, because it decides the shape of the video. It is not "show me your app." It is
**show the workflow being executed through the CLI**, and show two or three skills doing distinct
things. Technical Execution (40%) separately scores *"strong use of Snowflake CoCo CLI, Agent Skills
and tools."*

So CoCo drives. The console and the web viewer are where the *result* is inspected — they are the
Output, not the demo.

**Target 4:00.** Inside the 3–5 window with room to breathe. Do not rush to 3:00.

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
```

**Required: `pending = 1`, `attack_left = 0`, `inventory_tag = internal`.**

```bash
# 3. Both unattended tasks must be started, or the timeline on the web viewer shows an empty lane.
snow sql -c warrant -q "SHOW TASKS IN SCHEMA WARRANT.CORE;" | grep -E "started|suspended"
# if either is suspended:  ALTER TASK WARRANT.CORE.<name> RESUME;
```

Both must read `started`. `SCAN_FOR_EXCEPTIONS` sweeps hourly, so if you resume it just before
recording the Unattended section will show one lonely mark; leave it running a few hours and the
timeline fills in, which is the whole point of that shot.

- Terminal at **~16pt**, dark theme, window ~1400px wide. Anything smaller is unreadable after
  compression.
- Console tab open and showing **Active**, all tabs clicked once so nothing renders cold on camera.
- Web viewer open in a second tab.
- **Crop out the browser address bar** — it contains the account locator.
- Notifications off. One monitor. 1080p.

**The constraint that shapes everything:** `RUN_LOOP` takes 2–3 minutes — six model calls. You
cannot wait for it on camera. So section 2 starts it, you narrate over the first part, and you cut
to the completed result. Say that you cut. An honest jump-cut costs nothing; a fake real-time run
costs everything if a judge notices the clock.

---

## 0:00–0:25 · The problem

*No screen yet, or just the repo README.*

> "Enterprise ops teams don't lack insight — they lack action. And the reason agents that can *act*
> don't get deployed isn't capability. It's that nobody will grant one blanket authority over
> regulated data.
>
> So the question I set out to answer is: where does an agent's authority actually come from? My
> answer is that it should come from the data's own governance metadata — not from a rules list in
> application code."

---

## 0:25–1:35 · INPUT and PROCESSING — CoCo CLI drives the workflow

*Terminal, in the repo root. This is the section the spec is asking for.*

**Show the tools exist before using them.** The rubric scores *"strong use of Snowflake CoCo CLI,
Agent Skills **and tools**"* — so spend eight seconds proving there is a real tool surface, not just
a chat window.

```bash
cortex mcp list
```

> "The whole agent is exposed to CoCo as an MCP server: thirteen tools, eleven of them read-only,
> two that act. And no tool on it accepts an authority tier — there's no parameter to pass and no
> elevated value to ask for, so you can't prompt your way into a higher one."

```bash
cortex
```

> "Cortex Code CLI, open in the project. It loads `AGENTS.md` and six Agent Skills from
> `.cortex/skills/` — one per phase of the loop, plus one for operating it from here."

**Prompt 1 — a real tool call, and the differentiator, in one:**

```
Use the governance_posture and authority_manifest tools. What is the agent allowed to do right now, and what would change if INVENTORY were reclassified as regulated?
```

> "That's two MCP tools. The first reads the live tags; the second resolves every action in the
> registry against them. And the what-if is answered by the same resolver the executor uses — so it
> can't disagree with what would actually happen. Nothing was written to answer it."

**Prompt 2 — this is the end-to-end execution. Say the phases out loud as it works:**

```
Using the orchestrate-loop skill, run one full pass of the Warrant agent against the live account, then summarise what each phase did and how each action was routed.
```

> "That's detection running as a set-based MERGE off dynamic-table baselines — every threshold
> quoted from a runbook clause rather than chosen. Then reasoning: `AI_COMPLETE` under a JSON
> schema, grounded by Cortex Search over five operating procedures we parsed out of PDFs with
> `AI_PARSE_DOCUMENT`."

**⟶ Cut here.** Resume on the completed output.

> "Six exceptions. Five it handled on its own, one it stopped and escalated. Same loop, no
> `if table_name ==` anywhere."

**Prompt 3 — the third skill, and the differentiator:**

```
Using the classify-authority skill, explain why raise_replenishment needed a human but open_supplier_case did not.
```

> "There it is. The tier came from `SYSTEM$GET_TAG` on the tables each action touches — read live,
> never cached. `SHIPMENTS` is tagged open, so the supplier case just ran. `INVENTORY` is tagged
> internal, so the replenishment stopped and waited for me."

*That is three skills demonstrated, and the workflow executed through the CLI. Spec satisfied.*

---

## 1:35–2:10 · OUTPUT — the console

*Switch to the Streamlit console.*

> "Same run, in the approval console — Streamlit in Snowflake, inside the governed perimeter."

Point at the header tiles, then the pending card.

> "Six detected, five handled, one waiting on me, and the count it leads with is the refusals — not
> the throughput."

Point left, then right, on the card.

> "Left is what the detector measured. Right is what the model concluded, marked *model-generated*,
> because a reviewer should never have to guess which parts a machine wrote. It cites RB-002 §5 — a
> clause in a PDF the pipeline parsed at setup. And the tier rationale names the tag that forced the
> escalation."

---

## 2:10–3:00 · **The moment.** An approval that doesn't survive

*Worksheet, statement already typed. Run it.*

```sql
ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY = 'regulated';
```

> "Now governance reclassifies that table. No deploy. No code change. One tag."

*Console → Governance tab. It reads `regulated`.*

> "Read live, on every render."

*→ Awaiting your decision. Type a real reviewer's note:*

```
Checked in-transit is zero and SKU-1003 is not on quality hold. Quantity restores to safety-stock minimum.
```

*Click **Approve and execute**.*

> "And I approve it anyway."

*It refuses. **Let the red banner sit for two full seconds before speaking.***

> "I approved this. It still didn't happen.
>
> Authority is resolved *again* at execution time, so my approval couldn't outlive the policy it was
> granted under. Both facts are in the append-only log — that I approved, and that it was refused.
> An audit trail that only keeps the outcome can't tell you who tried."

*Put it back — off camera or fast:*

```bash
snow sql -c warrant -q "ALTER TABLE WARRANT.DATA.INVENTORY SET TAG WARRANT.CORE.SENSITIVITY = 'internal';"
```

---

## 3:00–3:30 · It survives a hostile document

> "The corpus is untrusted input, so we planted an attack in it — a fake procedure that claims to
> supersede RB-003 and grant the agent release authority. It ranks *first* for a quality query, and
> all six findings cite it. The routing doesn't move.
>
> But that's the weaker claim, and I'd rather show you the stronger one. I'm not asking you to
> believe the model resisted —"

```bash
uv run pytest tests/test_adversarial.py -q
```

> "— ten tests that **assume it complied completely**, and assert the outcome anyway. The tier comes
> from the registry. The tag comes from the object. The parameters are bound. 'The model resisted'
> is a property of a model that changes under you. 'The model's compliance changed nothing' is a
> property of the architecture."

---

## 3:30–4:00 · Close

*Web viewer. Scroll past the hero — the three tag rows resolve live — and stop at Evidence.*

> "Everything you've seen is also live at a public URL, read-only. And I'd rather show you that
> than assert it."

*Click **Approve and execute**. Let the panel render before you speak.*

> "Same buttons the console has, wired to the same statements — and it comes back green, because
> being refused is the pass condition. That's Snowflake's answer, not the page's. Read it closely:
> it isn't *permission denied*. Without USAGE on the procedure, Snowflake won't concede the
> executor exists. This role can't be talked into calling something it can't name.
>
> Everyone in this track will show you an agent that acts. This is one that **declines** — and whose
> declining doesn't depend on the model choosing to."

*Hold on the refusal for the last two seconds.*

---

## After recording

1. **Reset**, or the next run starts from a consumed queue:
   ```bash
   snow sql -c warrant -f sql/90_reset.sql && snow sql -c warrant -q "CALL WARRANT.CORE.RUN_LOOP('AUTO');"
   ```
2. Watch it once at 1× with sound. The only two things that must be legible at compression are the
   **terminal** and the **red refusal banner**.
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
