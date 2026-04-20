# Feature: Hyperintelligence Tier 1 — Runtime Schemas and Core Modules

**Status:** Done
**Created:** 2026-04-18
**Author:** GitHub Copilot
**Estimate:** L
**Supersedes:** None
**Upstream:** `docs/hyperintelligence_plan.md` (sections 7, 9.Tier 1, 10.items 1–10)

---

## Problem
The repository has strong governance and workflow metadata but no runtime
execution layer. The hyperintelligence plan identifies this as the primary
capability gap. Before any framework integrations, UI surfaces, or advanced
features can exist, the codebase needs typed runtime schemas, a task state
machine, an event envelope, a tool router with policy hooks, and baseline
observability utilities — all with tests.

This spec covers only Tier 1 (immediate wins) from the hyperintelligence plan:
the foundational modules that everything else depends on.

## Success criteria
- `src/agent_runtime/` exists as an installable Python package with typed schemas.
- Task state machine enforces allowed transitions and emits events.
- Event envelope schema supports frontend/backend contract stability.
- Tool router wraps tool calls with policy decisions, retries, and structured logging.
- Observability helpers inject trace correlation fields.
- All modules have corresponding tests in `tests/unit/`.
- `pyproject.toml` declares dependencies and test configuration.
- `docs/product-direction.md` acknowledges the runtime direction.

---

## Requirements

### Functional
- [x] Create `pyproject.toml` with pydantic, pytest, and ruff dependencies.
- [x] Create `src/agent_runtime/__init__.py` package.
- [x] Create `src/agent_runtime/schemas.py` with Pydantic models: `TaskState`, `PlanStep`, `Plan`, `ToolCallStatus`, `ToolCall`, `MemoryEntry`, `EvaluationFinding`, `EvaluationResult`, `RunArtifact`, `Task`.
- [x] Create `src/agent_runtime/state_machine.py` with valid transition map and transition function that enforces invariants.
- [x] Create `src/agent_runtime/events.py` with typed event envelope (`AgentEvent`) and event types for state transitions and tool calls.
- [x] Create `src/agent_runtime/tool_router.py` with policy decision outcomes (allow/deny/require_approval), timeout defaults, and retry classification.
- [x] Create `src/agent_runtime/observability.py` with structured logger helpers that inject `trace_id`, `run_id`, `task_id`, `step_id`.
- [x] Add `tests/unit/test_state_machine.py` for allowed and forbidden transitions.
- [x] Add `tests/unit/test_events_schema.py` for event serialization and required fields.
- [x] Add `tests/unit/test_tool_router_policy.py` for allow/deny/approval branches.
- [x] Add `tests/unit/test_observability_fields.py` for trace field presence.
- [x] Add `tests/unit/test_schemas.py` for Pydantic model validation (extra-forbid, required fields, constraints).

### Non-functional
- [x] All public functions and methods have type hints.
- [x] `extra="forbid"` on all Pydantic models.
- [x] Minimum 80% line + branch coverage on new code (100% achieved).
- [x] No I/O in schema or state machine modules (pure logic).
- [x] Compatible with Python 3.14.

---

## Affected components

| Path | Action |
|---|---|
| `pyproject.toml` | Create |
| `src/agent_runtime/__init__.py` | Create |
| `src/agent_runtime/schemas.py` | Create |
| `src/agent_runtime/state_machine.py` | Create |
| `src/agent_runtime/events.py` | Create |
| `src/agent_runtime/tool_router.py` | Create |
| `src/agent_runtime/observability.py` | Create |
| `tests/__init__.py` | Create |
| `tests/unit/__init__.py` | Create |
| `tests/unit/test_schemas.py` | Create |
| `tests/unit/test_state_machine.py` | Create |
| `tests/unit/test_events_schema.py` | Create |
| `tests/unit/test_tool_router_policy.py` | Create |
| `tests/unit/test_observability_fields.py` | Create |
| `docs/product-direction.md` | Update |
| `docs/architecture.md` | Update |

---

## External context
- Upstream plan: `docs/hyperintelligence_plan.md`
- Pydantic v2 documentation for `ConfigDict(extra="forbid")` and model patterns.
- No external research brief required; all design decisions are in the upstream plan.

---

## Documentation impact
- `docs/product-direction.md` must be updated to acknowledge the runtime direction.
- `docs/architecture.md` must be updated to describe `src/agent_runtime/` once modules are created.

---

## Architecture plan

### Module dependency graph

```
schemas.py          ← foundational types, no imports from other agent_runtime modules
    ↑
state_machine.py    ← imports schemas (TaskState, Task)
    ↑
events.py           ← imports schemas (TaskState, ToolCall, etc.)
    ↑
observability.py    ← standalone structured logging, no agent_runtime imports
    ↑
tool_router.py      ← imports schemas, events, observability
```

### State machine transitions

```
PENDING → PLANNING
PLANNING → EXECUTING | FAILED | CANCELLED
EXECUTING → VALIDATING | FAILED | CANCELLED
VALIDATING → LEARNING | EXECUTING (revision) | FAILED | CANCELLED
LEARNING → DONE | FAILED
FAILED → (terminal)
DONE → (terminal)
CANCELLED → (terminal)
```

### Tool router policy

The tool router classifies each tool call request against a policy table:
- **allow**: execute immediately with timeout and structured logging
- **deny**: reject with policy reason, emit denied event
- **require_approval**: pause and emit approval-required event

Error classification for retry decisions:
- **TRANSIENT**: network timeouts, rate limits → exponential backoff retry
- **PERMANENT**: auth failures, invalid input → immediate failure
- **POLICY**: denied by policy → no retry, emit event

---

## Data model changes
None — no database in Tier 1. All models are in-memory Pydantic schemas.

---

## Out of scope (deferred to later tiers)
- Planner, executor, validator, learning modules (Tier 2)
- Semantic mapper and retrieval adapters (Tier 2)
- React frontend pages (Tier 2)
- Database persistence and API routes (Tier 2)
- External framework integrations (Tier 3)
