"""Fail the build when a counted claim in the documentation disagrees with the repository.

The judge-facing documents quote figures — how many tests, how many modules type-check, how many
Snowflake services are wired up — and those figures are the first thing a sceptical reviewer
checks. They are also the first thing to rot: every one of them has drifted at least once during
this build, always because something legitimate was added and the prose was not re-read.

Prose cannot be linted, but *counted* claims can. Each rule below pairs a fact derived from the
repository with the sentences that state it, and fails if they disagree. That converts a whole
class of embarrassment — a README claiming 189 tests in a repo with 230 — from something a human
has to remember into something CI refuses to merge.

Deliberately narrow. It checks numbers that are mechanically derivable and nothing else: no
attempt to validate a claim like "the model never contributes SQL text", which is what
``lint_sql_boundary.py`` is for. A checker that guesses is worse than no checker, because its
silence stops meaning anything.

    uv run python tools/check_doc_claims.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS = (
    "README.md",
    "docs/rubric_alignment.md",
    "docs/judges_walkthrough.md",
    "docs/deck_content.md",
    # Not a document, but it states a count about the repository in front of the public, which is
    # the same failure mode. It claimed nine adversarial tests while pytest collects ten, because
    # the count was taken by grepping `def test_` and the file parametrises.
    "web/components/tested.tsx",
)


def measure(argv: list[str], pattern: str) -> int:
    """Run one of the project's own checks and read a figure out of what it printed.

    Args:
        argv: The command, after ``python -m`` or the interpreter, run with a fixed argv.
        pattern: A regex whose first group captures the figure, matched against stdout.

    Returns:
        The figure the tool reported.

    Raises:
        RuntimeError: The tool printed nothing matching, which means it failed or changed its
            output format. Either way the comparison below would be meaningless, so this stops
            rather than reporting a number nobody measured.

    Running the real tool rather than re-deriving its count in this file is the whole point. An
    independent re-derivation is a second implementation that can disagree with the first — the
    initial version of this script guessed the module count by globbing and was wrong by seven,
    which would have "verified" a correct document as broken.
    """
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell, no runtime input
        [sys.executable, *argv], capture_output=True, text=True, cwd=ROOT, check=False
    )
    match = re.search(pattern, result.stdout + result.stderr)
    if not match:
        raise RuntimeError(
            f"`{' '.join(argv)}` printed nothing matching /{pattern}/:\n"
            f"{(result.stdout + result.stderr)[-2000:]}"
        )
    return int(match.group(1))


def collected_tests() -> int:
    """Count every test in the suite, including the ones the default filter excludes.

    Returns:
        The total, with ``-m ''`` clearing the ``not integration`` filter configured in pyproject
        so this is the size of the suite rather than the size of one run of it.
    """
    return measure(
        ["-m", "pytest", "--collect-only", "-q", "-m", ""], r"(\d+)(?:/\d+)? tests? collected"
    )


def passing_tests() -> int:
    """Run the suite as the documents tell a reader to run it.

    Returns:
        How many tests passed.
    """
    return measure(["-m", "pytest", "-q"], r"(\d+) passed")


def typed_modules() -> int:
    """Ask mypy how many modules it checks.

    Returns:
        The count mypy reports, so the figure and the tool cannot disagree.
    """
    return measure(["-m", "mypy"], r"no issues found in (\d+) source files?")


def scanned_modules() -> int:
    """Ask the SQL-composition boundary lint how many modules it walked.

    Returns:
        The count that lint reports.
    """
    return measure(["tools/lint_sql_boundary.py"], r"across (\d+) module")


def corpus_documents() -> int:
    """Ask the corpus builder how many documents it verified.

    Returns:
        The count, which spans both document sets — the five operating procedures and the one
        planted adversarial document — because that is what the tool prints and therefore what
        the documents quote.
    """
    return measure(["tools/build_corpus.py", "--check"], r"(\d+) document\(s\) verified")


def adversarial_tests() -> int:
    """Count the tests in the injection suite, as pytest collects them.

    Returns:
        The collected total, which is larger than the number of ``def test_`` lines because the
        module parametrises. Derived rather than counted by eye for exactly that reason.
    """
    return measure(
        ["-m", "pytest", "tests/test_adversarial.py", "--collect-only", "-q", "-m", ""],
        r"(\d+) tests? collected",
    )


def declared_services() -> int:
    """Count the rows in the README's Snowflake-services table.

    Returns:
        How many services the README claims, counted from the table itself.

    Raises:
        RuntimeError: The table heading has been renamed or removed.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(
        r"## Snowflake services used\n(.*?)\n\*\*Deliberately not used", readme, re.S
    )
    if not section:
        raise RuntimeError("could not find the Snowflake services table in README.md")
    rows = [line for line in section.group(1).splitlines() if line.startswith("| **")]
    return len(rows)


# Each rule is (name, how to derive the truth, how the documents phrase it). The pattern must
# capture the number in group 1, and every occurrence across every document is checked — a figure
# quoted twice and updated once is exactly the failure this exists to catch.
#
# Every literal space is `\s+`, because these figures are quoted inside prose that Markdown wraps
# at 100 columns. A pattern that assumes a single space silently stops matching the moment a
# sentence is reflowed, and a rule that matches nothing reports success.
RULES: tuple[tuple[str, Callable[[], int], str], ...] = (
    # The lookahead hands "N tests, each naming …" to the injection-suite rule below. Without it
    # both rules match that one sentence, the whole-suite rule loses, and a correct figure gets
    # reported as wrong.
    ("tests in the suite", collected_tests, r"\*?\*?(\d+)\s+tests\b(?!,\s+each\s+naming)"),
    ("tests that pass", passing_tests, r"(\d+)\s+passed"),
    ("modules mypy checks", typed_modules, r"(\d+)\s+source\s+files"),
    (
        "modules the SQL boundary covers",
        scanned_modules,
        r"boundary\s+holds\s+across\s+(\d+)\s+module",
    ),
    ("documents in the corpus", corpus_documents, r"(\d+)\s+document\(s\)\s+verified"),
    ("Snowflake services claimed", declared_services, r"\*\*(\d+)\s+services"),
    ("tests in the injection suite", adversarial_tests, r"(\d+)\s+tests,\s+each\s+naming"),
)


