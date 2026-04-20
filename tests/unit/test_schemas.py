"""Tests for agent_runtime.schemas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent_runtime.schemas import (
    EvaluationFinding,
    EvaluationResult,
    EvaluationStatus,
    MemoryEntry,
    MemoryScope,
    Plan,
    PlanStep,
    RunArtifact,
    RunArtifactStatus,
    Task,
    TaskClass,
    TaskState,
    ToolCall,
    ToolCallStatus,
    VerificationEntry,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# TaskState
# ---------------------------------------------------------------------------


class TestTaskState:
    def test_all_values_are_strings(self) -> None:
        for state in TaskState:
            assert isinstance(state.value, str)

    def test_terminal_states_present(self) -> None:
        assert TaskState.DONE in TaskState
        assert TaskState.FAILED in TaskState
        assert TaskState.CANCELLED in TaskState


# ---------------------------------------------------------------------------
# PlanStep
# ---------------------------------------------------------------------------


class TestPlanStep:
    def test_valid_construction_defaults_depends_on_empty(self) -> None:
        step = PlanStep(
            step_id=_id(),
            title="Do the thing",
            input_contract="task goal",
            output_contract="result artifact",
            done_condition="artifact exists",
        )
        assert step.depends_on == []

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlanStep(
                step_id=_id(),
                title="x",
                input_contract="x",
                output_contract="x",
                done_condition="x",
                unknown_field="oops",
            )

    def test_depends_on_populated(self) -> None:
        step = PlanStep(
            step_id=_id(),
            title="Step 2",
            depends_on=["step-1"],
            input_contract="x",
            output_contract="x",
            done_condition="x",
        )
        assert step.depends_on == ["step-1"]


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


class TestPlan:
    def test_revision_defaults_to_one(self) -> None:
        plan = Plan(plan_id=_id(), task_id=_id(), steps=[])
        assert plan.revision == 1

    def test_revision_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Plan(plan_id=_id(), task_id=_id(), steps=[], revision=0)

    def test_negative_revision_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Plan(plan_id=_id(), task_id=_id(), steps=[], revision=-1)


# ---------------------------------------------------------------------------
# ToolCall
# ---------------------------------------------------------------------------


class TestToolCall:
    def test_valid_construction_sets_defaults(self) -> None:
        tc = ToolCall(
            call_id=_id(),
            task_id=_id(),
            step_id=_id(),
            tool_name="read_file",
            status=ToolCallStatus.SUCCESS,
            started_at=_now(),
            trace_id=_id(),
        )
        assert tc.ended_at is None
        assert tc.retry_count == 0

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall(
                call_id=_id(),
                task_id=_id(),
                step_id=_id(),
                tool_name="read_file",
                status="invalid_status",
                started_at=_now(),
                trace_id=_id(),
            )

    def test_negative_retry_count_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall(
                call_id=_id(),
                task_id=_id(),
                step_id=_id(),
                tool_name="read_file",
                status=ToolCallStatus.SUCCESS,
                started_at=_now(),
                trace_id=_id(),
                retry_count=-1,
            )

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ToolCall(
                call_id=_id(),
                task_id=_id(),
                step_id=_id(),
                tool_name="read_file",
                status=ToolCallStatus.SUCCESS,
                started_at=_now(),
                trace_id=_id(),
                unknown="oops",
            )


# ---------------------------------------------------------------------------
# MemoryEntry
# ---------------------------------------------------------------------------


class TestMemoryEntry:
    def test_confidence_at_zero_is_valid(self) -> None:
        entry = MemoryEntry(
            memory_id=_id(),
            scope=MemoryScope.WORKING,
            summary="context summary",
            source="test",
            confidence=0.0,
            created_at=_now(),
        )
        assert entry.confidence == 0.0

    def test_confidence_at_one_is_valid(self) -> None:
        entry = MemoryEntry(
            memory_id=_id(),
            scope=MemoryScope.EPISODIC,
            summary="context summary",
            source="test",
            confidence=1.0,
            created_at=_now(),
        )
        assert entry.confidence == 1.0

    @pytest.mark.parametrize("confidence", [-0.1, 1.1, 2.0])
    def test_confidence_out_of_range_rejected(self, confidence: float) -> None:
        with pytest.raises(ValidationError):
            MemoryEntry(
                memory_id=_id(),
                scope=MemoryScope.WORKING,
                summary="x",
                source="test",
                confidence=confidence,
                created_at=_now(),
            )


# ---------------------------------------------------------------------------
# EvaluationFinding
# ---------------------------------------------------------------------------


class TestEvaluationFinding:
    @pytest.mark.parametrize("severity", ["low", "medium", "high", "critical"])
    def test_valid_severities_accepted(self, severity: str) -> None:
        finding = EvaluationFinding(severity=severity, summary="something happened")
        assert finding.severity == severity

    def test_invalid_severity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationFinding(severity="catastrophic", summary="oops")

    def test_remediation_is_optional(self) -> None:
        finding = EvaluationFinding(severity="low", summary="minor issue")
        assert finding.remediation is None

    def test_evidence_defaults_empty(self) -> None:
        finding = EvaluationFinding(severity="high", summary="something")
        assert finding.evidence == []


# ---------------------------------------------------------------------------
# EvaluationResult
# ---------------------------------------------------------------------------


class TestEvaluationResult:
    def test_valid_construction_findings_default_empty(self) -> None:
        result = EvaluationResult(
            task_id=_id(),
            status=EvaluationStatus.PASS,
            confidence=0.9,
            evaluated_at=_now(),
        )
        assert result.findings == []

    def test_confidence_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationResult(
                task_id=_id(),
                status=EvaluationStatus.PASS,
                confidence=1.5,
                evaluated_at=_now(),
            )

    def test_confidence_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvaluationResult(
                task_id=_id(),
                status=EvaluationStatus.FAIL,
                confidence=-0.1,
                evaluated_at=_now(),
            )


# ---------------------------------------------------------------------------
# VerificationEntry
# ---------------------------------------------------------------------------


class TestVerificationEntry:
    @pytest.mark.parametrize("status", ["passed", "failed", "not-run", "advisory"])
    def test_valid_statuses_accepted(self, status: str) -> None:
        entry = VerificationEntry(kind="unit-tests", status=status, details="ran OK")
        assert entry.status == status

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VerificationEntry(kind="unit-tests", status="skipped", details="")

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VerificationEntry(kind="unit-tests", status="passed", details="ok", extra="bad")


# ---------------------------------------------------------------------------
# RunArtifact
# ---------------------------------------------------------------------------


class TestRunArtifact:
    def test_schema_version_defaults_to_one(self) -> None:
        artifact = RunArtifact(
            run_id=_id(),
            task_class=TaskClass.GREENFIELD_FEATURE,
            objective="build thing",
            status=RunArtifactStatus.DONE,
            summary="completed",
        )
        assert artifact.schema_version == 1

    def test_verification_accepts_typed_entries(self) -> None:
        artifact = RunArtifact(
            run_id=_id(),
            task_class=TaskClass.TEST_ONLY,
            objective="add tests",
            status=RunArtifactStatus.DONE,
            summary="all passed",
            verification=[
                VerificationEntry(kind="pytest", status="passed", details="100 tests"),
            ],
        )
        assert len(artifact.verification) == 1
        assert artifact.verification[0].kind == "pytest"

    def test_invalid_task_class_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RunArtifact(
                run_id=_id(),
                task_class="made-up-class",
                objective="x",
                status=RunArtifactStatus.DONE,
                summary="x",
            )

    def test_touched_paths_and_risks_default_empty(self) -> None:
        artifact = RunArtifact(
            run_id=_id(),
            task_class=TaskClass.TRIVIAL,
            objective="x",
            status=RunArtifactStatus.DONE,
            summary="x",
        )
        assert artifact.touched_paths == []
        assert artifact.residual_risks == []


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestTask:
    def test_state_defaults_to_pending(self) -> None:
        task = Task(
            task_id=_id(),
            objective="do something",
            trace_id=_id(),
            created_at=_now(),
            updated_at=_now(),
        )
        assert task.state == TaskState.PENDING
        assert task.plan is None

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Task(
                task_id=_id(),
                objective="x",
                trace_id=_id(),
                created_at=_now(),
                updated_at=_now(),
                unexpected="x",
            )
