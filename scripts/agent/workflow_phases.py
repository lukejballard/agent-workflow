"""Orchestrator workflow phase state machine.

Encodes the allowed transitions between the 10-phase orchestrator workflow
defined in workflow-manifest.json plus terminal states (aborted, escalated).
Distinct from src/agent_runtime/state_machine.py which governs task-level
runtime states (PENDING→PLANNING→…→DONE).

Usage (library):
    from scripts.agent.workflow_phases import (
        WorkflowPhase,
        InvalidTransitionError,
        validate_transition,
        validate_packet,
    )

Usage (CLI):
    python scripts/agent/workflow_phases.py validate-transition classify execute-or-answer
    python scripts/agent/workflow_phases.py validate-packet path/to/packet.json
    python scripts/agent/workflow_phases.py list-transitions classify
    python scripts/agent/workflow_phases.py set-phase execute-or-answer
    python scripts/agent/workflow_phases.py get-phase
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Phase enum
# ---------------------------------------------------------------------------

class WorkflowPhase(str, Enum):
    """All valid phases in the orchestrator workflow."""

    GOAL_ANCHOR           = "goal-anchor"
    CLASSIFY              = "classify"
    BREADTH_SCAN          = "breadth-scan"
    DEPTH_DIVE            = "depth-dive"
    LOCK_REQUIREMENTS     = "lock-requirements"
    CHOOSE_APPROACH       = "choose-approach"
    ADVERSARIAL_CRITIQUE  = "adversarial-critique"
    REVISE                = "revise"
    EXECUTE_OR_ANSWER     = "execute-or-answer"
    TRACEABILITY_AND_VERIFY = "traceability-and-verify"
    # Terminal states
    ABORTED               = "aborted"
    ESCALATED             = "escalated"


# Phases that count as "not yet classified" — edits are pre-mature in these.
PRE_CLASSIFICATION_PHASES: frozenset[WorkflowPhase] = frozenset({
    WorkflowPhase.GOAL_ANCHOR,
    WorkflowPhase.CLASSIFY,
})

# Phases from which no outgoing transition is allowed.
TERMINAL_PHASES: frozenset[WorkflowPhase] = frozenset({
    WorkflowPhase.ABORTED,
    WorkflowPhase.ESCALATED,
})

# ---------------------------------------------------------------------------
# Allowed transition table
# ---------------------------------------------------------------------------
# Design principles:
#   • Normal sequential flow — each phase advances to the next.
#   • Trivial-task shortcut — classify → execute-or-answer (skip spec/plan steps).
#   • Depth-skip — breadth-scan → choose-approach (shallow task, skip depth-dive).
#   • Spec-skip — depth-dive → choose-approach (no spec needed for this classification).
#   • Low-risk skip — choose-approach → execute-or-answer (skip adversarial critique).
#   • Critique PASS — adversarial-critique → execute-or-answer.
#   • Critique REJECT — adversarial-critique → revise.
#   • Retry loop — revise → adversarial-critique (max 2 passes enforced by orchestrator).
#   • Major revision — revise → choose-approach (approach itself must change).
#   • Any non-terminal phase → aborted (emergency exit).
#   • Any non-terminal phase → escalated (confidence-based exit).

ALLOWED_TRANSITIONS: dict[WorkflowPhase, frozenset[WorkflowPhase]] = {
    WorkflowPhase.GOAL_ANCHOR: frozenset({
        WorkflowPhase.CLASSIFY,
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.CLASSIFY: frozenset({
        WorkflowPhase.BREADTH_SCAN,        # normal
        WorkflowPhase.EXECUTE_OR_ANSWER,   # trivial shortcut
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.BREADTH_SCAN: frozenset({
        WorkflowPhase.DEPTH_DIVE,          # normal
        WorkflowPhase.CHOOSE_APPROACH,     # shallow task, skip depth-dive
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.DEPTH_DIVE: frozenset({
        WorkflowPhase.LOCK_REQUIREMENTS,   # normal
        WorkflowPhase.CHOOSE_APPROACH,     # no spec needed for this classification
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.LOCK_REQUIREMENTS: frozenset({
        WorkflowPhase.CHOOSE_APPROACH,
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.CHOOSE_APPROACH: frozenset({
        WorkflowPhase.ADVERSARIAL_CRITIQUE, # normal
        WorkflowPhase.EXECUTE_OR_ANSWER,    # low-risk, skip critique
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.ADVERSARIAL_CRITIQUE: frozenset({
        WorkflowPhase.REVISE,              # REJECT verdict
        WorkflowPhase.EXECUTE_OR_ANSWER,   # PASS verdict
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.REVISE: frozenset({
        WorkflowPhase.ADVERSARIAL_CRITIQUE, # retry critique
        WorkflowPhase.EXECUTE_OR_ANSWER,    # auto-approve after revise
        WorkflowPhase.CHOOSE_APPROACH,      # major revision — re-plan
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.EXECUTE_OR_ANSWER: frozenset({
        WorkflowPhase.TRACEABILITY_AND_VERIFY,
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    WorkflowPhase.TRACEABILITY_AND_VERIFY: frozenset({
        WorkflowPhase.ABORTED,
        WorkflowPhase.ESCALATED,
    }),
    # Terminal states allow no outgoing transitions.
    WorkflowPhase.ABORTED:   frozenset(),
    WorkflowPhase.ESCALATED: frozenset(),
}


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class InvalidTransitionError(ValueError):
    """Raised when a phase transition is not in the allowed table."""

    def __init__(self, from_phase: WorkflowPhase, to_phase: WorkflowPhase) -> None:
        super().__init__(
            f"Transition from {from_phase.value!r} to {to_phase.value!r} is not allowed."
        )
        self.from_phase = from_phase
        self.to_phase = to_phase


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def is_terminal(phase: WorkflowPhase) -> bool:
    """Return True if *phase* is a terminal phase (no outgoing transitions)."""
    return phase in TERMINAL_PHASES


def validate_transition(from_phase: WorkflowPhase | str, to_phase: WorkflowPhase | str) -> bool:
    """Return True when the transition *from_phase* → *to_phase* is allowed.

    Accepts either WorkflowPhase enum values or raw phase-name strings.
    Raises ValueError for unrecognised phase names.
    """
    if isinstance(from_phase, str):
        from_phase = WorkflowPhase(from_phase)
    if isinstance(to_phase, str):
        to_phase = WorkflowPhase(to_phase)
    return to_phase in ALLOWED_TRANSITIONS[from_phase]


def transition(from_phase: WorkflowPhase | str, to_phase: WorkflowPhase | str) -> WorkflowPhase:
    """Advance from *from_phase* to *to_phase*, returning the new phase.

    Raises InvalidTransitionError when the transition is not allowed.
    """
    if isinstance(from_phase, str):
        from_phase = WorkflowPhase(from_phase)
    if isinstance(to_phase, str):
        to_phase = WorkflowPhase(to_phase)
    if not validate_transition(from_phase, to_phase):
        raise InvalidTransitionError(from_phase, to_phase)
    return to_phase


def list_transitions(phase: WorkflowPhase | str) -> list[WorkflowPhase]:
    """Return the allowed successor phases from *phase*, sorted by name."""
    if isinstance(phase, str):
        phase = WorkflowPhase(phase)
    return sorted(ALLOWED_TRANSITIONS[phase], key=lambda p: p.value)


# ---------------------------------------------------------------------------
# Context packet validation
# ---------------------------------------------------------------------------

# Valid phase strings accepted in context packets (matches context-packet.schema.json).
_VALID_PHASE_VALUES: frozenset[str] = frozenset(p.value for p in WorkflowPhase)


def validate_packet(packet: dict[str, Any]) -> list[str]:
    """Validate context-packet fields that relate to workflow phases.

    Returns a list of error strings (empty when the packet is valid).
    Designed to be called from sync_agent_platform.py alongside the
    existing validate_context_packet_example checks.
    """
    errors: list[str] = []

    raw_phase = packet.get("current_phase")
    if raw_phase is None:
        errors.append("context packet is missing required field 'current_phase'")
        return errors

    if not isinstance(raw_phase, str):
        errors.append(f"context packet 'current_phase' must be a string, got {type(raw_phase).__name__}")
        return errors

    if raw_phase not in _VALID_PHASE_VALUES:
        errors.append(
            f"context packet 'current_phase' value {raw_phase!r} is not a recognised workflow phase. "
            f"Valid values: {sorted(_VALID_PHASE_VALUES)}"
        )

    return errors


# ---------------------------------------------------------------------------
# Session file integration (shared with pretool_approval_policy.py)
# ---------------------------------------------------------------------------

_SESSION_FILE = os.environ.get("AGENT_SESSION_FILE", "/tmp/agent-budget.json")


def _read_session() -> dict[str, Any]:
    try:
        return json.loads(Path(_SESSION_FILE).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_session(data: dict[str, Any]) -> None:
    path = Path(_SESSION_FILE)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(path)
    except OSError:
        pass


def set_workflow_phase(phase: WorkflowPhase | str) -> WorkflowPhase:
    """Persist *phase* in the session file and return the WorkflowPhase.

    Validates the transition from the current session phase before writing.
    Raises InvalidTransitionError when the transition is not allowed.
    Raises ValueError for unrecognised phase names.
    """
    if isinstance(phase, str):
        phase = WorkflowPhase(phase)

    data = _read_session()
    raw_current = data.get("current_phase")

    if raw_current is not None:
        try:
            current = WorkflowPhase(raw_current)
        except ValueError:
            # Unknown current phase in session file — allow overwrite.
            current = None
        if current is not None and not validate_transition(current, phase):
            raise InvalidTransitionError(current, phase)

    data["current_phase"] = phase.value
    _write_session(data)
    return phase


def get_workflow_phase() -> WorkflowPhase | None:
    """Return the current workflow phase from the session file, or None."""
    raw = _read_session().get("current_phase")
    if raw is None:
        return None
    try:
        return WorkflowPhase(raw)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_validate_transition(args: argparse.Namespace) -> int:
    try:
        ok = validate_transition(args.from_phase, args.to_phase)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if ok:
        print(f"ALLOWED: {args.from_phase!r} → {args.to_phase!r}")
        return 0
    print(f"FORBIDDEN: {args.from_phase!r} → {args.to_phase!r}", file=sys.stderr)
    return 1


def _cmd_validate_packet(args: argparse.Namespace) -> int:
    try:
        packet = json.loads(Path(args.file).read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR reading packet: {exc}", file=sys.stderr)
        return 2
    errors = validate_packet(packet)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    phase = packet.get("current_phase", "(none)")
    print(f"OK: current_phase={phase!r}")
    return 0


def _cmd_list_transitions(args: argparse.Namespace) -> int:
    try:
        successors = list_transitions(args.phase)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if successors:
        print(f"From {args.phase!r} the following transitions are allowed:")
        for p in successors:
            print(f"  → {p.value}")
    else:
        print(f"No outgoing transitions from {args.phase!r} (terminal phase).")
    return 0


def _cmd_set_phase(args: argparse.Namespace) -> int:
    try:
        phase = set_workflow_phase(args.phase)
    except InvalidTransitionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Phase set to {phase.value!r} in {_SESSION_FILE}")
    return 0


def _cmd_get_phase(_args: argparse.Namespace) -> int:
    phase = get_workflow_phase()
    if phase is None:
        print("(no current_phase in session file)")
        return 0
    print(phase.value)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Orchestrator workflow phase state machine CLI."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_vt = sub.add_parser("validate-transition", help="Check whether a phase transition is allowed.")
    p_vt.add_argument("from_phase", help="Source phase name.")
    p_vt.add_argument("to_phase", help="Target phase name.")

    p_vp = sub.add_parser("validate-packet", help="Validate current_phase in a context packet JSON.")
    p_vp.add_argument("file", help="Path to the context packet JSON file.")

    p_lt = sub.add_parser("list-transitions", help="List all allowed transitions from a phase.")
    p_lt.add_argument("phase", help="Source phase name.")

    p_sp = sub.add_parser("set-phase", help="Write current_phase to the session file.")
    p_sp.add_argument("phase", help="Phase name to set.")

    sub.add_parser("get-phase", help="Read current_phase from the session file.")

    args = parser.parse_args(argv)

    dispatch = {
        "validate-transition": _cmd_validate_transition,
        "validate-packet":     _cmd_validate_packet,
        "list-transitions":    _cmd_list_transitions,
        "set-phase":           _cmd_set_phase,
        "get-phase":           _cmd_get_phase,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
