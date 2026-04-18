# Feature: Practitioner Session Review and Prescription V1

**Status:** Draft
**Created:** 2026-04-14
**Author:** GitHub Copilot
**Estimate:** L
**Supersedes:** Archived studio-centered planning as the first validated practitioner workflow

---

## Problem
The repository now states the correct product direction, but it still lacks a concrete,
implementation-ready workflow that matches the baseball biomechanics use case. The inherited
planning artifacts focus on pipeline authoring and operations rather than the work a coach,

### Shared error response contract
Unless otherwise noted, error responses should use this shape:
therapist, or performance practitioner actually needs to do.

The first validated workflow should let a practitioner move from an athlete session to a
reviewed assessment, compare that session against a baseline or prior session, draft a
prescription, and generate a shareable output. Without that workflow, future runtime work will
continue to drift into generic platform behavior instead of a clear biomechanics product.

A second constraint is now verified: the current repository and its git history do not contain
`src/`, `frontend/`, `tests/`, or `deploy/` runtime trees. This spec is therefore the working
implementation target for the next restoration wave, but code execution cannot begin until those
runtime surfaces are restored from an external source.

## Success criteria
- A practitioner can create or select an athlete, register a session, review an assessment,
  compare it against a baseline session, draft a prescription, and export a report in one
  coherent workflow.
- The workflow language is specific to baseball biomechanics rather than generic pipeline
  management.
- The workflow is concrete enough to guide future backend, frontend, test, and deployment work
  once runtime trees are restored.
- The replacement planning artifacts under `specs/` and `openspec/` align to this workflow.

---

## Requirements

### Functional
- [ ] The product must support creating or selecting an athlete record before session review begins.
- [ ] The product must support registering a new biomechanics session with capture metadata,
      including session date, athlete handedness context, capture type, and one or more asset references.
- [ ] The product must support creating an assessment draft for a session and tracking its status as
      `draft`, `in_review`, or `finalized`.
- [ ] The product must support recording structured assessment findings, including finding type,
      body region or movement phase, practitioner confidence, severity, and free-text notes.
- [ ] The product must support comparing a session against at least one baseline or prior session and
      presenting meaningful deltas for practitioner review.
- [ ] The product must support drafting a prescription composed of one or more prescription items,
      each with a cue, drill or intervention, dosage guidance, goal, and follow-up recommendation.
- [ ] The product must support generating a shareable report snapshot from the reviewed assessment and
      prescription without exposing raw internal editing state.
- [ ] The product must record who created, reviewed, updated, and shared assessments and prescriptions.

### Non-functional
- [ ] Performance: assessment workspace initial load should complete within 2 seconds for an athlete
      with up to 25 prior sessions in the default view.
- [ ] Security: write operations require practitioner-authenticated access; share links must be
      time-bound and revocable.
- [ ] Accessibility: the session review, comparison, prescription, and report-share workflows must be
      keyboard accessible and meet WCAG AA expectations.
- [ ] Observability: the implementation must log create, review, finalize, and share actions with
      actor and entity IDs; metrics must exist for session creation, assessment finalization, and
      report sharing.

---

## Affected components
- `docs/product-direction.md`
- `docs/specs/active/practitioner-session-review-and-prescription-v1.md`
- `specs/005-athlete-session-domain-foundation/`
- `specs/006-practitioner-assessment-workspace/`
- `specs/007-prescription-delivery-and-followup/`
- `openspec/changes/practitioner-assessment-workflow/`
- Future restored runtime surfaces:
  - `src/biomechanics_ai/models/`
  - `src/biomechanics_ai/storage/`
  - `src/biomechanics_ai/collector/`
  - `frontend/src/pages/`
  - `frontend/src/api/`
  - `frontend/src/types/`
  - `tests/`

---

## External context
No external research materially changed this design. The governing inputs are the explicit user
request, `docs/product-direction.md`, and the verified absence of application runtime trees in the
current repository and its git history.

---

## Documentation impact
- `docs/product-direction.md` should reference this workflow as the first implementation target.
- `specs/README.md` should list the new biomechanics replacement specs as current planning inputs.
- Archived studio-era specs and OpenSpec proposals should point to these replacement artifacts.

---

## Architecture plan
This workflow is intentionally split into three future implementation surfaces:

1. Domain foundation: athlete, session, assessment, and report entities.
2. Practitioner workspace: review, comparison, and assessment editing.
3. Prescription and follow-up: intervention planning, report generation, and share workflows.

The implementation precondition is explicit: runtime trees must be restored from an external source
before backend, frontend, and test work can begin. This repository does not currently contain those
surfaces, and git history inspection on 2026-04-14 confirmed they were never committed here.

---

## API design

For future implementation, the first workflow should expose the following routes.

