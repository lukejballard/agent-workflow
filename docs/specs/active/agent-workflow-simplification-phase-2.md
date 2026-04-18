# Feature: Agent Workflow Simplification Phase 2

**Status:** In Review
**Created:** 2026-04-14
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** None

---

## Problem
The first simplification phase made workflow drift blocking, but the repository still lacks a
measurable workflow benchmark and still carries substantial duplication between the default
orchestrator and the prompt wrappers that are supposed to sit on top of it.

If left unchanged, contributors will keep paying a drift tax across prompt wrappers, docs, and CI,
and the repo will still be unable to prove that prompt entrypoints preserve the intended agent,
tool, and placeholder contracts over time.

## Success criteria
This phase is successful when the repository has a deterministic workflow benchmark harness for the
prompt control plane, the prompt wrappers become thin task-shaping shims around the orchestrator,
and the broader local verification path exercises the new benchmark alongside existing gates.

---

## Requirements

### Functional
- [x] Add a repo-local workflow benchmark manifest that defines the expected contract for each
      supported prompt wrapper.
- [x] Add a repo-local workflow benchmark checker under `scripts/agent/` that validates prompt
      wrapper agent selection, tool exposure, and required placeholder contract against the
      benchmark manifest.
- [x] Add unit tests for the workflow benchmark checker, including at least one passing repository
      benchmark run and failing cases for missing files, missing placeholders, and tool drift.
- [x] Simplify the prompt wrappers so they rely on orchestrator-level behavior for generic workflow
      rules and retain only task-specific shaping instructions.
- [x] Preserve the intended least-privilege split between execution-oriented wrappers and
      research/review-oriented wrappers.
- [x] Update the workflow-governance CI lane to run the workflow benchmark checker as a blocking
      step.
- [x] Update local verification scripts so the benchmark checker runs during narrow and broad
      workflow verification.
- [x] Update the runbook and setup guide to describe the new benchmark harness, the thinner-wrapper
      model, and how to run the checks locally.
- [x] Perform a broader verification pass after the implementation and record the outcome in this
      spec.

### Non-functional
- [x] Performance: keep the benchmark checker deterministic, local, and standard-library only.
- [x] Security: do not add remote execution, model invocation, or widened tool access in this
      phase.
- [x] Documentation: explain that the benchmark harness validates workflow contracts, not end-to-end
      model quality.
- [x] Regression safety: do not remove specialized prompt entrypoints that are still documented and
      intentionally exposed.

---

## Affected components
- `docs/specs/active/agent-workflow-simplification-phase-2.md`
- `.github/agent-platform/workflow-benchmarks.json`
- `scripts/agent/check_workflow_benchmarks.py`
- `tests/unit/test_check_workflow_benchmarks.py`
- `.github/prompts/*.prompt.md`
- `.github/workflows/pr-quality.yml`
- `scripts/agent/verify-narrow.sh`
- `scripts/agent/verify-broad.sh`
- `.github/workflows/ci.yml`
- `.specify/scripts/powershell/update-agent-context.ps1`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
This phase reuses external guidance captured in:
- `docs/specs/research/agent-architecture-benchmark-research.md`
- `docs/specs/research/agent-workflow-simplification-research.md`

That guidance still points toward simpler wrappers, deterministic control-plane checks, and repo-
local measurement before any attempt at richer runtime orchestration.

---

## Documentation impact
The runbook and setup guide must change because this phase adds a new local and CI workflow check
and changes how contributors should think about the prompt wrappers.

No product-facing docs are required because this work affects contributor workflow only.

---

## Architecture plan
Add a small benchmark manifest plus a standard-library checker that validates stable workflow
contracts for each prompt wrapper: file presence, `agent: orchestrator`, intended tool tier, and
required placeholders or prompt anchors.

Then simplify the prompt wrappers so they stop repeating orchestrator-level workflow rules and act
as thin task-shaping entrypoints instead. Wire the checker into `pr-quality.yml` and the local
verify scripts so future control-plane changes are both measured and enforced.

Preferred approach:
- create a fixture-driven static benchmark harness
- simplify wrappers without deleting the specialized entrypoints
- gate CI and local verification on the benchmark harness

Alternative considered:
- attempt an end-to-end prompt evaluation harness that executes prompts through a model or editor
  runtime

