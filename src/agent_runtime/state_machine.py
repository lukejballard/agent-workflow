"""Task state machine — pure transition logic with no I/O."""

from __future__ import annotations

from datetime import datetime, timezone

from agent_runtime.schemas import Task, TaskState

# ---------------------------------------------------------------------------
# Allowed transition table
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.PENDING: frozenset({TaskState.PLANNING}),
    TaskState.PLANNING: frozenset({
        TaskState.EXECUTING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    }),
    TaskState.EXECUTING: frozenset({
        TaskState.VALIDATING,
        TaskState.FAILED,
        TaskState.CANCELLED,
    }),
    TaskState.VALIDATING: frozenset({
        TaskState.LEARNING,
        TaskState.EXECUTING,  # revision loop
        TaskState.FAILED,
        TaskState.CANCELLED,
    }),
    TaskState.LEARNING: frozenset({
        TaskState.DONE,
        TaskState.FAILED,
    }),
    TaskState.DONE: frozenset(),
    TaskState.FAILED: frozenset(),
    TaskState.CANCELLED: frozenset(),
}

_TERMINAL_STATES: frozenset[TaskState] = frozenset({
    TaskState.DONE,
    TaskState.FAILED,
    TaskState.CANCELLED,
})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class StateTransitionError(Exception):
    """Raised when a state transition is not in the allowed table."""

    def __init__(self, from_state: TaskState, to_state: TaskState) -> None:
        super().__init__(
            f"Transition from {from_state.value!r} to {to_state.value!r} is not allowed."
        )
        self.from_state = from_state
        self.to_state = to_state


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_terminal(state: TaskState) -> bool:
    """Return True if *state* is a terminal (non-transitionable) state."""
    return state in _TERMINAL_STATES


def transition(task: Task, target: TaskState) -> Task:
    """Return a new Task with its state updated to *target*.

    The original task is not mutated.

    Raises:
        StateTransitionError: if the transition is not in the allowed table.
    """
    allowed = ALLOWED_TRANSITIONS.get(task.state, frozenset())
    if target not in allowed:
        raise StateTransitionError(task.state, target)
    return task.model_copy(update={"state": target, "updated_at": datetime.now(timezone.utc)})
