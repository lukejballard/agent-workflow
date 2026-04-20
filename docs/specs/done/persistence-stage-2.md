# Persistence Stage 2 — Executor Checkpoint / Resume

**Status:** Done
**Slug:** persistence-stage-2
**ADR:** [ADR-002](../../architecture/decisions/ADR-002-durability-roadmap.md#stage-2)

## Goal

Add `ExecutorCheckpoint`-based step-level persistence so the executor can
resume a partially-completed plan after a process restart without re-running
already-terminal steps.

## Requirements

- [x] `ExecutorCheckpoint` DTO added to `schemas.py` (immutable; keyed by
      `(task_id, step_id)`; carries `idempotency_key`, `status`, `ended_at`).
- [x] `CheckpointStore` protocol in `executor.py` with `save(checkpoint)`,
      `load(task_id, step_id) -> ExecutorCheckpoint | None`, and `list_for_task(task_id)`.
- [x] `InMemoryCheckpointStore` concrete implementation.
- [x] `InMemoryExecutor` accepts optional `checkpoint_store: CheckpointStore`; writes a
      checkpoint after each terminal step; skips execution when an existing
      terminal checkpoint is found.
- [x] `checkpoints` table added to `storage/tables.py`.
- [x] `SQLCheckpointStore` in `storage/store.py` implementing `CheckpointStore`.
- [x] Alembic migration `0002` adds the checkpoints table.
- [x] `tests/unit/test_executor_checkpoints.py` (17 tests: 6 InMemoryCheckpointStore, 6 executor integration, 5 SQLCheckpointStore).
- [x] 378 backend tests passing, 100% coverage across 18 modules.

## Out of Scope

- Async SQLAlchemy.
- Run artifact persistence (separate spec).
- Stage 3 (Temporal/Prefect).
