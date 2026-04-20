"""SQLAlchemy Core table definitions for the agent runtime storage layer.

All tables share a single ``MetaData`` instance so that ``metadata.create_all``
and Alembic autogenerate work correctly.
"""

from __future__ import annotations

import sqlalchemy as sa

metadata = sa.MetaData()

tasks_table = sa.Table(
    "tasks",
    metadata,
    sa.Column("task_id", sa.Text, primary_key=True),
    sa.Column("data", sa.Text, nullable=False),
    sa.Column("updated_at", sa.Text, nullable=False),
)

plans_table = sa.Table(
    "plans",
    metadata,
    sa.Column("task_id", sa.Text, primary_key=True),
    sa.Column("data", sa.Text, nullable=False),
)

events_table = sa.Table(
    "events",
    metadata,
    sa.Column("event_id", sa.Text, primary_key=True),
    sa.Column("task_id", sa.Text, nullable=False),
    sa.Column("sequence", sa.Integer, nullable=False),
    sa.Column("occurred_at", sa.Text, nullable=False),
    sa.Column("data", sa.Text, nullable=False),
)

# Explicit index for the most common query pattern: lookup events by task.
sa.Index("ix_events_task_id", events_table.c.task_id)

checkpoints_table = sa.Table(
    "checkpoints",
    metadata,
    sa.Column("task_id", sa.Text, nullable=False),
    sa.Column("step_id", sa.Text, nullable=False),
    sa.Column("idempotency_key", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("ended_at", sa.Text, nullable=False),
    sa.PrimaryKeyConstraint("task_id", "step_id", name="pk_checkpoints"),
)

sa.Index("ix_checkpoints_task_id", checkpoints_table.c.task_id)
