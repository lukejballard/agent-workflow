"""Add checkpoints table for executor step-level checkpoint/resume.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-18

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checkpoints",
        sa.Column("task_id", sa.Text, nullable=False),
        sa.Column("step_id", sa.Text, nullable=False),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("ended_at", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("task_id", "step_id", name="pk_checkpoints"),
    )
    op.create_index("ix_checkpoints_task_id", "checkpoints", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_checkpoints_task_id", table_name="checkpoints")
    op.drop_table("checkpoints")
