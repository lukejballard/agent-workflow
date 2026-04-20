"""Step executor with idempotency tracking and optional checkpoint/resume."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable, Protocol, runtime_checkable

from agent_runtime.schemas import (
    ExecutionRecord,
    ExecutorCheckpoint,
    Plan,
    PlanStep,
    StepExecutionStatus,
)

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

# A handler receives the PlanStep and returns (status, output, error).
StepHandlerFn = Callable[
    [PlanStep],
    tuple[StepExecutionStatus, str | None, str | None],
]

_TERMINAL_STATUSES: frozenset[StepExecutionStatus] = frozenset(
    {StepExecutionStatus.DONE, StepExecutionStatus.FAILED}
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ExecutorError(Exception):
    """Raised when the executor cannot process the requested step."""


# ---------------------------------------------------------------------------
# CheckpointStore protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class CheckpointStore(Protocol):
    """Write/read executor checkpoints so completed steps survive restarts."""

    def save(self, checkpoint: ExecutorCheckpoint) -> None:
        """Persist *checkpoint*, replacing any existing entry for the same key."""
        ...

    def load(self, task_id: str, step_id: str) -> ExecutorCheckpoint | None:
        """Return the checkpoint for *(task_id, step_id)*, or ``None``."""
        ...

    def list_for_task(self, task_id: str) -> list[ExecutorCheckpoint]:
        """Return all checkpoints for *task_id*, ordered by ``ended_at``."""
        ...


# ---------------------------------------------------------------------------
# InMemoryCheckpointStore
# ---------------------------------------------------------------------------


class InMemoryCheckpointStore:
    """In-process checkpoint store for testing and local development."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], ExecutorCheckpoint] = {}

    def save(self, checkpoint: ExecutorCheckpoint) -> None:
        self._store[(checkpoint.task_id, checkpoint.step_id)] = checkpoint

    def load(self, task_id: str, step_id: str) -> ExecutorCheckpoint | None:
        return self._store.get((task_id, step_id))

    def list_for_task(self, task_id: str) -> list[ExecutorCheckpoint]:
        results = [cp for (tid, _), cp in self._store.items() if tid == task_id]
        return sorted(results, key=lambda cp: cp.ended_at)


class InMemoryExecutor:
    """Executes plan steps and deduplicates calls by idempotency key.

    If a step has already reached a terminal state (DONE or FAILED) under a
    given *idempotency_key*, subsequent calls with that key are no-ops and
    return the existing record without invoking the handler again.

    When a *checkpoint_store* is supplied the executor writes an
    ``ExecutorCheckpoint`` after each terminal step and consults the store
    before executing so that already-completed steps are skipped on restart.
    This means a fresh ``InMemoryExecutor`` instance (as created after a
    process restart) will skip any step that already has a terminal checkpoint.
    """

    def __init__(self, checkpoint_store: CheckpointStore | None = None) -> None:
        self._records: dict[str, ExecutionRecord] = {}
        self._checkpoint_store = checkpoint_store

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_from_checkpoint(
        self,
        checkpoint: ExecutorCheckpoint,
        step: PlanStep,
        task_id: str,
        trace_id: str,
    ) -> ExecutionRecord:
        """Reconstruct a minimal ``ExecutionRecord`` from a checkpoint."""
        return ExecutionRecord(
            idempotency_key=checkpoint.idempotency_key,
            step_id=step.step_id,
            task_id=task_id,
            trace_id=trace_id,
            status=checkpoint.status,
            started_at=checkpoint.ended_at,
            ended_at=checkpoint.ended_at,
        )

    def _write_checkpoint(self, record: ExecutionRecord) -> None:
        if self._checkpoint_store is None or record.ended_at is None:
            return
        self._checkpoint_store.save(
            ExecutorCheckpoint(
                task_id=record.task_id,
                step_id=record.step_id,
                idempotency_key=record.idempotency_key,
                status=record.status,
                ended_at=record.ended_at,
            )
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        plan: Plan,
        step_id: str,
        idempotency_key: str,
        handler: StepHandlerFn,
        trace_id: str = "",
    ) -> ExecutionRecord:
        """Execute *step_id* from *plan* using *handler*.

        Args:
            plan: The plan containing the step.
            step_id: ID of the step to execute.
            idempotency_key: Unique key for deduplication. Repeated calls with
                the same key and a terminal prior outcome are no-ops.
            handler: Callable that performs the actual work.
            trace_id: Correlation identifier injected into the record.

        Returns:
            The ``ExecutionRecord`` for this invocation (possibly from cache
            or from a persisted checkpoint).

        Raises:
            ExecutorError: if *step_id* is not found in *plan*.
        """
        # 1. In-memory cache hit.
        existing = self._records.get(idempotency_key)
        if existing is not None and existing.status in _TERMINAL_STATUSES:
            return existing

        step = next((s for s in plan.steps if s.step_id == step_id), None)
        if step is None:
            raise ExecutorError(
                f"Step {step_id!r} not found in plan {plan.plan_id!r}"
            )

        resolved_trace = trace_id or str(uuid.uuid4())

        # 2. Durable checkpoint hit -- skip re-execution on restart.
        if self._checkpoint_store is not None:
            checkpoint = self._checkpoint_store.load(plan.task_id, step_id)
            if checkpoint is not None and checkpoint.status in _TERMINAL_STATUSES:
                record = self._load_from_checkpoint(checkpoint, step, plan.task_id, resolved_trace)
                self._records[idempotency_key] = record
                return record

        started_at = datetime.now(timezone.utc)

        try:
            status, output, error = handler(step)
        except Exception as exc:  # Catch-all: record failure for all handler errors.
            record = ExecutionRecord(
                idempotency_key=idempotency_key,
                step_id=step_id,
                task_id=plan.task_id,
                trace_id=resolved_trace,
                status=StepExecutionStatus.FAILED,
                output=None,
                error=str(exc),
                started_at=started_at,
                ended_at=datetime.now(timezone.utc),
            )
            self._records[idempotency_key] = record
            self._write_checkpoint(record)
            return record

        record = ExecutionRecord(
            idempotency_key=idempotency_key,
            step_id=step_id,
            task_id=plan.task_id,
            trace_id=resolved_trace,
            status=status,
            output=output,
            error=error,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
        )
        self._records[idempotency_key] = record
        self._write_checkpoint(record)
        return record

    def get_record(self, idempotency_key: str) -> ExecutionRecord | None:
        """Return the stored record for *idempotency_key*, or None."""
        return self._records.get(idempotency_key)
