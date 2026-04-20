"""Tests for agent_runtime.state_machine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from agent_runtime.schemas import Task, TaskState
from agent_runtime.state_machine import (
    ALLOWED_TRANSITIONS,
    StateTransitionError,
    is_terminal,
    transition,
)


def _make_task(state: TaskState = TaskState.PENDING) -> Task:
    now = datetime.now(timezone.utc)
    return Task(
        task_id=str(uuid.uuid4()),
        objective="test objective",
        state=state,
        trace_id=str(uuid.uuid4()),
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", [TaskState.DONE, TaskState.FAILED, TaskState.CANCELLED])
def test_is_terminal_returns_true_for_terminal_states(state: TaskState) -> None:
    assert is_terminal(state) is True


@pytest.mark.parametrize(
    "state",
    [
        TaskState.PENDING,
        TaskState.PLANNING,
        TaskState.EXECUTING,
        TaskState.VALIDATING,
        TaskState.LEARNING,
    ],
)
def test_is_terminal_returns_false_for_active_states(state: TaskState) -> None:
    assert is_terminal(state) is False


# ---------------------------------------------------------------------------
# Allowed transitions
# ---------------------------------------------------------------------------

_ALLOWED_CASES: list[tuple[TaskState, TaskState]] = [
    (TaskState.PENDING, TaskState.PLANNING),
    (TaskState.PLANNING, TaskState.EXECUTING),
    (TaskState.PLANNING, TaskState.FAILED),
    (TaskState.PLANNING, TaskState.CANCELLED),
    (TaskState.EXECUTING, TaskState.VALIDATING),
    (TaskState.EXECUTING, TaskState.FAILED),
    (TaskState.EXECUTING, TaskState.CANCELLED),
    (TaskState.VALIDATING, TaskState.LEARNING),
    (TaskState.VALIDATING, TaskState.EXECUTING),  # revision loop
    (TaskState.VALIDATING, TaskState.FAILED),
    (TaskState.VALIDATING, TaskState.CANCELLED),
    (TaskState.LEARNING, TaskState.DONE),
    (TaskState.LEARNING, TaskState.FAILED),
]


@pytest.mark.parametrize("from_state,to_state", _ALLOWED_CASES)
def test_allowed_transition_updates_state(from_state: TaskState, to_state: TaskState) -> None:
    task = _make_task(from_state)
    updated = transition(task, to_state)
    assert updated.state == to_state


def test_transition_returns_new_task_not_mutating_original() -> None:
    task = _make_task(TaskState.PENDING)
    updated = transition(task, TaskState.PLANNING)
    assert updated is not task
    assert task.state == TaskState.PENDING


def test_transition_updates_updated_at_timestamp() -> None:
    task = _make_task(TaskState.PENDING)
    original_ts = task.updated_at
    updated = transition(task, TaskState.PLANNING)
    assert updated.updated_at >= original_ts


def test_transition_preserves_other_fields() -> None:
    task = _make_task(TaskState.PENDING)
    updated = transition(task, TaskState.PLANNING)
    assert updated.task_id == task.task_id
    assert updated.objective == task.objective
    assert updated.trace_id == task.trace_id


# ---------------------------------------------------------------------------
# Forbidden transitions
# ---------------------------------------------------------------------------

_FORBIDDEN_CASES: list[tuple[TaskState, TaskState]] = [
    (TaskState.PENDING, TaskState.EXECUTING),
    (TaskState.PENDING, TaskState.DONE),
    (TaskState.PENDING, TaskState.FAILED),
    (TaskState.PLANNING, TaskState.VALIDATING),
    (TaskState.PLANNING, TaskState.DONE),
    (TaskState.EXECUTING, TaskState.PLANNING),
    (TaskState.EXECUTING, TaskState.DONE),
    (TaskState.LEARNING, TaskState.PLANNING),
    (TaskState.LEARNING, TaskState.CANCELLED),
]


@pytest.mark.parametrize("from_state,to_state", _FORBIDDEN_CASES)
def test_forbidden_transition_raises(from_state: TaskState, to_state: TaskState) -> None:
    task = _make_task(from_state)
    with pytest.raises(StateTransitionError):
        transition(task, to_state)


# ---------------------------------------------------------------------------
# Terminal states block all outgoing transitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("terminal", [TaskState.DONE, TaskState.FAILED, TaskState.CANCELLED])
@pytest.mark.parametrize("target", list(TaskState))
def test_terminal_state_blocks_all_transitions(terminal: TaskState, target: TaskState) -> None:
    task = _make_task(terminal)
    with pytest.raises(StateTransitionError):
        transition(task, target)


# ---------------------------------------------------------------------------
# ALLOWED_TRANSITIONS completeness
# ---------------------------------------------------------------------------


def test_allowed_transitions_covers_all_states() -> None:
    """Every TaskState must have an entry in the transition table."""
    for state in TaskState:
        assert state in ALLOWED_TRANSITIONS, f"{state} missing from ALLOWED_TRANSITIONS"


# ---------------------------------------------------------------------------
# Error attributes
# ---------------------------------------------------------------------------


def test_state_transition_error_exposes_from_and_to_state() -> None:
    task = _make_task(TaskState.PENDING)
    with pytest.raises(StateTransitionError) as exc_info:
        transition(task, TaskState.DONE)
    err = exc_info.value
    assert err.from_state == TaskState.PENDING
    assert err.to_state == TaskState.DONE


def test_state_transition_error_message_contains_state_names() -> None:
    task = _make_task(TaskState.PENDING)
    with pytest.raises(StateTransitionError) as exc_info:
        transition(task, TaskState.DONE)
    assert "PENDING" in str(exc_info.value)
    assert "DONE" in str(exc_info.value)
