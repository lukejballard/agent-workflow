"""FastAPI router for agent-runtime task lifecycle endpoints.

All state is held in a ``RuntimeStore`` dataclass that is injected via
FastAPI's dependency system.  Pass a fresh store in tests by overriding
``get_store`` through ``app.dependency_overrides``.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent_runtime.events import AgentEvent
from agent_runtime.planner import BasicPlanner, PlannerError
from agent_runtime.schemas import Plan, PlanStep, Task, TaskState
from agent_runtime.state_machine import StateTransitionError, transition


# ---------------------------------------------------------------------------
# In-memory store (injectable)
# ---------------------------------------------------------------------------


@dataclass
class RuntimeStore:
    """Mutable in-memory store for tasks, plans, and task events.

    Use ``app.dependency_overrides[get_store] = lambda: RuntimeStore()``
    in tests to ensure per-test isolation.
    """

    tasks: dict[str, Task] = field(default_factory=dict)
    plans: dict[str, Plan] = field(default_factory=dict)
    events: dict[str, list[AgentEvent]] = field(default_factory=dict)


_default_store: RuntimeStore = RuntimeStore()


def get_store() -> RuntimeStore:
    """Return the singleton store.  Override for test isolation."""
    return _default_store


def configure_store(store: RuntimeStore) -> None:  # type: ignore[type-arg]
    """Replace the module-level default store.

    Call this during application startup to substitute a persistent backend.
    Tests should use ``app.dependency_overrides[get_store]`` instead so that
    each test gets an isolated in-memory instance.
    """
    global _default_store
    _default_store = store  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class CreateTaskRequest(BaseModel):
    objective: str
    trace_id: str = ""


class TransitionRequest(BaseModel):
    target_state: TaskState


class CreatePlanRequest(BaseModel):
    steps: list[PlanStep]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["agent-runtime"])


@router.post("/tasks", status_code=201)
def create_task(
    body: CreateTaskRequest,
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> Task:
    """Create a new task in PENDING state."""
    now = datetime.now(timezone.utc)
    task = Task(
        task_id=str(uuid.uuid4()),
        objective=body.objective,
        state=TaskState.PENDING,
        trace_id=body.trace_id or str(uuid.uuid4()),
        created_at=now,
        updated_at=now,
    )
    store.tasks[task.task_id] = task
    return task


@router.get("/tasks")
def list_tasks(
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> list[Task]:
    """Return all tasks."""
    return list(store.tasks.values())


@router.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> Task:
    """Return a single task by ID, or 404 if not found."""
    task = store.tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/transitions")
def transition_task(
    task_id: str,
    body: TransitionRequest,
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> Task:
    """Advance a task's state via the state machine.

    Returns the updated task (200), or 404 / 422 on failure.
    """
    task = store.tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        updated = transition(task, body.target_state)
    except StateTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store.tasks[task_id] = updated
    return updated


@router.post("/tasks/{task_id}/plan", status_code=201)
def create_plan_for_task(
    task_id: str,
    body: CreatePlanRequest,
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> Plan:
    """Validate and attach a plan to an existing task.

    Returns 201 with the created plan, or 404 / 422 on failure.
    """
    task = store.tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    planner = BasicPlanner()
    try:
        plan = planner.create_plan(
            task_id=task_id,
            trace_id=task.trace_id,
            steps=body.steps,
        )
    except PlannerError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc
    store.plans[task_id] = plan
    return plan


@router.get("/tasks/{task_id}/plan")
def get_task_plan(
    task_id: str,
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> Plan:
    """Return the plan for a task, or 404 if task or plan is missing."""
    if task_id not in store.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    plan = store.plans.get(task_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/tasks/{task_id}/events")
async def stream_task_events(
    task_id: str,
    store: Annotated[RuntimeStore, Depends(get_store)],
) -> StreamingResponse:
    """Stream task events as Server-Sent Events (SSE).

    Yields a ``ping`` heartbeat followed by any buffered events for the task.
    The stream stays open; clients reconnect with ``EventSource`` on close.

    Returns 404 if the task does not exist.
    """
    if task_id not in store.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    buffered: list[AgentEvent] = list(store.events.get(task_id, []))

    async def _generate() -> AsyncIterator[str]:
        # Initial heartbeat so the client knows the connection is live.
        yield "data: ping\n\n"
        await asyncio.sleep(0)

        for event in buffered:
            yield f"data: {event.model_dump_json()}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