Why rejected:
- it would be nondeterministic and credential-dependent
- the repository does not expose a stable local runtime API for that path
- the resulting checks would be harder to run locally and harder to trust in CI

---

## API design

No product API changes.
This phase changes workflow scripts, benchmark fixtures, prompt wrappers, CI, and contributor docs.

---

## Data model changes

No application data model changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the benchmark manifest and checker, revert prompt-wrapper simplification,
  and revert the workflow and doc changes.
- Breaking change? No product-facing breaking change. Workflow contributors get stricter prompt
  contract validation.

---

## Edge cases

| Edge case | Handling |
|---|---|
| A prompt wrapper widens or narrows tools unintentionally | The benchmark checker must fail with a specific tool mismatch. |
| A prompt wrapper loses a required placeholder while still existing | The benchmark checker must fail with the missing placeholder. |
| A wrapper remains intentionally least-privilege | The benchmark manifest must encode that lower-privilege contract explicitly. |
| The wrappers are simplified but docs still describe them as independent workflows | Update docs to describe them as orchestrator wrappers and benchmarked entrypoints. |
| Broader verification fails because of unrelated workspace drift | Report the failure honestly and distinguish it from this phase's targeted checks. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The benchmark checker becomes too brittle by validating wording instead of contracts | Medium | Medium | Validate only stable contract properties and keep body checks minimal. |
| Prompt simplification accidentally removes a needed tool or placeholder | Medium | High | Encode exact tool and placeholder expectations in the benchmark manifest and tests. |
| Contributors overread the benchmark harness as a true model-quality eval | Medium | Medium | Document the scope clearly as contract validation, not runtime quality measurement. |

---

## Breaking changes
No runtime or API breaking changes.
This phase tightens prompt-control-plane validation and reduces wrapper duplication.

---

## Testing strategy
- **Unit:** add pytest coverage for the workflow benchmark checker and manifest handling.
- **Integration:** run `python scripts/agent/check_workflow_benchmarks.py` against the repository
  benchmark manifest.
- **Integration:** run the workflow-governance checks and metadata sync checks after the prompt and
  doc updates.
- **Integration:** run the broader local verification script and record whether failures are caused
  by this change set or by unrelated existing drift.
- **E2E:** not required; this phase does not add product behavior.

### Verification completed
- `python -m pytest tests/unit/test_check_workflow_benchmarks.py tests/unit/test_check_workflow_traceability.py -q` passed.
- `python scripts/agent/check_workflow_benchmarks.py` passed.
- `python scripts/agent/sync_agent_platform.py --check` passed.
- `python -m pytest tests/unit/ -v --tb=short` passed.
- `python -m ruff check src tests` passed.
- `python -m bandit -r src -c pyproject.toml -ll` passed.
- `python -m black --check src tests` still fails because unrelated repository files under `src/` and
      `tests/unit/test_workflow_api.py` would be reformatted.
- `python -m isort src tests --check-only` still fails because unrelated repository files under
      `src/` and `tests/unit/test_workflow_api.py` have import-order drift.
- `python -m pip_audit` reports 42 known vulnerabilities across 16 packages; this phase did not
      change dependency versions.
- Frontend verification drift was corrected by replacing stale `npm run lint` calls with
      `npm run typecheck` in local and CI workflow surfaces.
- `npm.cmd run build` in `frontend/` still fails due existing TypeScript errors in
      `frontend/src/hooks/usePractitionerWorkflow.ts`.
- `npm.cmd test -- --run` in `frontend/` still fails because `expect` is undefined in
      `frontend/src/test-setup.ts` during `frontend/src/__tests__/PractitionerWorkspacePage.test.tsx`.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Workflow benchmark manifest exists and covers each supported prompt wrapper
- [x] Workflow benchmark checker exists under `scripts/agent/`
- [x] Unit tests cover passing and failing benchmark cases
- [x] Prompt wrappers are simplified without removing intended entrypoints
- [x] Least-privilege prompt wrappers remain least-privilege
- [x] PR quality runs the benchmark checker as a blocking step
- [x] Local verification scripts run the benchmark checker
- [x] `docs/runbooks/agent-mode.md` documents the benchmark harness and thinner-wrapper model
- [x] `docs/copilot-setup.md` documents the benchmark harness and thinner-wrapper model
- [x] Broader verification was attempted and the result is recorded in this spec