"""
The deployed page transcribes three things it cannot import, and a transcription rots.

The public viewer is a separate TypeScript app with no access to ``mcp/`` or ``eval/``, so its
tool surface, skill list and scorecard are copies. That is worse than a stale README: it is the
first thing a reviewer reads, it is on a public URL, and it is the section arguing that the
surface is governed. The screenshots are copies for the same reason — Next serves only from
``web/public/`` — and nothing else would stop one becoming a different picture from the README's.

These are structural-equality checks rather than numbers quoted in prose, which is why they sit
beside :data:`RULES` rather than inside it.
"""

COCO = "web/components/coco.tsx"
TESTED = "web/components/tested.tsx"


def mcp_surface_failures() -> list[str]:
    """Check the page's tool, resource and skill lists against the server and the skills tree.

    Returns:
        One message per disagreement, empty if the page matches.
    """
    server = (ROOT / "mcp" / "warrant_mcp" / "server.py").read_text(encoding="utf-8")
    coco = (ROOT / COCO).read_text(encoding="utf-8")

    tools = re.findall(r"@mcp\.tool\((.*?)\)\s*\ndef (\w+)", server, re.S)
    kinds = {name: "read" if '"readOnlyHint": True' in body else "act" for body, name in tools}
    failures = []
    for name, kind in kinds.items():
        if f'["{name}", ' not in coco:
            failures.append(f"{COCO}: does not list the tool {name}")
        elif f'"{kind}"],' not in coco.split(f'["{name}", ')[1].split("\n")[0]:
            failures.append(f"{COCO}: lists {name} as the wrong kind, not {kind}")

    listed = len(re.findall(r'^\s+\["\w+", ".*?", "(?:read|act)"\],$', coco, re.M))
    if listed != len(tools):
        failures.append(f"{COCO}: lists {listed} tools; the server defines {len(tools)}")

    failures += [
        f"{COCO}: does not list the resource {uri}"
        for uri in re.findall(r'@mcp\.resource\(\s*\n?\s*"([^"]+)"', server)
        if uri not in coco
    ]

    skills = sorted(p.name for p in (ROOT / ".cortex" / "skills").iterdir() if p.is_dir())
    if f"{len(skills)} CoCo skills" not in coco:
        failures.append(f"{COCO}: does not say '{len(skills)} CoCo skills'")
    failures += [f"{COCO}: does not list the skill {s}" for s in skills if f'["{s}", ' not in coco]
    return failures


def recorded_claims_failures() -> list[str]:
    """Check the page's scorecard figures and its copies of the console screenshots.

    Returns:
        One message per disagreement, empty if the page matches.
    """
    tested = (ROOT / TESTED).read_text(encoding="utf-8")
    scorecard = json.loads((ROOT / "eval" / "scorecard.json").read_text(encoding="utf-8"))
    cases = scorecard["cases_evaluated"]
    perfect = f"{len(cases)}/{len(cases)}"

    failures = [f"{TESTED}: does not list the case {c}" for c in cases if f'"{c}"' not in tested]
    for rate, value in scorecard["rates"].items():
        if f'["{rate}", ' not in tested:
            failures.append(f"{TESTED}: does not list the rate {rate}")
        # The page prints one ratio per rate, so a rate below 1.0 must stop reading n/n.
        if value < 1.0 and perfect in tested:
            failures.append(f"{TESTED}: shows {perfect}, but {rate} is {value}")

    for source in sorted((ROOT / "docs" / "images").glob("*.png")):
        served = ROOT / "web" / "public" / "console" / source.name
        where = f"web/public/console/{source.name}"
        if not served.exists():
            failures.append(f"{where}: missing; copy it from docs/images/")
        elif served.read_bytes() != source.read_bytes():
            failures.append(f"{where}: differs from docs/images/")
    return failures


def main() -> int:
    """Check every counted claim against the repository.

    Returns:
        ``0`` if every figure agrees, ``1`` otherwise.
    """
    texts = {name: (ROOT / name).read_text(encoding="utf-8") for name in DOCUMENTS}
    failures: list[str] = []

    for label, derive, pattern in RULES:
        actual = derive()
        found = False
        for name, text in texts.items():
            for match in re.finditer(pattern, text):
                found = True
                claimed = int(match.group(1))
                line = text[: match.start()].count("\n") + 1
                if claimed != actual:
                    failures.append(f"{name}:{line}: claims {claimed} {label}; there are {actual}")
        status = "ok" if found else "not stated in any document"
        print(f"  {actual:>4}  {label:<34} {status}")

    for label, derive_failures in (
        ("deployed page vs the MCP server", mcp_surface_failures),
        ("deployed page vs eval and images", recorded_claims_failures),
    ):
        found = derive_failures()
        print(f"  {'':>4}  {label:<34} {'drifted' if found else 'ok'}")
        failures.extend(found)

    if failures:
        print(
            "\ndocumentation disagrees with the repository:\n  " + "\n  ".join(failures),
            file=sys.stderr,
        )
        return 1

    print("\nEvery counted claim matches the repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
