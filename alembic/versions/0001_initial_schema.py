"""Initial schema — create tasks, plans, and events tables.

Revision ID: 0001
Revises:
Create Date: 2026-04-18

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("task_id", sa.Text, primary_key=True),
        sa.Column("data", sa.Text, nullable=False),
        sa.Column("updated_at", sa.Text, nullable=False),
    )
    op.create_table(
        "plans",
        sa.Column("task_id", sa.Text, primary_key=True),
        sa.Column("data", sa.Text, nullable=False),
    )
    op.create_table(
        "events",
        sa.Column("event_id", sa.Text, primary_key=True),
        sa.Column("task_id", sa.Text, nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("occurred_at", sa.Text, nullable=False),
        sa.Column("data", sa.Text, nullable=False),
    )
    op.create_index("ix_events_task_id", "events", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_events_task_id", table_name="events")
    op.drop_table("events")
    op.drop_table("plans")
    op.drop_table("tasks")
