#!/usr/bin/env python3
"""Check that changed prompt files still satisfy their benchmark marker contracts.

For each changed file that is a workflow prompt (.github/prompts/*.prompt.md),
this script verifies that all `required_markers` defined in the matching
benchmark entry (workflow-benchmarks.json) are still present in the file.

This is distinct from check_workflow_benchmarks.py which validates ALL benchmarks;
this script is PR-scoped and validates only the changed subset.

If a prompt file is changed but has no benchmark entry, that is advisory (warn,
not fail).

Usage
-----
  python scripts/agent/check_workflow_traceability.py --changed-files-file changed-files.txt
  python scripts/agent/check_workflow_traceability.py --changed-files stdin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for ancestor in [start, *start.parents]:
        if (ancestor / ".github").is_dir():
            return ancestor
    return start


def _load_benchmarks(repo_root: Path) -> dict[str, dict]:
    """Return a dict mapping prompt path → benchmark entry."""
    benchmarks_path = repo_root / ".github" / "agent-platform" / "workflow-benchmarks.json"
    if not benchmarks_path.exists():
        return {}
    try:
        data = json.loads(benchmarks_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {bm["path"]: bm for bm in data.get("benchmarks", []) if "path" in bm}


def _read_changed_files(args: argparse.Namespace) -> list[str]:
    if args.changed_files_file == "stdin":
        return sys.stdin.read().splitlines()
    path = Path(args.changed_files_file)
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def check_traceability(repo_root: Path, changed_files: list[str]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) after checking changed prompt contracts."""
    benchmarks_by_path = _load_benchmarks(repo_root)
    errors: list[str] = []
    warnings: list[str] = []

    # Normalise paths to forward-slash for comparison
    normalised = [f.replace("\\", "/").lstrip("./") for f in changed_files if f.strip()]

    for rel_path in normalised:
        # Only inspect files that look like workflow prompt files
        if not (rel_path.startswith(".github/prompts/") and rel_path.endswith(".prompt.md")):
            continue

        full_path = repo_root / rel_path
        if not full_path.exists():
            continue  # Deleted file — no content to check

        content = full_path.read_text(encoding="utf-8")
        bm = benchmarks_by_path.get(rel_path)

        if bm is None:
            warnings.append(
                f"WARNING: {rel_path} was changed but has no benchmark entry; "
                "consider adding one to workflow-benchmarks.json"
            )
            continue

        for marker in bm.get("required_markers", []):
            if marker not in content:
                errors.append(
                    f"contract violation in {rel_path}: "
                    f"required marker no longer present\n  missing: {marker!r}"
                )

    return errors, warnings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--changed-files-file",
        default="stdin",
        metavar="PATH|stdin",
        help=(
            "Path to a newline-delimited file of changed file paths "
            "(as produced by 'git diff --name-only ...'). Use 'stdin' to read from stdin."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root. Defaults to the nearest ancestor containing .github/.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = (args.repo_root or _find_repo_root(Path.cwd())).resolve()
    changed_files = _read_changed_files(args)

    errors, warnings = check_traceability(repo_root, changed_files)

    for warning in warnings:
        print(warning)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"workflow traceability passed: {len(changed_files)} changed file(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
