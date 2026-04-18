# Feature: Verification Recovery Wave 1

> Note: This completed spec was closed using workflow-equivalent local verification on 2026-04-15.
> GitHub Actions status was not directly queryable from this environment because the remote repository
> and Actions UI/API were not accessible here.

**Status:** Done
**Created:** 2026-04-15
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** docs/specs/active/agent-workflow-simplification-phase-2.md

---

## Problem
The broader verification pass from the workflow simplification work still cannot go green for three
separate reasons.

First, several practitioner-workflow frontend files were accidentally committed as concatenated
duplicates, which breaks typechecking, build output, and frontend tests. Second, the frontend test
setup imports the Jest matcher extension path that assumes a global `expect`, which does not match
the repo's Vitest setup. Third, the Python verification path is noisy and incomplete: Black and
isort are running without repo-local configuration, and local `pip-audit` is scanning the ambient
developer environment instead of the project's pinned dependencies.

If left unchanged, the repository will keep failing broad verification for reasons that mix true
product breakage with tooling noise, and contributors will be unable to distinguish a real code
regression from a local environment artifact.

## Success criteria
- Frontend practitioner-workflow files build and typecheck cleanly without concatenation artifacts.
- Frontend unit tests run under Vitest with matcher setup that matches the configured test runtime.
- Selecting an existing session in the practitioner workflow loads the latest saved assessment
  instead of forcing a duplicate assessment create path.
- Python formatting and import-order checks run with explicit repo-local configuration and pass for
  the currently drifted files.
- Python dependency audit checks only project-owned pinned dependencies, reports actionable findings,
  and distinguishes deferred transitive follow-up from local environment noise.

---

## Requirements

### Functional
- [x] Restore the practitioner-workflow frontend files that were concatenated with duplicate copies
      so each file has exactly one coherent implementation.
- [x] Keep the newer intended frontend improvements where the duplicated files disagree rather than
      blindly restoring the older half.
- [x] Update the practitioner workflow hook and typed API layer so selecting a session loads the
      latest saved assessment from the existing backend endpoint.
- [x] Fix the frontend Vitest setup so `@testing-library/jest-dom` integrates with Vitest globals.
- [x] Add a repo-local Python dependency audit helper that audits the project's pinned dependencies
      from `pyproject.toml` instead of the entire local environment.
- [x] Add unit tests for the new dependency audit helper.
- [x] Update local and CI verification surfaces to use the project-scoped dependency audit helper.
- [x] Align Python formatting and import-order configuration in `pyproject.toml` with the current
      repo style and restore the flagged files to compliance.

### Non-functional
- [x] Performance: keep the dependency audit helper standard-library only and avoid adding new heavy
      frontend or backend dependencies.
- [x] Security: keep dependency auditing blocking for project-owned dependencies and do not widen
      frontend or backend auth behavior.
- [x] Accessibility: preserve the current semantic and labeled practitioner workspace controls while
      repairing the duplicated frontend files.
- [x] Observability: verification commands must fail with actionable output that distinguishes
      frontend restore issues, formatting drift, and dependency findings.

---

## Affected components
- docs/specs/done/verification-recovery-wave-1.md
- frontend/src/App.tsx
- frontend/src/main.tsx
- frontend/src/pages/PractitionerWorkspacePage.tsx
- frontend/src/hooks/usePractitionerWorkflow.ts
- frontend/src/api/http.ts
- frontend/src/api/workflow.ts
- frontend/src/types/workflow.ts
- frontend/src/components/AssessmentPanel.tsx
- frontend/src/components/PrescriptionPanel.tsx
- frontend/src/components/ComparisonPanel.tsx
- frontend/src/components/SetupPanel.tsx
- frontend/src/__tests__/PractitionerWorkspacePage.test.tsx
- frontend/src/test-setup.ts
- pyproject.toml
- src/biomechanics_ai/config/settings.py
- src/biomechanics_ai/collector/errors.py
- src/biomechanics_ai/collector/server.py
- src/biomechanics_ai/collector/workflow_routes.py
- src/biomechanics_ai/services/workflow_service.py
- scripts/agent/check_python_dependency_audit.py
- tests/unit/test_check_python_dependency_audit.py
- scripts/agent/verify-broad.sh
- .github/workflows/ci.yml
- docs/runbooks/agent-mode.md
- docs/copilot-setup.md
- Python files currently failing Black/isort under src/ and tests/

---

## External context
No external research materially changes this design.
The implementation is driven by the current repository state, the active practitioner-workflow
specs, and the verification failures observed locally.

---

## Documentation impact
- Update docs/runbooks/agent-mode.md and docs/copilot-setup.md if the verification commands change.
- No product-facing docs are required because this wave restores frontend correctness and verification
  discipline without introducing new user-facing routes.
- Archive the working recovery spec to `docs/specs/done/` once the verification snapshot is clean.

---

## Architecture plan
Treat the frontend failures as a corrupted-file recovery, not a redesign. Restore each concatenated
file to a single implementation, keeping the newer typed improvements where the two halves differ.

Use the existing backend assessment lookup endpoint during session selection so the frontend does not
create duplicate assessments when a practitioner revisits a session.

For Python verification, prefer tighter scoping over weaker enforcement. Add explicit Black/isort
configuration to match the repo's formatting rules, format the currently drifted files, and replace
environment-wide `pip-audit` calls with a project-scoped audit helper driven by pinned dependencies
from `pyproject.toml`.

