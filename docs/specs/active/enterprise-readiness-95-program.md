# Feature: Enterprise Readiness 95 Program

> Note: This active spec still reflects an inherited platform-hardening program. It
> is retained for historical and process context, not as a validated biomechanics
> product requirement.

**Status:** Draft
**Created:** 2026-04-13
**Author:** @github-copilot
**Estimate:** XL
**Supersedes:** PRODUCT_AUDIT_REPORT.md (baseline conclusions only)

---

## Problem
The product direction is already enterprise-facing, but the current platform defaults,
verification posture, and deployment contract do not yet support an honest 95%+
enterprise-readiness claim.

The audit found that product capability is ahead of platform trust.
Several high-severity blockers are still present in default or release-critical paths:

- Control-plane access falls back to anonymous access with an effective default role of `admin`
  when API keys are unset.
- JWT-backed user auth exists, but the shipped frontend and env defaults keep it disabled.
- Backend validation is broad and mostly green, but overall Python coverage is only `64%`.
- Frontend lint, typecheck, build, and dependency audit pass, but the Vitest suite is red with
  seven timeout failures across four files.
- Kubernetes deployment drift exists: the hardened frontend image serves on `8080`, while the
  shipped manifest still targets container port `80`.
- CI workflows do not declare least-privilege `permissions`, and actions remain pinned only to
  mutable major-version tags.
- `pip-audit` still reports known vulnerable packages in the active Python environment.
- `.env.example` and deployment defaults still favor permissive or non-placeholder values in areas
  that should be explicit for enterprise use.

If this is not corrected at the platform level, the product can look more mature than the runtime,
security, and verification evidence can support.

## Success criteria
The platform can only be scored at `95%+` enterprise readiness when all of the following are true:

- Security and access control score `95/100` or better:
  no anonymous admin-equivalent control-plane access, shared/prod deployments require explicit
  authentication configuration, and RBAC behavior is verified by tests.
- Release confidence score `95/100` or better:
  backend and frontend CI gates are green, the frontend timeout failures are eliminated, and the
  repo meets the stated `80%` coverage bar for the critical product surfaces that define release risk.
- Deployment/runtime correctness score `95/100` or better:
  Docker and Kubernetes assets are internally consistent, validated, and documented for the hardened
  runtime contract.
- Supply-chain and CI governance score `95/100` or better:
  high-severity dependency findings are remediated or explicitly accepted with tracked rationale,
  workflow permissions are least-privilege, and action pinning policy is enforced.
- Operability and observability score `95/100` or better:
  system health, logs, metrics, tracing, alerting, and run/audit evidence remain truthful and
  verifiable in production-like environments.
- Documentation and accessibility score `95/100` or better:
  deployment/auth/docs reflect the real defaults and behavior, and user-facing flows have both
  regression and accessibility evidence.

---

## Requirements

### Functional
- [ ] Capture an enterprise-readiness baseline for the current repo with verified PASS / WARN / FAIL findings,
      not aspirational statements.
- [ ] Split remediation into staged waves with explicit entry criteria, exit criteria, and verification artifacts.
- [ ] Wave 1 must harden default access control, correct deployment contract drift, and remove the ability to
      unintentionally run a shared control plane with anonymous admin-equivalent access.
- [ ] Wave 2 must restore regression trust by eliminating current red frontend tests and materially improving
      backend and frontend coverage on the highest-risk surfaces.
- [ ] Wave 3 must close supply-chain and CI governance gaps, including vulnerable dependency remediation,
      workflow permissions, and action pinning policy.
- [ ] Wave 4 must close enterprise evidence gaps in accessibility automation, operational runbooks,
      release traceability, and product-facing trust surfaces.
- [ ] Each wave must leave behind a verifiable artifact set: updated spec, green targeted tests, updated docs,
      and explicit residual-risk accounting.

### Non-functional
- [ ] Performance: hardening work must preserve the repo's stated targets for API latency and frontend bundle growth;
      no wave may add blocking request-path work without bounded queries and measured impact.
