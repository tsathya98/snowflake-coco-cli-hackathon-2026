#!/usr/bin/env python3
"""Render the operating-procedure corpus from Markdown source into PDFs.

The corpus is the agent's grounding evidence, so it has to be two things at once: a set of
**real documents** the pipeline genuinely parses, and something a reviewer can read a diff of.
Markdown under ``corpus/`` is the source of truth; the PDFs in ``corpus/pdf/`` are generated from
it.

That ordering matters beyond convenience. A threshold in a detector is supposed to be traceable
to a documented procedure, and if the procedure were an opaque binary then "traceable" would mean
"take our word for it". Here a reviewer reads the clause, reads the detector, and sees they agree.

**The PDFs are committed, and that is why rendering is byte-deterministic.** Committing them
means provisioning needs no PDF toolchain — which matters because the Snowflake CLI and this
renderer do not necessarily live in the same environment. The cost of committing generated
binaries is that they can drift from their source, so the creation date and producer string are
pinned and ``--check`` re-renders in memory and compares bytes. CI runs ``--check``, so a
Markdown edit that was never re-rendered fails the build instead of quietly shipping a stale
document.

Front matter carries the fields the pipeline needs as metadata (``doc_id``, ``title``,
``category``) so they are not re-derived by parsing the rendered text — the parse recovers prose,
not identifiers.

Usage:
    uv run python tools/build_corpus.py            # render every corpus/*.md
    uv run python tools/build_corpus.py --check    # byte-compare against what is committed
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Two independent document sets, each with its own manifest.
#
# The adversarial set is rendered and verified exactly like the real corpus, and is deliberately
# NOT written into the same manifest — sql/15_corpus.sql builds DATA.RUNBOOKS from
# manifest.json alone, so a hostile document cannot reach the corpus through provisioning. Only
# scripts/injection_drill.sh stages it, and it says so on the way in.
SETS = (
    (ROOT / "corpus", ROOT / "corpus" / "pdf", "manifest.json"),
    (ROOT / "corpus" / "adversarial", ROOT / "corpus" / "adversarial" / "pdf", "manifest.json"),
)

REQUIRED_KEYS = ("doc_id", "title", "category")

# Pinned so rendering is reproducible byte-for-byte. Without these, fpdf2 stamps the current
# timestamp and its own version into every file, `--check` could never compare bytes, and the
# committed PDFs would be unverifiable against their source. The date is arbitrary and fixed; it
# is not a claim about when anything happened.
PDF_CREATED = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
PDF_PRODUCER = "warrant corpus builder"

# The PDF core fonts cover Latin-1 only, and Markdown source is full of typographic characters.
# Folding them to ASCII beats shipping a Unicode TTF: the alternative is committing a font binary
# to satisfy five em dashes, and a controlled procedure rendered in a core font would be ASCII in
# the first place. Done here rather than in the source files so the Markdown stays pleasant to
# read.
TYPOGRAPHY = str.maketrans(
    {
        "—": "--",  # em dash
        "–": "-",  # en dash
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        " ": " ",  # non-breaking space
        "→": "->",
    }
)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split YAML-ish front matter from the document body.

    Deliberately hand-rolled rather than pulling in a YAML parser: the front matter is a flat
    ``key: value`` block by construction, and a corpus builder is a poor reason to add a
    dependency with a parsing surface.

    Args:
        text: Full contents of a corpus Markdown file.

    Returns:
        A ``(metadata, body)`` pair.

    Raises:
        ValueError: If the front-matter block is missing or absent a required key.
    """
    if not text.startswith("---\n"):
        raise ValueError("missing front matter; expected a leading '---' line")
    _, block, body = text.split("---\n", 2)

    metadata: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip()

    missing = [key for key in REQUIRED_KEYS if not metadata.get(key)]
    if missing:
        raise ValueError(f"front matter is missing {', '.join(missing)}")
    return metadata, body.strip()


