"""Step result validator — evaluates execution records and produces confidence-scored results."""

from __future__ import annotations

from datetime import datetime, timezone

from agent_runtime.schemas import (
    EvaluationFinding,
    EvaluationResult,
    EvaluationStatus,
    ExecutionRecord,
    StepExecutionStatus,
)


class BasicValidator:
    """Validates execution records and produces a confidence-scored ``EvaluationResult``.

    Confidence is the ratio of DONE steps to total steps (0.0–1.0).
    Every FAILED step produces an ``EvaluationFinding`` at severity ``"high"``.
    An empty record list is treated as a full pass with confidence 1.0.
    """

    def validate(
        self,
        task_id: str,
        records: list[ExecutionRecord],
        constraints: list[str] | None = None,
    ) -> EvaluationResult:
        """Evaluate *records* for the given *task_id*.

        Args:
            task_id: ID of the task being validated.
            records: Execution records to evaluate.
            constraints: Optional constraint labels acknowledged in the evaluation
                (recorded for audit; not applied by this implementation).

        Returns:
            An ``EvaluationResult`` with PASS or FAIL status, confidence, and findings.
        """
        if not records:
            return EvaluationResult(
                task_id=task_id,
                status=EvaluationStatus.PASS,
                confidence=1.0,
                findings=[],
                evaluated_at=datetime.now(timezone.utc),
            )

        findings: list[EvaluationFinding] = []

        for record in records:
            if record.status == StepExecutionStatus.FAILED:
                findings.append(
                    EvaluationFinding(
                        severity="high",
                        summary=f"Step {record.step_id!r} failed during execution.",
                        evidence=[record.error or "(no error message captured)"],
                        remediation=f"Investigate step {record.step_id!r} and retry.",
                    )
                )

        done_count = sum(1 for r in records if r.status == StepExecutionStatus.DONE)
        confidence = done_count / len(records)
        status = EvaluationStatus.PASS if not findings else EvaluationStatus.FAIL

        return EvaluationResult(
            task_id=task_id,
            status=status,
            confidence=confidence,
            findings=findings,
            evaluated_at=datetime.now(timezone.utc),
        )
