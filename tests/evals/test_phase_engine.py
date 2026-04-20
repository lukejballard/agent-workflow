"""Tests for phase state machine enforcement."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / ".github" / "hooks"))

from session_schema import SessionState, PHASE_INDEX
from phase_engine import (
    BOOTSTRAP_FILES,
    advance_phase,
    can_edit_in_phase,
    detect_phase,
    is_bootstrap_complete,
    get_skippable_phases,
)


class TestBootstrapDetection:
    def test_empty_reads_not_bootstrapped(self):
        assert not is_bootstrap_complete([])

    def test_partial_bootstrap_fails(self):
        assert not is_bootstrap_complete([".github/agents.md"])

    def test_full_bootstrap_passes(self):
        reads = [
            ".github/agents.md",
            ".github/agent-platform/workflow-manifest.json",
        ]
        assert is_bootstrap_complete(reads)

    def test_bootstrap_case_insensitive(self):
        reads = [
            ".GitHub/AGENTS.md",
            ".GitHub/Agent-Platform/Workflow-Manifest.json",
        ]
        assert is_bootstrap_complete(reads)

    def test_bootstrap_with_full_paths(self):
        reads = [
            "c:/users/dev/repo/.github/agents.md",
            "c:/users/dev/repo/.github/agent-platform/workflow-manifest.json",
        ]
        assert is_bootstrap_complete(reads)


class TestPhaseDetection:
    def test_initial_state_stays_at_goal_anchor(self):
        state = SessionState()
        assert detect_phase(state) == "goal-anchor"

    def test_bootstrap_triggers_classify(self):
        state = SessionState(
            read_files=[
                ".github/agents.md",
                ".github/agent-platform/workflow-manifest.json",
            ]
        )
        detected = detect_phase(state)
        assert detected == "classify"

    def test_many_reads_trigger_breadth_scan(self):
        state = SessionState(
            current_phase="classify",
            phase_index=PHASE_INDEX["classify"],
            read_files=[f"file{i}.py" for i in range(5)]
            + [
                ".github/agents.md",
                ".github/agent-platform/workflow-manifest.json",
            ],
            bootstrap_complete=True,
        )
        detected = detect_phase(state)
        assert detected == "depth-dive"

    def test_edits_force_execute_phase(self):
        state = SessionState(
            current_phase="classify",
            phase_index=PHASE_INDEX["classify"],
            edit_count=1,
        )
        detected = detect_phase(state)
        assert detected == "execute-or-answer"

    def test_never_detects_backward(self):
        state = SessionState(
            current_phase="execute-or-answer",
            phase_index=PHASE_INDEX["execute-or-answer"],
            read_files=["one.py"],
        )
        detected = detect_phase(state)
        assert PHASE_INDEX.get(detected, 0) >= PHASE_INDEX["execute-or-answer"]

    def test_requirements_locked_advances_past_gate(self):
        state = SessionState(
            current_phase="lock-requirements",
            phase_index=PHASE_INDEX["lock-requirements"],
            requirements_locked=True,
            bootstrap_complete=True,
            read_files=[f"f{i}" for i in range(10)]
            + [
                ".github/agents.md",
                ".github/agent-platform/workflow-manifest.json",
            ],
        )
        detected = detect_phase(state)
        assert detected == "choose-approach"


class TestPhaseAdvancement:
    def test_forward_advance_succeeds(self):
        state = SessionState()
        result = advance_phase(state, "classify")
        assert result is True
        assert state.current_phase == "classify"
        assert len(state.phase_history) == 1

    def test_backward_advance_fails(self):
        state = SessionState(
            current_phase="depth-dive",
            phase_index=PHASE_INDEX["depth-dive"],
        )
        result = advance_phase(state, "classify")
        assert result is False
        assert state.current_phase == "depth-dive"

    def test_same_phase_advance_fails(self):
        state = SessionState(
            current_phase="classify",
            phase_index=PHASE_INDEX["classify"],
        )
        result = advance_phase(state, "classify")
        assert result is False

    def test_history_records_transition(self):
        state = SessionState()
        advance_phase(state, "classify")
        entry = state.phase_history[0]
        assert entry["from"] == "goal-anchor"
        assert entry["to"] == "classify"
        assert "timestamp" in entry


class TestEditGates:
    def test_goal_anchor_blocks_edits(self):
        state = SessionState(current_phase="goal-anchor", phase_index=0)
        allowed, reason = can_edit_in_phase(state)
        assert not allowed
        assert "blocked" in reason.lower()

    def test_classify_blocks_edits(self):
        state = SessionState(
            current_phase="classify",
            phase_index=PHASE_INDEX["classify"],
        )
        allowed, _ = can_edit_in_phase(state)
        assert not allowed

    def test_breadth_scan_blocks_edits(self):
        state = SessionState(
            current_phase="breadth-scan",
            phase_index=PHASE_INDEX["breadth-scan"],
        )
        allowed, _ = can_edit_in_phase(state)
        assert not allowed

    def test_execute_allows_edits(self):
        state = SessionState(
            current_phase="execute-or-answer",
            phase_index=PHASE_INDEX["execute-or-answer"],
        )
        allowed, _ = can_edit_in_phase(state)
        assert allowed

    def test_verify_allows_edits(self):
        state = SessionState(
            current_phase="traceability-and-verify",
            phase_index=PHASE_INDEX["traceability-and-verify"],
        )
        allowed, _ = can_edit_in_phase(state)
        assert allowed

    def test_trivial_task_bypasses_caution_phases(self):
        state = SessionState(
            current_phase="depth-dive",
            phase_index=PHASE_INDEX["depth-dive"],
            task_class="trivial",
        )
        allowed, _ = can_edit_in_phase(state)
        assert allowed

    def test_caution_phase_blocks_normal_edits(self):
        state = SessionState(
            current_phase="choose-approach",
            phase_index=PHASE_INDEX["choose-approach"],
        )
        allowed, reason = can_edit_in_phase(state)
        assert not allowed
        assert "execute-or-answer" in reason


class TestPhaseSkipRules:
    def test_trivial_skips_lock_and_critique(self):
        skips = get_skippable_phases("trivial")
        assert "lock-requirements" in skips
        assert "adversarial-critique" in skips

    def test_research_skips_execute(self):
        skips = get_skippable_phases("research-only")
        assert "execute-or-answer" in skips

    def test_unknown_class_skips_nothing(self):
        skips = get_skippable_phases("unknown-class")
        assert len(skips) == 0
