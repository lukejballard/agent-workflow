# Feature: UI Accessibility Regression Sweep

> Note: This completed spec is historical UI-hardening context. Any product-surface
> assumptions inside it belong to the inherited platform shell unless revalidated.

**Status:** Done
**Created:** 2026-04-13
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** frontend-enterprise-hardening.md

---

## Problem
The frontend shell was improved globally, but the most regression-prone mobile controls still needed proof and deeper follow-through.
Shared selectors alone do not guarantee that dashboard quick actions, docs navigation, onboarding-tour prompts, Studio landing controls, and the full Studio editor remain readable and usable at mobile widths.
If this is left unverified, small regressions can reappear silently in CSS overrides or less-travelled authoring flows.

## Success criteria
The key user-facing routes should keep 44x44 touch targets on mobile for shared and page-level controls, the Studio editor should remain operable at a narrow viewport with seeded data, and Playwright should catch regressions on the dashboard, docs, and Studio entry paths.

---

## Requirements

### Functional
- [x] Dashboard, docs, Studio landing, and Studio editor remain usable at a 375px viewport without critical controls dropping below 44x44.
- [x] Page-level controls that bypassed earlier shared-shell fixes are updated to meet the same target sizing and readability baseline.
- [x] Playwright assertions cover the mobile target sizes for the dashboard shell, docs nav, and Studio landing entry path.
- [x] The full Studio editor route is exercised with seeded data so deeper authoring controls are reviewed instead of only the landing page.
- [x] Architecture docs explain the ingestion boundary and both pipeline onboarding paths clearly.

### Non-functional
- [x] Performance: no new runtime dependencies and no new heavy client-side work on existing routes.
- [x] Security: no new auth or data-flow changes; all test stubbing stays inside the test boundary.
- [x] Accessibility: touched interactive elements meet the 44x44 minimum and preserve visible focus.
- [x] Observability: existing runtime health and dashboard contracts remain unchanged.

---

## Affected components
- `docs/specs/done/ui-accessibility-regression-sweep.md`
- `frontend/src/index.css`
- `frontend/tests/playwright/dashboard.spec.ts`
- `frontend/tests/playwright/docs.spec.ts`
- `frontend/tests/playwright/landing.spec.ts`
- `frontend/tests/playwright/studio.spec.ts`
- `frontend/tests/playwright/support/mobileUi.ts`
- `docs/architecture.md`
- `README.md`
- `docs/quickstart.md`

---

## External context
No external research materially changed this design.
This sweep was driven by the repository accessibility rules, existing frontend architecture, and the user request.

---

## Documentation impact
- Keep the top-level ingestion explanation in `README.md` and `docs/quickstart.md` aligned with a deeper architecture section.
- Add a dedicated architecture section that explains how SDK events and Studio definitions both cross the collector ingestion boundary.

---

## Architecture plan
Use a narrow brownfield sweep instead of a redesign.

1. Fix remaining page-level sizing and readability regressions in shared CSS where later overrides or local components still win.
2. Exercise the full Studio editor with seeded API responses to inspect the real authoring surface, not just the landing page.
3. Add Playwright assertions around mobile target sizes for the highest-risk routes so regressions fail visibly.
4. Refresh architecture docs so contributors and users can understand how pipelines enter the system and become observable.

---

## API design
No backend API contract changes.
Playwright coverage stayed at the browser boundary and only mocked existing frontend API requests.

---

## Data model changes
No database or backend schema changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Dashboard has no pipelines | Validate empty-state controls still meet touch target rules |
| Docs page loads without notifications data | Mock only the unread-count request and still assert docs-nav sizing |
| Studio landing has no pipeline definitions or templates | Mock empty arrays and assert the creation and navigation controls remain usable |
| Studio editor has seeded but minimal pipeline data | Provide a small realistic snapshot with at least one step so editor controls and side panels render |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Later CSS overrides silently reintroduce undersized controls | Medium | High | Add explicit Playwright size assertions on the final rendered controls |
| Studio editor mocks drift from the real API shape | Medium | Medium | Reuse existing Studio test fixtures and service shapes where possible |
| Mobile fixes improve size but introduce layout overflow | Medium | Medium | Re-run responsive browser checks at 375px on the rebuilt preview |

---

## Breaking changes
No intentional breaking API or workflow changes.
Only CSS behavior, docs clarity, and regression coverage changed.

---

## Testing strategy
- **Unit:** keep existing component and unit coverage unchanged unless the editor audit reveals a component-level regression.
- **Integration:** no new backend integration tests.
- **E2E:** add Playwright assertions for mobile target sizing on dashboard, docs, and Studio landing and editor flows.
- **Performance:** confirm the frontend still builds successfully.
- **Security:** ensure browser-level mocks do not alter production code paths.

---

## Verification snapshot
- [x] `npm run build` succeeds for the frontend.
- [x] Targeted Playwright coverage passes for dashboard, docs, Studio landing, and seeded Studio editor flows.
- [x] The refreshed build was verified against current `dist` assets after a stale preview bundle was ruled out.
- [x] The deterministic frontend unit failure in `RunDetailsPage.test.tsx` was corrected and the affected focused rerun passes.
- [x] Full frontend Vitest coverage passes in single-worker mode with global thresholds above the gate (`87.17%` statements, `80.53%` branches, `85.6%` functions, `87.54%` lines).
- [x] The Python CI-equivalent rerun passes after the repository recovery wave (`ruff check .`, `black --check .`, `mypy`, `pytest --cov --cov-report=xml --cov-fail-under=80`).
- [x] CI-style Playwright execution against the Vite dev server passes locally after aligning the host binding and narrowing browser-route mocks.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] All functional requirements implemented
- [x] All unit tests pass (80%+ coverage on new code)
- [x] All integration tests pass
- [x] E2E happy path passes in Playwright
- [x] CI green (lint, typecheck, tests, coverage, build, security scan)
- [x] Observability added (logs, metrics, health check if new service)
- [x] Accessibility requirements met (if UI change)
- [x] Breaking changes coordinated (if applicable)