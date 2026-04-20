"""Structured logging helpers with contextvars-based correlation field injection.

Usage
-----
    from agent_runtime.observability import CorrelationContext, correlation_context, get_logger

    logger = get_logger(__name__)

    with correlation_context(CorrelationContext(trace_id="abc", task_id="task-1")):
        logger.info("step started")   # record will carry trace_id, task_id, etc.
"""

from __future__ import annotations

import contextvars
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


# ---------------------------------------------------------------------------
# Correlation context data class
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CorrelationContext:
    """Immutable correlation identifiers injected into every log record."""

    trace_id: str
    run_id: str | None = None
    task_id: str | None = None
    step_id: str | None = None
    tool_call_id: str | None = None


# ---------------------------------------------------------------------------
# ContextVar storage
# ---------------------------------------------------------------------------

_correlation: contextvars.ContextVar[CorrelationContext | None] = contextvars.ContextVar(
    "agent_runtime_correlation", default=None
)


@contextmanager
def correlation_context(ctx: CorrelationContext) -> Iterator[None]:
    """Set the active correlation context for the current async/thread context.

    Resets to the previous context on exit, making nesting safe.
    """
    token = _correlation.set(ctx)
    try:
        yield
    finally:
        _correlation.reset(token)


def get_correlation() -> CorrelationContext | None:
    """Return the currently active correlation context, or None."""
    return _correlation.get()


# ---------------------------------------------------------------------------
# Logging filter
# ---------------------------------------------------------------------------


class CorrelationFilter(logging.Filter):
    """Reads the active CorrelationContext from a contextvar and injects its
    fields into every log record as attributes.

    Fields added:
        trace_id, run_id, task_id, step_id, tool_call_id
    """

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _correlation.get()
        record.trace_id = ctx.trace_id if ctx else None
        record.run_id = ctx.run_id if ctx else None
        record.task_id = ctx.task_id if ctx else None
        record.step_id = ctx.step_id if ctx else None
        record.tool_call_id = ctx.tool_call_id if ctx else None
        return True


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with a CorrelationFilter attached.

    Idempotent — calling this multiple times with the same *name* will not
    attach duplicate filters.
    """
    logger = logging.getLogger(name)
    if not any(isinstance(f, CorrelationFilter) for f in logger.filters):
        logger.addFilter(CorrelationFilter())
    return logger
