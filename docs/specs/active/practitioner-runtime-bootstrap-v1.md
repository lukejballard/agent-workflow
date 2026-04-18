# Feature: Practitioner Runtime Bootstrap V1

**Status:** In Progress
**Created:** 2026-04-14
**Author:** GitHub Copilot
**Estimate:** L
**Supersedes:** None

---

## Problem
The repository now has a validated practitioner workflow spec, but it still has no runtime code
to execute that workflow. The backend, frontend, and tests were absent from the workspace, so the
product could be described but not exercised.

Waiting for an external code restore is no longer the only viable path. The repository can also be
restored by bootstrapping a fresh runtime that implements the first practitioner workflow directly
from the active specs.

This phase creates the smallest viable application slice:
- a FastAPI backend under `src/biomechanics_ai/`
- a React + TypeScript frontend under `frontend/`
- tests under `tests/` and `frontend/src/__tests__/`

The slice is intentionally narrow. It proves athlete creation, session registration, assessment
review, comparison, prescription drafting, report sharing, and share revocation without trying to
rebuild the inherited pipeline-era platform.

## Success criteria
- The repository contains a runnable backend and frontend aligned to the practitioner workflow.
- The backend exposes authenticated workflow endpoints plus `/health` and `/metrics`.
- The frontend can drive the workflow with explicit loading, empty, success, and error states.
- Backend tests cover happy path, auth boundary, edge cases, and comparison/share behaviors.
- Frontend tests cover at least the primary empty-state and interaction shell.

---

## Requirements

### Functional
- [ ] Create the Python package and FastAPI app under `src/biomechanics_ai/`.
- [ ] Implement authenticated endpoints for athlete creation and listing.
- [ ] Implement authenticated endpoints for session creation and listing per athlete.
- [ ] Implement authenticated endpoints for assessment creation, retrieval, update, and finalization.
- [ ] Implement authenticated comparison for a session against a baseline session.
- [ ] Implement authenticated prescription creation and report sharing.
- [ ] Implement authenticated share revocation.
- [ ] Create a frontend route that lets a practitioner work through the entire flow in one page.

### Non-functional
- [ ] Performance: default workflow read endpoints remain under 200 ms p95 for small local datasets.
- [ ] Security: all write endpoints require Bearer auth and explicit role checks; no secrets or PII are logged.
- [ ] Accessibility: the new page is keyboard navigable, labelled, and WCAG AA-oriented.
- [ ] Observability: request count and latency metrics exist; backend logs include actor and entity IDs; `/health` exists.

---

## Affected components
- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `src/biomechanics_ai/`
- `frontend/`
- `tests/`
- `docs/architecture.md`
- `README.md`
- `docs/product-direction.md`

---

## External context
No external research materially changed this design. The governing inputs are:
- the explicit user request to continue with a fresh scaffold
- `docs/specs/active/practitioner-session-review-and-prescription-v1.md`
- `specs/005-athlete-session-domain-foundation/`
- `specs/006-practitioner-assessment-workspace/`
- `specs/007-prescription-delivery-and-followup/`

---

## Documentation impact
- `README.md` must gain a runnable bootstrap path.
- `docs/architecture.md` must describe the new backend, frontend, and local persistence model.
- `docs/product-direction.md` must reference this bootstrap spec as the active runtime restoration path.

---

## Architecture plan
Use a thin-route backend plus service and storage layers:

1. `collector/` owns request parsing, auth checks, response shaping, and orchestration.
2. `services/` owns workflow rules such as comparison derivation, assessment finalization, and share revocation.
3. `storage/` owns local persistence for bootstrap recovery.
4. `models/` owns Pydantic request and response schemas.
5. `observability/` owns metrics setup and middleware helpers.

The bootstrap storage model is local file-backed persistence aligned to the future practitioner
entities. This keeps the first runtime slice small and testable while preserving the domain model
needed for a later relational migration.

The frontend uses React Router with one primary practitioner workspace page. Components stay thin.
API calls live in `frontend/src/api/`, shared shapes live in `frontend/src/types/`, and page-level
orchestration lives in a custom hook.

---

## API design

