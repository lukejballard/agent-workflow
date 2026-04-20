# Persistence Stage 3 — Temporal Durable Execution Backend

**Status:** In Progress
**Slug:** persistence-stage-3
**ADR:** [ADR-002](../../architecture/decisions/ADR-002-durability-roadmap.md#stage-3)
**Research:** [temporal-prefect-durable-engine-research.md](../research/temporal-prefect-durable-engine-research.md)

## Context

Multi-worker deployment is confirmed. Exactly-once step execution is required.
The Stage 2 `InMemoryCheckpointStore` / `SQLCheckpointStore` mechanism provides
at-least-once semantics — two workers racing the same `(task_id, step_id)` tuple
will both run the handler. Temporal is adopted as the execution backend to satisfy
the exactly-once requirement.

Temporal is introduced as an **execution backend only**. The HTTP API, planner,
validator, state machine, and `workflow-manifest.json` orchestration contract are
unchanged.

## Requirements

- [x] `pyproject.toml` adds `temporalio>=1.0`.
- [x] `PlanStep.handler_name: str = "default"` — backward-compatible optional field
      that names the registered handler for this step type.
- [x] `src/agent_runtime/temporal_runner.py`:
  - `HandlerRegistry = dict[str, StepHandlerFn]` type alias.
  - Module-level `_GLOBAL_REGISTRY` + `register_handler(name, fn)` + `get_handler(name)`.
  - `ExecuteStepInput` dataclass (all primitive/string fields; step serialised as JSON).
  - `execute_step_activity` — `@activity.defn` resolves handler from registry, runs
    step, returns `ExecutionRecord` as `dict` for Temporal's default JSON converter.
  - `PlanWorkflow` — `@workflow.defn` iterates plan steps in order, dispatches each
    to `execute_step_activity`, returns `list[dict]`.
  - `TemporalPlanRunner` wraps `temporalio.client.Client`; `run_plan(plan, trace_id)`
    starts `PlanWorkflow` and returns `list[ExecutionRecord]`.
- [x] `src/agent_runtime/temporal_worker.py` — worker entry point; reads
      `TEMPORAL_HOST`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE` from env.
- [x] `app.py` lifespan wires `TemporalPlanRunner` when `TEMPORAL_HOST` is set;
      starts an in-process worker; stores runner on `app.state.temporal_runner`;
      shuts down the worker on exit.
- [x] `tests/unit/test_temporal_runner.py` (≥ 10 tests):
  - Registry: register, get, missing key.
  - Activity: success path, handler missing, handler exception, fallback to "default".
  - `TemporalPlanRunner.run_plan` with mocked client.
  - `app.py` lifespan with `TEMPORAL_HOST` set.
- [x] Existing 378 tests continue to pass, 100% coverage maintained.

## Out of Scope

- `/tasks/{task_id}/plan/execute` HTTP endpoint (separate spec).
- Temporal Cloud billing / namespace configuration.
- Prefect integration.
- Signal / query handlers.
- Child workflows.
