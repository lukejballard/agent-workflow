"""Tests for agent_runtime.events."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent_runtime.events import (
    AgentEvent,
    EventType,
    make_approval_required_event,
    make_state_transition_event,
    make_tool_finished_event,
    make_tool_started_event,
)
from agent_runtime.schemas import TaskState, ToolCallStatus


# ---------------------------------------------------------------------------
# AgentEvent model validation
# ---------------------------------------------------------------------------


class TestAgentEvent:
    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentEvent(
                event_id="e1",
                event_type=EventType.TASK_STATE_TRANSITION,
                trace_id="t1",
                task_id="task1",
                occurred_at=datetime.now(timezone.utc),
                sequence=0,
                unknown_extra="oops",
            )

    def test_negative_sequence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentEvent(
                event_id="e1",
                event_type=EventType.TASK_STATE_TRANSITION,
                trace_id="t1",
                task_id="task1",
                occurred_at=datetime.now(timezone.utc),
                sequence=-1,
            )

    def test_optional_fields_default_to_none(self) -> None:
        event = AgentEvent(
            event_id="e1",
            event_type=EventType.TOOL_CALL_STARTED,
            trace_id="t1",
            task_id="task1",
            occurred_at=datetime.now(timezone.utc),
            sequence=0,
        )
        assert event.run_id is None
        assert event.step_id is None

    def test_payload_defaults_to_empty_dict(self) -> None:
        event = AgentEvent(
            event_id="e1",
            event_type=EventType.TOOL_CALL_STARTED,
            trace_id="t1",
            task_id="task1",
            occurred_at=datetime.now(timezone.utc),
            sequence=0,
        )
        assert event.payload == {}

    def test_occurred_at_is_datetime(self) -> None:
        now = datetime.now(timezone.utc)
        event = AgentEvent(
            event_id="e1",
            event_type=EventType.APPROVAL_REQUIRED,
            trace_id="t1",
            task_id="task1",
            occurred_at=now,
            sequence=0,
        )
        assert isinstance(event.occurred_at, datetime)


# ---------------------------------------------------------------------------
# make_state_transition_event
# ---------------------------------------------------------------------------


def test_make_state_transition_event_has_correct_type() -> None:
    event = make_state_transition_event(
        task_id="task1",
        trace_id="trace1",
        from_state=TaskState.PENDING,
        to_state=TaskState.PLANNING,
        sequence=1,
    )
    assert event.event_type == EventType.TASK_STATE_TRANSITION


def test_make_state_transition_event_payload_contains_states() -> None:
    event = make_state_transition_event(
        task_id="task1",
        trace_id="trace1",
        from_state=TaskState.PENDING,
        to_state=TaskState.PLANNING,
        sequence=1,
    )
    assert event.payload["from_state"] == TaskState.PENDING.value
    assert event.payload["to_state"] == TaskState.PLANNING.value


def test_make_state_transition_event_has_unique_event_ids() -> None:
    e1 = make_state_transition_event(
        task_id="task1", trace_id="t1",
        from_state=TaskState.PENDING, to_state=TaskState.PLANNING, sequence=0,
    )
    e2 = make_state_transition_event(
        task_id="task1", trace_id="t1",
        from_state=TaskState.PENDING, to_state=TaskState.PLANNING, sequence=1,
    )
    assert e1.event_id != e2.event_id


def test_make_state_transition_event_run_id_optional() -> None:
    event = make_state_transition_event(
        task_id="t", trace_id="tr",
        from_state=TaskState.PENDING, to_state=TaskState.PLANNING,
        sequence=0, run_id="run-99",
    )
    assert event.run_id == "run-99"


# ---------------------------------------------------------------------------
# make_tool_started_event
# ---------------------------------------------------------------------------


def test_make_tool_started_event_has_correct_type() -> None:
    event = make_tool_started_event(
        task_id="task1",
        trace_id="trace1",
        step_id="step1",
        tool_name="read_file",
        call_id="call1",
        sequence=5,
    )
    assert event.event_type == EventType.TOOL_CALL_STARTED


def test_make_tool_started_event_carries_step_id() -> None:
    event = make_tool_started_event(
        task_id="task1", trace_id="t1", step_id="step-x",
        tool_name="read_file", call_id="c1", sequence=0,
    )
    assert event.step_id == "step-x"


def test_make_tool_started_event_payload_contains_tool_and_call_id() -> None:
    event = make_tool_started_event(
        task_id="t", trace_id="tr", step_id="s",
        tool_name="grep_search", call_id="call-42", sequence=0,
    )
    assert event.payload["tool_name"] == "grep_search"
    assert event.payload["call_id"] == "call-42"


# ---------------------------------------------------------------------------
# make_tool_finished_event
# ---------------------------------------------------------------------------


def test_make_tool_finished_event_success_maps_to_finished_type() -> None:
    event = make_tool_finished_event(
        task_id="task1", trace_id="t1", step_id="s1",
        tool_name="read_file", call_id="c1",
        status=ToolCallStatus.SUCCESS, sequence=6,
    )
    assert event.event_type == EventType.TOOL_CALL_FINISHED


@pytest.mark.parametrize("status", [ToolCallStatus.ERROR, ToolCallStatus.TIMEOUT])
def test_make_tool_finished_event_failure_maps_to_failed_type(status: ToolCallStatus) -> None:
    event = make_tool_finished_event(
        task_id="task1", trace_id="t1", step_id="s1",
        tool_name="read_file", call_id="c1",
        status=status, sequence=7,
    )
    assert event.event_type == EventType.TOOL_CALL_FAILED


def test_make_tool_finished_event_denied_maps_to_failed_type() -> None:
    event = make_tool_finished_event(
        task_id="t", trace_id="tr", step_id="s",
        tool_name="run_in_terminal", call_id="c",
        status=ToolCallStatus.DENIED, sequence=0,
    )
    assert event.event_type == EventType.TOOL_CALL_FAILED


def test_make_tool_finished_event_payload_contains_status() -> None:
    event = make_tool_finished_event(
        task_id="t", trace_id="tr", step_id="s",
        tool_name="read_file", call_id="c",
        status=ToolCallStatus.SUCCESS, sequence=0,
    )
    assert event.payload["status"] == ToolCallStatus.SUCCESS.value


# ---------------------------------------------------------------------------
# make_approval_required_event
# ---------------------------------------------------------------------------


def test_make_approval_required_event_has_correct_type() -> None:
    event = make_approval_required_event(
        task_id="task1", trace_id="t1",
        tool_name="github_push",
        reason="remote write requires approval",
        sequence=3,
    )
    assert event.event_type == EventType.APPROVAL_REQUIRED


def test_make_approval_required_event_payload_contains_tool_and_reason() -> None:
    event = make_approval_required_event(
        task_id="task1", trace_id="t1",
        tool_name="github_push",
        reason="remote write requires approval",
        sequence=3,
    )
    assert event.payload["tool_name"] == "github_push"
    assert event.payload["reason"] == "remote write requires approval"


def test_make_approval_required_event_step_id_optional() -> None:
    event = make_approval_required_event(
        task_id="t", trace_id="tr",
        tool_name="github_push", reason="needs approval",
        sequence=0, step_id="step-1",
    )
    assert event.step_id == "step-1"
