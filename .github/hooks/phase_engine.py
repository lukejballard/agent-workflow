"""Phase state machine with advisory detection and enforcement."""
from __future__ import annotations

from session_schema import (
    PHASE_INDEX,
    SessionState,
)

BOOTSTRAP_FILES = frozenset(
    {
        ".github/agents.md",
        ".github/agent-platform/workflow-manifest.json",
    }
)

# Phases where edit tools are blocked
READ_ONLY_PHASES = frozenset(
    {
        "goal-anchor",
        "classify",
        "breadth-scan",
    }
)

# Phases where edits require explicit justification
CAUTION_PHASES = frozenset(
    {
        "depth-dive",
        "lock-requirements",
        "choose-approach",
        "adversarial-critique",
        "revise",
    }
)

# Phases where edits flow freely (within scope)
EDIT_PHASES = frozenset(
    {
        "execute-or-answer",
        "self-review",
        "critique",
        "traceability-and-verify",
    }
)

# Task classes that skip certain phases (from workflow-manifest.json)
PHASE_SKIP_RULES: dict[str, frozenset[str]] = {
    "trivial": frozenset(
        {"lock-requirements", "adversarial-critique", "revise"}
    ),
    "research-only": frozenset(
        {
            "lock-requirements",
            "choose-approach",
            "adversarial-critique",
            "revise",
            "execute-or-answer",
        }
    ),
    "review-only": frozenset(
        {
            "lock-requirements",
            "adversarial-critique",
            "revise",
            "execute-or-answer",
        }
    ),
    "docs-only": frozenset({"adversarial-critique"}),
    "test-only": frozenset({"adversarial-critique"}),
}


def is_bootstrap_complete(read_files: list[str]) -> bool:
    """Check if both bootstrap files have been read."""
    norm_reads = {r.replace("\\", "/").lower() for r in read_files}
    return all(
        any(read.endswith(boot) for read in norm_reads)
        for boot in BOOTSTRAP_FILES
    )


def detect_phase(state: SessionState) -> str:
    """Return an advisory phase suggestion without mutating state."""
    current_idx = PHASE_INDEX.get(state.current_phase, 0)

    if state.edit_count > 0:
        execute_idx = PHASE_INDEX["execute-or-answer"]
        if current_idx < execute_idx:
            return "execute-or-answer"
        return state.current_phase

    if not is_bootstrap_complete(state.read_files):
        return state.current_phase if current_idx >= 0 else "goal-anchor"

    if state.requirements_locked:
        lock_idx = PHASE_INDEX["lock-requirements"]
        if current_idx <= lock_idx:
            return "choose-approach"

    read_count = len(state.read_files)
    classify_idx = PHASE_INDEX["classify"]
    breadth_idx = PHASE_INDEX["breadth-scan"]
    depth_idx = PHASE_INDEX["depth-dive"]

    if read_count <= 2 and current_idx < classify_idx:
        return "classify"
    elif read_count <= 6 and current_idx < breadth_idx:
        return "breadth-scan"
    elif read_count > 6 and current_idx < depth_idx:
        return "depth-dive"

    return state.current_phase


def advance_phase(state: SessionState, target_phase: str) -> bool:
    """Advance to target phase using explicit session declaration."""
    success, _ = state.declare_phase(target_phase)
    return success


def can_edit_in_phase(
    state: SessionState,
) -> tuple[bool, str]:
    """Check if editing is allowed given the current phase and task class.

    Returns (allowed, reason). reason is empty when allowed.
    """
    phase = state.current_phase
    task_class = state.task_class

    if phase in EDIT_PHASES:
        return True, ""

    # Trivial and docs-only tasks may edit earlier
    if task_class in ("trivial", "docs-only"):
        if phase not in READ_ONLY_PHASES or task_class == "trivial":
            return True, ""

    if phase in READ_ONLY_PHASES:
        return False, (
            f"Edits are blocked during the '{phase}' phase. "
            "Complete bootstrap and context loading before editing."
        )

    if phase in CAUTION_PHASES:
        return False, (
            f"Edits during the '{phase}' phase require advancement to "
            "'execute-or-answer'. Lock requirements and complete planning first."
        )

    return True, ""


def get_skippable_phases(task_class: str) -> frozenset[str]:
    """Return the set of phases that can be skipped for a task class."""
    return PHASE_SKIP_RULES.get(task_class, frozenset())
