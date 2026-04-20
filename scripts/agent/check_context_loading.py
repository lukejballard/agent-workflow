"""Validate progressive context loading contract in orchestrator instructions.

ISSUE-08: The orchestrator's Phase 0 bootstrap section must read exactly two
files — AGENTS.md and workflow-manifest.json — before classifying the task.
This script parses the agent markdown to assert that:

  1. A Phase 0 section exists.
  2. Phase 0 contains exactly 2 numbered list items.
  3. Item 1 references AGENTS.md (case-insensitive path match).
  4. Item 2 references workflow-manifest.json (case-insensitive path match).
  5. No additional numbered items creep into Phase 0 over time.

Run as a CI gate to prevent instruction drift.

Usage:
    python scripts/agent/check_context_loading.py
    python scripts/agent/check_context_loading.py --target .github/agents/orchestrator.agent.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default agent file to check relative to the repo root.
DEFAULT_TARGET = ".github/agents/orchestrator.agent.md"

# Expected backtick-wrapped paths/names for the two Phase 0 reads.
# Patterns match any backtick-delimited string that *contains* the filename,
# so both `AGENTS.md` and `path/to/AGENTS.md` are accepted.
PHASE0_ITEM_1_PATTERN = re.compile(r"`[^`]*agents\.md[^`]*`", re.IGNORECASE)
PHASE0_ITEM_2_PATTERN = re.compile(r"`[^`]*workflow-manifest\.json[^`]*`", re.IGNORECASE)

# Regex to detect Phase 0 heading variants:
#   ## Phase 0 — Bootstrap
#   ## Phase 0: Bootstrap
#   ## Phase 0
PHASE0_HEADING = re.compile(r"^##\s+Phase 0", re.IGNORECASE | re.MULTILINE)

# Regex to detect the next ## section heading (marks end of Phase 0).
NEXT_H2 = re.compile(r"^##\s+", re.MULTILINE)

# Regex for numbered list items: lines starting with "1." "2." etc.
NUMBERED_ITEM = re.compile(r"^\s{0,3}\d+\.\s+", re.MULTILINE)


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------

def check_context_loading(repo_root: Path, target: str = DEFAULT_TARGET) -> list[str]:
    """Parse *target* and validate the Phase 0 progressive loading contract.

    Returns a list of error strings (empty when the file is valid).
    """
    errors: list[str] = []
    agent_file = repo_root / target

    if not agent_file.exists():
        return [f"Target file not found: {agent_file.relative_to(repo_root).as_posix()}"]

    text = agent_file.read_text(encoding="utf-8")

    # --- Locate Phase 0 section ---
    phase0_match = PHASE0_HEADING.search(text)
    if not phase0_match:
        errors.append(
            f"{target}: No 'Phase 0' heading found. "
            "The orchestrator must have a bootstrap section that reads exactly "
            "AGENTS.md and workflow-manifest.json before any other action."
        )
        return errors

    phase0_start = phase0_match.end()

    # Find the next ## heading after Phase 0 to bound the section.
    next_h2 = NEXT_H2.search(text, phase0_start)
    phase0_body = text[phase0_start: next_h2.start() if next_h2 else len(text)]

    # --- Extract numbered list items from Phase 0 body ---
    # Split body into lines and collect items that start numbered list entries.
    # We gather the full text of each item (item text may span one line here).
    item_lines: list[str] = []
    for line in phase0_body.splitlines():
        if NUMBERED_ITEM.match(line):
            item_lines.append(line.strip())

    item_count = len(item_lines)

    if item_count == 0:
        errors.append(
            f"{target}: Phase 0 section contains no numbered list items. "
            "Expected exactly 2: one for AGENTS.md and one for workflow-manifest.json."
        )
        return errors

    if item_count != 2:
        errors.append(
            f"{target}: Phase 0 section has {item_count} numbered item(s) but must have exactly 2. "
            "Phase 0 must read only AGENTS.md and workflow-manifest.json before classification. "
            "Move any additional reads to Phase 1 or later, conditioned on the task classification."
        )

    # --- Validate item content ---
    if item_count >= 1:
        if not PHASE0_ITEM_1_PATTERN.search(item_lines[0]):
            errors.append(
                f"{target}: Phase 0 item 1 does not reference `AGENTS.md`. "
                f"Found: {item_lines[0]!r}"
            )

    if item_count >= 2:
        if not PHASE0_ITEM_2_PATTERN.search(item_lines[1]):
            errors.append(
                f"{target}: Phase 0 item 2 does not reference `workflow-manifest.json`. "
                f"Found: {item_lines[1]!r}"
            )

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate orchestrator Phase 0 progressive context loading contract."
    )
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help=f"Repo-relative path to the agent file to check (default: {DEFAULT_TARGET}).",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent.parent
    errors = check_context_loading(repo_root, args.target)

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"context-loading check passed: {args.target} Phase 0 contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
