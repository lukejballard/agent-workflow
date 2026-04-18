# Feature: Frontend Coverage Recovery Wave 3

**Status:** Completed
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** (previous repo-specific spec removed — see docs/specs/README.md for policy on repo-specific specs)

---

## Problem
Wave 2 materially improved the frontend snapshot, but the verified frontend report still remains below both the repository expectation and the user-raised 90% target.
The largest remaining tracked sinks are no longer broad API or studio helper files. They are concentrated in branch-heavy onboarding, contextual-help, alerting, and run-detail surfaces where the current tests prove only the most obvious flows.
If the next wave keeps adding route smoke coverage without attacking those branch paths directly, function and branch coverage will continue to lag behind line coverage.

## Success criteria
This wave should raise coverage by targeting the remaining branch-heavy frontend surfaces with direct regression tests instead of more denominator-only imports.
The post-wave snapshot should show measurable improvement in statements, functions, and branches, with specific recovery in `FirstRunGuide`, `HelpPanel`, `AlertRulesPage`, `AlertsPage`, `RunDetailsPage`, and `useRunDetails`.

---

## Requirements

### Functional
- [x] Add direct regression tests for `frontend/src/components/FirstRunGuide.tsx`, covering stored-role initialization, dismiss and tour flows, clipboard success or fallback handling, and role-specific actions.
- [x] Expand `frontend/src/__tests__/HelpPanel.test.tsx` to cover default-topic fallback, close behavior, keyboard and focus-management behavior, and copy-URL handling.
- [x] Expand alerting page coverage so `frontend/src/pages/AlertRulesPage.tsx` and `frontend/src/pages/AlertsPage.tsx` execute their remaining callback and conditional render branches instead of only basic tab or anchor behavior.
- [x] Add direct regression coverage for `frontend/src/hooks/useRunDetails.ts`, including realtime refresh gating, anomaly mapping, and toggle behavior.
- [x] Expand run-detail page coverage so `frontend/src/pages/RunDetailsPage.tsx` covers missing-run, anomaly acknowledgment, create-alert modal, help fallback, and empty timeline branches.
- AuditPage remains deferred for a later wave because the higher-value onboarding, alerting, and run-detail sinks delivered the biggest verified gains in this tranche.

### Non-functional
- [x] Accessibility: new tests prefer semantic and accessible locators, and touched user-visible flows preserve keyboard-usable behavior.
- [x] Regression safety: tests remain deterministic, with clipboard, storage, and realtime dependencies mocked at the boundary.
- [x] Performance: no new full-suite timeouts are introduced; any slow interaction tests are stabilized before closeout.
- [x] Documentation: this spec records the measured delta and remaining gaps against the 90% program target honestly.

---

## Affected components
- `docs/specs/active/frontend-coverage-recovery-wave-3.md`
- `frontend/src/components/FirstRunGuide.tsx`
- `frontend/src/components/HelpPanel.tsx`
- `frontend/src/pages/AlertRulesPage.tsx`
- `frontend/src/pages/AlertsPage.tsx`
- `frontend/src/pages/AuditPage.tsx`
- `frontend/src/pages/RunDetailsPage.tsx`
- `frontend/src/hooks/useRunDetails.ts`
- `frontend/src/__tests__/AlertRulesPage.coverage.test.tsx`
- `frontend/src/__tests__/AlertsPage.coverage.test.tsx`
- `frontend/src/__tests__/AuditPage.test.tsx`
- `frontend/src/__tests__/FirstRunGuide.test.tsx`
- `frontend/src/__tests__/HelpPanel.test.tsx`
- `frontend/src/__tests__/RunDetailsPage.coverage.test.tsx`
- `frontend/src/__tests__/RunDetailsPage.test.tsx`
- `frontend/src/__tests__/useRunDetails.test.ts`

---

## External context
No external context materially changes this wave.
The scope is driven by the local coverage report, repository testing standards, and the existing frontend architecture.

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
Use a branch-recovery strategy instead of another breadth-only page wave.

- Target denominator files that are already in the coverage report and still underperform badly on statements, functions, or branches.
- Prefer direct component or hook tests where page-level mocking would hide the uncovered logic.
- Keep page tests focused on visible behavior and callback wiring when that is the actual missing surface.
- Mock clipboard, localStorage, and realtime boundaries deterministically so the new tests are stable in the full suite.