### `GET /health`
- **Auth required:** no
- **Required scope:** none
- **Success response (200):**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_seconds": 12
}
```
- **Error responses:** none

### `GET /metrics`
- **Auth required:** no
- **Required scope:** none
- **Success response (200):** Prometheus text response
- **Error responses:** none

### `GET /athletes`
- **Auth required:** yes
- **Required scope:** `athlete:read`
- **Success response (200):**
```json
{
  "items": [
    {
      "athlete_id": "uuid",
      "display_name": "string",
      "handedness": "right",
      "primary_position": "pitcher",
      "competition_level": "college"
    }
  ]
}
```
- **Error responses:**
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot view athletes in this scope.", "details": [] } }`

### `POST /athletes`
- **Auth required:** yes
- **Required scope:** `athlete:write`
- **Request body:** same as the broader practitioner workflow spec
- **Success response (201):** same as the broader practitioner workflow spec
- **Error responses:** same as the broader practitioner workflow spec

### `GET /athletes/{athlete_id}/sessions`
- **Auth required:** yes
- **Required scope:** `session:read`
- **Success response (200):**
```json
{
  "items": [
    {
      "session_id": "uuid",
      "athlete_id": "uuid",
      "session_date": "2026-04-14",
      "capture_type": "video",
      "session_label": "Bullpen check-in",
      "status": "registered"
    }
  ]
}
```
- **Error responses:**
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot view sessions for this athlete.", "details": [] } }`
  - `404` - `{ "error": { "code": "athlete_not_found", "message": "Athlete was not found.", "details": [] } }`

### `POST /athletes/{athlete_id}/sessions`
- **Auth required:** yes
- **Required scope:** `session:write`
- **Request body:** same as the broader practitioner workflow spec
- **Success response (201):** same as the broader practitioner workflow spec
- **Error responses:** same as the broader practitioner workflow spec

### `GET /assessments/{assessment_id}`
- **Auth required:** yes
- **Required scope:** `assessment:read`
- **Success response (200):**
```json
{
  "assessment_id": "uuid",
  "session_id": "uuid",
  "status": "draft",
  "summary": "string",
  "source": "manual",
  "findings": [
    {
      "finding_id": "uuid",
      "finding_type": "lead_leg_block",
      "movement_phase": "foot_strike",
      "severity": "medium",
      "confidence": 0.8,
      "notes": "string"
    }
  ]
}
```
- **Error responses:**
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot view this assessment.", "details": [] } }`
  - `404` - `{ "error": { "code": "assessment_not_found", "message": "Assessment was not found.", "details": [] } }`

### `POST /sessions/{session_id}/assessments`
- **Auth required:** yes
- **Required scope:** `assessment:write`
- **Request body:** same as the broader practitioner workflow spec
- **Success response (201):** same as the broader practitioner workflow spec
- **Error responses:** same as the broader practitioner workflow spec

### `PUT /assessments/{assessment_id}`
- **Auth required:** yes
- **Required scope:** `assessment:write`
- **Request body:** same shape as `GET /assessments/{assessment_id}` without IDs
- **Success response (200):** same shape as `GET /assessments/{assessment_id}`
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_assessment", "message": "Assessment payload is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot update this assessment.", "details": [] } }`
  - `404` - `{ "error": { "code": "assessment_not_found", "message": "Assessment was not found.", "details": [] } }`
  - `409` - `{ "error": { "code": "stale_assessment", "message": "Assessment has changed and must be reloaded.", "details": [] } }`

### `POST /assessments/{assessment_id}/finalize`
- **Auth required:** yes
- **Required scope:** `assessment:finalize`
- **Request body:** same as the broader practitioner workflow spec
- **Success response (200):** same as the broader practitioner workflow spec
- **Error responses:** same as the broader practitioner workflow spec

### `GET /sessions/{session_id}/comparison`
- **Auth required:** yes
- **Required scope:** `assessment:read`
- **Request query:** `baseline_session_id=<uuid>`
- **Success response (200):** same as the broader practitioner workflow spec
- **Error responses:** same as the broader practitioner workflow spec

