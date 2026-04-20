# ADR-002: Runtime Durability Roadmap

**Status:** Accepted
**Date:** 2026-04-18
**Author:** GitHub Copilot
**Context:** `docs/hyperintelligence_plan.md` (Tier 2–3), `src/agent_runtime/`, completed checklist items 1–30.

---

## Context

The agent runtime is now feature-complete at the scaffold stage: all 14 modules,
327 unit tests at 100% coverage, a FastAPI ASGI entry point, SSE streaming, and a
React operator frontend.  The current storage layer is fully in-memory — all state
is lost on process restart.  This is acceptable for local development and demo
scenarios but creates three hard blockers for production use:

1. **No checkpoint or resume**: if the process restarts mid-task, the task is lost.
2. **No replay**: SSE consumers that join late miss buffered events.
3. **No cross-process sharing**: horizontal scaling is impossible because each
   worker has an isolated `RuntimeStore`.

The hyperintelligence plan (Tier 2, items 5–6 and Tier 3, item 1) identifies
durable execution as the next major investment.

---

## Decision

This ADR records the staged durability roadmap and the constraints each stage
must satisfy.

### Stage 1 — Persistent backing store (Tier 2)

Replace the in-memory `RuntimeStore` with a persistence-backed implementation.

**Constraints:**
- The `RuntimeStore` interface contract (`tasks`, `plans`, `events`) must not
  change.  Existing FastAPI DI injection points must remain valid.
- Storage is injected at application startup, not imported globally.  Tests
  continue to inject the in-memory implementation.
- Candidate backend: SQLite (dev/CI) → PostgreSQL (production).  Use
  SQLAlchemy Core (not ORM) with Alembic migrations to keep the layer thin and
  auditable.
- All writes are idempotent.  Task‐ID and event‐ID collisions must be detected
  and converted to no-ops, not errors, to support safe retries.
- Run artifacts produced by `artifacts.py` are persisted in the same store
  under a separate table/namespace.

### Stage 2 — Durable execution semantics (Tier 2/3 bridge)

Add checkpoint-and-resume behavior to the executor without adopting an external
workflow engine.

**Constraints:**
- `executor.py` gains an `ExecutorCheckpoint` DTO written after each step
  completion.  On restart, the executor reads the latest checkpoint for a
  task_id and skips already-completed steps.
- No changes to `planner.py`, `validator.py`, or the HTTP layer; only
  `executor.py` and `artifacts.py` change.
- Idempotency key: `(task_id, step_id)`.  A completed step with the same key
  must never be re-executed.

### Stage 3 — Durable distributed engine (Tier 3, optional)

Evaluate Temporal (or Prefect as a lighter stepping stone) once Stage 1 and
Stage 2 are stable and a concrete multi-worker requirement exists.

**Constraints:**
- Temporal is introduced as an *execution backend*, not a replacement for the
  orchestration contract.  `workflow-manifest.json` and the module boundary
  rules from ADR-001 remain authoritative.
- The decision to adopt Temporal requires a benchmarked cost/benefit analysis
  against the Stage 2 checkpoint mechanism.  This analysis must be captured in
  a `docs/specs/research/` brief before any code is written.
- Prefect is acceptable as a stepping stone if the team needs faster
  observability wins; the same constraint applies.

---

## Rejected Alternatives

### Adopt Temporal immediately
**Rejected.** The current in-process model has no need for multi-node
coordination yet.  Temporal's operational overhead (cluster, SDK version
management, workflow determinism rules) would slow delivery without
delivering production value.

### Use a message broker (Redis, RabbitMQ) for event streaming
**Rejected for Stage 1.** Adds an operational dependency before the storage
contract is stable.  Revisit in Stage 3 if fan-out event consumption becomes
a concrete requirement.

### Add durable storage to the `RuntimeStore` directly in-place
**Rejected.** `RuntimeStore` is a dataclass used directly in 20+ test cases.
Changing it in-place risks test pollution and coupling.  The injection pattern
(passing a concrete implementation through FastAPI DI) allows clean swapping
without touching tests.

---

## Consequences

- **Positive:** Each stage is independently shippable and independently
  testable.  Production readiness improves incrementally without a big-bang
  rewrite.
- **Positive:** The module boundary rule from ADR-001 is preserved across all
  stages.
- **Negative:** Stage 2 introduces a `ExecutorCheckpoint` write per step, which
  adds a synchronous storage call in the hot path.  This is acceptable for
  moderate task throughput; high-throughput scenarios may require batching.
- **Constraint:** `schemas.py` must not import from any storage layer.  The
  checkpoint DTO lives in `schemas.py`; the write logic lives in `executor.py`
  and `artifacts.py`.

---

## Related

- ADR-001: Agent Runtime Module Boundaries
- `docs/hyperintelligence_plan.md` §Tier 2 and §Tier 3
- `src/agent_runtime/executor.py` — step runner (current skeleton)
- `src/agent_runtime/artifacts.py` — run artifact persistence
- `src/agent_runtime/routes.py` — `RuntimeStore` injection point
