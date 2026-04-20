# Research Brief: Temporal vs Prefect vs Stage-2 Checkpoints

**Slug:** temporal-prefect-durable-engine-research
**Referenced by:** `docs/architecture/decisions/ADR-002-durability-roadmap.md` (Stage 3)
**Date:** 2026-04-18
**Status:** Complete

---

## Questions Asked

1. What is Temporal's execution model and what does adoption cost?
2. What is Prefect's execution model and how does it differ from Temporal?
3. How do both compare to the Stage 2 in-process checkpoint mechanism already implemented?
4. Which option is appropriate for which scale/requirement threshold?
5. What concrete multi-worker requirement would justify adopting an external engine?

---

## Sources / Basis for Analysis

- Temporal v1.x SDK (Python) public documentation and best-practices guides
- Prefect v3.x `@flow` / `@task` API and result-persistence docs
- Stage 2 implementation: `src/agent_runtime/executor.py`, `src/agent_runtime/storage/store.py`, `alembic/versions/0002_add_checkpoints_table.py`
- General distributed-systems literature on workflow engine trade-offs
- Vercel Labs / similar agentic orchestration benchmarks referenced in `docs/specs/research/vercel-labs-agent-skills-research.md`

---

## Findings

### Stage 2 Checkpoint Mechanism (current)

| Property | Detail |
|---|---|
| **Resumability** | Resumes after process restart at step granularity |
| **Horizontal scaling** | ❌ No — the in-memory `_records` dict is per-process; concurrent workers executing the same task would race |
| **Retries** | ❌ No — the caller decides retry by re-calling `execute()`; no back-off policy |
| **Visibility** | ❌ No workflow UI; observable only through existing SSE/API |
| **Infra footprint** | SQLite (dev) / PostgreSQL (prod) already present for Stage 1 |
| **Ops complexity** | None beyond the existing DB |
| **Adoption cost** | Already done; ~750 LOC across executor + storage modules |

**Verified limitation:** `InMemoryExecutor._records` is instance-scoped. Two workers starting the same `(task_id, step_id)` tuple simultaneously will each execute the handler once and race on the `SQLCheckpointStore.save()` UPDATE→INSERT path. The upsert is idempotent (last writer wins) but both handlers will have run — this is an *at-least-once* execution model under concurrent restarts, not exactly-once.

---

### Temporal

**Model:** Activities (individual units of work) run inside Workflows (deterministic replay log). The Temporal server is the durable state machine; workers are stateless and can restart freely. The server guarantees exactly-once semantics (activity outcomes are persisted before the worker receives them).

| Property | Detail |
|---|---|
| **Resumability** | Full, deterministic re-hydration from event history |
| **Horizontal scaling** | ✅ Task queue–based; any number of workers can pick up activities |
| **Retries** | ✅ First-class; configurable per-activity with back-off and timeout |
| **Visibility** | ✅ Temporal Web UI with full workflow execution graph, failure traces |
| **Infra footprint** | Temporal Server (Cassandra or PostgreSQL backend) + separate worker processes |
| **Ops complexity** | High — requires running/operating Temporal Server (managed: Temporal Cloud ~$0.067 / action; self-managed: significant ops burden) |
| **SDK** | `temporalio` Python SDK; every Agent step becomes an `@activity`; plan execution loop becomes a `@workflow` |
| **Adoption cost** | Full rewrite of `executor.py` + `routes.py` to Workflow/Activity pattern; Temporal type stubs in `schemas.py`; separate worker entry point; new infra |

**Key constraint from ADR:** Temporal must be introduced as an *execution backend*, not a replacement for the orchestration contract. `workflow-manifest.json` and module boundary rules remain authoritative.

**When justified:** Only when at least one of these is true:
- Multiple concurrent workers executing the same plan in a shared cluster
- Exactly-once semantics required (financial, compliance, or destructive-action tasks)
- Activity-level retry policy with configurable back-off is a hard requirement
- The operator team has capacity to own a Temporal Server or budget for Temporal Cloud

---

### Prefect

**Model:** Flows (Python functions decorated with `@flow`) orchestrate Tasks (`@task`). Results are persisted to a configurable storage backend. Prefect Server (or Cloud) provides scheduling, observability, and retry management. Workers are pull-based from work pools.

