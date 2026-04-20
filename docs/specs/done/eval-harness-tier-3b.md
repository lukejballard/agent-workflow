# Feature: Eval Harness — Tier 3b

**Status:** Done
**Created:** 2025-01-01
**Author:** GitHub Copilot
**Estimate:** L
**Supersedes:** None
**Related:** `docs/hyperintelligence_plan.md`, `docs/specs/active/orchestrator-adversarial-audit-and-redesign.md` (ISSUE-20)

---

## Problem

The agent orchestration system has no automated quality measurement. There is
no repeatable way to verify that the orchestrator's Phase progression, risk
classification, confidence modeling, and adversarial critique produce
consistently correct outputs across a representative task corpus. Without a
benchmark corpus and grading rubric, every change to the orchestration contract
is unverifiable beyond code review.

---

## Success Criteria

- A CLI-runnable eval entry point exists at `evals/run_evals.py`.
- A benchmark corpus of 15+ graded tasks exists under `evals/tasks/`.
- Each task defines an input prompt, expected output properties, and a graded
  rubric.
- The eval runner grades each task against the rubric and emits a structured
  JSON report.
- CI can run the eval suite in dry-run mode (schema-validation-only, no LLM
  calls) to detect regressions in task corpus structure.
- An overall pass rate threshold of ≥ 85% is documented and enforced by the CLI.

---

## Requirements

### Functional

- [x] Create `evals/` directory with `run_evals.py` entry point and
      `README.md` documentation.
- [x] Define a task schema (`evals/task.schema.json`) with fields:
      `id`, `title`, `taskClass`, `prompt`, `expectedProperties`, `rubric`,
      `tags`, and `notes`.
- [x] Populate `evals/tasks/` with at least 15 benchmark tasks covering:
  - trivial one-liner tasks
  - brownfield improvement tasks with clear scope
  - greenfield features with spec-required
  - research-only requests
  - multi-surface changes that require adversarial review
  - tasks that should trigger specific skills (test-hardening, observability-inject, etc.)
- [x] Each rubric defines graded dimensions: `classification` (correct task
      class?), `phase_coverage` (required phases reached?), `spec_created` (spec
      file created when required?), `skill_triggered` (correct skills loaded?),
      `adversarial_triggered` (review invoked for medium/high-risk?).
- [x] `run_evals.py --dry-run` validates all task JSON files against
      `task.schema.json` without executing any LLM calls.
- [x] `run_evals.py --report` emits a JSON summary with per-task verdicts and
      an aggregate pass rate.

### Non-functional

- [x] The dry-run mode must complete in under 10 seconds.
- [x] Task files must be human-readable JSON5 or JSON — no binary formats.
- [x] The schema must enforce `id` uniqueness and `taskClass` membership
      against the allowed values in `workflow-manifest.json`.
- [x] All eval infrastructure must be importable without LLM credentials (CI
      safe).

---

## Affected Components

| Path | Change |
|---|---|
| `evals/` | New directory with eval infrastructure |
| `evals/run_evals.py` | CLI entry point |
| `evals/task.schema.json` | Task schema definition |
| `evals/tasks/` | Benchmark task corpus |
| `evals/README.md` | Usage documentation |
| `.github/agent-platform/workflow-manifest.json` | Add `evals` to `verificationRoutes` |
| `.github/agent-platform/repo-map.json` | Add `evals/` area after sync |

---

## Approach

### Phase 1 — Schema and dry-run infrastructure

1. Define `evals/task.schema.json` with required fields and enum constraints.
2. Implement `run_evals.py --dry-run` to validate all task files using
   `jsonschema` (or a lightweight fallback) without LLM calls.
3. Add `evals/` to the `verificationRoutes.contracts` in `workflow-manifest.json`
   and re-sync `repo-map.json`.

### Phase 2 — Benchmark corpus

Populate `evals/tasks/` with representative tasks organized by `taskClass`.
Each task targets a specific orchestrator behavior from the workflow contract,
leaving a paper trail from ISSUE-20 and the adversarial audit spec findings.

Minimum corpus:

| id | Class | Dimension tested |
|---|---|---|
| `trivial-doc-edit` | trivial | No spec required, low-risk inline critique only |
| `trivial-one-liner` | trivial | No phases required beyond execute |
| `research-only-api` | research-only | No code changes, research output only |
| `review-only-diff` | review-only | Phase 6 reviewer invoked correctly |
| `brownfield-bug-fix` | brownfield-improvement | Spec optional, test-hardening triggered |
| `brownfield-api-change` | brownfield-improvement | Adversarial critique required (high-risk) |
| `greenfield-new-module` | greenfield-feature | Spec required before code |
| `greenfield-complex-feature` | greenfield-feature | DAG decomposition required |
| `implement-from-spec` | implement-from-existing-spec | Spec read, no new spec created |
| `test-only-coverage` | test-only | No spec required, regression-audit triggered |
| `docs-only-update` | docs-only | No adversarial review required |
| `multi-surface-change` | brownfield-improvement | observability-inject + spec required |
| `security-relevant-change` | brownfield-improvement | Security review + high-risk flag |
| `confidence-low-escalate` | brownfield-improvement | Low confidence → escalation path |
| `context-health-trim` | brownfield-improvement | Working set > 70% → trim triggered |

### Phase 3 — CI integration

Add a step to `.github/workflows/` (or a VS Code task) that runs
`python evals/run_evals.py --dry-run` on every push to main.

---

## Risks

| Risk | Mitigation |
|---|---|
| LLM eval runs are non-deterministic | Use `--dry-run` for CI; live eval is manual |
| Rubric dimensions are subjective | Document grading criteria precisely in schema |
| Task corpus drifts from orchestrator contract | Re-run corpus review after each agent contract change |

---

## Open Questions

1. Should the eval runner support a `--model` flag to route against different models in `workflow-manifest.json → modelRouter`?
2. Should tasks carry `expectedContextPacket` snippets for structural assertion?
3. Should the pass rate threshold be per-dimension or only on overall verdict?
