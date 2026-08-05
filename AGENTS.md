# AGENTS.md — project context for CoCo CLI

Loaded automatically at session start. Keep it short and current.

> 🔴 **Deploy the console with `sql/36_console.sql`, never with `snow streamlit deploy`.**
> The CLI path produces an app *object* that fails to load with an unattributable "Python
> Interpreter Error" — the cause is the object, not the app file. `sql/36_console.sql` records
> the diagnosis and the four object properties that differ.
>
> The transferable lesson is in §4: when Streamlit in Snowflake reports a bare
> "Python Interpreter Error", check `INFORMATION_SCHEMA.QUERY_HISTORY` for queries from the app
> *before* forming any theory about the code. Zero queries means zero lines executed, and every
> hypothesis about dtypes, emoji or widgets is then aimed at a stage that never ran.

## What this project is

**Warrant** — a governed autonomous operations agent on Snowflake, for the Snowflake CoCo CLI
Hackathon 2026, Problem Statement 1 (Intelligent Workflow Automation Agent).

The loop: **detect an operational exception → reason about it → classify what authority the
response requires → act or escalate → audit.**

The differentiator: **authority tier is derived from Snowflake object tags on the data an action
touches**, not from a hardcoded rules list. Governance policy and agent behaviour are the same
artifact.

## Hard constraints — do not violate

- **Python only** for application logic (the hackathon rules mandate Python/Java/Scala and score it).
  No TypeScript, no Go.
- **Everything runs inside Snowflake.** No external LLM APIs — use `AI_COMPLETE`. No external
  orchestration. External Access Integrations are unavailable on trial accounts anyway.
- **Synthetic data only.** Never introduce real, proprietary, or personal data.
- **Never commit secrets.** The repo is statically analysed for security as part of judging.
  Credentials live in `~/.snowflake/connections.toml`, never here.
- **Authority defaults down, never up.** If tier resolution is ambiguous, escalate.
- All SQL must be **idempotent** — `CREATE OR REPLACE` / `CREATE IF NOT EXISTS`. Judges will re-run it.

## Conventions

- Package root `src/warrant/`, five subpackages: `detect`, `reason`, `authority`, `act`,
  `orchestrate`, plus `common` for shared types.
- SQL in `sql/`, numbered and run in filename order: `00` setup → `40` orchestration.
  `90_reset.sql` returns the pipeline to a pre-run state and deliberately spares `ACTION_AUDIT`.
  Two ordering constraints are not obvious from the numbers: the document corpus must be on
  `@WARRANT.CORE.DOCS` before `15_corpus.sql` parses it, and `15` must precede `30`, which
  indexes the table `15` builds. `scripts/setup.sh` is the authority on the sequence.
- **The operating procedures are documents, not string literals.** `corpus/*.md` is the source of
  truth; `corpus/pdf/` holds byte-deterministic renders, committed so provisioning needs no PDF
  toolchain, and `tools/build_corpus.py --check` in CI stops them drifting. Never add a runbook
  as a `VARCHAR` in SQL — `DATA.RUNBOOKS` is derived from the parse, and editing it directly puts
  the corpus and the documents out of step.
- **Two governance controls, doing different jobs.** The `SENSITIVITY` tag decides what the agent
  may *do*; the `LOT_REF_MASK` masking policy decides what it may *see*. Reads are deliberately
  tag-exempt, so the mask is what stops an agent that may not act on a regulated record from
  reading every field of it. Both are re-applied in `sql/10` because `CREATE OR REPLACE TABLE`
  silently drops tags and policies alike.
- **Every function takes its Snowpark `Session` as its first positional argument.** Nothing in
  `src/warrant/` calls `get_active_session()`; only the stored-procedure entry points in
  `sql/40_orchestration.sql` and the Streamlit app do. This is what makes the pipeline
  unit-testable without a warehouse, and it is why the 100% coverage gate is achievable.
- **Changing the prompt, the model id, the action registry or the corpus means re-running the
  reasoning eval.** `uv run python tools/evaluate_reasoning.py --live -c <conn>` rewrites
  `eval/scorecard.json`; CI's `--check` fails if a case in `eval/cases.json` has no recorded
  result. The eval is the only thing here that measures the model rather than the boundary around
  it, so a change that improves the tests and quietly degrades the reasoning is exactly what it is
  for.
