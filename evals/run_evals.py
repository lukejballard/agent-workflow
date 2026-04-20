#!/usr/bin/env python3
"""Eval harness entry point.

Usage
-----
  python evals/run_evals.py --dry-run      # validate task corpus only (CI-safe)
  python evals/run_evals.py --report       # emit JSON pass/fail report to stdout
  python evals/run_evals.py --help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
TASKS_DIR = EVALS_DIR / "tasks"
SCHEMA_PATH = EVALS_DIR / "task.schema.json"
MANIFEST_PATH = EVALS_DIR.parent / ".github" / "agent-platform" / "workflow-manifest.json"
PASS_RATE_THRESHOLD = 0.85

VALID_TASK_CLASSES = {
    "trivial",
    "research-only",
    "review-only",
    "brownfield-improvement",
    "greenfield-feature",
    "implement-from-existing-spec",
    "test-only",
    "docs-only",
}

VALID_RUBRIC_OPTIONS = {"required", "advisory", "skip", "forbidden"}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_task(task_path: Path, schema: dict) -> list[str]:
    """Return a list of validation errors for one task file."""
    errors: list[str] = []
    label = task_path.name

    try:
        task = json.loads(task_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{label}: failed to parse — {exc}"]

    if not isinstance(task, dict):
        return [f"{label}: must be a JSON object"]

    # Try jsonschema if available, otherwise do a lightweight manual check
    try:
        import jsonschema  # type: ignore

        try:
            jsonschema.validate(instance=task, schema=schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{label}: schema error — {exc.message}")
        return errors
    except ImportError:
        pass

    # Lightweight manual validation (fallback when jsonschema is not installed)
    required_fields = {"id", "title", "taskClass", "prompt", "rubric", "tags"}
    missing = sorted(required_fields - set(task.keys()))
    if missing:
        errors.append(f"{label}: missing required fields: {', '.join(missing)}")
        return errors

    task_id = task.get("id", "")
    if not isinstance(task_id, str) or not task_id:
        errors.append(f"{label}: id must be a non-empty string")
    elif not all(c.isalnum() or c == "-" for c in task_id):
        errors.append(f"{label}: id must be kebab-case (a-z0-9 and hyphens only)")

    task_class = task.get("taskClass")
    if task_class not in VALID_TASK_CLASSES:
        errors.append(f"{label}: taskClass '{task_class}' is not valid")

    prompt = task.get("prompt", "")
    if not isinstance(prompt, str) or len(prompt) < 10:
        errors.append(f"{label}: prompt must be at least 10 characters")

    rubric = task.get("rubric")
    if not isinstance(rubric, dict):
        errors.append(f"{label}: rubric must be an object")
    else:
        if "classification" not in rubric:
            errors.append(f"{label}: rubric.classification is required")
        for key in ("classification", "phase_coverage", "spec_created", "adversarial_triggered"):
            val = rubric.get(key)
            if val is not None and val not in VALID_RUBRIC_OPTIONS:
                errors.append(f"{label}: rubric.{key} value '{val}' is not valid")

    tags = task.get("tags")
    if not isinstance(tags, list) or not tags:
        errors.append(f"{label}: tags must be a non-empty array")

    return errors


def collect_task_files() -> list[Path]:
    if not TASKS_DIR.exists():
        return []
    return sorted(TASKS_DIR.glob("*.json"))


def load_trigger_index() -> dict[str, set[str]] | None:
    """Return a mapping of skill-name → set-of-trigger-tags from the manifest.

    Returns None when the manifest cannot be loaded (non-fatal).
    """
    if not MANIFEST_PATH.exists():
        return None
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    skills_section = manifest.get("skills", {})
    return {
        skill_name: set(entry.get("triggers", []))
        for skill_name, entry in skills_section.items()
        if isinstance(entry, dict)
    }


def validate_trigger_resolution(task: dict, trigger_index: dict[str, set[str]]) -> list[str]:
    """Check that every skill in rubric.skill_triggered can be reached by the task's tags.

    Returns a list of warning strings (not errors — a task author might intentionally
    claim a skill that the manifest doesn't cover, e.g. for future work).
    """
    warnings: list[str] = []
    rubric = task.get("rubric", {})
    claimed_skills = rubric.get("skill_triggered", [])
    if not isinstance(claimed_skills, list):
        return warnings

    task_tags: set[str] = set(task.get("tags", []))
    label = task.get("id", "<unknown>")

    for skill in claimed_skills:
        if skill not in trigger_index:
            warnings.append(
                f"{label}: skill '{skill}' in rubric.skill_triggered is not in workflow-manifest.json"
            )
            continue
        trigger_tags = trigger_index[skill]
        if not task_tags & trigger_tags:
            warnings.append(
                f"{label}: skill '{skill}' claimed in rubric.skill_triggered but none of its "
                f"trigger tags {sorted(trigger_tags)} appear in task tags {sorted(task_tags)}"
            )
    return warnings


def run_dry_run() -> int:
    """Validate all task files against the schema. Returns exit code."""
    schema = load_schema()
    task_files = collect_task_files()
    trigger_index = load_trigger_index()

    if not task_files:
        print(f"ERROR: no task files found in {TASKS_DIR}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []
    ids_seen: set[str] = set()

    for task_path in task_files:
        errors = validate_task(task_path, schema)
        if not errors:
            try:
                task = json.loads(task_path.read_text(encoding="utf-8"))
                task_id = task.get("id", "")
                if task_id in ids_seen:
                    errors.append(f"{task_path.name}: duplicate id '{task_id}'")
                ids_seen.add(task_id)
                # Trigger resolution check (ISSUE-23)
                if trigger_index is not None:
                    all_warnings.extend(validate_trigger_resolution(task, trigger_index))
            except Exception:
                pass
        all_errors.extend(errors)

    for warning in all_warnings:
        print(f"WARNING: {warning}")

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"dry-run passed: {len(task_files)} task(s) validated successfully")
    return 0


def run_report() -> int:
    """Emit a JSON report of pass/fail verdicts. Returns exit code."""
    schema = load_schema()
    task_files = collect_task_files()

    if not task_files:
        print(json.dumps({"error": f"no task files found in {TASKS_DIR}"}))
        return 1

    results = []
    pass_count = 0

    for task_path in task_files:
        errors = validate_task(task_path, schema)
        passed = len(errors) == 0
        if passed:
            pass_count += 1
            try:
                task = json.loads(task_path.read_text(encoding="utf-8"))
                task_id = task.get("id", task_path.stem)
            except Exception:
                task_id = task_path.stem
        else:
            task_id = task_path.stem
        results.append({
            "id": task_id,
            "file": task_path.name,
            "passed": passed,
            "errors": errors,
        })

    total = len(task_files)
    pass_rate = pass_count / total if total > 0 else 0.0
    report = {
        "total": total,
        "passed": pass_count,
        "failed": total - pass_count,
        "pass_rate": round(pass_rate, 4),
        "threshold": PASS_RATE_THRESHOLD,
        "threshold_met": pass_rate >= PASS_RATE_THRESHOLD,
        "results": results,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["threshold_met"] else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate task corpus schema only (CI-safe, no LLM calls).",
    )
    mode.add_argument(
        "--report",
        action="store_true",
        help="Emit a JSON pass/fail report based on task schema validation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.report:
        return run_report()
    # Default to --dry-run
    return run_dry_run()


if __name__ == "__main__":
    raise SystemExit(main())
