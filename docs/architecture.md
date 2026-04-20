# Architecture

## Repository Goal

This repository is an agent-driven software delivery scaffold that has grown
into a production-minded engineering intelligence layer.  It combines a
workflow-governance control plane (`.github/`) with a typed Python runtime
core (`src/agent_runtime/`) and a React/TypeScript operator frontend
(`frontend/`).

## Verified Repo State

The following areas are present and verified:

- `.github/` — workflow governance, instructions, prompts, agents, and
  canonical metadata (workflow-manifest, repo-map, skill-registry, schemas).
- `docs/` — architecture, product direction, specs, and runbooks.
- `src/agent_runtime/` — 19 Python modules, 396 unit tests, 100% test coverage.
- `frontend/src/` — Vite/React/TypeScript scaffold with typed API client,
  hooks, a control-center page, and four agent components.
- `tests/unit/` — 396 passing unit tests covering all backend modules.
- `scripts/` — metadata validation and hygiene helpers.

## Current Architecture

The architecture has four layers:

### 1. Workflow-governance layer (`/.github/`)
Defines instructions, prompts, agents, approval hooks, and canonical metadata.
This layer is the policy kernel — it routes tasks, registers skills, and
governs the orchestration contract.

### 2. Documentation and planning layer (`/docs/`, `/specs/`, `/openspec/`)
Captures requirements, specs, process, and repo operating rules.  Active specs
in `docs/specs/active/` are the single source of truth for in-flight work.

### 3. Runtime engine (`/src/agent_runtime/`)
A pure-Python agent runtime with strict module boundaries (see ADR-001).

| Module | Responsibility |
|---|---|
| `schemas.py` | All Pydantic DTOs — foundational, no intra-package imports |
| `state_machine.py` | Immutable task lifecycle transitions |
| `events.py` | Typed event envelope for UI and audit consumers |
| `observability.py` | Structured logging with correlation field injection |
| `tool_router.py` | Policy-driven tool call classification |
| `planner.py` | DAG plan assembly with cycle detection |
| `executor.py` | Idempotent step execution with terminal deduplication |
| `validator.py` | Confidence-scored evaluation with structured findings |
| `learning.py` | Evidence-threshold pattern extraction from run artifacts |
| `memory_service.py` | Scoped in-memory entry storage and retrieval |
| `artifacts.py` | Run artifact persistence (in-memory, upsert semantics) |
| `routes.py` | FastAPI router — thin task lifecycle API endpoints |
| `app.py` | ASGI application factory — mounts CORS middleware, route router, and Temporal worker lifespan |
| `temporal_runner.py` | Temporal workflow definition — deterministic plan execution with `workflow.uuid4()` |
| `temporal_worker.py` | Temporal worker factory — registers workflow and activity types for the runtime worker |
| `persistence.py` | Pluggable run-artifact persistence layer with in-memory and file-backed backends |
| `session.py` | Session-scoped factory for runtime service composition |
| `config.py` | Environment-driven configuration with default values and validation |

### 4. Operator frontend (`/frontend/`)
A React 19 / TypeScript / Vite 8 SPA that lets operators inspect and
control the runtime.  No API calls in components; all data flows through
typed hooks and API helpers.

| Area | Contents |
|---|---|
| `src/types/agentRuntime.ts` | TypeScript interfaces mirroring backend schemas |
| `src/api/agentRuntime.ts` | One typed function per API endpoint |
| `src/hooks/useTaskStream.ts` | SSE event-stream subscription hook |
| `src/hooks/useTaskCommands.ts` | Mutation helpers (createTask, transition, plan) |
| `src/pages/AgentControlCenter.tsx` | Task queue page with new-task form |
| `src/components/agent/TaskCard.tsx` | Task summary with state badge |
| `src/components/agent/PlanViewer.tsx` | DAG plan step list with status |
| `src/components/agent/TraceTimeline.tsx` | Chronological event stream |
| `src/components/agent/ApprovalPanel.tsx` | Approve / deny operator controls |

## API Surface

All routes are under `/api` and backed by the `RuntimeStore` (in-memory;
overridable via FastAPI DI for testing).

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/tasks` | Create task (PENDING) — 201 |
| `GET` | `/api/tasks` | List all tasks — 200 |
| `GET` | `/api/tasks/{id}` | Get task — 200 / 404 |
| `POST` | `/api/tasks/{id}/transitions` | Advance state — 200 / 404 / 422 |
| `POST` | `/api/tasks/{id}/plan` | Attach validated plan — 201 / 404 / 422 |
| `GET` | `/api/tasks/{id}/plan` | Get plan — 200 / 404 |
| `GET` | `/api/tasks/{id}/events` | Stream task events as SSE — 200 / 404 |

## Documentation Rules

- Every claim in this file must be traceable to verified code or a spec in
  `docs/specs/`.
- When a new API endpoint is added, update the API Surface table above.
- ADRs for major decisions live in `docs/architecture/decisions/`.

## Source of Truth

- `docs/product-direction.md` — product and direction guidance
- `docs/specs/active/` — in-flight requirements
- `docs/architecture/decisions/` — binding architectural decisions
- `docs/runbooks/agent-mode.md` — operational runbook

