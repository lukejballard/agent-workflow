"""SQLAlchemy Core-backed runtime store.

``SQLRuntimeStore`` exposes the same ``tasks``, ``plans``, and ``events``
attributes as the in-memory ``RuntimeStore`` dataclass, but persists every
write to a relational database.  All writes are idempotent: an UPDATE is
attempted first; if no rows are affected an INSERT follows, guaranteeing safe
retries without duplicate-key errors.
"""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping

import sqlalchemy as sa
from sqlalchemy import Engine

from agent_runtime.events import AgentEvent
from agent_runtime.schemas import ExecutorCheckpoint, Plan, Task
from agent_runtime.storage.tables import checkpoints_table, events_table, plans_table, tasks_table


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _upsert(
    conn: sa.Connection,
    table: sa.Table,
    pk_col: str,
    pk_val: str,
    row: dict[str, object],
) -> None:
    """Update an existing row or insert a new one (portable upsert).

    Attempts an UPDATE first.  If ``rowcount`` is 0 there was nothing to
    update and a fresh INSERT is executed instead.  Both operations run
    inside the caller's transaction.
    """
    result = conn.execute(
        sa.update(table).where(table.c[pk_col] == pk_val).values(**row)
    )
    if result.rowcount == 0:
        conn.execute(sa.insert(table).values(**{pk_col: pk_val, **row}))


# ---------------------------------------------------------------------------
# MutableMapping views
# ---------------------------------------------------------------------------


class _TaskView(MutableMapping[str, Task]):
    """Dict-like view over the ``tasks`` table."""

    __slots__ = ("_engine",)

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def __getitem__(self, key: str) -> Task:
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(tasks_table.c.data).where(tasks_table.c.task_id == key)
            ).one_or_none()
        if row is None:
            raise KeyError(key)
        return Task.model_validate_json(row.data)

    def __setitem__(self, key: str, value: Task) -> None:
        with self._engine.begin() as conn:
            _upsert(
                conn,
                tasks_table,
                "task_id",
                key,
                {"data": value.model_dump_json(), "updated_at": value.updated_at.isoformat()},
            )

    def __delitem__(self, key: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.delete(tasks_table).where(tasks_table.c.task_id == key))

    def __iter__(self) -> Iterator[str]:
        with self._engine.connect() as conn:
            rows = conn.execute(sa.select(tasks_table.c.task_id)).all()
        return iter(row.task_id for row in rows)

    def __len__(self) -> int:
        with self._engine.connect() as conn:
            return conn.execute(
                sa.select(sa.func.count()).select_from(tasks_table)
            ).scalar_one()

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(tasks_table.c.task_id).where(tasks_table.c.task_id == key)
            ).one_or_none()
        return row is not None


class _PlanView(MutableMapping[str, Plan]):
    """Dict-like view over the ``plans`` table."""

    __slots__ = ("_engine",)

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def __getitem__(self, key: str) -> Plan:
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(plans_table.c.data).where(plans_table.c.task_id == key)
            ).one_or_none()
        if row is None:
            raise KeyError(key)
        return Plan.model_validate_json(row.data)

    def __setitem__(self, key: str, value: Plan) -> None:
        with self._engine.begin() as conn:
            _upsert(conn, plans_table, "task_id", key, {"data": value.model_dump_json()})

    def __delitem__(self, key: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.delete(plans_table).where(plans_table.c.task_id == key))

    def __iter__(self) -> Iterator[str]:
        with self._engine.connect() as conn:
            rows = conn.execute(sa.select(plans_table.c.task_id)).all()
        return iter(row.task_id for row in rows)

    def __len__(self) -> int:
        with self._engine.connect() as conn:
            return conn.execute(
                sa.select(sa.func.count()).select_from(plans_table)
            ).scalar_one()

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(plans_table.c.task_id).where(plans_table.c.task_id == key)
            ).one_or_none()
        return row is not None