| Property | Detail |
|---|---|
| **Resumability** | ✅ Via result caching and `persist_result=True`; resumes at task level on re-run |
| **Horizontal scaling** | ✅ Work pools; multiple workers drain the same queue |
| **Retries** | ✅ Per-task `retries=` and `retry_delay_seconds=` |
| **Visibility** | ✅ Prefect UI (flow runs, task states, logs) |
| **Infra footprint** | Prefect Server (SQLite or PostgreSQL) + optional object storage for results |
| **Ops complexity** | Medium — lighter than Temporal; `prefect server start` for local; Prefect Cloud is free-tier-available |
| **SDK** | `prefect` Python package; steps become `@task`; plan execution loop becomes `@flow` |
| **Adoption cost** | Moderate — `executor.py` refactored to Prefect flow/task model; `schemas.py` unchanged; result types serializable via Pydantic already |

**Key difference from Temporal:** Prefect does not enforce deterministic replay. Resumability is task-level result caching, not event-sourced history. This means at-least-once semantics under concurrent workers unless the task cache key is unique per invocation and the result backend is consistent.

**When justified:** When the team needs observability and retry wins faster than Temporal adoption, with a lower ops bar and no strictly-once requirement.

---

## Comparison Matrix

| Dimension | Stage 2 Checkpoints | Prefect | Temporal |
|---|---|---|---|
| Exactly-once execution | ❌ (at-least-once under concurrent restart) | ❌ (task cache is best-effort) | ✅ |
| Multi-worker horizontal scale | ❌ | ✅ | ✅ |
| Per-step retries with back-off | ❌ | ✅ | ✅ |
| Workflow UI / observability | ❌ | ✅ | ✅ |
| New infra required | ❌ (uses existing DB) | ✅ (Prefect Server / Cloud) | ✅ (Temporal Server / Cloud) |
| Adoption cost | ✅ Already done | Medium | High |
| Ops complexity | Minimal | Medium | High |
| Suitable for single-worker dev/CI | ✅ | ✅ | ✅ |
| Suitable for multi-worker production | ❌ | ✅ | ✅ |

---

## Constraints / Decisions Added to Local Implementation

1. **Stage 2 is sufficient until a concrete multi-worker requirement exists.** The existing `SQLCheckpointStore` + `InMemoryExecutor` is the right production choice for single-process deployments.

2. **If a multi-worker requirement is confirmed, adopt Prefect first** unless exactly-once semantics are required. Prefect's lower ops footprint, Pydantic-compatible result types, and free-tier Cloud make it the better stepping stone for this codebase.

3. **Temporal is justified only when exactly-once semantics, financial compliance, or destructive-action guarantees become a hard requirement**, or the team is running Temporal Cloud and has validated the per-action cost against expected throughput.

4. **Migration path:** Stage 2 → Prefect requires: (a) wrapping `InMemoryExecutor.execute()` as a `@task` inside a `@flow` plan runner; (b) replacing `CheckpointStore` with Prefect's result cache; (c) adding a `PrefectCheckpointStore` adapter that reads from Prefect result storage for hybrid rollout. Schema types stay unchanged.

5. **The `workflow-manifest.json` orchestration contract and ADR-001 module boundaries are non-negotiable.** Any engine is a backend detail injected at `app.py` lifespan; the HTTP API, planner, and validator layers do not change.

---

## Open Questions (Human Decision Required)

| # | Question | Impact |
|---|---|---|
| 1 | Is there a confirmed target deployment that requires >1 concurrent worker? | Primary gate for Stage 3 |
| 2 | Are there tasks that require exactly-once execution guarantees (financial, destructive, compliance)? | Choice between Prefect and Temporal |
| 3 | Does the team have capacity to own a Prefect or Temporal Server, or budget for Cloud? | Affects ops feasibility |
| 4 | What is the target throughput (actions/min)? Temporal Cloud is billed per action. | Cost model for Temporal |
| 5 | Should Stage 3 be deferred indefinitely in favor of extending Stage 2 with a distributed lock (e.g., Redis SETNX) to make the at-least-once gap safe for concurrent workers? | Alternative lower-cost path |