- Every `AI_COMPLETE` call uses `response_format` with an explicit JSON schema — never parse prose.
- Every `AI_COMPLETE` call passes `return_error_details` — silent NULLs in a scheduled pipeline
  are miserable to debug, and a live demo needs a displayable row rather than an aborted query.
- **No SQL may be composed from runtime data.** Statements are module-level constants; values go
  through `params=[...]`. `tools/lint_sql_boundary.py` fails the build otherwise, and it runs in CI.
- **Writes bind one JSON object, not positional parameters.** Inside a Python stored procedure
  Snowpark renders a bound `None` as the string `'None'` — a numeric column rejects it loudly and
  a `VARCHAR` accepts it silently. `PARSE_JSON` makes a JSON `null` a SQL `NULL` on both paths.
- **Tags are read with `SYSTEM$GET_TAG`, fully qualified, never cached.**
  `ACCOUNT_USAGE.TAG_REFERENCES` lags up to two hours, which would make the central claim false.
- Streams are consumed with `INSERT`/`MERGE`, never a bare `SELECT` — a `SELECT` does not advance
  the offset and the task will reprocess forever.
- Tasks and alerts are created suspended; a script that creates one must `RESUME` it explicitly,
  or say why it left it suspended. `SCAN_FOR_EXCEPTIONS` stays suspended on purpose.
- Warehouses are `X-SMALL` with `AUTO_SUSPEND = 60`, under a 100-credit resource monitor.
- **No email address, or any other environment-specific value, is committed.** Those live in
  `WARRANT.CORE.CONFIG`, populated at setup time from the running account.

## Objects

- Database `WARRANT`, schemas `CORE` (pipeline), `DATA` (synthetic source), `AUDIT` (immutable log)
- Tag `WARRANT.CORE.SENSITIVITY` with values `open | internal | regulated`
- Masking policy `WARRANT.CORE.LOT_REF_MASK` on `DATA.QUALITY_HOLDS.lot_ref`; role
  `WARRANT_QUALITY_OWNER` sees through it, `WARRANT_ROLE` does not
- Stages `CORE.CODE` (packaged python), `CORE.DOCS` (the document corpus), `CORE.STREAMLIT`
- Agent `CORE.WARRANT_ANALYST` — read-only by construction. **Do not give it a `generic` tool
  bound to `RUN_LOOP` or `EXECUTE_ACTION`.** A chat surface that can invoke the executor routes
  around the console, the approval queue and the human, which is the entire control.
- `ACTION_AUDIT` is append-only — never `UPDATE` or `DELETE` from it

## Testing

The full gate, which is exactly what CI runs:

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy \
  && uv run python tools/lint_sql_boundary.py \
  && uv run pytest --cov --cov-report=term-missing
```

Coverage is gated at **100% branch coverage** of `src/warrant`. Every module is unit-testable
because sessions are injected; `tests/conftest.py` provides a `FakeSession` that records each
statement and its bound values, and implements only the Snowpark surface this codebase is
sanctioned to use — reaching for anything else raises `AttributeError`, which is a signal worth
having. Anything needing a warehouse is `@pytest.mark.integration` and excluded by default;
run it with `uv run pytest -m integration`.

One test file per module, named `test_<module>.py`. Plain functions with
`@pytest.mark.parametrize` — no test classes.

**One deliberate exception: `tests/test_adversarial.py`.** It is cross-module because the attacks
it models are cross-module — a poisoned document enters at `reason`, tries to escalate at
`authority`, and is stopped at `act`. Split per module, one security argument would be scattered
across four files with nowhere for a reviewer to look. Each test names the control that stops it,
and each assumes **the model complied with the attack**, because "the model refused" is a property
of a model that changes under you and "the model's compliance changed nothing" is a property of the
architecture. The attack text is read from `corpus/adversarial/` at import so the document and the
tests cannot drift.

## When generating code

Prefer a small number of well-named, tested functions over breadth. Imports at module top,
never inside a function. No 1–3 line helpers. The repo is judged on code quality, security,
efficiency, testing and accessibility — not just whether the demo runs.

When a governance rule matters, make it executable. A rule enforced only by a comment lasts
until the next deadline.