def render(metadata: dict[str, str], body: str) -> bytes:
    """Lay one procedure out as a PDF.

    The layout is deliberately plain — headings, paragraphs, a header block. It is not trying to
    be a hard test of a document parser; it is trying to be an honest one, which means real page
    structure and real text extraction rather than a string handed straight to the indexer.

    Args:
        metadata: Front-matter fields.
        body: Markdown body, with ``#`` headings and blank-line-separated paragraphs.

    Returns:
        The PDF as bytes.
    """
    metadata = {key: value.translate(TYPOGRAPHY) for key, value in metadata.items()}
    body = body.translate(TYPOGRAPHY)

    pdf = FPDF(format="A4", unit="mm")
    pdf.set_creation_date(PDF_CREATED)
    pdf.set_producer(PDF_PRODUCER)
    pdf.set_title(metadata["title"])
    pdf.set_subject(f"{metadata['doc_id']} ({metadata['category']})")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, metadata["title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(
        0,
        5,
        f"{metadata['doc_id']}  |  category: {metadata['category']}  |  "
        f"revision {metadata.get('revision', '-')}  |  "
        f"effective {metadata.get('effective', '-')}  |  "
        f"owner: {metadata.get('owner', '-')}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            level = len(block) - len(block.lstrip("#"))
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 13 if level <= 1 else 11)
            pdf.multi_cell(0, 6, block.lstrip("# ").strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 11)
            continue
        pdf.set_font("Helvetica", "", 11)
        # Collapse source wrapping so the PDF re-wraps to its own measure; a parser should see
        # paragraphs, not the line breaks of whoever edited the Markdown.
        pdf.multi_cell(
            0,
            5.5,
            " ".join(line.strip() for line in block.splitlines()),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(2)

    return bytes(pdf.output())


def reconcile(target: pathlib.Path, content: bytes | str, check: bool, label: str) -> str | None:
    """Write a generated artifact, or verify the committed one against it.

    Args:
        target: Where the artifact lives.
        content: What it should contain. ``bytes`` for a PDF, ``str`` for the manifest — the
            type selects binary or UTF-8 text handling on both the write and the comparison.
        check: Verify and write nothing, rather than write.
        label: How to name this artifact if it turns out to be stale.

    Returns:
        ``None`` if the artifact was written, or is present and current. Otherwise a
        human-readable description of how it is out of date.

    The PDFs and the manifest were being written and compared by two blocks that differed only
    in bytes-versus-text, and they had already drifted into describing the same failure with two
    different phrasings. One implementation cannot drift from itself.
    """
    binary = isinstance(content, bytes)
    if not check:
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return None

    if not target.exists():
        return f"{label} (missing)"
    current = target.read_bytes() if binary else target.read_text(encoding="utf-8")
    return None if current == content else f"{label} (differs from source)"


def build_set(
    source_dir: pathlib.Path,
    output_dir: pathlib.Path,
    manifest_name: str,
    check: bool,
) -> tuple[list[str], int]:
    """Render or verify one document set, and its manifest.

    Args:
        source_dir: Directory holding the Markdown sources, read non-recursively.
        output_dir: Where the rendered PDFs and the manifest live.
        manifest_name: Filename of the manifest inside ``output_dir``.
        check: Verify against what is committed and write nothing, rather than rendering.

    Returns:
        ``(stale, rendered)`` — the human-readable descriptions of anything out of date (empty
        when everything matches, and always empty unless ``check``), and how many documents were
        processed.

    Raises:
        ValueError: A source document is malformed, or two of them share a ``doc_id``. Raised
            rather than returned because a broken source is not a stale artifact: it cannot be
            fixed by re-rendering, so it must not be reported alongside things that can.
    """
    # `*.md` only at the top level, so corpus/adversarial/ is not swept into the real corpus.
    sources = sorted(source_dir.glob("*.md"))
    if not sources:
        raise ValueError(f"no documents found under {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    manifest: list[dict[str, str]] = []

    for source in sources:
        try:
            metadata, body = parse_front_matter(source.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ValueError(f"{source.name}: {error}") from error

        target = output_dir / f"{metadata['doc_id']}.pdf"
        manifest.append({**metadata, "file": target.name, "source": source.name})
        rendered = render(metadata, body)

        # Byte comparison, not mtime: git does not preserve modification times, so a timestamp
        # check would pass or fail according to checkout order rather than according to whether
        # the document is current.
        difference = reconcile(target, rendered, check, source.name)
        if difference:
            stale.append(difference)
        elif not check:
            print(f"{source.name:52s} -> {target.relative_to(ROOT)}  {len(rendered):>6d} bytes")

    # The manifest is staged next to the documents and joined to them in sql/15_corpus.sql.
    # Identifiers, titles and categories are metadata, so they come from front matter rather
    # than being scraped out of the parsed prose — deriving a primary key from rendered output
    # would make document layout load-bearing, and reflowing a page would re-key the corpus.
    ids = [entry["doc_id"] for entry in manifest]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate doc_id under {source_dir}: {', '.join(duplicates)}")

    target = output_dir / manifest_name
    rendered_manifest = json.dumps(manifest, indent=2) + "\n"
    difference = reconcile(target, rendered_manifest, check, str(target.relative_to(ROOT)))
    if difference:
        stale.append(difference)
    elif not check:
        print(f"{'(manifest)':52s} -> {target.relative_to(ROOT)}")

    return stale, len(sources)


def main() -> int:
    """Render or verify the whole corpus.

    Returns:
        ``0`` on success. ``1`` if ``--check`` found a missing or stale artifact, or if any
        source document is malformed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-render in memory and byte-compare against what is committed; write nothing",
    )
    args = parser.parse_args()

    stale: list[str] = []
    rendered_count = 0

    for source_dir, output_dir, manifest_name in SETS:
        try:
            set_stale, count = build_set(source_dir, output_dir, manifest_name, args.check)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        stale.extend(set_stale)
        rendered_count += count

    if stale:
        print(
            "corpus artifacts do not match their source:\n  "
            + "\n  ".join(stale)
            + "\n\nRun: uv run python tools/build_corpus.py",
            file=sys.stderr,
        )
        return 1

    print(f"{rendered_count} document(s) {'verified' if args.check else 'rendered'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