Alternative considered:
- Expand only page-level route suites for more uncovered pages.

Why rejected:
- The current report shows the highest-return gaps are in already-tracked branch-heavy files, not just in untouched routes.
- More page-only smoke coverage would likely increase import breadth without materially improving branch or function coverage.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Stored onboarding role is invalid or the guide was previously dismissed | Tests verify the component falls back safely and hides when expected |
| Clipboard writes fail in onboarding or help flows | Tests verify user-visible fallback behavior instead of assuming clipboard success |
| Help panel is opened with an unknown topic | Tests verify it falls back to the default help configuration |
| Alerts page has a test-result banner, empty history, or alternate active tab | Tests cover the conditional branches directly |
| Run details are opened without a route param or with no anomalies | Tests cover early-return and hidden-section branches |
| Realtime events target a different run ID | Hook tests verify refresh only happens for the active run |
| Audit log filters produce no results or export fails | Secondary audit tests cover these branches if included in scope |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New tests become brittle because they over-mock local component structure | Medium | Medium | Assert on user-visible behavior and mock only the true I/O boundaries |
| Clipboard or realtime tests become flaky in the full suite | Medium | High | Stub browser APIs explicitly and avoid timing-based assertions |
| Coverage gain is smaller than expected because remaining sinks are more fragmented | Medium | Medium | Prioritize the tracked files with both low coverage and low current test depth, then rerun the full suite before extending scope |

---

## Testing strategy
- **Component:** `FirstRunGuide`, `HelpPanel`
- **Page-level:** `AlertRulesPage`, `AlertsPage`, `RunDetailsPage`, `AuditPage`
- **Hook-level:** `useRunDetails`
- **Full verification:** targeted Vitest run for the touched files, then full frontend suite with coverage, then frontend build

## Results
- Targeted Vitest tranche: 6 files, 19 tests, all passing.
- Full frontend Vitest suite: 59 files, 295 tests, all passing.
- Updated frontend coverage snapshot: 80.43% statements, 69.67% branches, 81.54% functions, 80.93% lines.
- Previous verified wave-2 snapshot: 77.96% statements, 67.40% branches, 76.93% functions, 78.61% lines.
- Verified file-level recovery:
	- `FirstRunGuide.tsx`: 85.00 / 92.85 / 82.35 / 83.78, up from 47.50 / 39.28 / 23.52 / 48.64.
	- `HelpPanel.tsx`: 55.93 / 33.33 / 80.00 / 56.14, up from 49.15 / 27.77 / 66.66 / 49.12.
	- `AlertRulesPage.tsx`: 100.00 / 50.00 / 100.00 / 100.00, up from 33.33 / 50.00 / 27.27 / 33.33.
	- `AlertsPage.tsx`: 94.44 / 87.50 / 93.75 / 93.75, up from 33.33 / 66.66 / 25.00 / 37.50.
	- `RunDetailsPage.tsx`: 97.14 / 93.10 / 85.71 / 96.77, up from 54.28 / 58.62 / 50.00 / 58.06.
	- `useRunDetails.ts`: 97.14 / 92.30 / 100.00 / 96.96, up from 68.57 / 46.15 / 63.63 / 69.69.

## Residual gaps
- The tranche improved the frontend baseline materially, but the program-level 90% target remains unmet.
- The biggest remaining weak files in the touched area are `HelpPanel.tsx` and `AuditPage.tsx`.
- Other denominator-heavy sinks still pulling the aggregate down include `CreateAlertFromFailure.tsx`, `AlertRuleCreateForm.tsx`, `AlertRulesList.tsx`, and several older page surfaces outside this tranche.
- A follow-up wave should prioritize those remaining branch-heavy sinks before broadening back into lower-yield route coverage.

---

## Acceptance criteria
- [x] FirstRunGuide regression suite added and passing
- [x] HelpPanel regression suite expanded and passing
- [x] AlertRulesPage and AlertsPage coverage improved with direct branch-path assertions
- [x] useRunDetails coverage improved with direct hook tests
- [x] RunDetailsPage coverage improved with anomaly and modal branches covered
- [x] Full frontend suite rerun with updated coverage snapshot against the 90% target
- [x] Frontend build rerun successfully
- [x] Residual risks summarized honestly