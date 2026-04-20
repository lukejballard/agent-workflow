#!/usr/bin/env python3
"""Validate workflow benchmark prompt files.

Reads `.github/agent-platform/workflow-benchmarks.json` and checks:
  1. Each benchmark's `path` file exists.
  2. Every `required_marker` string is present in the file content.

Exit code 0 = all benchmarks pass.
Exit code 1 = one or more benchmarks fail.

Usage
-----
  python scripts/agent/check_workflow_benchmarks.py
  python scripts/agent/check_workflow_benchmarks.py --repo-root /path/to/repo
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


def check_benchmarks(repo_root: Path) -> list[str]:
    benchmarks_path = repo_root / ".github" / "agent-platform" / "workflow-benchmarks.json"
    if not benchmarks_path.exists():
        return [f"workflow-benchmarks.json not found at {benchmarks_path}"]

    try:
        data = json.loads(benchmarks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"workflow-benchmarks.json is invalid JSON: {exc}"]

    benchmarks = data.get("benchmarks", [])
    if not isinstance(benchmarks, list):
        return ["workflow-benchmarks.json: 'benchmarks' must be a list"]

    errors: list[str] = []

    for bm in benchmarks:
        bm_id = bm.get("id", "<unknown>")
        path_str = bm.get("path")
        if not path_str:
            errors.append(f"benchmark '{bm_id}': missing 'path'")
            continue

        prompt_path = repo_root / path_str
        if not prompt_path.exists():
            errors.append(f"benchmark '{bm_id}': file not found — {path_str}")
            continue

        content = prompt_path.read_text(encoding="utf-8")
        for marker in bm.get("required_markers", []):
            if marker not in content:
                errors.append(
                    f"benchmark '{bm_id}': required marker not found in {path_str}\n"
                    f"  missing: {marker!r}"
                )

    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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

    errors = check_benchmarks(repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    benchmarks_path = repo_root / ".github" / "agent-platform" / "workflow-benchmarks.json"
    data = json.loads(benchmarks_path.read_text(encoding="utf-8"))
    count = len(data.get("benchmarks", []))
    print(f"workflow benchmarks passed: {count} benchmark(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
