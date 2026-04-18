# Feature: Frontend Enterprise Hardening

**Status:** Implemented (superseded by platform-hardening-wave-2.md)
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** None

---

## Problem
The current frontend presents valuable product capabilities, but several high-trust surfaces do not meet the repo's own standards for enterprise UX, architecture, or verification.
The dashboard onboarding experience uses under-styled role controls and mixed inline styling, the in-app documentation and help surfaces are not fully integrated, and several touched frontend areas still issue direct `fetch()` calls from pages, components, or context instead of going through typed API helpers.
If left unchanged, nontechnical evaluators will encounter avoidable friction, contributors will keep shipping architectural drift, and the product will overstate confidence relative to its current regression coverage.

## Success criteria
The dashboard should provide a clear, polished, role-based onboarding path for first-time users, the docs and contextual help surfaces should guide nontechnical and technical users through the platform without dead-end links, and the touched frontend surfaces should align with the repository architecture rules.
Verification should prove the updated onboarding, docs, and help flows render correctly, support keyboard and accessible interaction, and retain working regression coverage in unit and Playwright tests.

## Outcome
This wave delivered the dashboard onboarding, docs/help integration, and shared frontend helper migration described here.
Broader frontend consistency cleanup, additional coverage uplift, and backend/deployment hardening were continued in `platform-hardening-wave-2.md` so the remaining enterprise-readiness work stayed explicit instead of being hand-waved inside this spec.

---

## Requirements

### Functional
- [ ] The dashboard first-run experience presents clearly styled role-selection controls and structured action cards that are readable on desktop and mobile.
- [ ] The role-based onboarding content explains the purpose of each path in business-oriented language and provides valid next actions for each role.
- [ ] The in-app documentation home page adds deeper guidance that helps users understand how the platform is organized, how common workflows map to pages, and where to go next.
- [ ] The contextual help panel links to valid in-platform documentation routes for each supported topic and uses consistent shared styling rather than ad hoc inline layout.
- [ ] Touched frontend pages, components, and context modules stop calling `fetch()` directly and instead use typed helpers in `frontend/src/api/`.
- [ ] The login, search, and anomaly-explanation flows retain equivalent behavior while using the shared API layer for auth headers, error construction, and boundary handling.
- [ ] Automated regression coverage is added or updated for the dashboard onboarding, docs/help journeys, and touched API-backed interactions.

### Non-functional
- [ ] Performance: the changes add no new heavy runtime dependencies and keep the current route-level lazy-loading approach intact.
- [ ] Security: touched frontend network calls use the shared HTTP/auth path, no unsafe HTML rendering is introduced, and user-facing docs do not overclaim security guarantees beyond verified platform behavior.
- [ ] Accessibility: the updated onboarding, docs, and help controls provide accessible names, visible focus treatment, keyboard support, and WCAG AA-friendly contrast.
- [ ] Observability: user-visible error and empty states remain explicit for touched async flows so failures are diagnosable without inspecting source code.

---

## Affected components
- `docs/specs/active/frontend-enterprise-hardening.md`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/components/FirstRunGuide.tsx`
- `frontend/src/components/RoleSelector.tsx`
- `frontend/src/pages/DocsPage.tsx`
- `frontend/src/pages/DocsTopicPage.tsx`
- `frontend/src/components/HelpPanel.tsx`
- `frontend/src/components/docs/RoleQuickStart.tsx`
- `frontend/src/components/docs/TaskGuide.tsx`
- `frontend/src/components/docs/OperationalRunbook.tsx`
- `frontend/src/components/docs/docsContent.ts`
- `frontend/src/pages/docsContent.ts`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/components/AnomalyExplanation.tsx`
- `frontend/src/components/NLQueryBar.tsx`
- `frontend/src/api/http.ts`
- `frontend/src/api/` (new typed helpers for auth/search/rca as needed)
- `frontend/src/index.css`
- `frontend/src/__tests__/DashboardPage.test.tsx`
- `frontend/src/__tests__/` (new or updated docs/help/auth/search tests as needed)
- `frontend/tests/playwright/` (updated or new docs/dashboard regression coverage)

