# Feature: Platform Hardening Wave 2

> Note: This spec is inherited platform-hardening context and is not a validated
> biomechanics product requirement.

**Status:** Implemented
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** docs/specs/active/frontend-enterprise-hardening.md

---

## Problem
The first hardening pass improved dashboard onboarding, docs, and helper-backed frontend flows, but major enterprise-readiness gaps remain across the product.
Important frontend surfaces still depend heavily on inline styling and ad hoc interaction logic, regression coverage remains materially below repository targets, and backend/deployment security posture still depends on permissive defaults and minimally hardened container/runtime configuration.

## Success criteria
The next pass should reduce frontend UI debt on the highest-signal operational pages, materially raise regression coverage on newly hardened user journeys and helper modules, and strengthen backend/deployment security controls without breaking current development workflows.
All security messaging must remain honest: this wave improves concrete controls and defaults, but does not claim absolute certification or eliminate all platform risk.

---

## Requirements

### Functional
- [x] The highest-value remaining inline-style-heavy frontend surfaces are refactored toward shared CSS-backed structure, starting with getting-started, notifications, audit, and notification-bell flows.
- [x] Frontend interactions on those touched pages retain the same user-visible behavior while becoming more consistent and easier to maintain.
- [x] Additional frontend regression tests are added for touched operational pages/components and for low-coverage helper modules introduced in prior work.
- [x] Backend runtime security is strengthened with clearer, configurable CORS and trusted-host controls instead of hardcoded-only origin behavior.
- [x] Backend security headers are strengthened beyond the current baseline while remaining compatible with API, SSE, and browser-based use.
- [x] Container hardening is improved through safer Docker defaults, non-root execution, and better build hygiene.
- [x] Deployment and environment documentation is updated so operators know which variables and network boundaries matter in production.

### Non-functional
- [x] Accessibility: touched frontend controls preserve accessible names, visible focus, and keyboard-usable interactions.
- [x] Security: no new secrets are introduced in source, touched auth/networking paths avoid over-broad defaults, and deployment docs clearly describe expected trust boundaries.
- [x] Performance: frontend cleanup does not add heavy dependencies and backend hardening does not add blocking request-path work.
- [x] Regression safety: all touched frontend and backend changes land with automated tests or documented residual risk.

### Explicit non-goals
- [x] No new backend API routes or response-schema changes are introduced in this wave.
- [x] No database schema or data migration is introduced in this wave.

---

## Affected components
- `docs/specs/active/platform-hardening-wave-2.md`
- `frontend/src/pages/GettingStartedPage.tsx`
- `frontend/src/components/GettingStartedModule.tsx`
- `frontend/src/pages/NotificationsPage.tsx`
- `frontend/src/components/NotificationBell.tsx`
- `frontend/src/pages/AuditPage.tsx`
- `frontend/src/index.css`
- `frontend/src/__tests__/` (new/updated tests for touched pages/components and helper modules)
- `src/biomechanics_ai/config/settings.py`
- `src/biomechanics_ai/collector/security_middleware.py`
- `src/biomechanics_ai/collector/server.py`
- `tests/unit/` (new backend config/security tests)
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `.dockerignore`
- `docker-compose.yml`
- `.env.example`
- `docs/deployment.md`

---

## Architecture plan
Use a targeted hardening pass, not a broad redesign.

Preferred approach:
- Replace repeated inline-style-heavy frontend patterns with CSS-backed classes and lightweight presentational helpers on the highest-signal operational pages.
- Add focused tests for the touched frontend pages and low-coverage API/helper modules to raise confidence where the previous pass added new behavior.
- Move backend CORS/trusted-host configuration into explicit settings helpers, strengthen API security headers, and cover those behaviors with unit tests.
- Improve container defaults by using non-root runtime users, tighter image hygiene, and deployment docs that describe the intended production security posture.

Alternative considered:
- Rewrite the frontend shell and broader backend auth/deploy model in one pass.

Why rejected:
- The blast radius would be high and verification quality would fall.
- The current gaps are concentrated in maintainability debt, coverage holes, and hardening defaults that can be improved incrementally.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Frontend cleanup changes visual behavior unintentionally | Medium | Medium | Keep tests on touched interactions and validate in browser after styling changes |
| New security defaults break local development or existing deploys | Medium | High | Preserve dev-safe defaults, make stricter behavior configurable, and document migration clearly |
| Coverage increases on touched files but repo-wide target still remains unmet | High | Medium | Report actual coverage honestly and focus new tests on the highest-risk surfaces |
| Container hardening changes image/runtime assumptions | Medium | High | Keep external ports stable, document runtime changes, and build-verify final images where possible |

---

## Edge cases and rollback
- Development and tests must continue to work when trusted-host and allowed-origin env vars are unset.
- Production deployments must be able to opt into explicit origin and host allow-lists without changing application code.
- The frontend runtime port exposed to users must remain unchanged even if the internal container port becomes unprivileged.
- If stricter deployment defaults cause operator issues, rollback is limited to restoring the previous Dockerfiles/compose env values and disabling the new host/origin env configuration.

---

## Testing strategy
- **Frontend unit/component:** touched page/component interactions, helper modules, empty/error/filter states, and notification/audit behaviors.
- **Backend unit:** CORS/trusted-host parsing, security-header behavior, and configuration defaults.
- **Build validation:** frontend build plus static validation of Dockerfile and compose changes.
- **Browser validation:** spot-check the touched frontend operational pages in a live browser after refactors.
- **Security checks:** npm audit for frontend, targeted static scan for raw HTML injection / direct fetch drift on touched frontend code, and explicit residual-risk reporting for unverified backend/deploy controls.

## Verification summary
- Backend targeted tests passed: `25 passed in 4.84s` for security/config and auth-adjacent coverage.
- Frontend targeted onboarding regression passed after stabilization: `2 passed` in `GettingStartedPage.test.tsx`.
- Frontend full suite passed with coverage: `28` test files, `185` tests.
- Frontend coverage after this wave: statements `62.84%`, branches `53.06%`, functions `60.67%`, lines `64.14%`.
- Frontend lint, typecheck, and build were re-run successfully; production build output was verified.

## Residual risks
- Repo-wide frontend coverage remains below the repository-wide `80%` target; this wave materially improved coverage on touched surfaces but did not close the entire gap.
- Existing React `act(...)` warnings remain in `RunsPage.test.tsx`; they did not fail the suite, but they still represent test debt.
- Frontend consistency cleanup was intentionally targeted to the highest-value operational pages, not every remaining inline-style surface in the repo.

---

## Acceptance criteria
- [x] Touched frontend cleanup implemented
- [x] Touched frontend regression tests pass
- [x] Backend security/configuration tests pass
- [x] Frontend lint, typecheck, tests, and build pass
- [x] Docs and env/deploy guidance updated for new security controls
- [x] Residual risks and non-addressed repo-wide debt documented honestly