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
    ("tests in the suite", collected_tests, r"\*?\*?(\d+)\s+tests\b"),
    ("tests that pass", passing_tests, r"(\d+)\s+passed"),
    ("modules mypy checks", typed_modules, r"(\d+)\s+source\s+files"),
    (
        "modules the SQL boundary covers",
        scanned_modules,
        r"boundary\s+holds\s+across\s+(\d+)\s+module",
    ),
    ("documents in the corpus", corpus_documents, r"(\d+)\s+document\(s\)\s+verified"),
    ("Snowflake services claimed", declared_services, r"\*\*(\d+)\s+services"),
)


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
