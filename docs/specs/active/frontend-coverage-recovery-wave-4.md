# Feature: Frontend Coverage Recovery Wave 4

**Status:** Completed
**Created:** 2026-04-13
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** docs/specs/active/frontend-coverage-recovery-wave-3.md

---

## Problem
Wave 3 raised the frontend baseline materially, but the verified snapshot is still well below the repository target and the user-raised 90% goal.
The largest remaining tracked sinks are now concentrated in `AuditPage`, `HelpPanel`, and the alert-creation surfaces where the current tests still miss many conditional branches, callback paths, and empty or error states.
If the next tranche keeps broadening route coverage without attacking those branch-heavy files directly, branch and function coverage will continue to lag the overall denominator.

## Success criteria
This wave should improve the verified frontend snapshot by covering the remaining high-yield branch surfaces in `AuditPage`, `HelpPanel`, `CreateAlertFromFailure`, `AlertRuleCreateForm`, and `AlertRulesList`.
The post-wave report should show measurable recovery in statements, functions, and branches for those files, with no regressions in the full frontend suite or build.

---

## Requirements

### Functional
- [x] Expand `frontend/src/__tests__/HelpPanel.test.tsx` to cover stored-feedback recovery, remaining keyboard focus-loop behavior, and clipboard-failure handling.
- [x] Expand `frontend/src/__tests__/AuditPage.test.tsx` to cover loading, error, filtered-empty, sort-toggle, refresh, and export-failure branches using the real page behavior.
- [x] Add direct regression coverage for `frontend/src/components/CreateAlertFromFailure.tsx`, including context rendering, channel add or remove behavior, validation, and success callbacks.
- [x] Expand `frontend/src/__tests__/AlertRuleCreateForm.test.tsx` so additional rule-type, preview, and empty-channel branches execute instead of only the failure and anomaly happy path.
- [x] Expand `frontend/src/__tests__/AlertRulesList.test.tsx` so the list renders additional rule previews, severity states, channel-badge variants, and loading or error states.

### Non-functional
- [x] Accessibility: new tests prefer semantic queries and preserve keyboard-usable behavior on the touched surfaces.
- [x] Regression safety: tests remain deterministic, with network and toast boundaries mocked explicitly where needed.
- [x] Brownfield discipline: no production behavior changes are introduced unless a verified testability or correctness issue blocks coverage.
- [x] Documentation: this spec records the recovery intent and measured results honestly against the 90% goal.

---

## Affected components
- `docs/specs/active/frontend-coverage-recovery-wave-4.md`
- `frontend/src/components/HelpPanel.tsx`
- `frontend/src/pages/AuditPage.tsx`
- `frontend/src/components/CreateAlertFromFailure.tsx`
- `frontend/src/components/alerts/AlertRuleCreateForm.tsx`
- `frontend/src/components/alerts/AlertRulesList.tsx`
- `frontend/src/__tests__/AuditPage.test.tsx`
- `frontend/src/__tests__/AlertRuleCreateForm.test.tsx`
- `frontend/src/__tests__/AlertRulesList.test.tsx`
- `frontend/src/__tests__/HelpPanel.test.tsx`
- `frontend/src/__tests__/CreateAlertFromFailure.test.tsx`

---

## External context
No external context materially changes this wave.
The scope is driven by the local coverage report, repository testing standards, and the current frontend architecture.

## Documentation impact
No contributor-facing or user-facing docs should change beyond this active spec because the intended product behavior remains the same.
This spec is the working source of truth for the recovery scope, verification evidence, and residual gaps.

## API design
No API contract changes are planned.
This wave targets frontend regression coverage only.

## Data model changes
No data model changes.

## Breaking changes
No breaking changes.

---

## Architecture plan
Use direct branch recovery against the current denominator-heavy sinks rather than broadening route smoke coverage.

- Keep `AuditPage` on its real `useFetch` path so sorting, filtering, refresh, and export logic are exercised together.
- Prefer direct component tests for `CreateAlertFromFailure`, `AlertRuleCreateForm`, and `AlertRulesList` because page-level mocking would hide the uncovered logic.
- Expand `HelpPanel` only where remaining keyboard and fallback branches are still unverified.
- Mock network and toast boundaries explicitly so the new tests remain deterministic in the full suite.

