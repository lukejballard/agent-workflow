# Feature: Runs Surface Follow-up Hardening

> Note: This spec is inherited platform UI context. It is retained as archival
> material until baseball-biomechanics-ai defines equivalent user-facing surfaces.

**Status:** Implemented
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** S
**Supersedes:** docs/specs/active/platform-hardening-wave-2.md

---

## Problem
The previous hardening wave left one visible frontend regression-safety gap on the runs surface.
`RunsPage` still emits React `act(...)` warnings in Vitest, retains static inline styling in the filter controls, and lacks coverage for several important behaviors such as realtime refresh, compare selection, custom date filtering, and formatting edge cases used directly on the page.
If left unresolved, the warnings will keep obscuring real failures and the runs surface will remain an avoidable weak spot in frontend regression confidence.

## Success criteria
The `RunsPage` test file should run cleanly without React `act(...)` warnings, the remaining static inline filter styling should move into shared CSS classes, and regression tests should cover the highest-risk existing runs workflows and formatting helpers without changing user-visible behavior.

---

## Requirements

### Functional
- [x] `RunsPage` tests no longer emit React `act(...)` warnings during normal Vitest execution.
- [x] Remaining static inline filter/date control styling in `RunsPage` is replaced with shared CSS classes.
- [x] Regression tests cover search, custom date filtering, realtime refresh, compare selection, and DAG/compare navigation behaviors on `RunsPage`.
- [x] Formatting helper tests cover the date and duration edge cases rendered on the runs surface.

### Non-functional
- [x] Accessibility: touched controls retain accessible names, button semantics, and visible focus behavior.
- [x] Regression safety: no changes are introduced to backend APIs or route contracts.
- [x] Performance: the follow-up introduces no new runtime dependencies and keeps the existing paginated runs model intact.
- [x] Documentation: no user-facing docs change is required because behavior remains the same; the active spec must record the verification results.

---

## Affected components
- `docs/specs/active/runs-surface-followup-hardening.md`
- `frontend/src/pages/RunsPage.tsx`
- `frontend/src/index.css`
- `frontend/src/__tests__/RunsPage.test.tsx`
- `frontend/src/__tests__/formatters.test.ts`
- `frontend/src/utils/formatters.ts`

---

## External context
No external context materially changes this work.
The follow-up is driven by local test output, repository testing standards, and the previously documented residual risk from the platform hardening wave.

---

## Documentation impact
No user-facing or contributor-facing docs should change because this work preserves behavior and focuses on implementation quality, regression coverage, and test-signal cleanup.
This spec is the only documentation artifact that needs updating with the verification outcome.

---

## Architecture plan
Keep the page behavior unchanged while tightening the implementation and tests.

- Replace the remaining static inline filter/date layout styles with scoped CSS classes in `index.css`.
- Strengthen `RunsPage` tests so every test that triggers mount-time async state changes waits for the corresponding UI effect instead of ending early.
- Add targeted runs-surface regression tests for realtime updates, compare flow, navigation hooks, and custom date/search parameter handling.
- Add formatter tests for `relativeTime`, `formatDuration`, and adjacent helpers used on the runs surface.

---

## API design
No API changes.

---

## Data model changes
No data model changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Search input contains leading/trailing whitespace | Query is trimmed before the API call and covered by regression tests |
| Custom date end value is selected | End-of-day timestamp is sent so the chosen day remains inclusive |
| Realtime event is unrelated to run ingestion | No refetch is triggered |
| Compare selection exceeds two runs | Existing UI cap remains enforced and tested |
| Future timestamps or short durations are formatted | Helper tests cover the boundary outputs |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Test rewrite masks real async behavior | Low | Medium | Assert visible outcomes and API calls instead of implementation details |
| CSS cleanup causes layout drift on the runs toolbar | Low | Low | Preserve existing class structure and validate with targeted tests |
| Coverage improves only locally around the runs surface | High | Low | Treat this as a focused follow-up and report remaining repo-wide gaps honestly |

---

## Breaking changes
No breaking changes.

---

## Testing strategy
- **Unit/component:** `RunsPage` mount, filters, compare flow, realtime refresh, navigation hooks.
- **Unit/helper:** `formatters.ts` boundary cases used by runs UI.
- **Integration:** not required because no backend/API contract changes are introduced.
- **E2E:** not required for this focused follow-up if targeted Vitest coverage and existing route behavior remain unchanged.

## Verification summary
- `npm.cmd run test -- src/__tests__/RunsPage.test.tsx src/__tests__/formatters.test.ts` passed with 29/29 tests green.
- The targeted `RunsPage` suite no longer emitted the previously reproduced React `act(...)` warning.
- `npm.cmd run build` completed without TypeScript compiler errors after the follow-up changes.

---

## Acceptance criteria
- [x] `RunsPage` warning-free test execution verified
- [x] Runs surface regression tests added and passing
- [x] Formatter helper tests added and passing
- [x] Static inline runs filter styles removed
- [x] Residual risks updated honestly in the final summary

---

## Outcome
The follow-up removed the remaining static inline styling from the runs filter controls, added explicit accessible names for the search and custom date inputs, and strengthened `RunsPage` regression coverage around search trimming, custom date filters, compare selection, DAG navigation, pagination, and realtime refresh. Helper coverage was also added for the formatter functions used directly on the runs surface.

Residual risk remains outside this focused scope: this work improves the runs surface signal quality and helper coverage, but it does not by itself raise repo-wide frontend coverage on unrelated pages.