### `POST /assessments/{assessment_id}/prescriptions`
- **Auth required:** yes
- **Required scope:** `prescription:write`
- **Request body:** same as the broader practitioner workflow spec
- **Success response (201):** same as the broader practitioner workflow spec
- **Error responses:** same as the broader practitioner workflow spec

### `POST /prescriptions/{prescription_id}/share`
- **Auth required:** yes
- **Required scope:** `report:share`
- **Request body:** same as the broader practitioner workflow spec
- **Success response (201):**
```json
{
  "share_id": "uuid",
  "prescription_id": "uuid",
  "delivery_mode": "link",
  "expires_at": "2026-04-17T12:00:00Z",
  "share_url": "http://localhost:8000/report-shares/public-token"
}
```
- **Error responses:** same as the broader practitioner workflow spec

### `POST /report-shares/{share_id}/revoke`
- **Auth required:** yes
- **Required scope:** `report:revoke`
- **Success response (200):**
```json
{
  "share_id": "uuid",
  "status": "revoked"
}
```
- **Error responses:**
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot revoke this share.", "details": [] } }`
  - `404` - `{ "error": { "code": "share_not_found", "message": "Share was not found.", "details": [] } }`

### `GET /report-shares/{share_token}`
- **Auth required:** no
- **Required scope:** none
- **Success response (200):**
```json
{
  "athlete_display_name": "string",
  "session_label": "string",
  "assessment_summary": "string",
  "comparison": [],
  "prescription_items": []
}
```
- **Error responses:**
  - `404` - `{ "error": { "code": "share_not_found", "message": "Share was not found.", "details": [] } }`
  - `410` - `{ "error": { "code": "share_expired", "message": "Share link has expired or was revoked.", "details": [] } }`

---

## Data model changes

The bootstrap implementation stores domain entities in local file-backed persistence with shapes aligned to:
- athlete
- session
- session_asset
- assessment
- assessment_finding
- prescription
- prescription_item
- report_share
- workflow_audit_event

### Migration notes
- Is this migration reversible? Yes. The bootstrap uses local file-backed persistence and can be removed by deleting the generated data file.
- Rollback plan: revert the runtime scaffold and remove the bootstrap data file.
- Breaking change? No. These are new runtime surfaces.

---

## Edge cases

| Edge case | Handling |
|---|---|
| No athletes exist yet | Frontend shows an explicit empty state and starts with athlete creation |
| First session has no baseline | Comparison panel returns a non-blocking empty state |
| Assessment update uses stale version | Backend returns `409` and the frontend prompts a reload |
| Share link is expired or revoked | Public route returns `410` with a safe message |
| Invalid token or missing token | Backend returns `401` and does not expose data |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bootstrap storage outgrows its local file model | Medium | Medium | Keep storage access isolated behind `storage/` and map entities directly to the future domain model |
| UI overreaches into future workflow scope | Medium | Medium | Keep the page limited to one practitioner flow and avoid scheduling or roster features |
| Auth setup frustrates local first-run | Medium | Low | Provide `.env.example`, clear startup docs, and a UI setup panel for base URL and token |

---

## Breaking changes
None. This work introduces new runtime code where none currently exists.

---

## Testing strategy
- **Unit:** backend auth checks, comparison derivation, share expiry, and service state transitions.
- **Integration:** full API happy path from athlete creation through share creation and revocation.
- **E2E:** deferred for a later slice; this bootstrap phase focuses on unit and integration plus frontend component tests.
- **Performance:** spot-check local workflow reads and writes against the bootstrap targets.
- **Security:** verify unauthenticated `401`, unauthorized `403`, and safe share expiry behavior.

---

## Acceptance criteria
- [ ] Backend package and app exist under `src/biomechanics_ai/`.
- [ ] Frontend package and practitioner workspace exist under `frontend/`.
- [ ] Authenticated workflow endpoints are implemented.
- [ ] `/health` and `/metrics` are implemented.
- [ ] Backend tests pass for happy path and key failure cases.
- [ ] Frontend component tests pass for the page shell and empty states.
- [ ] README and architecture docs are updated to describe the bootstrap runtime.
- [ ] Observability is added without logging secrets or PII.