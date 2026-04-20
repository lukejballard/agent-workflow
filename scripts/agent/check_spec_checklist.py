#!/usr/bin/env python3
"""Spec checklist completeness gate (ISSUE-19).

Validates that specs in ``docs/specs/done/`` have no unchecked ``- [ ]`` items.
A spec that has been archived to done/ must have all checklist boxes ticked.

Also reports (non-blocking) the count of unchecked items in ``docs/specs/active/``
specs so engineers can see in-progress coverage at a glance.

Exit code 0 = all done/ specs are fully checked (active/ issues are advisory).
Exit code 1 = one or more done/ specs still have unchecked items.

Usage
-----
  python scripts/agent/check_spec_checklist.py
  python scripts/agent/check_spec_checklist.py --repo-root /path/to/repo
  python scripts/agent/check_spec_checklist.py --fail-on-active   # also block on unchecked active/ items
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_UNCHECKED = re.compile(r"^\s*-\s*\[ \]", re.MULTILINE)


def _find_repo_root(start: Path) -> Path:
    for ancestor in [start, *start.parents]:
        if (ancestor / ".github").is_dir():
            return ancestor
    return start


def _count_unchecked(path: Path) -> int:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return len(_UNCHECKED.findall(content))


def check_spec_folder(
    folder: Path,
    *,
    blocking: bool,
    label: str,
) -> list[str]:
    """Check all markdown specs in *folder* for unchecked items.

    Returns a list of error/warning strings (empty = clean).
    """
    messages: list[str] = []
    if not folder.exists():
        return messages

    for spec in sorted(folder.glob("*.md")):
        count = _count_unchecked(spec)
        if count > 0:
            rel = spec.relative_to(spec.parents[2]) if spec.parents[2].exists() else spec
            prefix = "ERROR" if blocking else "WARNING"
            messages.append(
                f"{prefix}: {rel} ({label}) has {count} unchecked item(s) — "
                "all checklist boxes must be ticked before moving to done/"
                if blocking
                else f"{prefix}: {rel} ({label}) has {count} unchecked item(s)"
            )
    return messages


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root. Defaults to the nearest ancestor containing .github/.",
    )
    parser.add_argument(
        "--fail-on-active",
        action="store_true",
        help="Also exit with code 1 if active/ specs have unchecked items.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = (args.repo_root or _find_repo_root(Path.cwd())).resolve()

    specs_root = repo_root / "docs" / "specs"
    done_dir = specs_root / "done"
    active_dir = specs_root / "active"

    errors = check_spec_folder(done_dir, blocking=True, label="done")
    warnings = check_spec_folder(active_dir, blocking=args.fail_on_active, label="active")

    for msg in warnings:
        print(msg)

    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1

    if args.fail_on_active and any(m.startswith("ERROR") for m in warnings):
        return 1

    done_count = len(list(done_dir.glob("*.md"))) if done_dir.exists() else 0
    active_count = len(list(active_dir.glob("*.md"))) if active_dir.exists() else 0
    print(
        f"spec checklist passed: {done_count} done spec(s) fully checked, "
        f"{active_count} active spec(s) advisory-checked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
