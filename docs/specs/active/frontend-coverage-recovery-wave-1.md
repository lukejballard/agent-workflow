# Feature: Frontend Coverage Recovery Wave 1

**Status:** Implemented
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** docs/specs/active/notifications-surface-followup-hardening.md

---

## Problem
The last targeted frontend hardening pass improved the notifications workflow, but the repo still has several user-facing pages with no direct regression coverage at all.
The alerting workflow is the highest-risk uncovered surface because it combines page state, tab switching, rule/channel management entry points, and operator-facing empty states, yet it currently has a broken link path in some alert-rule CTAs and no page-level tests. Beyond alerting, other high-signal pages such as system health, executive reporting, docs topics, and login remain uncovered, which keeps repo-wide frontend coverage materially below the repository target.

## Success criteria
The alerting workflow should route users to the correct alert-rules page, expose clear stateful interactions with accessible controls, and gain direct regression coverage for its core page behaviors. The broader coverage recovery tranche should add meaningful tests to additional untested high-signal pages so the full frontend suite gains measurable coverage and stronger regression confidence without resorting to low-value coverage padding.

---

## Requirements

### Functional
- [x] Alerts empty states and alert-management CTAs route consistently to `/alerts/rules`.
- [x] The Alerts page tab controls expose explicit active-state semantics that can be verified accessibly in tests.
- [x] Alerts and Alert Rules page regression tests cover the primary page states and navigation entry points.
- [x] Additional repo-wide recovery tests cover at least the currently untested Health, Executive Dashboard, Docs Topic, and Login surfaces.
- [x] The broader coverage tranche uses meaningful assertions around loading, empty, error, and success states instead of smoke-only rendering checks.

### Non-functional
- [x] Accessibility: touched interactive controls have accessible names, visible focus behavior, and machine-verifiable active or navigation state.
- [x] Security: no new direct fetches or unsafe rendering are introduced; login tests remain helper-backed and do not bypass auth boundaries incorrectly.
- [x] Performance: no new runtime dependencies are added and page behavior remains unchanged outside the targeted routing and accessibility fixes.
- [x] Regression safety: all touched page behaviors are covered by Vitest tests and the full frontend suite is rerun with coverage after implementation.

---

## Affected components
- `docs/specs/active/frontend-coverage-recovery-wave-1.md`
- `frontend/src/pages/AlertsPage.tsx`
- `frontend/src/components/alerts/AlertHistoryTab.tsx`
- `frontend/src/components/alerts/AlertRulesList.tsx`
- `frontend/src/__tests__/AlertsPage.test.tsx`
- `frontend/src/__tests__/AlertRulesPage.test.tsx`
- `frontend/src/__tests__/ExecutiveDashboardPage.test.tsx`
- `frontend/src/__tests__/HealthPage.test.tsx`
- `frontend/src/__tests__/DocsTopicPage.test.tsx`
- `frontend/src/__tests__/LoginPage.test.tsx`
- `frontend/src/__tests__/AlertChannelsTab.test.tsx`
- `frontend/src/__tests__/AlertHistoryTab.test.tsx`
- `frontend/src/__tests__/AlertRuleCreateForm.test.tsx`
- `frontend/src/__tests__/AlertRulesList.test.tsx`

---

## External context
No external context materially changes this wave.
The approach is driven by repository testing standards, the current router and page structure, and the user-approved request to continue with another targeted pass and then widen into repo-wide coverage recovery.

---

## Documentation impact
No contributor or user-facing documentation changes are required beyond this active spec because the intended product behavior is unchanged.
The spec must record the route fix, the new regression evidence, and the residual repo-wide coverage risks that remain after this tranche.

---

## Architecture plan
Use a two-part brownfield recovery pass.

- First, harden the alerting surface at the root by correcting broken alert-rules navigation and making the page tab state easier to verify accessibly.
- Second, add page-level regression tests to other untested but high-signal user journeys that can raise coverage without inventing fake behavior.
- Re-run the full frontend suite with coverage after the targeted and broader recovery work lands.

Alternative considered:
- Continue with another single-surface-only follow-up and postpone wider coverage recovery again.

Why rejected:
- It would leave too many untested page-level workflows untouched and keep repo-wide coverage recovery stalled.
- The alerting route bug provides a clear root fix, but the user explicitly asked to move on to the broader repo-wide coverage recovery afterward.

---

## API design
No backend API changes.
Frontend tests will mock existing page dependencies through the current API and hook boundaries.

---

## Data model changes
No data model changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Alert history is empty | Empty-state CTA links to the real alert-rules route |
| Alert rules list is empty | Empty-state CTA links to the real alert-rules route |
| Alerts tab changes | Active state remains visible and testable through accessible button state |
| Executive dashboard has no data | Empty-state guidance remains visible and tested |
| Health page is loading or errors | Loading and retry paths are verified directly |
| Docs topic slug is invalid | Not-found state remains navigable back to docs home |
| Login fails | Error state remains explicit and no accidental navigation occurs |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Coverage increases through shallow render-only tests | Medium | High | Use user-visible assertions around state, navigation, and error handling |
| Mock-heavy page tests drift from real runtime behavior | Medium | Medium | Mock only page dependencies at the API or hook boundary and assert outcomes, not implementation details |
| Repo-wide coverage still remains below 80% after this wave | High | Medium | Report the post-wave snapshot honestly and treat this as the first recovery tranche, not the final one |

---

## Breaking changes
No breaking changes.

---

## Testing strategy
- **Unit/component:** alerting pages, executive dashboard page, health page, docs topic page, and login page.
- **Integration:** not required because no API or route contract changes are introduced beyond correcting an internal frontend link target.
- **E2E:** not required for this tranche if the page-level Vitest coverage and full frontend rerun remain green.
- **Accessibility:** verify active tab state, empty-state links, and login/health interactions through accessible locators.

---

## Acceptance criteria
- [x] Alert-rules navigation is consistent across the alerting workflow
- [x] Alerts page active tab state is accessibility-friendly and tested
- [x] Alerts and Alert Rules page tests added and passing
- [x] Health, Executive Dashboard, Docs Topic, and Login page tests added and passing
- [x] Full frontend suite rerun with updated coverage snapshot
- [x] Residual coverage risks summarized honestly

---

## Outcome
This wave closed a verified alerting navigation defect by routing alert-history and empty-rules CTAs to the real alert-rule creation entry point under `/alerts/rules#create-alert-rule` and by adding explicit pressed-state semantics to the alert view switcher.
It also expanded frontend regression coverage across the alerting surface and added new coverage for previously untested Health, Executive Dashboard, Docs Topic, and Login pages.

## Verification summary
- Targeted new page suites passed: 15/15 tests
- Targeted alert component suites passed: 8/8 tests
- Full frontend suite passed: 39 files / 232 tests
- Updated frontend coverage snapshot: 65.72% statements / 55.73% branches / 64.48% functions / 66.76% lines
- Frontend build verified with `npm.cmd run build`

## Residual risks
- Repo-wide frontend coverage remains below the repository target of 80%, so additional recovery waves are still required.
- The next highest-value gaps are now concentrated in lower-covered API helper modules, several settings and quality components, and remaining page surfaces such as Connections, Pipeline Catalog, and Streaming.