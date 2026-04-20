"""Temporal execution backend for the agent-runtime plan runner.

Stage 3 of ADR-002: wraps plan execution as a Temporal Workflow / Activity
pair so each step runs exactly-once and survives process restarts.

Architecture
------------
1. **Handler registry** — a module-level ``dict[str, StepHandlerFn]`` that
   maps logical handler names to Python callables.  Register handlers at
   application startup with ``register_handler()``.  The activity resolves
   handlers by name so arbitrary callables never need to cross process
   boundaries.

2. **Activity** — ``execute_step_activity`` is a Temporal activity that
   resolves the handler from the registry, runs the step, and returns the
   ``ExecutionRecord`` serialised as a plain dict.  Temporal guarantees
   exactly-once delivery; the activity receives each step at most once per
   workflow run.

3. **Workflow** — ``PlanWorkflow`` receives the plan as a JSON string,
   iterates the steps in order, dispatches each to ``execute_step_activity``,
   and returns a list of record dicts.  Passing JSON strings (rather than
   Pydantic objects) avoids payload-converter configuration dependencies.

4. **Runner** — ``TemporalPlanRunner`` wraps a Temporal ``Client`` and
   provides a single ``run_plan(plan, trace_id)`` async method.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy

from agent_runtime.executor import StepHandlerFn
from agent_runtime.schemas import ExecutionRecord, Plan, PlanStep, StepExecutionStatus


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

#: Type alias for the handler name → callable mapping.
HandlerRegistry = dict[str, StepHandlerFn]

#: Module-level registry populated at application startup.
_GLOBAL_REGISTRY: HandlerRegistry = {}


def register_handler(name: str, fn: StepHandlerFn) -> None:
    """Register *fn* as the step handler for ``PlanStep.handler_name == name``."""
    _GLOBAL_REGISTRY[name] = fn


def get_handler(name: str) -> StepHandlerFn | None:
    """Return the registered handler for *name*, or ``None``."""
    return _GLOBAL_REGISTRY.get(name)


# ---------------------------------------------------------------------------
# Activity input type
# ---------------------------------------------------------------------------


@dataclass
class ExecuteStepInput:
    """Temporal-serialisable input for ``execute_step_activity``.

    All fields are Python primitives.  ``step_json`` carries a JSON-encoded
    ``PlanStep`` — this avoids requiring a custom Temporal payload converter for
    Pydantic models while keeping the activity interface self-contained.
    """

    task_id: str
    plan_id: str
    step_id: str
    handler_name: str
    trace_id: str
    step_json: str  # == PlanStep.model_dump_json()


# ---------------------------------------------------------------------------
# Temporal Activity
# ---------------------------------------------------------------------------


@activity.defn
async def execute_step_activity(inp: ExecuteStepInput) -> dict[str, Any]:
    """Temporal activity: resolve handler, execute step, return record dict.

    Returns a plain ``dict`` (the JSON dump of an ``ExecutionRecord``) so
    Temporal's default converter can round-trip the value without any custom
    payload converter setup.

    Handler resolution order:
    1. ``_GLOBAL_REGISTRY[inp.handler_name]``
    2. ``_GLOBAL_REGISTRY["default"]``   (fallback)
    3. Return a FAILED record if neither is found.
    """
    handler = _GLOBAL_REGISTRY.get(inp.handler_name) or _GLOBAL_REGISTRY.get("default")
    started_at = datetime.now(timezone.utc)
    key = f"{inp.task_id}:{inp.step_id}"

    if handler is None:
        return ExecutionRecord(
            idempotency_key=key,
            step_id=inp.step_id,
            task_id=inp.task_id,
            trace_id=inp.trace_id,
            status=StepExecutionStatus.FAILED,
            output=None,
            error=f"No handler registered for {inp.handler_name!r}",
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
        ).model_dump(mode="json")

    step = PlanStep.model_validate_json(inp.step_json)

    try:
        status, output, error = handler(step)
    except Exception as exc:  # Catch-all: handler failures must not abort the workflow.
        return ExecutionRecord(
            idempotency_key=key,
            step_id=inp.step_id,
            task_id=inp.task_id,
            trace_id=inp.trace_id,
            status=StepExecutionStatus.FAILED,
            output=None,
            error=str(exc),
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
        ).model_dump(mode="json")

    return ExecutionRecord(
        idempotency_key=key,
        step_id=inp.step_id,
        task_id=inp.task_id,
        trace_id=inp.trace_id,
        status=status,
        output=output,
        error=error,
        started_at=started_at,
        ended_at=datetime.now(timezone.utc),
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Temporal Workflow
# ---------------------------------------------------------------------------


@workflow.defn
class PlanWorkflow:
    """Temporal workflow that executes every step of a Plan in order.

    Accepts the plan as a JSON string so the default Temporal payload converter
    handles serialisation without requiring ``temporalio.contrib.pydantic``.
    """

    @workflow.run
    async def run(self, plan_json: str, trace_id: str = "") -> list[dict[str, Any]]:
        """Execute all steps of *plan_json* in order and return record dicts."""
        plan = Plan.model_validate_json(plan_json)
        resolved_trace = trace_id or str(workflow.uuid4())
        results: list[dict[str, Any]] = []

        for step in plan.steps:
            record_dict = await workflow.execute_activity(
                execute_step_activity,
                ExecuteStepInput(
                    task_id=plan.task_id,
                    plan_id=plan.plan_id,
                    step_id=step.step_id,
                    handler_name=step.handler_name,
                    trace_id=resolved_trace,
                    step_json=step.model_dump_json(),
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            results.append(record_dict)

        return results


# ---------------------------------------------------------------------------
# TemporalPlanRunner
# ---------------------------------------------------------------------------


class TemporalPlanRunner:
    """High-level wrapper for running a ``Plan`` via the Temporal backend.

    Inject an instance of this class via ``app.state.temporal_runner``; it
    is created during the FastAPI application lifespan when ``TEMPORAL_HOST``
    is configured.
    """

    DEFAULT_TASK_QUEUE = "agent-runtime"

    def __init__(self, client: Client, task_queue: str = DEFAULT_TASK_QUEUE) -> None:
        self._client = client
        self._task_queue = task_queue

    async def run_plan(self, plan: Plan, trace_id: str = "") -> list[ExecutionRecord]:
        """Start a ``PlanWorkflow`` and await all step results.

        Args:
            plan:     The plan to execute.  Each step's ``handler_name`` must
                      be registered via ``register_handler()`` on every worker
                      that will process the workflow.
            trace_id: Correlation ID propagated into every ``ExecutionRecord``.

        Returns:
            ``ExecutionRecord`` list in step order.

        Raises:
            ``temporalio.exceptions.WorkflowFailureError`` if the workflow
            fails after exhausting retries.
        """
        raw: list[dict[str, Any]] = await self._client.execute_workflow(
            PlanWorkflow.run,
            args=[plan.model_dump_json(), trace_id or str(uuid.uuid4())],
            id=f"plan-{plan.plan_id}",
            task_queue=self._task_queue,
        )
        return [ExecutionRecord.model_validate(r) for r in raw]
