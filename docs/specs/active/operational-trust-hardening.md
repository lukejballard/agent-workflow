# Feature: Operational Trust Hardening

> Note: This spec describes inherited platform-trust work. Treat it as archival
> context until equivalent biomechanics runtime surfaces exist.

**Status:** In Progress
**Created:** 2026-04-13
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** None

---

## Problem
Two trust-critical product surfaces are misaligned with the real implementation.

First, the dashboard's System Health experience is backed by placeholder frontend data because no real backend endpoint exists. That leaves operators, support staff, and evaluators looking at a polished but non-truthful health surface.

Second, the repository's deployment contract consistently advertises `DATABASE_URL` for Docker Compose, Kubernetes, Helm, and `.env.example`, but the storage layer currently resolves only a SQLite path helper. If left unresolved, production-like deployments can believe they are targeting PostgreSQL while the application still defaults to SQLite behavior or invalid engine options.

These gaps directly reduce operator confidence, supportability, and production-readiness.

## Success criteria
The repository should expose a truthful backend-backed system health snapshot for the frontend health and settings pages, and runtime database configuration should honor the same environment contract documented across deploy assets.

An operator should be able to determine the real backend version, storage engine, ingestion freshness, alerting posture, and recent operational issues from the UI without placeholder data, and a deployment using `DATABASE_URL` should connect through the intended SQLAlchemy engine path.

---

## Requirements

### Functional
- [ ] Storage configuration resolves `DATABASE_URL` first, falls back to `BIOMECHANICS_AI_DB_PATH` only for local SQLite defaults, and creates engines with driver-appropriate connection arguments.
- [ ] The backend exposes `GET /system/health` that returns a bounded, backend-generated operational snapshot instead of placeholder data.
- [ ] The health payload includes real ingestion, connector, alerting, and storage subsystem sections plus recent issues derived from stored events and alert history.
- [ ] The health payload includes truthful service metadata needed by the settings surface, including backend service version and generation timestamp.
- [ ] Connector subsystem reporting uses only evidence available in the current codebase and explicitly surfaces warnings when runtime connectivity telemetry is not available.
- [ ] Frontend health data fetching stops falling back to synthetic placeholder payloads and instead consumes the real backend response or surfaces an actionable error state.
- [ ] The settings System Information panel stops hardcoding the software version and instead renders backend-derived version and storage details.

### Non-functional
- [ ] Performance: `GET /system/health` uses bounded look-back windows and a fixed small number of queries with no unbounded per-row loops across the full event history.
- [ ] Security: the health response exposes no secrets, raw connector credentials, or plaintext config; endpoint access follows the existing control-plane viewer access model.
- [ ] Accessibility: existing health-page and settings-page controls retain accessible names, retry/refresh affordances, and keyboard-usable behavior.
- [ ] Observability: new service and endpoint code log failure context without PII and integrate with the existing collector exception handling path.

---

## Affected components
- `docs/specs/active/operational-trust-hardening.md`
- `src/biomechanics_ai/storage/metadata.py`
- `src/biomechanics_ai/config/settings.py` (if shared storage helpers are added here)
- `src/biomechanics_ai/collector/server.py`
- `src/biomechanics_ai/collector/` (new service helper for system health aggregation if needed)
- `src/biomechanics_ai/models/` (response schema for system health if modeled centrally)
- `frontend/src/api/health.ts`
- `frontend/src/hooks/useHealthData.ts` (only if real-response handling changes)
- `frontend/src/types/health.ts`
- `frontend/src/components/settings/SystemInfo.tsx`
- `frontend/src/__tests__/HealthPage.test.tsx`
- `frontend/src/__tests__/` (new or updated tests for SystemInfo and health client as needed)
- `tests/integration/test_api_health.py`
- `tests/unit/` (new targeted storage/config and system-health service tests)
- `docs/architecture.md`
- `docs/deployment.md`

---

## External context
No external research materially changes this design.
The work is driven by repository evidence: current frontend placeholder health behavior, deployment/docs references to `DATABASE_URL`, and the repo's own audit artifact calling out the missing real health backend.

---

## Documentation impact
- Update `docs/architecture.md` to document the new `GET /system/health` operator endpoint.
- Update `docs/deployment.md` where necessary so database configuration language matches the corrected runtime behavior.
- No broader user-guide rewrite is required if the existing health-page UI continues to work against the new endpoint contract.

---

## Architecture plan
Use a focused brownfield hardening pass that fixes the operational contract at the source.

Preferred approach:
- Fix storage URL resolution in the shared storage layer so every caller of `get_engine()` and `get_session_factory()` inherits the corrected `DATABASE_URL` behavior.
- Add a dedicated backend system-health aggregation helper that reads bounded, already-stored operational evidence: recent ingest events, configured pipeline connection profiles, alert channel status, alert delivery history, and storage engine/file metadata.
- Keep `/health` as the simple liveness probe and add `/system/health` as the richer operator snapshot endpoint.
- Extend the frontend health type/API surface just enough to consume backend-derived service metadata and real subsystem detail.
- Preserve existing page structure and accessible interactions while removing placeholder fallback logic.

