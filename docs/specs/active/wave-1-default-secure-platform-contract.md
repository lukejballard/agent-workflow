# Feature: Wave 1 Default-Secure Platform Contract

> Note: This spec documents inherited platform-security work and should be treated as
> archival context rather than current biomechanics product scope.

**Status:** In Progress
**Created:** 2026-04-14
**Author:** GitHub Copilot
**Estimate:** M
**Supersedes:** (previous repo-specific spec removed — see docs/specs/README.md for policy on repo-specific specs)

---

## Problem
The control plane currently falls back to anonymous access when API-key auth is not configured,
and that fallback can resolve to an effective admin role. That makes shared deployments unsafe by
default, while the frontend still presents an admin mock user when auth is disabled and the shipped
Kubernetes frontend manifest no longer matches the hardened runtime image.

If this is not corrected, operators can deploy a misleadingly hardened platform that still exposes
control-plane data and mutation surfaces without explicit authentication and can fail at runtime in
Kubernetes because the frontend service targets the wrong container port.

## Success criteria
- Non-local control-plane requests return `401` unless explicit auth is configured.
- Local anonymous control-plane mode remains available for development, but resolves to `viewer`
  unless an operator explicitly elevates it.
- Frontend unauthenticated fallback behavior matches the backend's non-admin local-open posture.
- Shipped `.env.example` and Kubernetes manifests accurately describe and enforce the new runtime
  contract.

---

## Requirements

### Functional
- [x] Control-plane auth must reject anonymous requests for non-local hosts when no API key or role
      map is configured.
- [x] Local anonymous control-plane access must stay available for `localhost`, `127.0.0.1`, and
      test-only hosts, with a default fallback role of `viewer`.
- [x] Operators must be able to explicitly elevate local anonymous access through existing config,
      rather than by relying on an implicit admin default.
- [x] Frontend auth-disabled mode must no longer impersonate an admin user.
- [x] The Kubernetes frontend deployment and probes must target the actual unprivileged container
      port exposed by the frontend image.
- [x] Documentation and env examples must explain the local-open mode and the shared/prod auth
      requirement.

### Non-functional
- [x] Performance: auth checks must remain request-local string parsing with no additional I/O.
- [x] Security: anonymous admin-equivalent control-plane access must be removed.
- [ ] Accessibility: no UI accessibility regressions from frontend auth-disabled fallback changes.
- [x] Observability: existing auth and audit logging behavior must remain intact; no secrets logged.

---

## Affected components
- `src/biomechanics_ai/config/settings.py`
- `src/biomechanics_ai/collector/auth.py`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/__tests__/AuthContext.test.tsx`
- `.env.example`
- `deploy/kubernetes/frontend.yaml`
- `tests/unit/test_control_plane_auth.py`
- `tests/unit/test_alert_routes.py`
- `tests/unit/test_approval.py`
- `tests/unit/test_pipeline_definition_routes.py`
- Additional focused backend unit tests that rely on anonymous control-plane mutations
- Deployment and auth documentation that describes local-open mode and frontend runtime port

---

## External context
No external docs materially changed the design. This wave is driven by the active enterprise
readiness program spec and the verified local repo implementation.

---

## Documentation impact
- Update deployment and configuration docs that currently imply control-plane access stays open by
  default or do not explain the local-only anonymous mode.
- Update env comments so shared/prod auth requirements are explicit.

---

## Architecture plan
Tighten `require_control_plane_access()` so the auth decision is based on both configuration and
request locality:

1. When a role map or control-plane API key is configured, preserve the existing authenticated
   behavior and role enforcement.
2. When auth is not configured, allow anonymous control-plane access only for local/test hosts.
3. Change the fallback role default from `admin` to `viewer` so local-open mode is read-mostly by
   default.
4. Keep explicit elevation available through `BIOMECHANICS_AI_CONTROL_PLANE_DEFAULT_ROLE`, but
   document that it is only appropriate for deliberate local development.
5. Align frontend mock auth state and shipped deployment/config assets with that contract.

---

## API design

### Modified control-plane endpoints protected by `require_control_plane_access`
- **Auth required:** yes for non-local requests unless explicit API-key auth is configured
- **Local development exception:** anonymous local requests are allowed and resolve to the fallback
  control-plane role
- **Error responses:**
  - `401` — non-local anonymous request with no configured auth, or invalid/missing configured key
  - `403` — authenticated or anonymous principal lacks required role / permission

---

## Data model changes
No schema changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: restore the previous auth fallback behavior and Kubernetes frontend port mapping.
- Breaking change? Yes. Shared or production-like deployments without auth configuration will no
  longer receive anonymous control-plane access.

---

## Edge cases

| Edge case | Handling |
|---|---|
| TestClient requests with host `testserver` | Treat as local-open and preserve testability |
| Local browser request on `localhost:3000` proxied to backend | Treat as local-open |
| Remote/shared request with no auth configured | Return `401` and require explicit auth |
| Invalid fallback role env value | Normalize to `viewer` |
| Auth-disabled frontend mode | Expose a viewer mock user, not admin |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Existing tests depend on anonymous admin behavior | High | Medium | Add focused regression updates and explicit local test env setup only where needed |
| Operators relied on open shared deployments | Medium | High | Document the breaking change in env and deployment docs |
| Frontend behavior still assumes admin in auth-disabled mode | Medium | Medium | Add a focused frontend regression test or targeted verification |

---

## Breaking changes
Yes. Anonymous control-plane access is now local-only and read-only by default. Shared and
production-like deployments must configure control-plane auth explicitly.

---

## Testing strategy
- **Unit:** auth locality checks, fallback role normalization, local-open vs non-local `401`, and
  frontend mock auth role behavior.
- **Integration:** selected control-plane route assertions for `401` and `403` behavior.
- **E2E:** none in this slice.
- **Performance:** none required; logic is constant-time header and host inspection.
- **Security:** verify anonymous non-local access is blocked and local anonymous mutations do not
  inherit admin unless explicitly configured.

---

## Acceptance criteria
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