### Authorization model
- Practitioners can create and update athletes, sessions, assessments, and prescriptions for
  their accessible athlete records.
- Review-capable practitioners can finalize assessments and share reports.
- Administrators can revoke report shares and audit workflow activity across practitioners.

### Shared error response contract
Unless otherwise noted, error responses should use this shape:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": []
  }
}
```

### `POST /athletes`
- **Auth required:** yes
- **Required scope:** `athlete:write`
  - `400` - `{ "error": { "code": "invalid_athlete", "message": "Invalid or missing athlete field.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot create athletes for this scope.", "details": [] } }`
- **Request body:**
```json
{
  "display_name": "string - practitioner-visible athlete label",
  "handedness": "right|left|switch",
  "primary_position": "string",
  - `400` - `{ "error": { "code": "invalid_session", "message": "Session payload is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot register sessions for this athlete.", "details": [] } }`
  - `404` - `{ "error": { "code": "athlete_not_found", "message": "Athlete was not found.", "details": [] } }`
  "competition_level": "string",
  "notes": "string, optional"
}
```
- **Success response (201):**
```json
  - `400` - `{ "error": { "code": "invalid_assessment", "message": "Assessment payload is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot create assessments for this session.", "details": [] } }`
  - `404` - `{ "error": { "code": "session_not_found", "message": "Session was not found.", "details": [] } }`
{
  "athlete_id": "uuid",
  "display_name": "string",
  "handedness": "right",
  "primary_position": "pitcher",
  "competition_level": "college"
}
```
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_athlete", "message": "Invalid or missing athlete field.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot create athletes for this scope.", "details": [] } }`

### `POST /athletes/{athlete_id}/sessions`
- **Auth required:** yes
- **Required scope:** `session:write`
- **Request body:**
```json
{
  "session_date": "YYYY-MM-DD",
  "capture_type": "video|motion_capture|manual_review",
  "session_label": "string",
  "asset_refs": [
    {
  - `400` - `{ "error": { "code": "invalid_finalize_request", "message": "Assessment cannot be finalized in its current state.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot finalize this assessment.", "details": [] } }`
  - `404` - `{ "error": { "code": "assessment_not_found", "message": "Assessment was not found.", "details": [] } }`
      "asset_type": "video",
      "uri": "string",
      "camera_view": "open_side"
    }
  ],
  "notes": "string, optional"
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot view this comparison.", "details": [] } }`
  - `404` - `{ "error": { "code": "comparison_session_not_found", "message": "Session or baseline session was not found.", "details": [] } }`
  - `409` - `{ "error": { "code": "comparison_unavailable", "message": "Comparison data is not available yet.", "details": [] } }`
}
```
- **Success response (201):**
```json
{
  "session_id": "uuid",
  - `400` - `{ "error": { "code": "invalid_prescription", "message": "Prescription payload is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot create a prescription for this assessment.", "details": [] } }`
  - `404` - `{ "error": { "code": "assessment_not_found", "message": "Assessment was not found.", "details": [] } }`
  "athlete_id": "uuid",
  "status": "registered"
}
```
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_session", "message": "Session payload is invalid.", "details": [] } }`
  - `400` - `{ "error": { "code": "invalid_share_request", "message": "Share request is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot share this prescription.", "details": [] } }`
  - `404` - `{ "error": { "code": "prescription_not_found", "message": "Prescription was not found.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot register sessions for this athlete.", "details": [] } }`
  - `404` - `{ "error": { "code": "athlete_not_found", "message": "Athlete was not found.", "details": [] } }`

### `POST /sessions/{session_id}/assessments`
- **Auth required:** yes
- **Required scope:** `assessment:write`
- **Request body:**
```json

### New table: `workflow_audit_log`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| audit_id | uuid | no | generated | Primary key |
| actor_id | uuid | no | none | Practitioner or admin actor |
| entity_type | text | no | none | athlete, session, assessment, prescription, report_share |
| entity_id | uuid | no | none | Target entity |
| action | text | no | none | create, update, finalize, share, revoke |
| created_at | timestamptz | no | now() | Event time |
| metadata | jsonb | yes | null | Safe structured metadata |
{
  "source": "manual|assisted",
  "summary": "string, optional",
  "findings": [
    {
      "finding_type": "string",
      "movement_phase": "string",
      "severity": "low|medium|high",
      "confidence": 0.85,
      "notes": "string"
    }
  ]
}
```
- **Success response (201):**
```json
{
  "assessment_id": "uuid",
  "session_id": "uuid",
  "status": "draft"
}
```
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_assessment", "message": "Assessment payload is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot create assessments for this session.", "details": [] } }`
  - `404` - `{ "error": { "code": "session_not_found", "message": "Session was not found.", "details": [] } }`

