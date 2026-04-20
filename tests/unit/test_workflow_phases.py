"""Tests for scripts/agent/workflow_phases.py — orchestrator workflow FSM."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from scripts.agent.workflow_phases import (
    ALLOWED_TRANSITIONS,
    PRE_CLASSIFICATION_PHASES,
    TERMINAL_PHASES,
    InvalidTransitionError,
    WorkflowPhase,
    get_workflow_phase,
    is_terminal,
    list_transitions,
    main,
    set_workflow_phase,
    transition,
    validate_packet,
    validate_transition,
)


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phase", [WorkflowPhase.ABORTED, WorkflowPhase.ESCALATED])
def test_is_terminal_returns_true_for_terminal_phases(phase: WorkflowPhase) -> None:
    assert is_terminal(phase) is True


@pytest.mark.parametrize(
    "phase",
    [p for p in WorkflowPhase if p not in TERMINAL_PHASES],
)
def test_is_terminal_returns_false_for_non_terminal(phase: WorkflowPhase) -> None:
    assert is_terminal(phase) is False


# ---------------------------------------------------------------------------
# validate_transition
# ---------------------------------------------------------------------------


_ALLOWED_CASES: list[tuple[str, str]] = [
    # Sequential flow
    ("goal-anchor",           "classify"),
    ("classify",              "breadth-scan"),
    ("breadth-scan",          "depth-dive"),
    ("depth-dive",            "lock-requirements"),
    ("lock-requirements",     "choose-approach"),
    ("choose-approach",       "adversarial-critique"),
    ("adversarial-critique",  "revise"),
    ("revise",                "execute-or-answer"),
    ("execute-or-answer",     "traceability-and-verify"),
    # Shortcuts
    ("classify",              "execute-or-answer"),    # trivial task
    ("breadth-scan",          "choose-approach"),      # shallow, skip depth-dive
    ("depth-dive",            "choose-approach"),      # no spec needed
    ("choose-approach",       "execute-or-answer"),    # low-risk, skip critique
    ("adversarial-critique",  "execute-or-answer"),    # PASS verdict
    # Retry / major revision
    ("revise",                "adversarial-critique"), # retry loop
    ("revise",                "choose-approach"),      # major revision
    # Terminal escape from any non-terminal phase
    ("goal-anchor",           "aborted"),
    ("classify",              "escalated"),
    ("breadth-scan",          "aborted"),
    ("depth-dive",            "escalated"),
    ("lock-requirements",     "aborted"),
    ("choose-approach",       "escalated"),
    ("adversarial-critique",  "aborted"),
    ("revise",                "escalated"),
    ("execute-or-answer",     "aborted"),
    ("traceability-and-verify", "aborted"),
    ("traceability-and-verify", "escalated"),
]


@pytest.mark.parametrize("from_phase,to_phase", _ALLOWED_CASES)
def test_validate_transition_returns_true_for_allowed(from_phase: str, to_phase: str) -> None:
    assert validate_transition(from_phase, to_phase) is True


_FORBIDDEN_CASES: list[tuple[str, str]] = [
    # Cannot go backward in the main flow
    ("breadth-scan",          "goal-anchor"),
    ("breadth-scan",          "classify"),
    ("depth-dive",            "breadth-scan"),
    ("execute-or-answer",     "classify"),
    # Cannot jump forward over multiple phases (beyond defined shortcuts)
    ("goal-anchor",           "breadth-scan"),
    ("goal-anchor",           "execute-or-answer"),
    ("classify",              "lock-requirements"),
    ("classify",              "adversarial-critique"),
    ("breadth-scan",          "execute-or-answer"),
    ("lock-requirements",     "execute-or-answer"),
    # Terminal phases have no outgoing transitions
    ("aborted",               "classify"),
    ("aborted",               "goal-anchor"),
    ("escalated",             "classify"),
    ("escalated",             "execute-or-answer"),
    # Cannot go from PENDING→DONE without going through terminal flow
    ("execute-or-answer",     "choose-approach"),
]


@pytest.mark.parametrize("from_phase,to_phase", _FORBIDDEN_CASES)
def test_validate_transition_returns_false_for_forbidden(from_phase: str, to_phase: str) -> None:
    assert validate_transition(from_phase, to_phase) is False


def test_validate_transition_accepts_enum_values() -> None:
    assert validate_transition(WorkflowPhase.CLASSIFY, WorkflowPhase.BREADTH_SCAN) is True
    assert validate_transition(WorkflowPhase.ABORTED, WorkflowPhase.CLASSIFY) is False


def test_validate_transition_raises_for_unknown_phase() -> None:
    with pytest.raises(ValueError):
        validate_transition("not-a-phase", "classify")


# ---------------------------------------------------------------------------
# transition (raises on forbidden)
# ---------------------------------------------------------------------------


def test_transition_returns_to_phase_for_allowed() -> None:
    result = transition("classify", "breadth-scan")
    assert result == WorkflowPhase.BREADTH_SCAN


def test_transition_raises_invalid_transition_error_for_forbidden() -> None:
    with pytest.raises(InvalidTransitionError) as exc_info:
        transition("execute-or-answer", "classify")
    assert exc_info.value.from_phase == WorkflowPhase.EXECUTE_OR_ANSWER
    assert exc_info.value.to_phase == WorkflowPhase.CLASSIFY


def test_transition_error_message_is_descriptive() -> None:
    with pytest.raises(InvalidTransitionError, match="execute-or-answer.*classify"):
        transition("execute-or-answer", "classify")


# ---------------------------------------------------------------------------
# list_transitions
# ---------------------------------------------------------------------------


def test_list_transitions_returns_sorted_list_for_classify() -> None:
    successors = list_transitions("classify")
    assert WorkflowPhase.BREADTH_SCAN in successors
    assert WorkflowPhase.EXECUTE_OR_ANSWER in successors
    assert WorkflowPhase.ABORTED in successors
    assert WorkflowPhase.ESCALATED in successors
    # Sorted by value
    assert successors == sorted(successors, key=lambda p: p.value)


def test_list_transitions_returns_empty_for_terminal() -> None:
    assert list_transitions("aborted") == []
    assert list_transitions("escalated") == []


# ---------------------------------------------------------------------------
# validate_packet
# ---------------------------------------------------------------------------


def _minimal_packet(phase: str = "classify") -> dict:
    return {"current_phase": phase}


@pytest.mark.parametrize("phase", [p.value for p in WorkflowPhase])
def test_validate_packet_accepts_all_valid_phases(phase: str) -> None:
    errors = validate_packet(_minimal_packet(phase))
    assert errors == []


def test_validate_packet_rejects_unknown_phase() -> None:
    errors = validate_packet(_minimal_packet("not-a-phase"))
    assert len(errors) == 1
    assert "not-a-phase" in errors[0]


def test_validate_packet_rejects_missing_current_phase() -> None:
    errors = validate_packet({})
    assert any("missing" in e for e in errors)


def test_validate_packet_rejects_non_string_phase() -> None:
    errors = validate_packet({"current_phase": 42})
    assert len(errors) == 1


# ---------------------------------------------------------------------------
# set_workflow_phase / get_workflow_phase
# ---------------------------------------------------------------------------


@pytest.fixture()
def session_file(tmp_path, monkeypatch) -> str:
    path = str(tmp_path / "session.json")
    import scripts.agent.workflow_phases as wp
    monkeypatch.setattr(wp, "_SESSION_FILE", path)
    return path


def test_set_and_get_phase(session_file: str) -> None:
    import scripts.agent.workflow_phases as wp

    wp.set_workflow_phase("classify")
    assert wp.get_workflow_phase() == WorkflowPhase.CLASSIFY


def test_set_phase_allows_valid_transition(session_file: str) -> None:
    import scripts.agent.workflow_phases as wp

    wp.set_workflow_phase("classify")
    wp.set_workflow_phase("breadth-scan")
    assert wp.get_workflow_phase() == WorkflowPhase.BREADTH_SCAN


def test_set_phase_rejects_invalid_transition(session_file: str) -> None:
    import scripts.agent.workflow_phases as wp

    wp.set_workflow_phase("classify")
    with pytest.raises(InvalidTransitionError):
        wp.set_workflow_phase("goal-anchor")  # backward jump


def test_get_phase_returns_none_when_session_missing(tmp_path, monkeypatch) -> None:
    import scripts.agent.workflow_phases as wp
    monkeypatch.setattr(wp, "_SESSION_FILE", str(tmp_path / "nonexistent.json"))
    assert wp.get_workflow_phase() is None


def test_set_phase_allows_first_write_without_prior_phase(session_file: str) -> None:
    """No current_phase in session = any write is allowed."""
    import scripts.agent.workflow_phases as wp

    # Start fresh — no current_phase in session
    result = wp.set_workflow_phase("execute-or-answer")
    assert result == WorkflowPhase.EXECUTE_OR_ANSWER


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_validate_transition_allowed() -> None:
    rc = main(["validate-transition", "classify", "breadth-scan"])
    assert rc == 0


def test_cli_validate_transition_forbidden() -> None:
    rc = main(["validate-transition", "breadth-scan", "goal-anchor"])
    assert rc == 1


def test_cli_validate_transition_unknown_phase() -> None:
    rc = main(["validate-transition", "not-a-phase", "classify"])
    assert rc == 2


def test_cli_list_transitions_for_classify(capsys) -> None:
    rc = main(["list-transitions", "classify"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "breadth-scan" in out
    assert "execute-or-answer" in out


def test_cli_list_transitions_for_terminal(capsys) -> None:
    rc = main(["list-transitions", "aborted"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "terminal" in out.lower()


def test_cli_validate_packet_valid(tmp_path) -> None:
    packet = {"current_phase": "classify"}
    p = tmp_path / "packet.json"
    p.write_text(json.dumps(packet))
    rc = main(["validate-packet", str(p)])
    assert rc == 0


def test_cli_validate_packet_invalid(tmp_path) -> None:
    packet = {"current_phase": "not-a-phase"}
    p = tmp_path / "packet.json"
    p.write_text(json.dumps(packet))
    rc = main(["validate-packet", str(p)])
    assert rc == 1


def test_cli_validate_packet_missing_file() -> None:
    rc = main(["validate-packet", "/nonexistent/packet.json"])
    assert rc == 2


def test_cli_get_phase_no_session(tmp_path, monkeypatch, capsys) -> None:
    import scripts.agent.workflow_phases as wp
    monkeypatch.setattr(wp, "_SESSION_FILE", str(tmp_path / "nonexistent.json"))
    # Override the module-level constant used by the CLI entrypoint
    monkeypatch.setenv("AGENT_SESSION_FILE", str(tmp_path / "nonexistent.json"))
    rc = main(["get-phase"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "no current_phase" in out


def test_pre_classification_phases_constant() -> None:
    """PRE_CLASSIFICATION_PHASES must include goal-anchor and classify."""
    assert "goal-anchor" in PRE_CLASSIFICATION_PHASES
    assert "classify" in PRE_CLASSIFICATION_PHASES
    # Should not include later phases
    assert "execute-or-answer" not in PRE_CLASSIFICATION_PHASES


def test_every_phase_has_transition_entry() -> None:
    """ALLOWED_TRANSITIONS must have an entry for every WorkflowPhase."""
    for phase in WorkflowPhase:
        assert phase in ALLOWED_TRANSITIONS, f"Missing transition entry for {phase.value!r}"
