#!/usr/bin/env python3
"""Static memory allocation checker for NumWorks MicroPython scripts.

Usage:
    python3 tools/test_allocs.py games/maties.py
    python3 tools/test_allocs.py games/*.py

Parses the Python AST and flags any dynamic heap allocations (lists, tuples,
dicts, generators) that occur inside game-loop functions. Allocations in
global scope and whitelisted init functions are considered safe.

Exit code 0 = PASS, 1 = FAIL.
"""

import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from numworks.deploy import run_all_checks


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <script.py> [script2.py ...]")
        sys.exit(1)

    exit_code = 0
    for filepath in sys.argv[1:]:
        with open(filepath, "r") as f:
            source = f.read()

        print(f"\n{'='*60}")
        print(f"Checking: {filepath}")
        print(f"{'='*60}")

        checks = run_all_checks(source, filename=filepath)
        for check in checks:
            icon = "✓" if check.passed else "✗"
            print(f"  {icon} {check.name}: {check.message}")
            for detail in check.details:
                print(f"    {detail}")
            if not check.passed:
                exit_code = 1

    if exit_code == 0:
        print(f"\n[PASS] All checks passed.")
    else:
        print(f"\n[FAIL] One or more checks failed.")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
