# Feature: Hyperintelligence Tier 2b — Routes, Frontend, and Architecture Docs

**Status:** Done
**Created:** 2026-04-18
**Author:** GitHub Copilot
**Estimate:** XL
**Supersedes:** None
**Upstream:** `docs/hyperintelligence_plan.md` (sections 5, 6, 7, 10.items 23–30)

---

## Problem

Tier 1 and Tier 2 delivered a fully tested Python runtime core (12 modules, 276
tests, 100% coverage).  The runtime core is not yet accessible to operators or
systems: there are no API endpoints, no frontend scaffold, and the architecture
docs still declare the repo as "reserved."

Items 23–30 of the implementation checklist close that gap: they add a thin
FastAPI route layer, scaffold the React/TypeScript frontend, wire typed API
clients and hooks, and align the architecture documentation to the verified
implementation.

## Success criteria

- `src/agent_runtime/routes.py` exposes task lifecycle endpoints backed by the
  state machine and planner.
- `tests/unit/test_routes_task_lifecycle.py` covers all endpoint branches via
  FastAPI TestClient with DI-isolated stores.
- `frontend/` is a functioning Vite/React/TypeScript scaffold with `package.json`,
  `tsconfig`, `vite.config`, and `src/main.tsx`.
- `frontend/src/types/agentRuntime.ts` mirrors the backend Pydantic schemas.
- `frontend/src/api/agentRuntime.ts` provides one typed function per endpoint.
- `frontend/src/hooks/useTaskStream.ts` and `useTaskCommands.ts` wrap API and SSE.
- `frontend/src/pages/AgentControlCenter.tsx` is a thin page using hooks and components.
- `frontend/src/components/agent/` contains `TaskCard`, `PlanViewer`,
  `TraceTimeline`, and `ApprovalPanel`.
- All frontend components meet WCAG 2.1 AA accessibility requirements.
- `docs/architecture.md` is updated to reflect the verified runtime state.
- `docs/architecture/decisions/ADR-001-runtime-module-boundaries.md` is created.

---

## Requirements

### Functional — Backend
- [x] Add `fastapi>=0.115` to `pyproject.toml` production dependencies.
- [x] Add `httpx>=0.27` to `pyproject.toml` dev dependencies (TestClient).
- [x] Create `src/agent_runtime/routes.py` with a `RuntimeStore` dataclass for
      DI-injectable in-memory state.
- [x] Implement `POST /api/tasks` → 201 Task (PENDING).
- [x] Implement `GET /api/tasks` → 200 list[Task].
- [x] Implement `GET /api/tasks/{task_id}` → 200 Task | 404.
- [x] Implement `POST /api/tasks/{task_id}/transitions` → 200 Task | 404 | 422.
- [x] Implement `POST /api/tasks/{task_id}/plan` → 201 Plan | 404 | 422.
- [x] Implement `GET /api/tasks/{task_id}/plan` → 200 Plan | 404.
- [x] `routes.py` must never expose stack traces in error responses.

### Functional — Backend tests
- [x] Add `tests/unit/test_routes_task_lifecycle.py` with fixture that overrides
      `get_store` with a fresh `RuntimeStore` per test.
- [x] Test: POST /api/tasks creates PENDING task.
- [x] Test: GET /api/tasks returns created tasks.
- [x] Test: GET /api/tasks/{id} returns task or 404.
- [x] Test: Transition PENDING → PLANNING succeeds.
- [x] Test: Transition to an invalid state returns 422.
- [x] Test: Transition on missing task returns 404.
- [x] Test: POST plan on existing task returns 201 plan.
- [x] Test: POST plan with cycle returns 422.
- [x] Test: GET plan returns existing plan or 404.

### Functional — Frontend scaffold
- [x] Create `frontend/package.json` (React 19, Vite 8, TypeScript strict, Vitest 4,
      react-router-dom 7).
- [x] Create `frontend/tsconfig.json` + `frontend/tsconfig.app.json` (strict + noUncheckedIndexedAccess).
- [x] Create `frontend/vite.config.ts` with React plugin and Vitest jsdom environment.
- [x] Create `frontend/eslint.config.js` with TypeScript-ESLint rules.
- [x] Create `frontend/index.html` and `frontend/src/main.tsx`.
- [x] Create `frontend/src/App.tsx` with react-router-dom routes.

### Functional — Frontend feature files
- [x] Create `frontend/src/types/agentRuntime.ts` with all domain interfaces.
- [x] Create `frontend/src/api/agentRuntime.ts` with one typed function per endpoint.
- [x] Create `frontend/src/hooks/useTaskStream.ts` (SSE subscription, error state, clear).
- [x] Create `frontend/src/hooks/useTaskCommands.ts` (createTask, transitionTask, createPlan).
- [x] Create `frontend/src/pages/AgentControlCenter.tsx` (task queue + new task form).
- [x] Create `frontend/src/components/agent/TaskCard.tsx`.
- [x] Create `frontend/src/components/agent/PlanViewer.tsx`.
- [x] Create `frontend/src/components/agent/TraceTimeline.tsx`.
- [x] Create `frontend/src/components/agent/ApprovalPanel.tsx`.

### Non-functional
- [x] All interactive frontend elements meet WCAG 2.1 AA (aria-labels, semantic HTML,
      aria-live for dynamic content).
- [x] No `any` types in TypeScript files.
- [x] `routes.py` never leaks stack traces to clients.
- [x] Route handlers are thin: validate → call service → return shaped response.
- [x] New endpoint descriptions added to `docs/architecture.md`.

### Documentation
- [x] Update `docs/architecture.md` to reflect verified runtime state and API surface.
- [x] Create `docs/architecture/decisions/ADR-001-runtime-module-boundaries.md`.

---

## Affected components

| Path | Action |
|---|---|
| `pyproject.toml` | Extend (add fastapi, httpx) |
| `src/agent_runtime/routes.py` | Create |
| `tests/unit/test_routes_task_lifecycle.py` | Create |
| `frontend/package.json` | Create |
| `frontend/tsconfig.json` | Create |
| `frontend/tsconfig.app.json` | Create |
| `frontend/vite.config.ts` | Create |
| `frontend/eslint.config.js` | Create |
| `frontend/index.html` | Create |
| `frontend/src/main.tsx` | Create |
| `frontend/src/App.tsx` | Create |
| `frontend/src/types/agentRuntime.ts` | Create |
| `frontend/src/api/agentRuntime.ts` | Create |
| `frontend/src/hooks/useTaskStream.ts` | Create |
| `frontend/src/hooks/useTaskCommands.ts` | Create |
| `frontend/src/pages/AgentControlCenter.tsx` | Create |
| `frontend/src/components/agent/TaskCard.tsx` | Create |
| `frontend/src/components/agent/PlanViewer.tsx` | Create |
| `frontend/src/components/agent/TraceTimeline.tsx` | Create |
| `frontend/src/components/agent/ApprovalPanel.tsx` | Create |
| `docs/architecture.md` | Update |
| `docs/architecture/decisions/ADR-001-runtime-module-boundaries.md` | Create |

---

## Out of scope (deferred to Tier 3)
- FastAPI `app.py` with lifespan, middleware, and auth.
- WebSocket bi-directional stream endpoint.
- Database persistence layer.
- Frontend Vitest unit tests for components.
- Durable execution engine (Temporal).
- Advanced memory lifecycle platform.
