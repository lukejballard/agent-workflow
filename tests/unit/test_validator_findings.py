"""Tests for agent_runtime.validator — findings, severity, and confidence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from agent_runtime.schemas import EvaluationStatus, ExecutionRecord, StepExecutionStatus
from agent_runtime.validator import BasicValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record(
    step_id: str,
    status: StepExecutionStatus,
    error: str | None = None,
    output: str | None = None,
) -> ExecutionRecord:
    return ExecutionRecord(
        idempotency_key=str(uuid.uuid4()),
        step_id=step_id,
        task_id="task-1",
        trace_id="trace-1",
        status=status,
        error=error,
        output=output,
        started_at=_now(),
        ended_at=_now(),
    )


# ---------------------------------------------------------------------------
# Empty records
# ---------------------------------------------------------------------------


def test_validate_empty_records_returns_pass() -> None:
    result = BasicValidator().validate("task-1", [])
    assert result.status == EvaluationStatus.PASS


def test_validate_empty_records_returns_full_confidence() -> None:
    result = BasicValidator().validate("task-1", [])
    assert result.confidence == 1.0


def test_validate_empty_records_has_no_findings() -> None:
    result = BasicValidator().validate("task-1", [])
    assert result.findings == []


# ---------------------------------------------------------------------------
# All DONE
# ---------------------------------------------------------------------------


def test_validate_all_done_records_returns_pass() -> None:
    records = [
        _record("step-1", StepExecutionStatus.DONE),
        _record("step-2", StepExecutionStatus.DONE),
    ]
    result = BasicValidator().validate("task-2", records)
    assert result.status == EvaluationStatus.PASS


def test_validate_all_done_records_confidence_is_one() -> None:
    records = [_record("s1", StepExecutionStatus.DONE)]
    result = BasicValidator().validate("t", records)
    assert result.confidence == 1.0


def test_validate_all_done_no_findings() -> None:
    records = [_record("s1", StepExecutionStatus.DONE)]
    assert BasicValidator().validate("t", records).findings == []


# ---------------------------------------------------------------------------
# FAILED records
# ---------------------------------------------------------------------------


def test_validate_single_failed_record_returns_fail_status() -> None:
    records = [_record("step-bad", StepExecutionStatus.FAILED, error="oops")]
    result = BasicValidator().validate("task-3", records)
    assert result.status == EvaluationStatus.FAIL


def test_validate_failed_record_confidence_is_zero_when_all_fail() -> None:
    records = [
        _record("s1", StepExecutionStatus.FAILED),
        _record("s2", StepExecutionStatus.FAILED),
    ]
    result = BasicValidator().validate("t", records)
    assert result.confidence == pytest.approx(0.0)


def test_validate_mixed_records_confidence_reflects_done_ratio() -> None:
    records = [
        _record("s1", StepExecutionStatus.DONE),
        _record("s2", StepExecutionStatus.FAILED),
    ]
    result = BasicValidator().validate("t", records)
    assert result.confidence == pytest.approx(0.5)


def test_validate_failed_step_produces_one_finding_per_failure() -> None:
    records = [
        _record("step-A", StepExecutionStatus.FAILED, error="err A"),
        _record("step-B", StepExecutionStatus.DONE),
        _record("step-C", StepExecutionStatus.FAILED, error="err C"),
    ]
    result = BasicValidator().validate("t", records)
    assert len(result.findings) == 2


# ---------------------------------------------------------------------------
# Finding attributes
# ---------------------------------------------------------------------------


def test_validate_finding_severity_is_high_for_failed_step() -> None:
    records = [_record("step-X", StepExecutionStatus.FAILED, error="bad")]
    result = BasicValidator().validate("t", records)
    assert result.findings[0].severity == "high"


def test_validate_finding_summary_contains_step_id() -> None:
    records = [_record("my-step", StepExecutionStatus.FAILED, error="bad")]
    result = BasicValidator().validate("t", records)
    assert "my-step" in result.findings[0].summary


def test_validate_finding_evidence_contains_error_message() -> None:
    records = [_record("step-1", StepExecutionStatus.FAILED, error="specific error text")]
    result = BasicValidator().validate("t", records)
    evidence = result.findings[0].evidence
    assert any("specific error text" in e for e in evidence)


def test_validate_finding_evidence_fallback_when_no_error_message() -> None:
    records = [_record("step-1", StepExecutionStatus.FAILED, error=None)]
    result = BasicValidator().validate("t", records)
    assert result.findings[0].evidence  # must not be empty


def test_validate_finding_has_remediation() -> None:
    records = [_record("step-1", StepExecutionStatus.FAILED, error="err")]
    result = BasicValidator().validate("t", records)
    assert result.findings[0].remediation is not None


# ---------------------------------------------------------------------------
# Result metadata
# ---------------------------------------------------------------------------


def test_validate_task_id_is_preserved() -> None:
    result = BasicValidator().validate("specific-task-id", [])
    assert result.task_id == "specific-task-id"


def test_validate_evaluated_at_is_set() -> None:
    before = datetime.now(timezone.utc)
    result = BasicValidator().validate("t", [])
    assert result.evaluated_at >= before


def test_validate_confidence_is_in_range() -> None:
    records = [
        _record("s1", StepExecutionStatus.DONE),
        _record("s2", StepExecutionStatus.FAILED),
    ]
    result = BasicValidator().validate("t", records)
    assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------------
# Constraints parameter
# ---------------------------------------------------------------------------


def test_validate_accepts_constraints_without_error() -> None:
    records = [_record("s1", StepExecutionStatus.DONE)]
    result = BasicValidator().validate("t", records, constraints=["must not mutate DB"])
    assert result.status == EvaluationStatus.PASS
