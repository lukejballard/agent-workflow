"""Tests for scripts/agent/trace_logger.py — per-run execution trace logger."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.agent.trace_logger import (
    TraceLogger,
    VALID_EVENT_TYPES,
    VALID_STATUSES,
    log_phase_transition,
    log_tool_call,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def logger(tmp_path: Path) -> TraceLogger:
    return TraceLogger(run_id="test-run-001", runs_dir=tmp_path)


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------


def test_start_creates_trace_file(logger: TraceLogger, tmp_path: Path) -> None:
    logger.start()
    trace_path = tmp_path / "test-run-001" / "trace.json"
    assert trace_path.exists()


def test_start_sets_status_running(logger: TraceLogger) -> None:
    trace = logger.start()
    assert trace["status"] == "running"


def test_start_sets_run_id(logger: TraceLogger) -> None:
    trace = logger.start()
    assert trace["run_id"] == "test-run-001"


def test_start_sets_started_at(logger: TraceLogger) -> None:
    before = time.time()
    trace = logger.start()
    after = time.time()
    assert before <= trace["started_at"] <= after


def test_start_sets_finished_at_none(logger: TraceLogger) -> None:
    trace = logger.start()
    assert trace["finished_at"] is None


def test_start_initialises_empty_events(logger: TraceLogger) -> None:
    trace = logger.start()
    assert trace["events"] == []


def test_start_is_idempotent(logger: TraceLogger) -> None:
    first = logger.start()
    second = logger.start()
    assert first["trace_id"] == second["trace_id"]


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------


def test_log_appends_event(logger: TraceLogger) -> None:
    logger.start()
    logger.log("info", phase="classify", inputs={"msg": "hello"})
    trace_path = logger._trace_path_local()
    trace = json.loads(trace_path.read_text())
    assert len(trace["events"]) == 1
    assert trace["events"][0]["event_type"] == "info"


def test_log_unknown_event_type_raises(logger: TraceLogger) -> None:
    logger.start()
    with pytest.raises(ValueError, match="Unknown event_type"):
        logger.log("bogus_type")


def test_log_sets_phase(logger: TraceLogger) -> None:
    logger.start()
    logger.log("phase_transition", phase="breadth-scan")
    trace = json.loads(logger._trace_path_local().read_text())
    assert trace["events"][0]["phase"] == "breadth-scan"


def test_log_sets_token_usage(logger: TraceLogger) -> None:
    logger.start()
    logger.log("tool_call", tokens_in=100, tokens_out=50)
    trace = json.loads(logger._trace_path_local().read_text())
    usage = trace["events"][0]["token_usage"]
    assert usage["tokens_in"] == 100
    assert usage["tokens_out"] == 50


def test_log_sets_model_used(logger: TraceLogger) -> None:
    logger.start()
    logger.log("decision", model_used="gpt-4o")
    trace = json.loads(logger._trace_path_local().read_text())
    assert trace["events"][0]["model_used"] == "gpt-4o"


def test_log_sets_rationale(logger: TraceLogger) -> None:
    logger.start()
    logger.log("decision", decision_rationale="risk level: low, skipping adversarial")
    trace = json.loads(logger._trace_path_local().read_text())
    assert "low" in trace["events"][0]["decision_rationale"]


def test_log_auto_starts_trace(logger: TraceLogger) -> None:
    # No explicit start() call.
    logger.log("info")
    trace = json.loads(logger._trace_path_local().read_text())
    assert trace["status"] == "running"


def test_log_returns_event_dict(logger: TraceLogger) -> None:
    logger.start()
    event = logger.log("info")
    assert "event_id" in event
    assert event["event_type"] == "info"


def test_log_each_event_gets_unique_id(logger: TraceLogger) -> None:
    logger.start()
    e1 = logger.log("info")
    e2 = logger.log("info")
    assert e1["event_id"] != e2["event_id"]


def test_log_all_valid_event_types(logger: TraceLogger) -> None:
    logger.start()
    for etype in VALID_EVENT_TYPES:
        logger.log(etype)
    trace = json.loads(logger._trace_path_local().read_text())
    assert len(trace["events"]) == len(VALID_EVENT_TYPES)


# ---------------------------------------------------------------------------
# finish
# ---------------------------------------------------------------------------


def test_finish_sets_status(logger: TraceLogger) -> None:
    logger.start()
    trace = logger.finish("done")
    assert trace["status"] == "done"


def test_finish_sets_finished_at(logger: TraceLogger) -> None:
    logger.start()
    before = time.time()
    trace = logger.finish("done")
    after = time.time()
    assert before <= trace["finished_at"] <= after


def test_finish_invalid_status_raises(logger: TraceLogger) -> None:
    logger.start()
    with pytest.raises(ValueError, match="Unknown status"):
        logger.finish("unknown-status")


def test_finish_aborted_status(logger: TraceLogger) -> None:
    logger.start()
    trace = logger.finish("aborted")
    assert trace["status"] == "aborted"


def test_finish_failed_status(logger: TraceLogger) -> None:
    logger.start()
    trace = logger.finish("failed")
    assert trace["status"] == "failed"


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------


def test_summary_returns_expected_keys(logger: TraceLogger) -> None:
    logger.start()
    logger.log("phase_transition", phase="classify", inputs={"from": "goal-anchor", "to": "classify"})
    logger.log("tool_call", tokens_in=200, tokens_out=80)
    logger.finish("done")
    s = logger.summary()
    assert s["status"] == "done"
    assert s["event_count"] == 2
    assert s["phase_transition_count"] == 1
    assert s["tool_call_count"] == 1
    assert s["total_tokens_in"] == 200
    assert s["total_tokens_out"] == 80


def test_summary_missing_trace(tmp_path: Path) -> None:
    logger = TraceLogger(run_id="nonexistent", runs_dir=tmp_path)
    s = logger.summary()
    assert "error" in s


def test_summary_phases_seen(logger: TraceLogger) -> None:
    logger.start()
    logger.log("phase_transition", inputs={"from": "goal-anchor", "to": "classify"})
    logger.log("phase_transition", inputs={"from": "classify", "to": "breadth-scan"})
    s = logger.summary()
    assert "classify" in s["phases_seen"]
    assert "breadth-scan" in s["phases_seen"]


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def test_log_phase_transition(tmp_path: Path) -> None:
    event = log_phase_transition("run-abc", "goal-anchor", "classify", runs_dir=tmp_path)
    assert event["event_type"] == "phase_transition"
    assert event["inputs"]["from"] == "goal-anchor"
    assert event["inputs"]["to"] == "classify"


def test_log_tool_call(tmp_path: Path) -> None:
    event = log_tool_call(
        "run-def", "read_file", {"filePath": "src/AGENTS.md"},
        phase="breadth-scan", tokens_in=50, runs_dir=tmp_path
    )
    assert event["event_type"] == "tool_call"
    assert event["inputs"]["tool_name"] == "read_file"
    assert event["token_usage"]["tokens_in"] == 50


# ---------------------------------------------------------------------------
# TraceLogger run_id auto-generation
# ---------------------------------------------------------------------------


def test_auto_generated_run_id_is_unique(tmp_path: Path) -> None:
    l1 = TraceLogger(runs_dir=tmp_path)
    l2 = TraceLogger(runs_dir=tmp_path)
    assert l1.run_id != l2.run_id
