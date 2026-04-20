"""Tests for agent_runtime.executor — idempotency and step execution."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from agent_runtime.executor import ExecutorError, InMemoryExecutor
from agent_runtime.schemas import Plan, PlanStep, StepExecutionStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _step(step_id: str) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        title=f"Step {step_id}",
        input_contract="none",
        output_contract="none",
        done_condition="always",
    )


def _plan(*step_ids: str) -> Plan:
    return Plan(
        plan_id=str(uuid.uuid4()),
        task_id="task-99",
        steps=[_step(sid) for sid in step_ids],
    )


def _success_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    return (StepExecutionStatus.DONE, "success output", None)


def _fail_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    return (StepExecutionStatus.FAILED, None, "step logic failed")


def _raising_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    raise RuntimeError("unexpected crash")


# ---------------------------------------------------------------------------
# Basic execution
# ---------------------------------------------------------------------------


def test_execute_returns_execution_record_on_success() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _success_handler)
    assert record.status == StepExecutionStatus.DONE


def test_execute_record_carries_correct_step_id() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-A")
    record = executor.execute(plan, "step-A", "key-A", _success_handler)
    assert record.step_id == "step-A"


def test_execute_record_carries_correct_task_id() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _success_handler)
    assert record.task_id == plan.task_id


def test_execute_record_carries_output() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _success_handler)
    assert record.output == "success output"


def test_execute_fail_handler_sets_failed_status() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _fail_handler)
    assert record.status == StepExecutionStatus.FAILED


def test_execute_record_carries_error_from_fail_handler() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _fail_handler)
    assert record.error == "step logic failed"


def test_execute_record_has_started_at_timestamp() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    before = datetime.now(timezone.utc)
    record = executor.execute(plan, "step-1", "key-1", _success_handler)
    assert record.started_at >= before


def test_execute_record_has_ended_at_timestamp() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _success_handler)
    assert record.ended_at is not None


def test_execute_record_carries_idempotency_key() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "my-key", _success_handler)
    assert record.idempotency_key == "my-key"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_execute_same_key_after_done_does_not_call_handler_again() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    call_count = 0

    def counting_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
        nonlocal call_count
        call_count += 1
        return (StepExecutionStatus.DONE, "output", None)

    executor.execute(plan, "step-1", "key-1", counting_handler)
    assert call_count == 1

    executor.execute(plan, "step-1", "key-1", counting_handler)
    assert call_count == 1  # NOT incremented — idempotency enforced.


def test_execute_same_key_after_done_returns_original_record() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    first = executor.execute(plan, "step-1", "key-1", _success_handler)
    second = executor.execute(plan, "step-1", "key-1", _fail_handler)  # different handler
    assert second.status == StepExecutionStatus.DONE  # original status preserved
    assert second is first


def test_execute_same_key_after_failed_is_also_idempotent() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    call_count = 0

    def counting_fail_handler(
        step: PlanStep,
    ) -> tuple[StepExecutionStatus, str | None, str | None]:
        nonlocal call_count
        call_count += 1
        return (StepExecutionStatus.FAILED, None, "error")

    executor.execute(plan, "step-1", "key-fail", counting_fail_handler)
    executor.execute(plan, "step-1", "key-fail", counting_fail_handler)
    assert call_count == 1


def test_execute_different_keys_are_independent() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")

    r1 = executor.execute(plan, "step-1", "key-A", _success_handler)
    r2 = executor.execute(plan, "step-1", "key-B", _fail_handler)

    assert r1.status == StepExecutionStatus.DONE
    assert r2.status == StepExecutionStatus.FAILED


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------


def test_execute_raising_handler_results_in_failed_record() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _raising_handler)
    assert record.status == StepExecutionStatus.FAILED


def test_execute_raising_handler_captures_error_message() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _raising_handler)
    assert "unexpected crash" in (record.error or "")


def test_execute_raising_handler_stored_for_idempotency() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    call_count = 0

    def raising_once(
        step: PlanStep,
    ) -> tuple[StepExecutionStatus, str | None, str | None]:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("bang")

    executor.execute(plan, "step-1", "key-err", raising_once)
    executor.execute(plan, "step-1", "key-err", raising_once)
    assert call_count == 1  # second call hit the cache


# ---------------------------------------------------------------------------
# Error conditions
# ---------------------------------------------------------------------------


def test_execute_raises_executor_error_for_unknown_step() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    with pytest.raises(ExecutorError):
        executor.execute(plan, "step-MISSING", "key-1", _success_handler)


def test_execute_error_message_contains_step_id() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    with pytest.raises(ExecutorError) as exc_info:
        executor.execute(plan, "ghost-step", "key-1", _success_handler)
    assert "ghost-step" in str(exc_info.value)


# ---------------------------------------------------------------------------
# get_record
# ---------------------------------------------------------------------------


def test_get_record_returns_stored_record() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    executor.execute(plan, "step-1", "my-key", _success_handler)
    assert executor.get_record("my-key") is not None


def test_get_record_returns_none_for_unknown_key() -> None:
    executor = InMemoryExecutor()
    assert executor.get_record("nonexistent-key") is None


# ---------------------------------------------------------------------------
# trace_id propagation
# ---------------------------------------------------------------------------


def test_execute_carries_provided_trace_id() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _success_handler, trace_id="trace-xyz")
    assert record.trace_id == "trace-xyz"


def test_execute_generates_trace_id_when_not_provided() -> None:
    executor = InMemoryExecutor()
    plan = _plan("step-1")
    record = executor.execute(plan, "step-1", "key-1", _success_handler)
    assert record.trace_id != ""