### `POST /assessments/{assessment_id}/finalize`
- **Auth required:** yes
- **Required scope:** `assessment:finalize`
- **Request body:**
```json
{
  "review_summary": "string",
  "lock_findings": true
}
```
- **Success response (200):**
```json
{
  "assessment_id": "uuid",
  "status": "finalized",
  "finalized_at": "2026-04-14T18:00:00Z"
}
```
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_finalize_request", "message": "Assessment cannot be finalized in its current state.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot finalize this assessment.", "details": [] } }`
  - `404` - `{ "error": { "code": "assessment_not_found", "message": "Assessment was not found.", "details": [] } }`

### `GET /sessions/{session_id}/comparison?baseline_session_id={baseline_session_id}`
- **Auth required:** yes
- **Required scope:** `assessment:read`
- **Success response (200):**
```json
{
  "session_id": "uuid",
  "baseline_session_id": "uuid",
  "deltas": [
    {
      "metric_key": "lead_leg_block",
      "current_value": "string",
      "baseline_value": "string",
      "direction": "improved|regressed|unchanged",
      "notes": "string"
    }
  ]
}
```
- **Error responses:**
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot view this comparison.", "details": [] } }`
  - `404` - `{ "error": { "code": "comparison_session_not_found", "message": "Session or baseline session was not found.", "details": [] } }`
  - `409` - `{ "error": { "code": "comparison_unavailable", "message": "Comparison data is not available yet.", "details": [] } }`

### `POST /assessments/{assessment_id}/prescriptions`
- **Auth required:** yes
- **Required scope:** `prescription:write`
- **Request body:**
```json
{
  "summary": "string",
  "items": [
    {
      "cue": "string",
      "drill": "string",
      "dosage": "string",
      "goal": "string",
      "follow_up_days": 14
    }
  ]
}
```
- **Success response (201):**
```json
{
  "prescription_id": "uuid",
  "assessment_id": "uuid",
  "status": "draft"
}
```
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_prescription", "message": "Prescription payload is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot create a prescription for this assessment.", "details": [] } }`
  - `404` - `{ "error": { "code": "assessment_not_found", "message": "Assessment was not found.", "details": [] } }`

### `POST /prescriptions/{prescription_id}/share`
- **Auth required:** yes
- **Required scope:** `report:share`
- **Request body:**
```json
{
  "delivery_mode": "link|pdf",
  "expires_in_hours": 72,
  "include_comparison": true
}
```
- **Success response (201):**
```json
{
  "share_id": "uuid",
  "prescription_id": "uuid",
  "delivery_mode": "link",
  "expires_at": "2026-04-17T12:00:00Z"
}
```
- **Error responses:**
  - `400` - `{ "error": { "code": "invalid_share_request", "message": "Share request is invalid.", "details": [] } }`
  - `401` - `{ "error": { "code": "not_authenticated", "message": "Authentication is required.", "details": [] } }`
  - `403` - `{ "error": { "code": "forbidden", "message": "You cannot share this prescription.", "details": [] } }`
  - `404` - `{ "error": { "code": "prescription_not_found", "message": "Prescription was not found.", "details": [] } }`

---

## Data model changes

### New table: `athletes`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| athlete_id | uuid | no | generated | Primary key |
| display_name | text | no | none | Practitioner-visible label |
| handedness | text | no | none | right, left, or switch |
| primary_position | text | yes | null | Baseball role |
| competition_level | text | yes | null | Youth, high school, college, pro, other |
| created_at | timestamptz | no | now() | Audit field |
| created_by | uuid | no | none | Actor reference |

### New table: `sessions`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| session_id | uuid | no | generated | Primary key |
| athlete_id | uuid | no | none | Foreign key to athletes |
| session_date | date | no | none | Capture date |
| capture_type | text | no | none | video, motion_capture, manual_review |
| session_label | text | yes | null | Friendly label |
| status | text | no | registered | registered, assessed, archived |
| created_at | timestamptz | no | now() | Audit field |

### New table: `session_assets`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| asset_id | uuid | no | generated | Primary key |
| session_id | uuid | no | none | Foreign key to sessions |
| asset_type | text | no | none | video, image, document |
| uri | text | no | none | Storage reference |
| camera_view | text | yes | null | open_side, closed_side, rear, front |

### New table: `assessments`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| assessment_id | uuid | no | generated | Primary key |
| session_id | uuid | no | none | Foreign key to sessions |
| status | text | no | draft | draft, in_review, finalized |
| summary | text | yes | null | Practitioner summary |
| source | text | no | manual | manual or assisted |
| finalized_at | timestamptz | yes | null | Finalization timestamp |

