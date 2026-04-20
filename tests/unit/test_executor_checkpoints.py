"""Tests for executor checkpoint / resume — InMemoryCheckpointStore and
SQLCheckpointStore, plus InMemoryExecutor checkpoint integration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import Engine

from agent_runtime.executor import (
    CheckpointStore,
    ExecutorError,
    InMemoryCheckpointStore,
    InMemoryExecutor,
)
from agent_runtime.schemas import (
    ExecutorCheckpoint,
    Plan,
    PlanStep,
    StepExecutionStatus,
)
from agent_runtime.storage.db import create_engine_from_url
from agent_runtime.storage.store import SQLCheckpointStore
from agent_runtime.storage.tables import metadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _step(step_id: str) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        title=f"Step {step_id}",
        input_contract="none",
        output_contract="none",
        done_condition="always",
    )


def _plan(*step_ids: str) -> Plan:
    return Plan(
        plan_id=str(uuid.uuid4()),
        task_id="task-cp",
        steps=[_step(sid) for sid in step_ids],
    )


def _checkpoint(
    task_id: str = "task-cp",
    step_id: str = "s1",
    status: StepExecutionStatus = StepExecutionStatus.DONE,
) -> ExecutorCheckpoint:
    return ExecutorCheckpoint(
        task_id=task_id,
        step_id=step_id,
        idempotency_key=f"{task_id}:{step_id}",
        status=status,
        ended_at=datetime.now(timezone.utc),
    )


def _success(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    return StepExecutionStatus.DONE, "ok", None


def _fail(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    return StepExecutionStatus.FAILED, None, "oops"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sql_engine() -> Engine:
    eng = create_engine_from_url("sqlite:///:memory:")
    metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def sql_cp(sql_engine: Engine) -> SQLCheckpointStore:
    return SQLCheckpointStore(sql_engine)


# ---------------------------------------------------------------------------
# InMemoryCheckpointStore
# ---------------------------------------------------------------------------


def test_in_memory_store_save_and_load() -> None:
    store = InMemoryCheckpointStore()
    cp = _checkpoint()
    store.save(cp)
    loaded = store.load(cp.task_id, cp.step_id)
    assert loaded is not None
    assert loaded.step_id == cp.step_id


def test_in_memory_store_load_missing_returns_none() -> None:
    store = InMemoryCheckpointStore()
    assert store.load("t1", "missing") is None


def test_in_memory_store_save_overwrites_existing() -> None:
    store = InMemoryCheckpointStore()
    cp1 = _checkpoint(status=StepExecutionStatus.FAILED)
    cp2 = _checkpoint(status=StepExecutionStatus.DONE)
    store.save(cp1)
    store.save(cp2)
    loaded = store.load(cp2.task_id, cp2.step_id)
    assert loaded is not None
    assert loaded.status == StepExecutionStatus.DONE


def test_in_memory_store_list_for_task_empty() -> None:
    store = InMemoryCheckpointStore()
    assert store.list_for_task("t1") == []


def test_in_memory_store_list_for_task_filters_by_task() -> None:
    store = InMemoryCheckpointStore()
    store.save(_checkpoint("t1", "s1"))
    store.save(_checkpoint("t2", "s1"))
    assert len(store.list_for_task("t1")) == 1
    assert store.list_for_task("t1")[0].task_id == "t1"


def test_in_memory_store_implements_protocol() -> None:
    store = InMemoryCheckpointStore()
    assert isinstance(store, CheckpointStore)


# ---------------------------------------------------------------------------
# InMemoryExecutor + checkpoint integration
# ---------------------------------------------------------------------------


def test_executor_writes_checkpoint_on_success() -> None:
    cp_store = InMemoryCheckpointStore()
    executor = InMemoryExecutor(checkpoint_store=cp_store)
    plan = _plan("s1")
    executor.execute(plan, "s1", "key-1", _success)
    assert cp_store.load("task-cp", "s1") is not None


def test_executor_writes_checkpoint_on_failure() -> None:
    cp_store = InMemoryCheckpointStore()
    executor = InMemoryExecutor(checkpoint_store=cp_store)
    plan = _plan("s1")
    executor.execute(plan, "s1", "key-1", _fail)
    cp = cp_store.load("task-cp", "s1")
    assert cp is not None
    assert cp.status == StepExecutionStatus.FAILED


def test_executor_skips_step_with_terminal_checkpoint() -> None:
    """A new executor instance with an existing checkpoint must not call the handler."""
    cp_store = InMemoryCheckpointStore()
    cp_store.save(_checkpoint("task-cp", "s1", StepExecutionStatus.DONE))

    call_count = 0

    def counting_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
        nonlocal call_count
        call_count += 1
        return StepExecutionStatus.DONE, "late", None

    executor = InMemoryExecutor(checkpoint_store=cp_store)
    plan = _plan("s1")
    executor.execute(plan, "s1", "key-new", counting_handler)
    assert call_count == 0


def test_executor_resumes_from_checkpoint_returns_done() -> None:
    cp_store = InMemoryCheckpointStore()
    cp_store.save(_checkpoint("task-cp", "s1", StepExecutionStatus.DONE))
    executor = InMemoryExecutor(checkpoint_store=cp_store)
    plan = _plan("s1")
    record = executor.execute(plan, "s1", "key-new", _fail)
    assert record.status == StepExecutionStatus.DONE


def test_executor_without_checkpoint_store_executes_normally() -> None:
    executor = InMemoryExecutor()  # no checkpoint store
    plan = _plan("s1")
    record = executor.execute(plan, "s1", "key-1", _success)
    assert record.status == StepExecutionStatus.DONE


def test_executor_writes_checkpoint_on_handler_exception() -> None:
    cp_store = InMemoryCheckpointStore()
    executor = InMemoryExecutor(checkpoint_store=cp_store)
    plan = _plan("s1")

    def exploding(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
        raise RuntimeError("boom")

    executor.execute(plan, "s1", "key-1", exploding)
    cp = cp_store.load("task-cp", "s1")
    assert cp is not None
    assert cp.status == StepExecutionStatus.FAILED


# ---------------------------------------------------------------------------
# SQLCheckpointStore
# ---------------------------------------------------------------------------


def test_sql_cp_save_and_load(sql_cp: SQLCheckpointStore) -> None:
    cp = _checkpoint()
    sql_cp.save(cp)
    loaded = sql_cp.load(cp.task_id, cp.step_id)
    assert loaded is not None
    assert loaded.step_id == cp.step_id
    assert loaded.status == StepExecutionStatus.DONE


def test_sql_cp_load_missing_returns_none(sql_cp: SQLCheckpointStore) -> None:
    assert sql_cp.load("t1", "missing") is None


def test_sql_cp_save_overwrites_existing(sql_cp: SQLCheckpointStore) -> None:
    sql_cp.save(_checkpoint(status=StepExecutionStatus.FAILED))
    sql_cp.save(_checkpoint(status=StepExecutionStatus.DONE))
    loaded = sql_cp.load("task-cp", "s1")
    assert loaded is not None
    assert loaded.status == StepExecutionStatus.DONE


def test_sql_cp_list_for_task(sql_cp: SQLCheckpointStore) -> None:
    sql_cp.save(_checkpoint("t1", "s1"))
    sql_cp.save(_checkpoint("t1", "s2"))
    sql_cp.save(_checkpoint("t2", "s1"))
    results = sql_cp.list_for_task("t1")
    assert len(results) == 2
    assert all(cp.task_id == "t1" for cp in results)


def test_sql_cp_list_for_task_empty(sql_cp: SQLCheckpointStore) -> None:
    assert sql_cp.list_for_task("nobody") == []
