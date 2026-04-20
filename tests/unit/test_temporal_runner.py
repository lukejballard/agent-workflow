"""Tests for the Temporal execution backend (Stage 3 of ADR-002).

Strategy
--------
* **Activity tests** -- ``execute_step_activity`` is a plain async function
  decorated with ``@activity.defn``.  Outside a Temporal worker context it
  is callable directly, so we test it as a regular coroutine without standing
  up any Temporal infrastructure.

* **Runner tests** -- ``TemporalPlanRunner.run_plan`` delegates to
  ``client.execute_workflow``.  We mock the client so the unit test does not
  require a running Temporal server.

* **Registry tests** -- ``register_handler`` / ``get_handler`` manipulate the
  module-level ``_GLOBAL_REGISTRY``; a ``clear_registry`` autouse fixture
  isolates each test.

* **Workflow integration test** -- uses ``temporalio.testing.WorkflowEnvironment``
  in time-skipping mode to exercise ``PlanWorkflow.run`` end-to-end in an
  in-process Temporal test environment.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from agent_runtime.schemas import (
    ExecutionRecord,
    Plan,
    PlanStep,
    StepExecutionStatus,
)
from agent_runtime.temporal_runner import (
    ExecuteStepInput,
    PlanWorkflow,
    TemporalPlanRunner,
    _GLOBAL_REGISTRY,
    execute_step_activity,
    get_handler,
    register_handler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _step(step_id: str, handler_name: str = "default") -> PlanStep:
    return PlanStep(
        step_id=step_id,
        title=f"Step {step_id}",
        input_contract="none",
        output_contract="none",
        done_condition="always",
        handler_name=handler_name,
    )


def _plan(*step_ids: str, handler_name: str = "default") -> Plan:
    return Plan(
        plan_id=str(uuid.uuid4()),
        task_id="task-t3",
        steps=[_step(sid, handler_name) for sid in step_ids],
    )


def _success_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    return StepExecutionStatus.DONE, "ok", None


def _failing_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    return StepExecutionStatus.FAILED, None, "oops"


def _exploding_handler(step: PlanStep) -> tuple[StepExecutionStatus, str | None, str | None]:
    raise RuntimeError("boom")


def _make_input(
    step: PlanStep,
    handler_name: str = "default",
    task_id: str = "task-t3",
    plan_id: str = "plan-t3",
) -> ExecuteStepInput:
    return ExecuteStepInput(
        task_id=task_id,
        plan_id=plan_id,
        step_id=step.step_id,
        handler_name=handler_name,
        trace_id="trace-1",
        step_json=step.model_dump_json(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_registry():
    """Isolate each test from global registry side-effects."""
    saved = dict(_GLOBAL_REGISTRY)
    _GLOBAL_REGISTRY.clear()
    yield
    _GLOBAL_REGISTRY.clear()
    _GLOBAL_REGISTRY.update(saved)


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------


def test_register_and_get_handler() -> None:
    register_handler("my-handler", _success_handler)
    assert get_handler("my-handler") is _success_handler


def test_get_handler_missing_returns_none() -> None:
    assert get_handler("nonexistent") is None


def test_register_handler_overwrites_existing() -> None:
    register_handler("h", _success_handler)
    register_handler("h", _failing_handler)
    assert get_handler("h") is _failing_handler


# ---------------------------------------------------------------------------
# execute_step_activity -- direct coroutine invocation tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_activity_success_path() -> None:
    register_handler("default", _success_handler)
    step = _step("s1")
    result = await execute_step_activity(_make_input(step))

    assert result["status"] == StepExecutionStatus.DONE.value
    assert result["output"] == "ok"
    assert result["error"] is None
    assert result["step_id"] == "s1"
    assert result["task_id"] == "task-t3"


@pytest.mark.anyio
async def test_activity_handler_returns_failed_status() -> None:
    register_handler("default", _failing_handler)
    step = _step("s1")
    result = await execute_step_activity(_make_input(step))

    assert result["status"] == StepExecutionStatus.FAILED.value
    assert result["error"] == "oops"


@pytest.mark.anyio
async def test_activity_handler_exception_returns_failed_record() -> None:
    register_handler("default", _exploding_handler)
    step = _step("s1")
    result = await execute_step_activity(_make_input(step))

    assert result["status"] == StepExecutionStatus.FAILED.value
    assert "boom" in result["error"]


@pytest.mark.anyio
async def test_activity_no_handler_returns_failed_record() -> None:
    """No handler registered at all -- activity must not raise."""
    step = _step("s1")
    result = await execute_step_activity(_make_input(step, handler_name="unknown"))

    assert result["status"] == StepExecutionStatus.FAILED.value
    assert "unknown" in result["error"]


@pytest.mark.anyio
async def test_activity_falls_back_to_default_handler() -> None:
    """Unknown handler_name falls back to default if registered."""
    register_handler("default", _success_handler)
    step = _step("s1")
    result = await execute_step_activity(_make_input(step, handler_name="unknown"))

    assert result["status"] == StepExecutionStatus.DONE.value


@pytest.mark.anyio
async def test_activity_result_round_trips_to_execution_record() -> None:
    """The returned dict must be parseable back to ExecutionRecord."""
    register_handler("default", _success_handler)
    step = _step("s1")
    raw = await execute_step_activity(_make_input(step))
    record = ExecutionRecord.model_validate(raw)

    assert record.status == StepExecutionStatus.DONE
    assert record.idempotency_key == "task-t3:s1"


@pytest.mark.anyio
async def test_activity_idempotency_key_format() -> None:
    register_handler("default", _success_handler)
    step = _step("my-step")
    result = await execute_step_activity(
        _make_input(step, task_id="t1", handler_name="default")
    )
    assert result["idempotency_key"] == "t1:my-step"


# ---------------------------------------------------------------------------
# PlanWorkflow -- WorkflowEnvironment integration tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_plan_workflow_runs_all_steps_via_test_environment() -> None:
    """End-to-end: PlanWorkflow dispatches each step to execute_step_activity."""
    register_handler("default", _success_handler)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[PlanWorkflow],
            activities=[execute_step_activity],
        ):
            plan = _plan("s1", "s2")
            result_dicts = await env.client.execute_workflow(
                PlanWorkflow.run,
                args=[plan.model_dump_json(), "trace-wf"],
                id=f"wf-{uuid.uuid4()}",
                task_queue="test-queue",
            )

    records = [ExecutionRecord.model_validate(r) for r in result_dicts]
    assert len(records) == 2
    assert all(r.status == StepExecutionStatus.DONE for r in records)
    assert all(r.trace_id == "trace-wf" for r in records)


@pytest.mark.anyio
async def test_plan_workflow_generates_trace_id_when_empty() -> None:
    """When trace_id is empty the workflow generates a UUID trace."""
    register_handler("default", _success_handler)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[PlanWorkflow],
            activities=[execute_step_activity],
        ):
            plan = _plan("s1")
            result_dicts = await env.client.execute_workflow(
                PlanWorkflow.run,
                args=[plan.model_dump_json(), ""],
                id=f"wf-{uuid.uuid4()}",
                task_queue="test-queue",
            )

    records = [ExecutionRecord.model_validate(r) for r in result_dicts]
    assert records[0].trace_id != ""


# ---------------------------------------------------------------------------
# TemporalPlanRunner -- mock client tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_runner_calls_execute_workflow_with_plan_json() -> None:
    plan = _plan("s1", "s2")

    now_iso = datetime.now(timezone.utc).isoformat()
    mock_records = [
        {
            "idempotency_key": f"task-t3:{sid}",
            "step_id": sid,
            "task_id": "task-t3",
            "trace_id": "trace-x",
            "attempt": 1,
            "status": "done",
            "output": "ok",
            "error": None,
            "started_at": now_iso,
            "ended_at": now_iso,
        }
        for sid in ("s1", "s2")
    ]

    mock_client = MagicMock()
    mock_client.execute_workflow = AsyncMock(return_value=mock_records)

    runner = TemporalPlanRunner(mock_client, task_queue="test")
    records = await runner.run_plan(plan, trace_id="trace-x")

    assert len(records) == 2
    assert all(isinstance(r, ExecutionRecord) for r in records)
    assert all(r.status == StepExecutionStatus.DONE for r in records)


@pytest.mark.anyio
async def test_runner_uses_plan_id_as_workflow_id() -> None:
    plan = _plan("s1")
    now_iso = datetime.now(timezone.utc).isoformat()
    mock_record = {
        "idempotency_key": "task-t3:s1",
        "step_id": "s1",
        "task_id": "task-t3",
        "trace_id": "",
        "attempt": 1,
        "status": "done",
        "output": None,
        "error": None,
        "started_at": now_iso,
        "ended_at": now_iso,
    }

    mock_client = MagicMock()
    mock_client.execute_workflow = AsyncMock(return_value=[mock_record])

    runner = TemporalPlanRunner(mock_client)
    await runner.run_plan(plan)

    call_kwargs = mock_client.execute_workflow.call_args
    assert call_kwargs.kwargs["id"] == f"plan-{plan.plan_id}"


@pytest.mark.anyio
async def test_runner_default_task_queue() -> None:
    mock_client = MagicMock()
    runner = TemporalPlanRunner(mock_client)
    assert runner._task_queue == TemporalPlanRunner.DEFAULT_TASK_QUEUE


# ---------------------------------------------------------------------------
# PlanStep handler_name field
# ---------------------------------------------------------------------------


def test_plan_step_handler_name_defaults_to_default() -> None:
    step = PlanStep(
        step_id="x",
        title="X",
        input_contract="in",
        output_contract="out",
        done_condition="cond",
    )
    assert step.handler_name == "default"


def test_plan_step_custom_handler_name() -> None:
    step = PlanStep(
        step_id="x",
        title="X",
        input_contract="in",
        output_contract="out",
        done_condition="cond",
        handler_name="my-handler",
    )
    assert step.handler_name == "my-handler"