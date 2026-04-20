# Eval Harness

This directory contains the evaluation harness for the agent orchestration system.
It provides a benchmark corpus of graded tasks and a CLI runner to measure
orchestrator quality without requiring LLM calls in CI.

## Quick Start

```bash
# Validate all task files against the schema (CI-safe, no LLM calls)
python evals/run_evals.py --dry-run

# Emit a JSON pass/fail report to stdout
python evals/run_evals.py --report
```

## Directory Structure

```
evals/
  run_evals.py          CLI entry point
  task.schema.json      JSON Schema for task files
  tasks/                Benchmark task corpus
    *.json              One task per file
  README.md             This file
```

## Task Format

Each task file is a JSON object validated against `task.schema.json`:

```json
{
  "id": "unique-kebab-case-id",
  "title": "Human-readable title",
  "taskClass": "brownfield-improvement",
  "prompt": "The user prompt fed to the orchestrator (min 10 chars)",
  "rubric": {
    "classification": "required",
    "phase_coverage": "required",
    "spec_created": "required",
    "skill_triggered": ["test-hardening"],
    "adversarial_triggered": "required",
    "notes": "Grading notes"
  },
  "tags": ["brownfield", "backend"]
}
```

### Rubric Dimensions

| Dimension | Values | Meaning |
|---|---|---|
| `classification` | `required` / `advisory` / `skip` | Must the orchestrator correctly classify the task into `taskClass`? |
| `phase_coverage` | `required` / `advisory` / `skip` | Must the expected workflow phases be reached? |
| `spec_created` | `required` / `forbidden` / `advisory` / `skip` | Spec-file expectation |
| `skill_triggered` | `["skill-id", ...]` | Skills that must be loaded |
| `adversarial_triggered` | `required` / `forbidden` / `advisory` / `skip` | Phase 6 adversarial critique expectation |

### Valid `taskClass` Values

- `trivial`
- `research-only`
- `review-only`
- `brownfield-improvement`
- `greenfield-feature`
- `implement-from-existing-spec`
- `test-only`
- `docs-only`

## Pass Rate Threshold

The eval harness enforces a pass rate of **≥ 85%** across all tasks. The
`--report` mode exits with code `1` if the threshold is not met.

## Adding Tasks

1. Create a new JSON file in `evals/tasks/` using the schema above.
2. Run `python evals/run_evals.py --dry-run` to validate it.
3. Commit both the task file and this README update.

## CI Integration

Add this step to your CI workflow to catch corpus regressions:

```yaml
- name: Validate eval task corpus
  run: python evals/run_evals.py --dry-run
```

The dry-run completes in under 10 seconds and requires no external credentials.