Preferred approach:
- restore the corrupted frontend files directly
- keep the existing practitioner workflow architecture and typed API boundary
- scope dependency auditing to project-owned dependencies instead of the ambient environment
- preserve blocking verification while removing known local-noise sources

Alternative considered:
- only remove the duplicate frontend lines and leave the dependency audit and Python formatting path
  unchanged

Why rejected:
- it would leave broad verification red even after the frontend is repaired
- it would keep `pip-audit` findings dominated by unrelated local tooling packages
- it would not address the existing-session assessment reload gap in the practitioner workflow

---

## API design

No new backend endpoints.
This wave consumes the existing `GET /sessions/{session_id}/assessment` endpoint from the frontend.

---

## Data model changes

No database or persistence schema changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: restore the previous frontend files and verification commands if the recovery turns
  out to be incomplete.
- Breaking change? No API or schema breaking change.

---

## Edge cases

| Edge case | Handling |
|---|---|
| A selected session has no saved assessment | Load `null` from the session-assessment endpoint and keep the blank assessment form state. |
| A selected session already has a saved assessment | Rehydrate the assessment form with the existing record so update/finalize paths operate on the current version. |
| The dependency audit helper runs in a tool-rich local environment | Audit only the dependencies pinned in `pyproject.toml` and report those findings. |
| The repo has formatting drift but the local Black runtime is older than Black's default target | Set repo-local Black target versions explicitly so the check matches the project's Python target. |
| Concatenated frontend files disagree between the two halves | Preserve the newer typed or safer implementation rather than blindly taking the first or last half. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Restoring duplicated files drops an intended newer change | Medium | High | Compare both halves and keep the newer typed or safer implementation when they differ. |
| Project-scoped dependency auditing hides a real transitive framework issue | Medium | Medium | Keep transitive findings in the audit output and document deferred framework upgrades explicitly. |
| Formatting changes touch files outside the immediate frontend repair | Medium | Low | Limit formatting work to the currently failing files and validate with tests after reformatting. |

---

## Breaking changes
No intended runtime breaking changes.
Verification behavior becomes more precise by auditing project-owned dependencies rather than the
ambient local environment.

---

## Testing strategy
- **Unit:** add tests for the Python dependency audit helper and keep existing workflow-governance
  tests green.
- **Integration:** run frontend typecheck, build, and unit tests after restoring the duplicated files
  and Vitest setup.
- **Integration:** run backend unit tests plus Black/isort after adding repo-local formatting config.
- **E2E:** not required for this recovery wave because no new user-facing route or flow is added.
- **Security:** validate the project-scoped dependency audit output and capture any remaining
  transitive framework follow-up explicitly.

### Verification completed
- `python -m pytest tests/unit --cov=src/biomechanics_ai --cov-report=term-missing` passed with 19
      tests and 85% total backend coverage.
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm run test` passed.
- `python -m ruff check src tests scripts/agent` passed.
- `python -m black --check src tests scripts/agent` passed.
- `python -m isort --check-only src tests scripts/agent` passed.
- `python -m bandit -r src -c pyproject.toml -ll` passed.
- `python -m mypy src` passed (`Success: no issues found in 16 source files`).
- `python scripts/agent/check_workflow_benchmarks.py` passed.
- `python scripts/agent/sync_agent_platform.py --check` passed.
- `python scripts/agent/check_python_dependency_audit.py` passed with no known vulnerabilities after
      upgrading the backend framework pins to `fastapi==0.121.0` and `starlette==0.49.1`.
- `python -m pip install --dry-run "fastapi==0.121.0" "starlette==0.49.1"` confirmed the updated
      pinned pair resolves together.
- Re-verified on 2026-04-15 with workflow-equivalent local commands:
  - `npm.cmd run typecheck` passed in `frontend/`.
  - `npm.cmd run build` passed in `frontend/`.
  - `npm.cmd run test` passed in `frontend/`.
  - `python -m pytest <abs>/tests/unit -c <abs>/pyproject.toml --cov=<abs>/src/biomechanics_ai --cov-report=term-missing` passed with 19 tests and 85% total coverage.
  - `python -m ruff check <abs>/src <abs>/tests <abs>/scripts/agent` passed.
  - `python -m black --check --config <abs>/pyproject.toml <abs>/src <abs>/tests <abs>/scripts/agent` passed.
  - `python -m isort --check-only --settings-path <abs>/pyproject.toml <abs>/src <abs>/tests <abs>/scripts/agent` passed.
  - `python -m mypy <abs>/src` passed.
  - `python -m bandit -r <abs>/src -c <abs>/pyproject.toml -ll` passed with no issues identified.
  - `python <abs>/scripts/agent/check_python_dependency_audit.py` passed with no known vulnerabilities found.

### Closeout note
- GitHub Actions status could not be queried from this environment on 2026-04-15. The repository's
  GitHub Actions pages returned 404 and the GitHub repository API was not accessible here, so final
  closeout is based on successful local reproduction of the touched verification lanes.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] All functional requirements implemented
- [x] All unit tests pass (80%+ coverage on new code)
- [x] Frontend typecheck, build, and unit tests pass
- [x] Backend unit tests pass
- [x] Black and isort checks pass for the repo's current verification scope
- [x] Project-scoped dependency audit runs and documents any remaining deferred findings
- [x] Reviewer agent: PASS
- [x] Workflow-equivalent verification lanes reproduced cleanly locally for the touched surfaces
- [x] Accessibility requirements remain satisfied for the restored practitioner workspace