### New table: `assessment_findings`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| finding_id | uuid | no | generated | Primary key |
| assessment_id | uuid | no | none | Foreign key to assessments |
| finding_type | text | no | none | Domain-specific finding key |
| movement_phase | text | yes | null | Delivery phase |
| severity | text | no | none | low, medium, high |
| confidence | numeric | yes | null | 0.0-1.0 |
| notes | text | yes | null | Practitioner note |

### New table: `prescriptions`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| prescription_id | uuid | no | generated | Primary key |
| assessment_id | uuid | no | none | Foreign key to assessments |
| status | text | no | draft | draft, shared, archived |
| summary | text | yes | null | High-level plan |
| created_at | timestamptz | no | now() | Audit field |

### New table: `prescription_items`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| item_id | uuid | no | generated | Primary key |
| prescription_id | uuid | no | none | Foreign key to prescriptions |
| cue | text | no | none | Coaching cue |
| drill | text | no | none | Drill or intervention |
| dosage | text | no | none | Reps, sets, or weekly plan |
| goal | text | no | none | Intended outcome |
| follow_up_days | integer | yes | null | Recommended follow-up window |

### New table: `report_shares`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| share_id | uuid | no | generated | Primary key |
| prescription_id | uuid | no | none | Foreign key to prescriptions |
| delivery_mode | text | no | none | link or pdf |
| expires_at | timestamptz | yes | null | Link expiration |
| created_by | uuid | no | none | Actor reference |

### New table: `workflow_audit_log`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| audit_id | uuid | no | generated | Primary key |
| actor_id | uuid | no | none | Practitioner or admin actor |
| entity_type | text | no | none | athlete, session, assessment, prescription, report_share |
| entity_id | uuid | no | none | Target entity |
| action | text | no | none | create, update, finalize, share, revoke |
| created_at | timestamptz | no | now() | Event time |
| metadata | jsonb | yes | null | Safe structured metadata |

### Migration notes
- Is this migration reversible? Yes, as a schema-only change in the first rollout wave.
- Rollback plan: disable the workflow flag, preserve exported reports, and roll back the new tables if no
  production data migration has begun; otherwise leave tables in place and disable writes.
- Breaking change? No for the current repository state. Future runtime implementation adds new domain tables
  and endpoints but does not replace a validated existing contract.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Two athletes share the same display name | Use distinct IDs; UI disambiguates with level and position metadata |
| A session has no baseline comparison available | Comparison panel shows empty-state guidance instead of blocking assessment review |
| Asset upload or registration partially fails | Session remains registered with asset-level error state and retry guidance |
| Concurrent edits occur on the same assessment | Use optimistic version checking and return `409` on stale save |
| A practitioner tries to share an unfinalized assessment | Return `409` and require assessment finalization first |
| Share link expires before recipient opens it | Return a user-safe expired-link state and require practitioner to issue a new share |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Domain terms drift before runtime work starts | Medium | High | Keep this active spec and replacement specs as the only current planning anchors |
| The first workflow is too broad for the first restoration wave | Medium | Medium | Implement in three vertical slices: domain foundation, review workspace, prescription delivery |
| Missing runtime trees delay execution indefinitely | High | High | Keep restoration precondition explicit and do not pretend code work has started |
| Report sharing leaks more data than intended | Medium | High | Use time-bound reports built from explicit snapshot payloads rather than live editable records |

---

## Breaking changes
This is a future implementation spec. It does not break the current repository because the runtime implementation
is not present. The eventual code change introduces new entities and endpoints but does not replace a currently
validated biomechanics API.

---

## Testing strategy
- **Unit:** athlete/session validation, comparison delta derivation, prescription item validation, report snapshot generation.
- **Integration:** create athlete, register session, create assessment, compare sessions, save prescription, share report.
- **E2E:** practitioner selects athlete, registers session, reviews findings, compares against baseline, drafts prescription, exports shareable output.
- **Performance:** load athlete with 25 prior sessions and verify workspace load and comparison response thresholds.
- **Security:** role enforcement for write and share actions; expired-share handling; report redaction checks.

---

## Acceptance criteria
- [ ] Athlete, session, assessment, comparison, prescription, and report-share requirements are implemented.
- [ ] Replacement planning artifacts under `specs/` and `openspec/` align to this workflow.
- [ ] Runtime restoration precondition is documented explicitly in contributor-facing docs.
- [ ] Unit tests cover validation, comparison, and prescription edge cases at 80%+ coverage for new code.
- [ ] Integration tests cover the full practitioner happy path and major failure cases.
- [ ] E2E happy path covers session registration through report share.
- [ ] Accessibility requirements are met for review and prescription workflows.
- [ ] Observability is added for create, finalize, compare, and share actions.
