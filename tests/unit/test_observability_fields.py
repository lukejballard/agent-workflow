"""Tests for agent_runtime.observability."""

from __future__ import annotations

import logging

import pytest

from agent_runtime.observability import (
    CorrelationContext,
    CorrelationFilter,
    correlation_context,
    get_correlation,
    get_logger,
)


def _make_record() -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )


# ---------------------------------------------------------------------------
# CorrelationFilter — with active context
# ---------------------------------------------------------------------------


def test_filter_injects_trace_id() -> None:
    ctx = CorrelationContext(trace_id="trace-abc")
    with correlation_context(ctx):
        record = _make_record()
        CorrelationFilter().filter(record)
        assert record.trace_id == "trace-abc"


def test_filter_injects_run_id() -> None:
    ctx = CorrelationContext(trace_id="t", run_id="run-xyz")
    with correlation_context(ctx):
        record = _make_record()
        CorrelationFilter().filter(record)
        assert record.run_id == "run-xyz"


def test_filter_injects_task_id() -> None:
    ctx = CorrelationContext(trace_id="t", task_id="task-1")
    with correlation_context(ctx):
        record = _make_record()
        CorrelationFilter().filter(record)
        assert record.task_id == "task-1"


def test_filter_injects_step_id() -> None:
    ctx = CorrelationContext(trace_id="t", step_id="step-2")
    with correlation_context(ctx):
        record = _make_record()
        CorrelationFilter().filter(record)
        assert record.step_id == "step-2"


def test_filter_injects_tool_call_id() -> None:
    ctx = CorrelationContext(trace_id="t", tool_call_id="call-99")
    with correlation_context(ctx):
        record = _make_record()
        CorrelationFilter().filter(record)
        assert record.tool_call_id == "call-99"


def test_filter_returns_true() -> None:
    ctx = CorrelationContext(trace_id="t")
    with correlation_context(ctx):
        record = _make_record()
        assert CorrelationFilter().filter(record) is True


# ---------------------------------------------------------------------------
# CorrelationFilter — no active context
# ---------------------------------------------------------------------------


def test_filter_sets_all_fields_to_none_when_no_context() -> None:
    # Deliberately outside any correlation_context manager.
    # ContextVar default is None, so all injected fields must be None.
    filt = CorrelationFilter()
    record = _make_record()
    filt.filter(record)
    assert record.trace_id is None
    assert record.run_id is None
    assert record.task_id is None
    assert record.step_id is None
    assert record.tool_call_id is None


def test_filter_returns_true_when_no_context() -> None:
    record = _make_record()
    assert CorrelationFilter().filter(record) is True


# ---------------------------------------------------------------------------
# correlation_context context manager
# ---------------------------------------------------------------------------


def test_correlation_context_resets_after_exit() -> None:
    assert get_correlation() is None
    ctx = CorrelationContext(trace_id="temp")
    with correlation_context(ctx):
        assert get_correlation() is not None
        assert get_correlation().trace_id == "temp"  # type: ignore[union-attr]
    assert get_correlation() is None


def test_correlation_context_is_nestable() -> None:
    outer = CorrelationContext(trace_id="outer")
    inner = CorrelationContext(trace_id="inner")
    with correlation_context(outer):
        assert get_correlation().trace_id == "outer"  # type: ignore[union-attr]
        with correlation_context(inner):
            assert get_correlation().trace_id == "inner"  # type: ignore[union-attr]
        assert get_correlation().trace_id == "outer"  # type: ignore[union-attr]


def test_context_fields_visible_inside_manager() -> None:
    ctx = CorrelationContext(trace_id="t", run_id="r", task_id="tk", step_id="s", tool_call_id="c")
    with correlation_context(ctx):
        active = get_correlation()
        assert active is not None
        assert active.trace_id == "t"
        assert active.run_id == "r"
        assert active.task_id == "tk"
        assert active.step_id == "s"
        assert active.tool_call_id == "c"


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


def test_get_logger_attaches_correlation_filter() -> None:
    logger = get_logger("test.agent_runtime.obs")
    assert any(isinstance(f, CorrelationFilter) for f in logger.filters)


def test_get_logger_does_not_add_duplicate_filter() -> None:
    name = "test.agent_runtime.obs.dedupe"
    get_logger(name)
    get_logger(name)
    logger = logging.getLogger(name)
    correlation_filters = [f for f in logger.filters if isinstance(f, CorrelationFilter)]
    assert len(correlation_filters) == 1


def test_get_logger_returns_standard_logger() -> None:
    logger = get_logger("test.agent_runtime.obs.type")
    assert isinstance(logger, logging.Logger)
