# ADR-001: Agent Runtime Module Boundaries

**Status:** Accepted
**Date:** 2026-04-18
**Author:** GitHub Copilot
**Context:** `src/agent_runtime/`, `docs/hyperintelligence_plan.md` (sections 5, 7)

---

## Context

With Tiers 1 and 2 of the hyperintelligence plan implemented, the backend now
contains 12 domain modules plus a route layer.  Without documented boundaries,
future changes may introduce hidden coupling that defeats testability,
reversibility, and operator safety.

This ADR establishes the module responsibility contract that must not be
violated by subsequent changes.

---

## Decision

### 1. Dependency direction is strictly bottom-up

```
schemas.py          ← no intra-package imports (foundation)
     ↑
state_machine.py    ← imports schemas only
events.py           ← imports schemas only
observability.py    ← imports stdlib only
tool_router.py      ← imports schemas only
     ↑
planner.py          ← imports schemas
executor.py         ← imports schemas
validator.py        ← imports schemas
learning.py         ← imports schemas
memory_service.py   ← imports schemas
artifacts.py        ← imports schemas
     ↑
routes.py           ← imports all of the above; exposed to HTTP layer
```

No module may import from a higher layer.  Circular imports are a hard
failure.

### 2. Planner/Executor/Validator are boundary-isolated

- **Planner** returns `Plan` only.  It does not start execution or emit events.
- **Executor** consumes `Plan` and returns `ExecutionRecord` only.  It does not
  replan or call the validator.
- **Validator** consumes records and returns `EvaluationResult` only.  It does
  not mutate any store.
- **Learning** consumes `RunArtifact` objects asynchronously.  It does not
  trigger execution or modify plans.

These boundaries allow independent unit testing with no mocking of sibling
modules.

### 3. All storage is injected, never global

- `routes.py` uses FastAPI `Depends(get_store)` for the `RuntimeStore`.
- Tests override `get_store` via `app.dependency_overrides` to get per-test
  isolation **without** patching module globals.
- `InMemoryExecutor`, `InMemoryMemoryService`, and `InMemoryArtifactStore`
  are instantiated by callers, not as module-level singletons.

### 4. `schemas.py` is the single source of truth for domain types

All new domain datatypes belong in `schemas.py` (or a new schemas module
imported by it).  Defining ad-hoc Pydantic models inside route or service
modules is only acceptable for request/response bodies with no domain
equivalents.

### 5. Routes are thin

Route handlers do exactly three things: validate input, call service helpers,
and return shaped responses.  Business logic belongs in the domain modules, not
in route functions.

### 6. In-memory stores are the scaffold; persistence is deferred

Current stores (`RuntimeStore`, `InMemoryExecutor`, `InMemoryMemoryService`,
`InMemoryArtifactStore`) are explicitly scaffolds.  When persistence is
introduced, it must be introduced behind the same interface contracts already
tested against the in-memory implementations.

---

## Consequences

### Positive
- Each module has exactly one reason to change.
- Tests require no inter-module mocks.
- Storage implementations can be swapped without changing route or domain code.
- The route layer is easy to replace (e.g., with an ASGI app with lifespan) as
  the domain logic is not entangled with HTTP.

### Negative
- Strict DI requires a bit more boilerplate in route fixtures.
- External integrations (LangGraph, Temporal) must be wrapped in adapters to
  respect these boundaries.

---

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Module-level singletons for all stores | Hard to test; state leaks between tests |
| Route functions containing planning/execution logic | Couples HTTP lifecycle to domain logic; untestable in isolation |
| Single monolithic `agent.py` | Defeats hierarchy of testability and reversibility |
| Import-only-on-demand lazy loads | Adds indirection with no benefit at current scale |

---

## Related
- `docs/specs/active/hyperintelligence-tier-1.md`
- `docs/specs/active/hyperintelligence-tier-2.md`
- `docs/specs/active/hyperintelligence-tier-2b-routes-frontend.md`
- `docs/hyperintelligence_plan.md` — section 7.2 (execution model / module boundaries)
