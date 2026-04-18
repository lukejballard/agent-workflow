#!/usr/bin/env python3
"""Validate repository constitution and template references.

This script is intended for CI use. It exits with a non-zero code if
required constitution checks fail.

Checks performed:
- `.specify/memory/constitution.md` exists
- No unreplaced bracket placeholders like `[PLACEHOLDER]` or `[SOME_TOKEN]`
- Constitution contains a Version and Ratified date in ISO format YYYY-MM-DD
- `.specify/templates/plan-template.md` references the constitution path

Usage:
    python .specify/scripts/validate_constitution.py
    python .specify/scripts/validate_constitution.py --root /path/to/repo
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def find_placeholders(text: str) -> list[str]:
    return re.findall(r"\[[A-Z0-9_\-]+\]", text)


def check_constitution(root: Path) -> list[str]:
    errors: list[str] = []
    cons = root / ".specify" / "memory" / "constitution.md"
    if not cons.exists():
        errors.append(f"Missing constitution file: {cons}")
        return errors

    text = cons.read_text(encoding="utf-8")

    # placeholders
    ph = find_placeholders(text)
    if ph:
        errors.append(f"Found unreplaced placeholder tokens in constitution: {ph}")

    # version
    if not re.search(r"\bVersion\b[:\*]\s*\S+", text) and not re.search(
        r"Version:\s*[0-9]+\.[0-9]+(\.[0-9]+)?", text
    ):
        errors.append(
            "Constitution is missing a Version line " "(e.g. 'Version: 1.0.0')",
        )

    # ratified date
    if not re.search(r"Ratified\b[:\*]\s*\d{4}-\d{2}-\d{2}", text):
        errors.append("Constitution is missing a Ratified date in YYYY-MM-DD format")

    return errors


def check_plan_template(root: Path) -> list[str]:
    errors: list[str] = []
    plan = root / ".specify" / "templates" / "plan-template.md"
    if not plan.exists():
        errors.append(f"Missing plan template: {plan}")
        return errors

    text = plan.read_text(encoding="utf-8")
    if ".specify/memory/constitution.md" not in text:
        errors.append(
            "plan-template.md does not reference " ".specify/memory/constitution.md",
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".", help="Repository root")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    errs: list[str] = []

    errs += check_constitution(root)
    errs += check_plan_template(root)

    if errs:
        print("CONSTITUTION VALIDATION FAILED:\n")
        for e in errs:
            print(f"- {e}")
        print(
            "\nSee .specify/memory/constitution.md and "
            ".specify/templates/plan-template.md for guidance.",
        )
        return 2

    print("Constitution validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
