"""Tests for the SQLAlchemy Core-backed runtime store.

All tests use an in-memory SQLite database so they run without any external
service and remain isolated from each other.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import call, patch

import pytest
from sqlalchemy import Engine

from agent_runtime.events import AgentEvent, EventType
from agent_runtime.schemas import Plan, PlanStep, Task, TaskState
from agent_runtime.storage.db import create_engine_from_url
from agent_runtime.storage.store import SQLRuntimeStore
from agent_runtime.storage.tables import metadata


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine() -> Engine:
    """Fresh in-memory SQLite engine with all tables created."""
    eng = create_engine_from_url("sqlite:///:memory:")
    metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def store(engine: Engine) -> SQLRuntimeStore:
    return SQLRuntimeStore(engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(task_id: str = "t1", objective: str = "test") -> Task:
    now = datetime.now(timezone.utc)
    return Task(
        task_id=task_id,
        objective=objective,
        state=TaskState.PENDING,
        trace_id="trace-1",
        created_at=now,
        updated_at=now,
    )


def _make_plan(task_id: str = "t1") -> Plan:
    step = PlanStep(
        step_id="s1",
        title="Step 1",
        depends_on=[],
        input_contract="none",
        output_contract="none",
        done_condition="done",
    )
    return Plan(plan_id=str(uuid.uuid4()), task_id=task_id, steps=[step])


def _make_event(task_id: str = "t1", sequence: int = 0) -> AgentEvent:
    return AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.TASK_STATE_TRANSITION,
        trace_id="trace-1",
        task_id=task_id,
        occurred_at=datetime.now(timezone.utc),
        sequence=sequence,
        payload={"from": "PENDING", "to": "PLANNING"},
    )


# ---------------------------------------------------------------------------
# engine factory tests
# ---------------------------------------------------------------------------


def test_engine_factory_sqlite_sets_check_same_thread() -> None:
    with patch("agent_runtime.storage.db.sa.create_engine") as mock_create:
        create_engine_from_url("sqlite:///test.db")
    _, kwargs = mock_create.call_args
    assert kwargs["connect_args"]["check_same_thread"] is False


# ---------------------------------------------------------------------------
# Task view tests
# ---------------------------------------------------------------------------


def test_task_set_and_get(store: SQLRuntimeStore) -> None:
    task = _make_task()
    store.tasks[task.task_id] = task
    retrieved = store.tasks[task.task_id]
    assert retrieved.task_id == task.task_id
    assert retrieved.objective == task.objective


def test_task_contains_true(store: SQLRuntimeStore) -> None:
    task = _make_task()
    store.tasks[task.task_id] = task
    assert task.task_id in store.tasks


def test_task_contains_false(store: SQLRuntimeStore) -> None:
    assert "missing" not in store.tasks


def test_task_get_missing_returns_none(store: SQLRuntimeStore) -> None:
    assert store.tasks.get("missing") is None


def test_task_get_with_default(store: SQLRuntimeStore) -> None:
    sentinel = _make_task("sentinel")
    assert store.tasks.get("missing", sentinel) is sentinel


def test_task_getitem_missing_raises_key_error(store: SQLRuntimeStore) -> None:
    with pytest.raises(KeyError):
        _ = store.tasks["does-not-exist"]


def test_task_upsert_updates_existing(store: SQLRuntimeStore) -> None:
    task = _make_task()
    store.tasks[task.task_id] = task
    updated = task.model_copy(update={"objective": "updated"})
    store.tasks[task.task_id] = updated
    assert store.tasks[task.task_id].objective == "updated"


def test_task_upsert_no_duplicate_row(store: SQLRuntimeStore) -> None:
    task = _make_task()
    store.tasks[task.task_id] = task
    store.tasks[task.task_id] = task  # second write same key
    assert len(store.tasks) == 1


def test_task_list_values(store: SQLRuntimeStore) -> None:
    t1, t2 = _make_task("t1"), _make_task("t2")
    store.tasks["t1"] = t1
    store.tasks["t2"] = t2
    ids = {t.task_id for t in store.tasks.values()}
    assert ids == {"t1", "t2"}


def test_task_iter(store: SQLRuntimeStore) -> None:
    store.tasks["t1"] = _make_task("t1")
    store.tasks["t2"] = _make_task("t2")
    assert set(store.tasks) == {"t1", "t2"}


def test_task_contains_non_string_returns_false(store: SQLRuntimeStore) -> None:
    assert (123 in store.tasks) is False  # type: ignore[operator]


def test_task_len(store: SQLRuntimeStore) -> None:
    assert len(store.tasks) == 0
    store.tasks["t1"] = _make_task("t1")
    assert len(store.tasks) == 1


# ---------------------------------------------------------------------------
# Plan view tests
# ---------------------------------------------------------------------------


def test_plan_set_and_get(store: SQLRuntimeStore) -> None:
    plan = _make_plan()
    store.plans[plan.task_id] = plan
    retrieved = store.plans[plan.task_id]
    assert retrieved.plan_id == plan.plan_id
    assert len(retrieved.steps) == 1


def test_plan_get_missing_returns_none(store: SQLRuntimeStore) -> None:
    assert store.plans.get("missing") is None


def test_plan_upsert_replaces(store: SQLRuntimeStore) -> None:
    plan = _make_plan()
    store.plans["t1"] = plan
    new_plan = plan.model_copy(update={"revision": 2})
    store.plans["t1"] = new_plan
    assert store.plans["t1"].revision == 2
    assert len(store.plans) == 1


def test_plan_contains(store: SQLRuntimeStore) -> None:
    plan = _make_plan()
    store.plans["t1"] = plan
    assert "t1" in store.plans
    assert "t2" not in store.plans


# ---------------------------------------------------------------------------
# Event list view tests
# ---------------------------------------------------------------------------


def test_events_set_and_get(store: SQLRuntimeStore) -> None:
    events = [_make_event("t1", 0), _make_event("t1", 1)]
    store.events["t1"] = events
    retrieved = store.events["t1"]
    assert len(retrieved) == 2
    assert retrieved[0].sequence == 0
    assert retrieved[1].sequence == 1


def test_events_get_missing_returns_empty_list(store: SQLRuntimeStore) -> None:
    assert store.events.get("missing", []) == []


def test_events_getitem_missing_raises_key_error(store: SQLRuntimeStore) -> None:
    with pytest.raises(KeyError):
        _ = store.events["no-events"]


def test_events_setitem_replaces_existing(store: SQLRuntimeStore) -> None:
    store.events["t1"] = [_make_event("t1", 0)]
    replacement = [_make_event("t1", 0), _make_event("t1", 1)]
    store.events["t1"] = replacement
    assert len(store.events["t1"]) == 2


def test_events_contains(store: SQLRuntimeStore) -> None:
    store.events["t1"] = [_make_event("t1", 0)]
    assert "t1" in store.events
    assert "t2" not in store.events


def test_events_len_counts_distinct_tasks(store: SQLRuntimeStore) -> None:
    store.events["t1"] = [_make_event("t1", 0), _make_event("t1", 1)]
    store.events["t2"] = [_make_event("t2", 0)]
    assert len(store.events) == 2


def test_events_ordered_by_sequence(store: SQLRuntimeStore) -> None:
    # Insert in reverse order to verify ORDER BY sequence is applied.
    store.events["t1"] = [_make_event("t1", 2), _make_event("t1", 0), _make_event("t1", 1)]
    seqs = [e.sequence for e in store.events["t1"]]
    assert seqs == [0, 1, 2]


# ---------------------------------------------------------------------------
# __delitem__ tests (covers missing store.py lines)
# ---------------------------------------------------------------------------


def test_task_delitem_removes_row(store: SQLRuntimeStore) -> None:
    store.tasks["t1"] = _make_task("t1")
    del store.tasks["t1"]
    assert "t1" not in store.tasks


def test_plan_delitem_removes_row(store: SQLRuntimeStore) -> None:
    store.plans["t1"] = _make_plan("t1")
    del store.plans["t1"]
    assert "t1" not in store.plans


def test_events_delitem_removes_rows(store: SQLRuntimeStore) -> None:
    store.events["t1"] = [_make_event("t1", 0)]
    del store.events["t1"]
    assert "t1" not in store.events


# ---------------------------------------------------------------------------
# _PlanView __iter__ and __len__ (covers missing plan view lines)
# ---------------------------------------------------------------------------


def test_plan_iter(store: SQLRuntimeStore) -> None:
    store.plans["t1"] = _make_plan("t1")
    store.plans["t2"] = _make_plan("t2")
    assert set(store.plans) == {"t1", "t2"}


def test_plan_len(store: SQLRuntimeStore) -> None:
    assert len(store.plans) == 0
    store.plans["t1"] = _make_plan("t1")
    assert len(store.plans) == 1


def test_plan_contains_non_string_returns_false(store: SQLRuntimeStore) -> None:
    assert (123 in store.plans) is False  # type: ignore[operator]


# ---------------------------------------------------------------------------
# _EventListView __iter__ (covers missing event view lines)
# ---------------------------------------------------------------------------


def test_events_iter(store: SQLRuntimeStore) -> None:
    store.events["t1"] = [_make_event("t1", 0)]
    store.events["t2"] = [_make_event("t2", 0)]
    assert set(store.events) == {"t1", "t2"}


def test_events_contains_non_string_returns_false(store: SQLRuntimeStore) -> None:
    assert (123 in store.events) is False  # type: ignore[operator]


# ---------------------------------------------------------------------------
# configure_store (covers routes.py line 61)
# ---------------------------------------------------------------------------


def test_configure_store_replaces_default(store: SQLRuntimeStore) -> None:
    from agent_runtime.routes import RuntimeStore, configure_store

    original = RuntimeStore()
    configure_store(store)
    from agent_runtime import routes

    assert routes._default_store is store
    # Restore to avoid polluting other tests.
    configure_store(original)
