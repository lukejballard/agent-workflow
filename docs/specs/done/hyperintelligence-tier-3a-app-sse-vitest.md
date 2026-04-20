# Feature: Agent Runtime ASGI App, SSE Endpoint, and Vitest Component Tests

**Status:** Done
**Created:** 2026-04-18
**Author:** GitHub Copilot
**Estimate:** M
**Supersedes:** —

---

## Problem

Three gaps remain before the Tier 2 backend and frontend can be run end-to-end:

1. `src/agent_runtime/routes.py` defines a router but there is no ASGI `app` to mount it. `uvicorn` cannot start.
2. `frontend/src/hooks/useTaskStream.ts` subscribes to `GET /api/tasks/{id}/events` but that SSE endpoint is not implemented.
3. The React component scaffold has zero tests. Frontend changes have no safety net.

---

## Success criteria

- `uvicorn src.agent_runtime.app:app --reload` starts without error.
- `GET /api/tasks/{id}/events` returns an `text/event-stream` response that yields at least one `ping` heartbeat.
- `tests/unit/test_app_startup.py` confirms the app imports and its routes are registered (no round-trip HTTP test needed at this stage).
- `tests/unit/test_routes_sse.py` covers the SSE endpoint (200, task-not-found 404, correct content-type).
- `frontend/src/__tests__/` contains Vitest tests for all four agent components and the two hooks.
- All 310+ backend tests remain green at 100% coverage.

---

## Requirements

### Functional

- [x] Create `src/agent_runtime/app.py` with:
  - `create_app() -> FastAPI` factory
  - lifespan context manager (no-op for now)
  - CORS middleware (allow-all origins for development; tighten via env in production)
  - `router` from `routes.py` mounted at root
  - top-level `app = create_app()` for `uvicorn`
- [x] Add `GET /api/tasks/{task_id}/events` SSE endpoint to `routes.py`:
  - Returns `text/event-stream` with `EventSourceResponse`
  - Streams `data: ping\n\n` heartbeat once, then existing task events from `RuntimeStore`
  - Returns 404 if `task_id` is not found
- [x] Add `tests/unit/test_app_startup.py` — verify `create_app()` registers the expected route paths.
- [x] Add `tests/unit/test_routes_sse.py` — verify SSE content-type, 404 on missing task, and event data shape.
- [x] Add `frontend/src/__tests__/TaskCard.test.tsx`
- [x] Add `frontend/src/__tests__/PlanViewer.test.tsx`
- [x] Add `frontend/src/__tests__/TraceTimeline.test.tsx`
- [x] Add `frontend/src/__tests__/ApprovalPanel.test.tsx`
- [x] Add `frontend/src/__tests__/useTaskCommands.test.ts`

### Non-functional

- [x] CORS enabled; `allow_origins` read from `CORS_ORIGINS` env var (default `["*"]` for dev).
- [x] SSE endpoint uses `starlette.responses.StreamingResponse`; no extra dependencies.
- [x] All new Python code has type hints; `extra="forbid"` on any new Pydantic models.
- [x] ≥ 80% coverage on all new backend code (target 100%).
- [x] Vitest tests use `@testing-library/react` render + `userEvent`; no snapshot tests.
- [x] All components pass WCAG checks exposed via accessible queries (`getByRole`, `getByLabelText`).

---

## Affected components

**Backend:**
- `src/agent_runtime/app.py` (new)
- `src/agent_runtime/routes.py` (add SSE endpoint)
- `tests/unit/test_app_startup.py` (new)
- `tests/unit/test_routes_sse.py` (new)
- `pyproject.toml` (add `sse-starlette` or use bare `StreamingResponse`)

**Frontend:**
- `frontend/src/__tests__/TaskCard.test.tsx` (new)
- `frontend/src/__tests__/PlanViewer.test.tsx` (new)
- `frontend/src/__tests__/TraceTimeline.test.tsx` (new)
- `frontend/src/__tests__/ApprovalPanel.test.tsx` (new)
- `frontend/src/__tests__/useTaskCommands.test.ts` (new)
