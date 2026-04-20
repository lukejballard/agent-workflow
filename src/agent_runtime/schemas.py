"""Core Pydantic data models for the agent runtime."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class TaskState(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    LEARNING = "LEARNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ToolCallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    DENIED = "denied"


class TaskClass(str, Enum):
    TRIVIAL = "trivial"
    RESEARCH_ONLY = "research-only"
    REVIEW_ONLY = "review-only"
    BROWNFIELD_IMPROVEMENT = "brownfield-improvement"
    GREENFIELD_FEATURE = "greenfield-feature"
    IMPLEMENT_FROM_SPEC = "implement-from-existing-spec"
    TEST_ONLY = "test-only"
    DOCS_ONLY = "docs-only"


class MemoryScope(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    LONG_TERM = "long_term"


class EvaluationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


class RunArtifactStatus(str, Enum):
    IN_PROGRESS = "in-progress"
    BLOCKED = "blocked"
    REVIEW_NEEDED = "review-needed"
    DONE = "done"


# Constrained literal types shared by multiple models and the TypeScript contract.
FindingSeverity = Literal["low", "medium", "high", "critical"]
VerificationStatus = Literal["passed", "failed", "not-run", "advisory"]


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    title: str
    depends_on: list[str] = Field(default_factory=list)
    input_contract: str
    output_contract: str
    done_condition: str
    handler_name: str = Field(default="default")


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    task_id: str
    revision: int = Field(default=1, ge=1)
    steps: list[PlanStep]


# ---------------------------------------------------------------------------
# Tool call execution record
# ---------------------------------------------------------------------------


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    task_id: str
    step_id: str
    tool_name: str
    status: ToolCallStatus
    started_at: datetime
    ended_at: datetime | None = None
    retry_count: int = Field(default=0, ge=0)
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_id: str
    scope: MemoryScope
    summary: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime
    expires_at: datetime | None = None


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class EvaluationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: FindingSeverity
    summary: str
    evidence: list[str] = Field(default_factory=list)
    remediation: str | None = None


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    status: EvaluationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[EvaluationFinding] = Field(default_factory=list)
    evaluated_at: datetime


# ---------------------------------------------------------------------------
# Run artifact
# ---------------------------------------------------------------------------


class VerificationEntry(BaseModel):
    """Typed verification record — replaces the loose dict[str, str] pattern."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    status: VerificationStatus
    details: str


class RunArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    run_id: str
    task_class: TaskClass
    objective: str
    status: RunArtifactStatus
    summary: str
    touched_paths: list[str] = Field(default_factory=list)
    verification: list[VerificationEntry] = Field(default_factory=list)
    residual_risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    objective: str
    state: TaskState = TaskState.PENDING
    plan: Plan | None = None
    trace_id: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Step execution
# ---------------------------------------------------------------------------


class StepExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


class ExecutorCheckpoint(BaseModel):
    """Immutable record that a step reached a terminal state.

    Written by the executor after each terminal outcome.  On restart the
    executor reads these checkpoints to skip already-completed steps.

    Idempotency key: ``(task_id, step_id)``.
    """

    model_config = ConfigDict(extra="forbid")

    task_id: str
    step_id: str
    idempotency_key: str
    status: "StepExecutionStatus"
    ended_at: datetime


class ExecutionRecord(BaseModel):
    """Record of a single plan step execution attempt."""

    model_config = ConfigDict(extra="forbid")

    idempotency_key: str
    step_id: str
    task_id: str
    trace_id: str = ""
    attempt: int = Field(default=1, ge=1)
    status: StepExecutionStatus
    output: str | None = None
    error: str | None = None
    started_at: datetime
    ended_at: datetime | None = None


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------


class LearningSuggestion(BaseModel):
    """A pattern-based improvement recommendation derived from run artifacts."""

    model_config = ConfigDict(extra="forbid")

    category: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(ge=0)
    source_run_ids: list[str] = Field(default_factory=list)