Alternative considered:
- Mock `useFetch` and page-level alert managers everywhere to drive coverage through callback injection only.

Why rejected:
- That approach would raise raw line counts but leave the highest-risk local logic in `AuditPage` and the alert creation components effectively unverified.
- The remaining gaps are mostly inside the components themselves, so direct tests provide better regression value per added assertion.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Help panel loads invalid or unexpected stored feedback | Tests verify the panel falls back safely without breaking the session |
| Help panel keyboard focus reaches the first or last focusable control | Tests verify forward and reverse tab wrapping |
| Audit log fetch fails or returns no filtered matches | Tests verify the visible error and empty-state branches |
| Audit log sort changes across timestamp, actor, or action | Tests verify row order changes instead of only button clicks |
| Alert creation starts from a failed run with failed steps or anomalies | Tests verify the run context is surfaced in the modal |
| Alert creation is attempted with invalid local form state | Tests verify validation toasts instead of assuming the happy path |
| Alert rules render uncommon rule types or channel prefixes | Tests verify preview fallbacks and channel badge rendering without assuming only the common cases |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `AuditPage` tests become flaky because they depend on the real fetch hook timing | Medium | Medium | Use deterministic mocked API responses and wait only on visible state transitions |
| Component tests overfit internal DOM structure instead of visible behavior | Medium | Medium | Assert on user-visible text, control state, and callback effects rather than CSS shape |
| Coverage gains are smaller than expected because some branches are effectively dead from the current UI | Medium | Medium | Focus on the reachable branches first and record residual gaps honestly after verification |

---

## Testing strategy
- **Component:** `HelpPanel`, `CreateAlertFromFailure`, `AlertRuleCreateForm`, `AlertRulesList`
- **Page-level:** `AuditPage`
- **Full verification:** targeted Vitest run for the touched files, then full frontend suite with coverage, then frontend build if the tranche remains stable

## Results
- Targeted Vitest tranche: 5 files, 28 tests, all passing.
- Full frontend Vitest suite: 60 files, 312 tests, all passing.
- Updated frontend coverage snapshot: 84.48% statements, 74.69% branches, 84.42% functions, 85.01% lines.
- Previous verified wave-3 snapshot: 80.43% statements, 69.67% branches, 81.54% functions, 80.93% lines.
- Verified file-level recovery:
	- `HelpPanel.tsx`: 89.83 / 88.88 / 93.33 / 89.47, up from 55.93 / 33.33 / 80.00 / 56.14.
	- `AuditPage.tsx`: 88.70 / 90.90 / 72.72 / 88.33, up from 58.06 / 60.60 / 31.81 / 60.00.
	- `CreateAlertFromFailure.tsx`: 90.69 / 80.00 / 100.00 / 90.00, up from 0.00 / 0.00 / 0.00 / 0.00.
	- `AlertRuleCreateForm.tsx`: 83.72 / 91.48 / 68.75 / 83.72, up from 55.81 / 55.31 / 68.75 / 55.81.
	- `AlertRulesList.tsx`: 93.93 / 88.09 / 100.00 / 93.93, up from 54.54 / 38.09 / 100.00 / 54.54.
- Frontend production build completed successfully.

## Residual gaps
- The tranche improved the aggregate snapshot materially, but the program-level 90% target remains unmet.
- The remaining deficit is now smaller and more fragmented, with branch coverage still trailing the other aggregates.
- `AlertRuleCreateForm.tsx` still has function coverage gaps because several control callbacks are not all exercised in a single direct-render path.
- `AuditPage.tsx` improved sharply, but some local callback and pagination-edge branches still remain below the file's statement and branch recovery.
- A follow-up wave should now pivot to the next denominator-heavy files outside this tranche rather than revisit these surfaces first.

---

## Acceptance criteria
- [x] HelpPanel regression suite expanded and passing
- [x] AuditPage regression suite expanded and passing
- [x] CreateAlertFromFailure regression suite added and passing
- [x] AlertRuleCreateForm and AlertRulesList coverage improved with additional branch-path assertions
- [x] Targeted frontend suite rerun successfully
- [x] Full frontend suite rerun with updated coverage snapshot against the 90% target
- [x] Frontend build rerun successfully
- [x] Residual risks summarized honestly