"""SQLAlchemy engine factory for the agent runtime storage layer."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import Engine


def create_engine_from_url(url: str) -> Engine:
    """Create a SQLAlchemy engine from a connection URL.

    Adds ``check_same_thread=False`` for SQLite so FastAPI's multi-threaded
    request pool can share the connection without raising threading errors.
    """
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return sa.create_engine(url, connect_args=connect_args)