class _EventListView(MutableMapping[str, list[AgentEvent]]):
    """Dict-like view over the ``events`` table, keyed by task_id.

    A ``__setitem__`` call atomically replaces all events for the given task
    (DELETE existing rows then INSERT the new list).  ``__getitem__`` raises
    ``KeyError`` when no events exist for the key, so ``store.events.get(id, [])``
    returns ``[]`` for tasks with no recorded events.
    """

    __slots__ = ("_engine",)

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def __getitem__(self, key: str) -> list[AgentEvent]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                sa.select(events_table.c.data)
                .where(events_table.c.task_id == key)
                .order_by(events_table.c.sequence)
            ).all()
        if not rows:
            raise KeyError(key)
        return [AgentEvent.model_validate_json(row.data) for row in rows]

    def __setitem__(self, key: str, value: list[AgentEvent]) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.delete(events_table).where(events_table.c.task_id == key))
            for event in value:
                conn.execute(
                    sa.insert(events_table).values(
                        event_id=event.event_id,
                        task_id=key,
                        sequence=event.sequence,
                        occurred_at=event.occurred_at.isoformat(),
                        data=event.model_dump_json(),
                    )
                )

    def __delitem__(self, key: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(sa.delete(events_table).where(events_table.c.task_id == key))

    def __iter__(self) -> Iterator[str]:
        with self._engine.connect() as conn:
            rows = conn.execute(sa.select(events_table.c.task_id).distinct()).all()
        return iter(row.task_id for row in rows)

    def __len__(self) -> int:
        with self._engine.connect() as conn:
            return conn.execute(
                sa.select(sa.func.count(events_table.c.task_id.distinct()))
            ).scalar_one()

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(events_table.c.task_id).where(events_table.c.task_id == key)
            ).one_or_none()
        return row is not None


# ---------------------------------------------------------------------------
# Public store
# ---------------------------------------------------------------------------


class SQLRuntimeStore:
    """SQLAlchemy Core-backed runtime store.

    Exposes the same ``tasks``, ``plans``, and ``events`` attributes as the
    in-memory ``RuntimeStore`` dataclass so that both implementations are
    drop-in replacements through FastAPI's DI system.
    """

    def __init__(self, engine: Engine) -> None:
        self.tasks: _TaskView = _TaskView(engine)
        self.plans: _PlanView = _PlanView(engine)
        self.events: _EventListView = _EventListView(engine)


# ---------------------------------------------------------------------------
# SQL checkpoint store
# ---------------------------------------------------------------------------


class SQLCheckpointStore:
    """SQLAlchemy Core-backed ``CheckpointStore``.

    Implements the same interface as ``InMemoryCheckpointStore`` so the two
    implementations are transparent to ``InMemoryExecutor``.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, checkpoint: ExecutorCheckpoint) -> None:  # noqa: D401
        """Persist *checkpoint*, replacing any existing row with the same key."""
        with self._engine.begin() as conn:
            result = conn.execute(
                sa.update(checkpoints_table)
                .where(
                    checkpoints_table.c.task_id == checkpoint.task_id,
                    checkpoints_table.c.step_id == checkpoint.step_id,
                )
                .values(
                    idempotency_key=checkpoint.idempotency_key,
                    status=checkpoint.status.value,
                    ended_at=checkpoint.ended_at.isoformat(),
                )
            )
            if result.rowcount == 0:
                conn.execute(
                    sa.insert(checkpoints_table).values(
                        task_id=checkpoint.task_id,
                        step_id=checkpoint.step_id,
                        idempotency_key=checkpoint.idempotency_key,
                        status=checkpoint.status.value,
                        ended_at=checkpoint.ended_at.isoformat(),
                    )
                )

    def load(self, task_id: str, step_id: str) -> ExecutorCheckpoint | None:
        """Return the checkpoint for *(task_id, step_id)*, or ``None``."""
        with self._engine.connect() as conn:
            row = conn.execute(
                sa.select(checkpoints_table).where(
                    checkpoints_table.c.task_id == task_id,
                    checkpoints_table.c.step_id == step_id,
                )
            ).one_or_none()
        if row is None:
            return None
        from datetime import datetime, timezone
        from agent_runtime.schemas import StepExecutionStatus
        return ExecutorCheckpoint(
            task_id=row.task_id,
            step_id=row.step_id,
            idempotency_key=row.idempotency_key,
            status=StepExecutionStatus(row.status),
            ended_at=datetime.fromisoformat(row.ended_at).replace(tzinfo=timezone.utc),
        )

    def list_for_task(self, task_id: str) -> list[ExecutorCheckpoint]:
        """Return all checkpoints for *task_id*, ordered by ``ended_at``."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                sa.select(checkpoints_table)
                .where(checkpoints_table.c.task_id == task_id)
                .order_by(checkpoints_table.c.ended_at)
            ).all()
        from datetime import datetime, timezone
        from agent_runtime.schemas import StepExecutionStatus
        return [
            ExecutorCheckpoint(
                task_id=row.task_id,
                step_id=row.step_id,
                idempotency_key=row.idempotency_key,
                status=StepExecutionStatus(row.status),
                ended_at=datetime.fromisoformat(row.ended_at).replace(tzinfo=timezone.utc),
            )
            for row in rows
        ]
