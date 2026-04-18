# Feature: Launch Readiness Hardening

**Status:** Done
**Created:** 2026-04-12
**Author:** @lukejballard
**Estimate:** M
**Supersedes:** None

---

## Problem
The repository presented itself as launchable, but the highest-trust surfaces did not prove that claim.
The main gaps were broken frontend CI wiring, placeholder end-to-end startup in GitHub Actions, placeholder repo ownership, and contributor-facing documentation that did not reflect the real dashboard or verified API behaviour.
If left unresolved, the repo looked broader than it was trustworthy.

## Success criteria
The repository should prove that the real frontend package builds and tests in CI, that one meaningful full-stack Playwright path runs against a booted backend and seeded data, and that contributor-facing ownership and onboarding docs reflect the actual repo.
A new contributor should be able to identify the correct package boundaries and local frontend workflow without reverse-engineering the repo.

---

## Requirements

### Functional
- [x] GitHub Actions Node jobs run against the real `frontend/` package rather than assuming root-level scripts.
- [x] GitHub Actions E2E job starts the backend and frontend, waits for readiness, seeds demo data, and runs Playwright.
- [x] Playwright coverage includes one dashboard assertion backed by live seeded backend data.
- [x] `CODEOWNERS` uses real repository ownership instead of placeholders.
- [x] `frontend/README.md` documents the actual dashboard package, scripts, API proxy model, and test commands.
- [x] `docs/ci-cd.md` removes or corrects any API claims that are not verified by the current implementation.

### Non-functional
- [x] Performance: CI startup remains simple and uses the existing local dev server and SQLite defaults rather than adding Docker to the E2E job.
- [x] Security: no secrets or auth bypasses are introduced; documentation must not suggest unsupported badge or auth behaviour.
- [x] Accessibility: new or updated Playwright checks rely on accessible text or roles where practical.
- [x] Observability: CI captures backend and frontend logs on failure so stack boot issues are diagnosable.

---

## Affected components
- `.github/workflows/ci.yml`
- `frontend/tests/playwright/landing.spec.ts`
- `frontend/tests/playwright/studio.spec.ts`
- `frontend/tests/playwright/dashboard.spec.ts` (new)
- `frontend/README.md`
- `docs/ci-cd.md`
- `CODEOWNERS`
- `docs/specs/done/launch-readiness-hardening.md`

---

## Architecture plan
Keep the existing repo boundaries intact.

Preferred approach:
- Fix CI to use `frontend/` as the Node package root.
- Start the backend directly with `uvicorn` and the frontend with `vite` in the E2E job.
- Use the existing `/demo/seed` route to create deterministic live data for a meaningful dashboard check.
- Preserve current Studio smoke coverage while adding one dashboard check that proves data crosses the backend and frontend boundary.
- Repair trust surfaces in docs and ownership metadata.

Alternative considered:
- Create a root Node workspace with proxy scripts.

Why rejected:
- It adds packaging indirection without improving the product itself.
- The real problem was CI misunderstanding the current repo layout, not the lack of a root workspace.

---

## API design
No new API endpoints were added.
Documentation was corrected to match the currently implemented badge and CI-related APIs.

---

## Data model changes
No database schema changes.
The E2E job uses the existing SQLite default and demo seed routes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Backend starts slowly in CI | Add explicit readiness loops and fail with captured logs |
| Frontend starts before backend is ready | Wait for backend first, then start frontend and wait for `5173` |
| Dashboard shows first-run empty state | Seed demo data before Playwright starts |
| Playwright fails before stack teardown | Always upload backend and frontend logs as artifacts |
| Unsupported badge query examples remain in docs | Remove unsupported query examples and document verified behaviour only |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Playwright assertions remain too brittle | Medium | Medium | Use stable headings and known demo pipeline names |
| CI commands drift from local dev setup | Low | High | Reuse existing `uvicorn`, Vite, and package scripts |
| Docs still overstate behaviour elsewhere | Medium | Medium | Fix the highest-confidence verified drift in this pass and leave broader docs review out of scope |

---

## Breaking changes
No breaking runtime or API changes.
Contributor expectations changed because CI and docs now reflect the real package boundaries.

---

## Testing strategy
- **Unit:** keep existing frontend and backend unit test jobs; no new unit-only code paths are introduced.
- **Integration:** rely on existing backend integration coverage.
- **E2E:** add one dashboard Playwright test using seeded demo data; keep existing landing and Studio smoke tests.
- **Performance:** none beyond keeping CI startup lightweight.
- **Security:** ensure no credentials are added and docs do not promote unsupported auth or badge patterns.

---

## Verification snapshot
- [x] Frontend lint passes locally after excluding generated `coverage/` artifacts from ESLint input.
- [x] Frontend typecheck passes locally.
- [x] Frontend build passes locally.
- [x] Full frontend Vitest coverage passed earlier in this delivery wave above the enforced thresholds (`87.17%` statements, `80.53%` branches, `85.6%` functions, `87.54%` lines).
- [x] CI-style Playwright execution for landing, dashboard, and Studio flows passed earlier in this delivery wave.
- [x] Repo-local Python CI-equivalent gates now pass with `ruff check .`, `black --check .`, `mypy`, `pytest --cov --cov-report=xml --cov-fail-under=80`, `pip-audit`, and Bandit verification over explicit repo code paths (`83.33%` total coverage).

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