---

## External context
No external research materially changes this design.
The implementation is driven by the repository standards, the current frontend architecture, and the explicit user request.

---

## Documentation impact
- Update the in-platform documentation content and navigation so first-time users can understand platform areas, role-based entry points, and next-step workflows.
- Keep documentation claims aligned with currently implemented routes and UI behavior.
- No separate contributor docs are required unless implementation reveals current docs drift outside the in-app documentation experience.

---

## Architecture plan
Use a focused brownfield hardening approach rather than a full frontend rewrite.

Preferred approach:
- Improve the dashboard first-run experience by treating the role selector and option cards as a real onboarding surface with shared CSS classes, richer copy, and clearer hierarchy.
- Deepen the docs home page by adding a platform map, enterprise workflow guidance, and stronger role-based guidance driven by structured content objects instead of page-local ad hoc markup.
- Normalize contextual help and touched async flows around typed API helpers in `frontend/src/api/` so pages/components/context stop performing direct `fetch()` calls.
- Add regression tests around the updated UX and touched helper-backed flows, then verify the updated UI with Playwright across key routes.

Alternative considered:
- Perform a broad multi-page redesign and large-scale frontend state management refactor.

Why rejected:
- It would increase blast radius substantially and make verification weaker for this pass.
- The most acute issues are concentrated in onboarding, docs/help integration, and architecture drift, which can be corrected without reworking the entire app shell.

---

## API design
No backend API contract changes are expected.
This work only adds or refactors frontend API helper wrappers for existing endpoints such as auth, search, and anomaly explanation.

---

## Data model changes
No database or backend schema changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| First-time user has no role selected | Show neutral onboarding copy and non-destructive role choices |
| Clipboard API is unavailable | Keep fallback toast/help text rather than failing silently |
| Search query returns no results | Show explicit empty state and keep input usable |
| Help panel topic has no mapped docs page | Route to a valid default in-app docs topic instead of a broken link |
| Stored auth token is invalid | Clear auth state through shared validation path and keep login flow recoverable |
| Anomaly explanation request fails | Preserve a clear inline error state without breaking the anomaly list |
| Narrow viewport/mobile layout | Role controls, docs cards, and help content collapse without horizontal overflow |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| UX copy improves presentation but still overpromises unavailable product paths | Medium | High | Keep copy tied to implemented routes and visible pages only |
| Shared API-helper refactor introduces regressions in auth/search/error handling | Medium | High | Add focused unit tests for touched flows and preserve current runtime behavior |
| CSS changes bleed into unrelated pages | Medium | Medium | Scope selectors to existing component class names and verify with Playwright |
| Broad user request leads to unverifiable absolute security claims | High | High | Keep implementation honest, strengthen concrete frontend controls, and report residual limits explicitly |

---

## Breaking changes
No intentional breaking route or API changes.
User-facing onboarding copy, docs structure, and help-panel links will change, but the goal is to improve discoverability while preserving existing navigation targets.

---

## Testing strategy
- **Unit:** cover the updated dashboard onboarding, role selector behavior, docs/help linking, login flow, search behavior, and anomaly explanation states.
- **Integration:** use shared HTTP helper tests where touched helper logic changes auth or error-path behavior.
- **E2E:** verify dashboard and docs journeys in Playwright, including role-based onboarding visibility and docs navigation on a live frontend.
- **Performance:** confirm no new runtime dependency or route-loading regression is introduced by the touched code.
- **Security:** verify touched flows rely on shared auth/error helpers, avoid unsafe rendering, and keep docs claims aligned with implemented behavior.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [ ] All functional requirements implemented
- [ ] All unit tests pass (80%+ coverage on new code)
- [ ] All integration tests pass
- [ ] E2E happy path passes in Playwright
- [ ] Reviewer agent: PASS
- [ ] CI green (lint, typecheck, tests, coverage, build, security scan)
- [ ] Observability added (logs, metrics, health check if new service)
- [ ] Accessibility requirements met (if UI change)
- [ ] PR template filled out and linked to this spec
- [ ] Breaking changes coordinated (if applicable)