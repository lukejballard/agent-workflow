# Feature: <Name>

**Status:** Draft | In Review | Approved | In Progress | Done
**Created:** YYYY-MM-DD
**Author:** @github-handle
**Estimate:** S / M / L / XL
**Supersedes:** (ADR or spec, if applicable)

---

## Problem
What specific problem does this solve?
Who experiences it and how frequently?
What is the impact of not solving it?

## Success criteria
How will we know this is done and working in production?
What metrics will change?

---

## Requirements

### Functional
- [ ] Functional requirement 1 (concrete behaviour, not vague goal)
- [ ] Functional requirement 2

### Non-functional
- [ ] Performance: (e.g. "p95 response time < 200ms")
- [ ] Security: (e.g. "all endpoints require Bearer token")
- [ ] Accessibility: (e.g. "WCAG AA compliance for all new UI")
- [ ] Observability: (e.g. "all new endpoints have request count and latency metrics")

---

## Affected components
List every file, service, package, and database table that will be touched.

---

## External context
- Does this work require external docs, standards, ecosystem research, or competitor references?
- If yes, link the brief under `docs/specs/research/<slug>-research.md` and summarize the constraints or decisions it adds.
- If no, state that no external context materially changed the design.

---

## Documentation impact
- Which contributor, workflow, architecture, or user-facing docs must change with this work?
- If no docs change is needed, explain why the existing docs remain accurate.

---

## Architecture plan
Describe the approach in prose. Include a sequence diagram or component diagram
if the interaction is non-obvious.

---

## API design

For each new or modified endpoint:

### `POST /v1/example`
- **Auth required:** yes / no
- **Required scope:** `scope:name`
- **Request body:**
```json
{
  "field_name": "string — description and constraints"
}
```
- **Success response (201):**
```json
{
  "id": "uuid",
  "field_name": "string"
}
```
- **Error responses:**
  - `400` — validation error (field missing or invalid)
  - `401` — not authenticated
  - `403` — not authorised
  - `409` — conflict (e.g. duplicate)

---

## Data model changes

### New table: `example_table`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| id | uuid | no | gen_random_uuid() | Primary key |
| created_at | timestamptz | no | now() | |

### Migration notes
- Is this migration reversible? Yes / No
- Rollback plan: (describe how to roll back if deployment fails)
- Breaking change? Yes / No

---

## Edge cases
Enumerate every edge case and how it is handled.
If an edge case is out of scope, say so explicitly.

| Edge case | Handling |
|---|---|
| User submits empty input | Return 400 with field-level error |
| Concurrent duplicate submission | Return 409 via DB unique constraint |

---

## Risks
What could go wrong? What has the highest implementation uncertainty?

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| | | | |

---

## Breaking changes
Does this change break existing API consumers, DB schemas, or client code?
If yes: describe the migration path and any required coordination.

---

## Testing strategy
- **Unit:** what will be unit tested?
- **Integration:** which API endpoints and service interactions?
- **E2E:** which Playwright user flows?
- **Performance:** any load or latency tests needed?
- **Security:** any penetration or fuzzing needed?

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
