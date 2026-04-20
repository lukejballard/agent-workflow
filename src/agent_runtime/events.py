"""Typed event envelope for agent runtime state changes and tool calls."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agent_runtime.schemas import TaskState, ToolCallStatus


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    TASK_STATE_TRANSITION = "task.state_transition"
    TOOL_CALL_STARTED = "tool.call.started"
    TOOL_CALL_FINISHED = "tool.call.finished"
    TOOL_CALL_FAILED = "tool.call.failed"
    TOOL_CALL_DENIED = "tool.call.denied"
    APPROVAL_REQUIRED = "task.approval_required"


# ---------------------------------------------------------------------------
# Event envelope
# ---------------------------------------------------------------------------


class AgentEvent(BaseModel):
    """Immutable event envelope emitted by every significant runtime transition."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: EventType
    trace_id: str
    run_id: str | None = None
    task_id: str
    step_id: str | None = None
    occurred_at: datetime
    sequence: int = Field(ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


def make_state_transition_event(
    *,
    task_id: str,
    trace_id: str,
    from_state: TaskState,
    to_state: TaskState,
    sequence: int,
    run_id: str | None = None,
) -> AgentEvent:
    """Create a task.state_transition event."""
    return AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.TASK_STATE_TRANSITION,
        trace_id=trace_id,
        run_id=run_id,
        task_id=task_id,
        occurred_at=datetime.now(timezone.utc),
        sequence=sequence,
        payload={"from_state": from_state.value, "to_state": to_state.value},
    )


def make_tool_started_event(
    *,
    task_id: str,
    trace_id: str,
    step_id: str,
    tool_name: str,
    call_id: str,
    sequence: int,
    run_id: str | None = None,
) -> AgentEvent:
    """Create a tool.call.started event."""
    return AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.TOOL_CALL_STARTED,
        trace_id=trace_id,
        run_id=run_id,
        task_id=task_id,
        step_id=step_id,
        occurred_at=datetime.now(timezone.utc),
        sequence=sequence,
        payload={"tool_name": tool_name, "call_id": call_id},
    )


def make_tool_finished_event(
    *,
    task_id: str,
    trace_id: str,
    step_id: str,
    tool_name: str,
    call_id: str,
    status: ToolCallStatus,
    sequence: int,
    run_id: str | None = None,
) -> AgentEvent:
    """Create a tool.call.finished (success) or tool.call.failed event."""
    event_type = (
        EventType.TOOL_CALL_FINISHED
        if status == ToolCallStatus.SUCCESS
        else EventType.TOOL_CALL_FAILED
    )
    return AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        trace_id=trace_id,
        run_id=run_id,
        task_id=task_id,
        step_id=step_id,
        occurred_at=datetime.now(timezone.utc),
        sequence=sequence,
        payload={"tool_name": tool_name, "call_id": call_id, "status": status.value},
    )


def make_approval_required_event(
    *,
    task_id: str,
    trace_id: str,
    tool_name: str,
    reason: str,
    sequence: int,
    step_id: str | None = None,
    run_id: str | None = None,
) -> AgentEvent:
    """Create a task.approval_required event."""
    return AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.APPROVAL_REQUIRED,
        trace_id=trace_id,
        run_id=run_id,
        task_id=task_id,
        step_id=step_id,
        occurred_at=datetime.now(timezone.utc),
        sequence=sequence,
        payload={"tool_name": tool_name, "reason": reason},
    )