- [ ] Security: shared and production deployments must be default-secure by configuration contract,
      and open-access mode must be clearly demoted to local-only behavior.
- [ ] Accessibility: user-facing flows touched by the program must meet WCAG AA and gain automated accessibility checks,
      not only manual intent.
- [ ] Observability: new or changed runtime-critical paths must emit actionable logs, metrics, and traces,
      and audit evidence must remain exportable and truthful.

---

## Affected components
- `docs/specs/active/enterprise-readiness-95-program.md`
- `PRODUCT_AUDIT_REPORT.md`
- `.env.example`
- `README.md`
- `docs/architecture.md`
- `docs/deployment.md`
- `docs/quickstart.md`
- `docs/runbooks/`
- `src/biomechanics_ai/config/settings.py`
- `src/biomechanics_ai/auth/`
- `src/biomechanics_ai/collector/auth.py`
- `src/biomechanics_ai/collector/auth_routes.py`
- `src/biomechanics_ai/collector/security_middleware.py`
- `src/biomechanics_ai/collector/pipeline_routes.py`
- `src/biomechanics_ai/collector/server.py`
- `src/biomechanics_ai/collector/*_routes.py`
- `src/biomechanics_ai/observability/`
- `src/biomechanics_ai/execution/`
- `src/biomechanics_ai/storage/`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/api/`
- `frontend/src/pages/`
- `frontend/src/components/`
- `frontend/src/__tests__/`
- `frontend/tests/playwright/`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `docker-compose.yml`
- `deploy/kubernetes/backend.yaml`
- `deploy/kubernetes/frontend.yaml`
- `deploy/kubernetes/postgres.yaml`
- `deploy/kubernetes/ingress.yaml`
- `.github/workflows/ci.yml`
- `.github/workflows/continuous-audit.yml`
- `.github/workflows/pr-quality.yml`
- `tests/unit/`
- `tests/integration/`

---

## External context
No external research materially changed this design.
The plan is based on verified repository evidence, existing active specs, current workflow rules,
and live validation results gathered locally.

---

## Documentation impact
- Update `README.md`, `docs/architecture.md`, `docs/deployment.md`, and `docs/quickstart.md` so the
  auth, deployment, and runtime contracts describe the hardened defaults rather than permissive local behavior.
- Update runbooks and release guidance with the new required enterprise gates and acceptance evidence.
- Replace or clearly archive stale conclusions in `PRODUCT_AUDIT_REPORT.md` once the new program baseline is adopted.
- Ensure every wave updates its user-facing or operator-facing docs in the same change set as code.

---

## Architecture plan

### Audit baseline

| Dimension | Current score | Evidence | Target |
|---|---:|---|---:|
| Product capability | 84 | Broad pipeline, alerting, studio, observability, and health features exist | 95 |
| Security and access control | 42 | Anonymous control-plane fallback, disabled-by-default frontend auth, permissive role defaults | 95 |
| Backend quality and test confidence | 68 | `613` tests passed, but overall Python coverage is `64%` | 95 |
| Frontend quality and regression reliability | 61 | lint/typecheck/build/audit pass, but `7` Vitest failures remain | 95 |
| Deployment/runtime correctness | 58 | Kubernetes frontend port drift, mutable image tags, incomplete hardening alignment | 95 |
| Supply-chain and CI governance | 49 | `pip-audit` findings remain; workflows lack explicit `permissions`; mutable action tags | 95 |
| Observability and operational truth | 79 | real `/system/health`, metrics, tracing, alerting, audit routes exist | 95 |
| Docs, traceability, accessibility | 73 | strong docs footprint and semantic UI patterns, but limited automation and some drift risk | 95 |

**Weighted enterprise-readiness baseline:** `64/100`

### Verified audit signals

- Backend validation run:
  `pytest --cov=src/biomechanics_ai --cov-report=term --cov-report=xml; ruff check .; black --check .; python -m mypy; bandit -r src/ -c pyproject.toml -ll; pip-audit --skip-editable`
  produced `613 passed, 5 skipped, 2 xfailed`, overall coverage `64%`, green `ruff`, `black`, `mypy`, and no Bandit medium/high issues.
- Frontend validation run:
  `npm.cmd run lint; npm.cmd run typecheck; npm.cmd run test -- --coverage; npm.cmd run build; npm.cmd audit --audit-level=high`
  produced green lint, typecheck, build, and npm audit, but `7` failed tests in:
  `ExecutionDispatchesPanel.test.tsx`, `CreateAlertFromFailure.test.tsx`, `SettingsPage.test.tsx`, and `DocsPage.test.tsx`.
- Deployment scan found a frontend container port mismatch between the hardened nginx image and the Kubernetes manifest.
- Security scan found that enterprise-capable auth/RBAC exists in code, but default runtime posture still allows anonymous control-plane access unless operators explicitly configure auth.

### Chosen strategy

Use a four-wave brownfield hardening program rather than a single monolithic rewrite.

Preferred approach:
- Wave 1: secure the defaults and runtime contract first.
- Wave 2: restore regression trust and raise coverage on the highest-risk product paths.
- Wave 3: clean up supply-chain and CI governance debt.
- Wave 4: close enterprise evidence gaps in accessibility, runbooks, traceability, and launch readiness.

Alternative considered:
- Start with UX polish and broad coverage uplift before security and deploy hardening.

Why rejected:
- It would still leave the most severe release blockers in place.
- Enterprise trust is constrained by default access control and deployment truth before it is constrained by product polish.

### Program waves

#### Wave 1 — Default-secure platform contract
Scope:
- Remove anonymous admin-equivalent behavior from control-plane access.
- Make shared/prod auth requirements explicit in config, docs, and UI behavior.
- Align Docker, Compose, and Kubernetes runtime contracts, including the frontend port mismatch.
- Normalize enterprise-safe `.env.example` defaults and deployment guidance.

Exit criteria:
- Control-plane routes require explicit auth configuration for shared/prod use.
- Local open-access mode is deliberate, clearly documented, and non-admin by default.
- Kubernetes manifests match container runtime ports and hardening expectations.
- Auth boundary tests prove `401` / `403` behavior.

#### Wave 2 — Regression trust and coverage recovery
Scope:
- Eliminate the current frontend timeout failures.
- Raise backend coverage from `64%` toward the repo minimum, prioritizing auth, control-plane routes,
  CLI/runtime helpers, execution targets, and other low-signal modules.
- Add targeted frontend regression and Playwright coverage for currently fragile operational flows.

Exit criteria:
- Frontend Vitest suite is green.
- Backend and frontend critical-path modules meet or exceed the repo's `80%` coverage standard.
- No release-critical surfaces depend on coverage-padding tests.

#### Wave 3 — Supply-chain and CI governance hardening
Scope:
- Upgrade or constrain vulnerable Python dependencies.
- Add explicit workflow `permissions` and tighten third-party action pinning strategy.
- Reconcile CI gates with the actual release bar, including dependency, security, and docs drift policies.

Exit criteria:
- No untracked high-severity dependency findings remain.
- Workflow privileges are least-privilege and documented.
- Release gates reflect the real enterprise-readiness contract.

#### Wave 4 — Enterprise evidence and launch-readiness
Scope:
- Add automated accessibility checks for critical user-facing flows.
- Close documentation, runbook, and traceability drift.
- Audit operational evidence: health, metrics, alerting, audit exports, and release notes.
- Tighten any remaining product-trust surfaces that still overclaim maturity.

Exit criteria:
- Accessibility automation exists for critical UI flows.
- Product, deployment, and operator docs are aligned with the hardened platform.
- Enterprise launch checklist is evidence-backed rather than narrative-only.

---

## API design
This umbrella program spec does not directly introduce new endpoints.

Rules for execution:
- Any wave that changes an endpoint contract must create or refresh a wave-specific active spec before implementation.
- Security-sensitive endpoint changes must explicitly define auth requirements, request and response schemas,
  and `401` / `403` / `429` behavior.
- The existing auth, health, run, pipeline, audit, alert, and execution surfaces are part of the verification scope.

---

## Data model changes
No direct schema changes are defined by this umbrella program spec.
Wave-specific specs must declare any table or column changes before code is written.

### Migration notes
- Is this migration reversible? Yes, because this umbrella spec itself does not change the schema.
- Rollback plan: execution waves must document rollback per change set.
- Breaking change? Yes, at the program level:
  enterprise-hardening waves will tighten auth defaults, deployment assumptions, and CI expectations.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Local single-user demos still need a zero-friction path | Preserve explicit local-only mode, but make it deliberate and visibly non-enterprise |
| Existing shared deployments rely on permissive defaults | Provide migration notes before changing defaults and test both pre- and post-hardening behavior |
| Dependency upgrades cause secondary breakage | Batch by ecosystem, validate in CI, and track accepted exceptions explicitly |
| Frontend tests are timing out rather than asserting | Fix harness and component performance/root causes, not just test timeouts |
| A wave discovers new schema or API work | Split a child spec before implementation instead of smuggling scope into this umbrella plan |
| Operators use Kubernetes instead of Compose | Treat Compose and Kubernetes parity as a release gate, not an optional afterthought |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Tightening auth defaults breaks informal demo flows | Medium | High | Preserve explicit local mode, document migration, and add environment-specific tests |
| Dependency remediation causes cascading breakage | Medium | High | Upgrade in bounded batches with green CI evidence at each step |
| Coverage work becomes synthetic rather than risk-driven | Medium | Medium | Prioritize low-coverage, high-risk modules and reject assertion-light padding tests |
| Enterprise program scope balloons into an unshippable mega-change | High | High | Execute through wave-specific specs with independent gates and rollback paths |
| Documentation lags hardened behavior | Medium | High | Make docs/runbooks part of each wave's acceptance criteria |

---

## Breaking changes
Yes, at the platform contract level.

Expected coordinated changes include:
- shared or production-like deployments can no longer rely on anonymous control-plane access behaving as admin;
- deployment manifests and examples will change to reflect hardened runtime defaults;
- CI and release workflows may become stricter and fail work that currently passes.

Migration path:
- announce each wave's breaking changes in the wave spec and release notes;
- provide configuration examples for local, demo, and shared/prod modes;
- validate rollback paths for auth/deploy changes before rollout.

---

## Testing strategy
- **Unit:** auth boundary behavior, role and permission evaluation, config/default resolution, deployment helper logic,
  and low-coverage backend modules identified in the audit.
- **Integration:** protected control-plane routes, system-health truth paths, settings persistence, execution dispatch flows,
  audit export, and any deployment-sensitive API behavior.
- **E2E:** critical user journeys for login, dashboard, docs, system health, settings, alerts, runs, and pipeline operations.
- **Performance:** frontend timeout/root-cause analysis for current Vitest failures; bounded query validation on runtime-critical backend paths.
- **Security:** dependency audit, Bandit/SAST, auth negative-path tests, rate-limit verification where applicable,
  and workflow-permissions review.
- **Accessibility:** automated axe-style checks for critical pages plus manual keyboard and screen-reader spot checks.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [ ] Enterprise-readiness baseline and FAIL / WARN / PASS findings documented
- [ ] Wave 1 spec completed and default-secure platform blockers removed
- [ ] Wave 2 spec completed and regression trust restored
- [ ] Wave 3 spec completed and supply-chain / CI governance blockers removed
- [ ] Wave 4 spec completed and enterprise evidence gaps closed
- [ ] Backend and frontend CI green at the hardened release bar
- [ ] Critical-path coverage meets or exceeds the repo standard
- [ ] Documentation, deployment guides, and runbooks describe real behavior
- [ ] Residual risks are explicitly documented with owner and follow-up path
- [ ] Enterprise-readiness scorecard reaches `95/100` or higher on all tracked dimensions