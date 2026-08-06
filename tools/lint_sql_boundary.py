#!/usr/bin/env python3
"""Fail the build if SQL text could ever be composed from runtime data.

Warrant's security claim is specific: **the model contributes values, never SQL text.** A
prompt injection has nothing to write into, because there is no path from model output to
executed SQL. That claim is worth exactly as much as its enforcement, and a comment saying
"we always bind parameters" is enforced by nobody.

So this walks the AST of every module under ``src/`` and ``streamlit/`` and fails on two
things:

**A composed statement reaching the database.** The first argument to ``session.sql(...)``
must be a plain name or a literal — a module constant. An f-string, a ``.format()`` call, a
``%`` or a ``+`` there is rejected, because those are how runtime data becomes syntax.

**SQL-shaped strings built inside a function body.** Module scope is where the statements
live and is unreachable from runtime data; a function body is the only place tainted values
exist. So composing something that looks like SQL inside a function is rejected wherever it
happens, whether or not it is executed on the spot.

Run directly, or via ``uv run python tools/lint_sql_boundary.py``. Exits non-zero on any
finding, which is what wires it into CI.
"""

from __future__ import annotations

import ast
import pathlib
import sys

ROOTS = ("src", "streamlit", "tools", "mcp")

SQL_KEYWORDS = (
    "SELECT ",
    "INSERT ",
    "UPDATE ",
    "DELETE ",
    "MERGE ",
    "CREATE ",
    "DROP ",
    "ALTER ",
    "TRUNCATE ",
    "GRANT ",
    "CALL ",
)

COMPOSING = (ast.JoinedStr, ast.BinOp)
"""An f-string, or any binary operation — ``+`` concatenation and ``%`` formatting alike."""


def looks_like_sql(node: ast.AST) -> bool:
    """Whether a node contains a string fragment that reads as SQL.

    Args:
        node: Any AST node.

    Returns:
        ``True`` if a string constant beneath it starts a SQL statement. Deliberately
        keyword-based rather than clever: a false positive here costs one comment explaining
        why a string is safe, and a false negative costs the security claim.
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            text = child.value.lstrip().upper()
            if any(text.startswith(keyword) for keyword in SQL_KEYWORDS):
                return True
    return False


class Auditor(ast.NodeVisitor):
    """Collects boundary violations in one module."""

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.findings: list[str] = []
        self.depth = 0

    def report(self, node: ast.AST, problem: str) -> None:
        """Record a finding against a source location."""
        self.findings.append(f"{self.path}:{node.lineno}: {problem}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track that we are inside a function body, where runtime data lives."""
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    # ast dispatches on the node class name, so the visitor must carry ast's own casing.
    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:
        """Check that anything handed to ``session.sql`` is a constant, not a composition."""
        target = node.func
        if isinstance(target, ast.Attribute) and target.attr == "sql" and node.args:
            statement = node.args[0]
            if isinstance(statement, COMPOSING):
                self.report(
                    node,
                    "session.sql() received a composed string. Statements must be module "
                    "constants and values must be bound with ? parameters.",
                )
            elif not isinstance(statement, ast.Name | ast.Attribute | ast.Constant):
                self.report(
                    node,
                    f"session.sql() received a {type(statement).__name__}; expected a module "
                    "constant.",
                )
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Reject an f-string that reads as SQL inside a function body."""
        if self.depth and looks_like_sql(node):
            self.report(node, "SQL composed by f-string inside a function body.")
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Reject ``+`` or ``%`` composition of SQL inside a function body."""
        if self.depth and isinstance(node.op, ast.Add | ast.Mod) and looks_like_sql(node):
            self.report(node, "SQL composed by concatenation or % inside a function body.")
        self.generic_visit(node)


def audit(path: pathlib.Path) -> list[str]:
    """Audit one Python file.

    Args:
        path: The file to parse.

    Returns:
        Human-readable findings, empty when the file is clean.
    """
    auditor = Auditor(path)
    auditor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
    return auditor.findings


def main() -> int:
    """Audit every tracked module.

    Returns:
        ``0`` when the boundary holds, ``1`` otherwise.
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    findings: list[str] = []
    checked = 0
    for name in ROOTS:
        for path in sorted((root / name).rglob("*.py")):
            checked += 1
            findings.extend(audit(path))

    if findings:
        print(f"SQL boundary violated in {len(findings)} place(s):\n", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        print(
            "\nThe model must never be able to contribute SQL text. Keep statements as "
            "module-level constants and pass values through params=[...].",
            file=sys.stderr,
        )
        return 1

    print(f"SQL boundary holds across {checked} module(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