Alternative considered:
- Keep the frontend-side composition pattern and fetch multiple existing endpoints to synthesize health in the browser.

Why rejected:
- It would still leave the product without a truthful backend contract for operators.
- It would duplicate aggregation logic in the client and make support/debugging harder.
- It would not address the deployment/runtime mismatch around database configuration.

---

## API design

### `GET /system/health`
- **Auth required:** yes, via existing control-plane viewer access dependency. In open-access mode, the existing anonymous control-plane behavior still applies.
- **Request body:** none
- **Success response (200):**
```json
{
  "service_version": "0.2.0",
  "generated_at": "2026-04-13T09:30:00Z",
  "overall_status": "warning",
  "subsystems": {
    "ingestion": {
      "name": "Ingestion",
      "status": "healthy",
      "details": {
        "last_event_time": "2026-04-13T09:28:00Z",
        "events_per_minute": 12,
        "ingestion_errors_24h": 1
      }
    },
    "connectors": {
      "name": "Connectors",
      "status": "warning",
      "details": {
        "total_connections": 4,
        "healthy_connections": 4,
        "failed_connections": 0,
        "last_tested": null,
        "warnings": [
          "Runtime connectivity checks are not persisted yet; connector health reflects saved config validation only."
        ]
      }
    },
    "alerting": {
      "name": "Alerting",
      "status": "healthy",
      "details": {
        "active_channels": 2,
        "deliveries_24h": 8,
        "failures_24h": 0
      }
    },
    "storage": {
      "name": "Storage",
      "status": "healthy",
      "details": {
        "engine": "postgresql",
        "status": "connected",
        "approximate_size_mb": 128,
        "warnings": []
      }
    }
  },
  "recent_issues": [
    {
      "id": "run-error:demo-run-123:extract_orders",
      "severity": "warning",
      "category": "run_failure",
      "message": "Recent run failure detected in step 'extract_orders'.",
      "timestamp": "2026-04-13T08:51:00Z",
      "action_label": "Review runs",
      "action_link": "/runs"
    }
  ]
}
```
- **Error responses:**
  - `401` — invalid or missing control-plane credentials when auth is enabled
  - `403` — caller lacks viewer access
  - `500` — internal aggregation failure; no stack trace returned

---

## Data model changes
No database schema changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: restore the previous storage URL resolution and remove the new endpoint/client wiring if the health contract causes regressions.
- Breaking change? No

---

## Edge cases

| Edge case | Handling |
|---|---|
| No pipeline events have ever been ingested | Ingestion remains `unknown`; recent issues list is empty and the UI empty state remains truthful |
| `DATABASE_URL` points to a non-SQLite engine | Engine creation skips SQLite-only `check_same_thread` connection args |
| Connector profiles exist but there is no persisted runtime test history | Connector subsystem returns a warning and `last_tested=null` rather than inventing runtime health |
| Alert channels are configured only through env vars | Alerting subsystem includes env-backed channel status through the existing registry |
| Storage backend is SQLite and file path does not yet exist | Storage size reports `0` and includes a warning only if the DB cannot be inspected |
| Health aggregation hits an unexpected service failure | Endpoint returns a safe 500 error and logs context server-side |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Health status logic overstates certainty for connectors | Medium | High | Keep connector warnings explicit and use only persisted validation evidence |
| `DATABASE_URL` fix changes behavior in environments that implicitly relied on SQLite fallback | Medium | High | Make precedence explicit in code and docs; keep `BIOMECHANICS_AI_DB_PATH` fallback when `DATABASE_URL` is unset |
| New health endpoint adds slow queries on large datasets | Low | Medium | Use bounded look-back windows and aggregate queries only |
| Frontend assumes placeholder-safe data and mishandles real failures | Medium | Medium | Remove fallback intentionally and add tests for backend error paths |

---

## Breaking changes
No intentional API or schema break.
Runtime behavior changes for deployments that already set `DATABASE_URL`: they will now connect using the documented database URL instead of silently relying on SQLite-oriented behavior.

---

## Testing strategy
- **Unit:** storage URL resolution and engine creation; health aggregation helpers for ingestion, connector, alerting, storage, and recent-issue derivation.
- **Integration:** `GET /health` remains stable and `GET /system/health` returns real structured data against an in-memory test database.
- **E2E:** none required for this targeted pass because the existing frontend pages already cover the route shell; page-level regression is handled in Vitest.
- **Performance:** validate that the endpoint uses bounded queries and no accidental N+1 loops.
- **Security:** verify the response does not leak secrets or raw config values and that viewer-role dependency behavior is preserved.

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