"""Deployment pipeline for NumWorks calculator scripts.

Provides pre-deploy safety checks (static allocation analysis, size limits)
and a unified deploy workflow.
"""

import os
import sys
import ast
from pathlib import Path


# Maximum recommended script size in bytes.
# Scripts larger than this risk exhausting the 32KB MicroPython heap
# during AST compilation alone.
MAX_RECOMMENDED_SIZE = 20_000
MAX_HARD_LIMIT = 32_000

# Functions that are allowed to perform dynamic allocations
# (they run once at startup, not in the hot game loop).
INIT_FUNCTION_WHITELIST = frozenset([
    "Global",
    "init_gameplay_tables",
    "init_tables",
    "init_game",
    "init",
    "setup",
])


class AllocVisitor(ast.NodeVisitor):
    """AST visitor that detects dynamic heap allocations."""

    def __init__(self):
        self.allocations = []
        self.current_function = "Global"

    def visit_FunctionDef(self, node):
        prev = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev

    def _add(self, node, kind):
        self.allocations.append((node.lineno, self.current_function, kind))

    def visit_List(self, node):
        self._add(node, "List")
        self.generic_visit(node)

    def visit_Dict(self, node):
        self._add(node, "Dict")
        self.generic_visit(node)

    def visit_Set(self, node):
        self._add(node, "Set")
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self._add(node, "List Comprehension")
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self._add(node, "Dict Comprehension")
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self._add(node, "Set Comprehension")
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self._add(node, "Generator Expression")
        self.generic_visit(node)

    def visit_Tuple(self, node):
        is_const = all(isinstance(elt, ast.Constant) for elt in node.elts)
        if not is_const:
            self._add(node, "Dynamic Tuple")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in ("list", "dict", "set", "tuple"):
                self._add(node, f"Dynamic {node.func.id}() Call")
        self.generic_visit(node)


class DeployCheck:
    """Result of a single pre-deploy check."""

    def __init__(self, name, passed, message, details=None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or []


def check_syntax(source: str, filename: str = "<script>") -> DeployCheck:
    """Check that the script is valid Python."""
    try:
        ast.parse(source, filename=filename)
        return DeployCheck("Syntax", True, "Valid Python syntax")
    except SyntaxError as e:
        return DeployCheck("Syntax", False, f"SyntaxError on line {e.lineno}: {e.msg}")


def check_size(source: str) -> DeployCheck:
    """Check that the script fits within NumWorks storage and heap limits."""
    size = len(source.encode("utf-8"))
    if size > MAX_HARD_LIMIT:
        return DeployCheck(
            "Size", False,
            f"Script is {size:,} bytes — exceeds hard limit of {MAX_HARD_LIMIT:,} bytes"
        )
    if size > MAX_RECOMMENDED_SIZE:
        return DeployCheck(
            "Size", True,
            f"Script is {size:,} bytes — above recommended {MAX_RECOMMENDED_SIZE:,} bytes (may cause heap pressure)",
        )
    return DeployCheck("Size", True, f"Script is {size:,} bytes")


def check_allocations(source: str, filename: str = "<script>") -> DeployCheck:
    """Static AST analysis: ensure no dynamic allocations in hot game functions."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return DeployCheck("Allocations", False, "Cannot parse — syntax error")

    visitor = AllocVisitor()
    visitor.visit(tree)

    hot_allocs = [
        a for a in visitor.allocations
        if a[1] not in INIT_FUNCTION_WHITELIST
    ]

    if hot_allocs:
        details = [f"  Line {ln:3d} | {fn:20s} | {kind}" for ln, fn, kind in hot_allocs]
        return DeployCheck(
            "Allocations", False,
            f"Found {len(hot_allocs)} dynamic allocation(s) in game functions",
            details=details,
        )

    safe_count = len(visitor.allocations)
    return DeployCheck(
        "Allocations", True,
        f"Zero hot-loop allocations ({safe_count} safe init-only allocations)",
    )


def run_all_checks(source: str, filename: str = "<script>") -> list:
    """Run all pre-deploy checks and return a list of DeployCheck results."""
    return [
        check_syntax(source, filename),
        check_size(source),
        check_allocations(source, filename),
    ]
