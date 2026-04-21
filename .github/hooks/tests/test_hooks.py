import io
import json
import sys
import threading
import time

import pytest

import failure_index as failure_index_module
import posttool_validator as posttool
import pretool_approval_policy as pretool
import session_log as session_log_module
from failure_index import FailureIndex
from session_io_support import write_session_snapshot
from session_log import (
    append_log,
    append_memory,
    get_relevant_memory,
    read_log,
    read_memory,
    read_memory_recent_first,
)
from session_schema import CritiqueResult, PHASE_INDEX, SessionState, read_session, write_session
from tfidf import TFIDFIndex
from token_budget import check_budget, estimate_tokens, record_token_usage


@pytest.fixture
def session_path(tmp_path, monkeypatch):
    path = tmp_path / "session.json"
    monkeypatch.setenv("AGENT_SESSION_FILE", str(path))
    return path


def _state(**overrides):
    state = SessionState()
    for key, value in overrides.items():
        setattr(state, key, value)
    state.phase_index = PHASE_INDEX[state.current_phase]
    return state


def _write_state(session_path, **overrides):
    state = _state(**overrides)
    assert write_session(state, str(session_path))
    return state


def _run_hook(module, payload, monkeypatch):
    stdin = io.StringIO(json.dumps(payload))
    stdout = io.StringIO()
    monkeypatch.setattr(module.sys, "stdin", stdin)
    monkeypatch.setattr(module.sys, "stdout", stdout)
    exit_code = module.main()
    return exit_code, json.loads(stdout.getvalue())


def _run_hook_raw(module, payload, monkeypatch):
    stdin = io.StringIO(payload)
    stdout = io.StringIO()
    monkeypatch.setattr(module.sys, "stdin", stdin)
    monkeypatch.setattr(module.sys, "stdout", stdout)
    exit_code = module.main()
    return exit_code, json.loads(stdout.getvalue())


def _decision(output):
    return output["hookSpecificOutput"]["permissionDecision"]


def _reason(output):
    return output["hookSpecificOutput"]["permissionDecisionReason"]


def test_phase_gate_blocks_edit_during_breadth_scan(session_path, monkeypatch):
    _write_state(session_path, current_phase="breadth-scan")
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert "breadth-scan" in _reason(output)


def test_requirements_lock_gate_blocks_edit_when_unlocked(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="execute-or-answer",
        task_class="brownfield-improvement",
        requirements_locked=False,
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/models/user.py"}},
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert "requirements not locked" in _reason(output)


def test_requirements_lock_gate_passes_when_locked(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="execute-or-answer",
        task_class="brownfield-improvement",
        requirements_locked=True,
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/models/user.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}


def test_tool_call_limit_triggers_ask_at_threshold(session_path, monkeypatch):
    _write_state(session_path, tool_call_count=pretool.MAX_TOOL_CALLS - 1)
    _, output = _run_hook(
        pretool,
        {"tool_name": "read_file", "tool_input": {"filePath": "README.md"}},
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert str(pretool.MAX_TOOL_CALLS) in _reason(output)


def test_sensitive_path_blocks_edit_to_hooks_dir(session_path, monkeypatch):
    _write_state(session_path, current_phase="execute-or-answer")
    _, output = _run_hook(
        pretool,
        {
            "tool_name": "edit_file",
            "tool_input": {"filePath": ".github/hooks/pretool_approval_policy.py"},
        },
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert "Sensitive automation" in output["hookSpecificOutput"]["additionalContext"]


def test_destructive_command_denied(session_path, monkeypatch):
    _write_state(session_path)
    _, output = _run_hook(
        pretool,
        {"tool_name": "run_in_terminal", "tool_input": {"command": "rm -rf /tmp/test"}},
        monkeypatch,
    )
    assert _decision(output) == "deny"


def test_scope_gate_blocks_edit_outside_allowed_paths(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="execute-or-answer",
        allowed_paths=["src/api/"],
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/models/user.py"}},
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert "outside the task scope" in _reason(output)


def test_posttool_records_file_read(session_path, monkeypatch):
    _write_state(session_path)
    _, output = _run_hook(
        posttool,
        {"tool_name": "read_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}
    assert "src/main.py" in read_session(str(session_path)).read_files


def test_posttool_increments_edit_count(session_path, monkeypatch):
    _write_state(session_path)
    _, output = _run_hook(
        posttool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}
    assert read_session(str(session_path)).edit_count == 1


def test_session_write_creates_file_atomically(session_path):
    assert write_session(SessionState(), str(session_path))
    assert not session_path.with_suffix(".tmp").exists()
    assert json.loads(session_path.read_text(encoding="utf-8"))["schema_version"] == 4


def test_concurrent_write_does_not_corrupt_session(session_path):
    if sys.platform == "win32":
        pytest.importorskip("msvcrt")
    assert write_session(SessionState(), str(session_path))
    states = [_state(task_class="one"), _state(task_class="two")]
    threads = [
        threading.Thread(target=write_session, args=(state, str(session_path)))
        for state in states
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    parsed = SessionState.from_dict(json.loads(session_path.read_text(encoding="utf-8")))
    assert parsed.is_valid()
    assert parsed.task_class in {"", "one", "two"}


def test_confidence_gate_blocks_edit_when_low(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="execute-or-answer",
        task_class="brownfield-improvement",
        requirements_locked=True,
        confidence=0.3,
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert "Confidence is 0.30" in _reason(output)


def test_session_state_defaults_validate_cleanly():
    assert SessionState().validate() == []


def test_session_state_migrates_v2_to_v4():
    state = SessionState.from_dict(
        {
            "schema_version": 2,
            "current_phase": "classify",
            "tool_call_count": 1,
            "read_files": ["README.md"],
            "allowed_paths": [],
            "edit_count": 0,
            "phase_history": [],
            "bootstrap_complete": False,
            "requirements_locked": False,
            "verification_status": "pending",
            "task_class": "brownfield-improvement",
            "scope_justification": "",
            "last_updated": 0.0,
        }
    )
    assert state.schema_version == 4
    assert state.subtask_attempt_counts == {}
    assert state.confidence == 1.0
    assert state.failure_log == []
    assert state.critique_results == []
    assert state.phase_token_costs == {}


def test_declare_phase_advances_forward_only():
    state = SessionState()
    success, reason = state.declare_phase("classify")
    assert success is True
    assert "classify" in reason
    success, reason = state.declare_phase("classify")
    assert success is False
    assert "move forward" in reason


def test_critique_result_roundtrips_via_dict():
    critique = CritiqueResult(
        check_id="security",
        verdict="FAIL",
        rationale="sql injection",
    )
    assert CritiqueResult.from_dict(critique.to_dict()).verdict == "FAIL"


def test_session_state_serializes_critique_results(session_path):
    state = SessionState(
        critique_results=[CritiqueResult("security", "FAIL", "sql injection")],
    )
    assert write_session(state, str(session_path))
    assert read_session(str(session_path)).critique_results[0].verdict == "FAIL"


def test_critique_gate_blocks_fail_verdict_after_critique_phase(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="traceability-and-verify",
        critique_results=[CritiqueResult("x", "FAIL", "reason")],
        requirements_locked=True,
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert _decision(output) == "ask"
    assert "critique check" in _reason(output)


def test_critique_gate_passes_warn_verdict(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="traceability-and-verify",
        critique_results=[CritiqueResult("x", "WARN", "reason")],
        requirements_locked=True,
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}


def test_critique_gate_exempt_during_critique_phase(session_path, monkeypatch):
    _write_state(
        session_path,
        current_phase="critique",
        critique_results=[CritiqueResult("x", "FAIL", "reason")],
        requirements_locked=True,
    )
    _, output = _run_hook(
        pretool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}


def test_posttool_retries_session_write_once_on_failure(session_path, monkeypatch):
    _write_state(session_path)
    calls = {"count": 0}
    real_write = posttool.write_session

    def flaky_write(state, path=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return False
        return real_write(state, path)

    monkeypatch.setattr(posttool, "write_session", flaky_write)
    _, output = _run_hook(
        posttool,
        {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}
    assert calls["count"] == 2
    assert read_session(str(session_path)).edit_count == 1


def test_pretool_handles_malformed_payload_gracefully(monkeypatch, session_path):
    _write_state(session_path)
    _, output = _run_hook_raw(pretool, "{", monkeypatch)
    assert output == {"continue": True}


def test_session_log_round_trip(session_path):
    append_log("example", {"phase": "classify"})
    assert read_log()[-1]["event"] == "example"


def test_estimate_tokens_returns_positive_int():
    value = estimate_tokens("hello world")
    assert isinstance(value, int)
    assert value > 0


def test_estimate_tokens_scales_with_length():
    assert estimate_tokens("a" * 400) > estimate_tokens("a" * 40)


def test_record_token_usage_accumulates():
    state = SessionState()
    first = record_token_usage(state, "read_file", {"filePath": "a.py"})
    second = record_token_usage(state, "read_file", {"filePath": "b.py"})
    assert state.estimated_tokens_used == second
    assert second > first


def test_check_budget_within_returns_true_when_under():
    state = SessionState(estimated_tokens_used=1000)
    within, utilization, used = check_budget(state, budget=150000)
    assert within is True
    assert utilization < 1.0
    assert used == 1000


def test_check_budget_exceeded_returns_false():
    state = SessionState(estimated_tokens_used=200000)
    within, utilization, used = check_budget(state, budget=150000)
    assert within is False
    assert utilization > 100.0
    assert used == 200000


def test_tfidf_empty_corpus_returns_empty():
    assert TFIDFIndex([]).search("anything") == []


def test_tfidf_exact_term_match_scores_highest():
    docs = [{"text": "coroutine helper"}, {"text": "database pool"}]
    assert TFIDFIndex(docs, ["text"]).search("coroutine")[0]["text"] == "coroutine helper"


def test_tfidf_semantic_proximity():
    docs = [
        {"text": "forgot to await coroutine in async helper"},
        {"text": "database lock timeout"},
    ]
    top = TFIDFIndex(docs, ["text"]).search("async context manager")
    assert top and "forgot to await" in top[0]["text"]


def test_tfidf_empty_query_returns_empty():
    assert TFIDFIndex([{"text": "hello"}], ["text"]).search("") == []


def test_tfidf_top_k_limits_results():
    docs = [{"text": f"test item {index}"} for index in range(10)]
    assert len(TFIDFIndex(docs, ["text"]).search("test", top_k=3)) == 3


def test_phase_token_costs_populated_after_record_usage():
    state = SessionState(
        current_phase="execute-or-answer",
        phase_index=PHASE_INDEX["execute-or-answer"],
    )
    record_token_usage(state, "edit_file", {"path": "x.py", "content": "y"})
    assert "execute-or-answer" in state.phase_token_costs
    assert state.phase_token_costs["execute-or-answer"] > 0


def test_phase_token_costs_accumulate_across_calls():
    state = SessionState(
        current_phase="execute-or-answer",
        phase_index=PHASE_INDEX["execute-or-answer"],
    )
    first = record_token_usage(state, "edit_file", {"path": "x.py", "content": "y"})
    second = record_token_usage(state, "edit_file", {"path": "x.py", "content": "yz"})
    assert state.phase_token_costs["execute-or-answer"] == second
    assert second > first


def test_phase_token_costs_separate_by_phase():
    state = SessionState(
        current_phase="breadth-scan",
        phase_index=PHASE_INDEX["breadth-scan"],
    )
    record_token_usage(state, "read_file", {"filePath": "README.md"})
    state.current_phase = "execute-or-answer"
    state.phase_index = PHASE_INDEX["execute-or-answer"]
    record_token_usage(state, "edit_file", {"path": "x.py", "content": "y"})
    assert state.phase_token_costs["breadth-scan"] > 0
    assert state.phase_token_costs["execute-or-answer"] > 0


def test_append_memory_with_new_fields_roundtrips(session_path):
    append_memory(
        "classify",
        "test",
        facts_learned=["fact1"],
        assumptions_made=["assumption1"],
        corrections_applied=["correction1"],
        next_step_hint="do this next",
    )
    entry = read_memory()[0]
    assert entry["facts_learned"] == ["fact1"]
    assert entry["assumptions_made"] == ["assumption1"]
    assert entry["corrections_applied"] == ["correction1"]
    assert entry["next_step_hint"] == "do this next"


def test_read_memory_recent_first_ordering(session_path, monkeypatch):
    times = iter([100.0, 200.0])
    monkeypatch.setattr(session_log_module.time, "time", lambda: next(times))
    append_memory("classify", "older")
    append_memory("depth-dive", "newer")
    entries = read_memory_recent_first()
    assert entries[0]["summary"] == "newer"
    assert entries[1]["summary"] == "older"


def test_get_relevant_memory_returns_empty_when_no_match(session_path):
    append_memory("classify", "about databases", facts_learned=["db fact"])
    assert get_relevant_memory("unrelated topic xyz") == ""


def test_get_relevant_memory_returns_match(session_path):
    append_memory("classify", "auth flow", facts_learned=["JWT uses RS256"])
    assert "RS256" in get_relevant_memory("JWT authentication")


def test_failure_index_write_creates_file(tmp_path):
    index = FailureIndex(tmp_path / "failures")
    path = index.write(
        task_class="brownfield-improvement",
        phase_at_failure="execute-or-answer",
        symptom="import failed",
        root_cause="missing dependency",
    )
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["symptom"] == "import failed"


def test_failure_index_recent_returns_newest_first(tmp_path):
    index = FailureIndex(tmp_path / "failures")
    index.write(task_class="a", phase_at_failure="x", symptom="one", root_cause="r1")
    time.sleep(0.01)
    index.write(task_class="b", phase_at_failure="x", symptom="two", root_cause="r2")
    time.sleep(0.01)
    index.write(task_class="c", phase_at_failure="x", symptom="three", root_cause="r3")
    recent = index.recent(2)
    assert len(recent) == 2
    assert recent[0]["ts"] > recent[1]["ts"]


def test_failure_index_search_finds_tfidf_semantic_match(tmp_path):
    index = FailureIndex(tmp_path / "failures")
    index.write(
        task_class="brownfield-improvement",
        phase_at_failure="execute-or-answer",
        symptom="forgot to await coroutine in async helper",
        root_cause="missing await",
        prevention_pattern="always await coroutine results",
    )
    results = index.search("async coroutine", top_k=3)
    assert any("forgot to await" in record["symptom"] for record in results)


def test_failure_index_search_returns_empty_for_no_match(tmp_path):
    index = FailureIndex(tmp_path / "failures")
    index.write(
        task_class="brownfield-improvement",
        phase_at_failure="execute-or-answer",
        symptom="unrelated thing",
        root_cause="",
    )
    assert index.search("completely different topic xyz") == []


def test_failure_index_format_for_context_is_non_empty(tmp_path):
    index = FailureIndex(tmp_path / "failures")
    output = index.format_for_context(
        [{"symptom": "s", "root_cause": "r", "prevention_pattern": "p"}]
    )
    assert "Past failures" in output
    assert "Prevention:" in output


def test_read_memory_returns_newest_first(session_path, monkeypatch):
    times = iter([10.0, 20.0])
    monkeypatch.setattr(session_log_module.time, "time", lambda: next(times))
    append_memory("classify", "first")
    append_memory("depth-dive", "second")
    assert read_memory()[0]["summary"] == "second"


def test_append_memory_backward_compatible_with_old_args(session_path):
    append_memory("classify", "legacy summary")
    assert read_memory()[0]["summary"] == "legacy summary"


def test_get_relevant_memory_returns_empty_for_blank_topic(session_path):
    append_memory("classify", "legacy summary")
    assert get_relevant_memory("") == ""


def test_estimated_tokens_used_defaults_to_zero():
    assert SessionState().estimated_tokens_used == 0


def test_schema_v3_migrates_to_v4():
    state = SessionState.from_dict(
        {
            "schema_version": 3,
            "current_phase": "execute-or-answer",
            "tool_call_count": 2,
            "read_files": ["README.md"],
            "allowed_paths": ["src/"],
            "edit_count": 1,
            "phase_history": [],
            "bootstrap_complete": True,
            "requirements_locked": True,
            "verification_status": "pending",
            "task_class": "brownfield-improvement",
            "scope_justification": "phase3 migration",
            "subtask_attempt_counts": {},
            "confidence": 0.8,
            "failure_log": [],
            "estimated_tokens_used": 10,
        }
    )
    assert state.schema_version == 4
    assert state.critique_results == []
    assert state.phase_token_costs == {}


def test_schema_v4_roundtrips():
    original = SessionState().to_dict()
    assert SessionState.from_dict(original).to_dict() == original


def test_posttool_writes_failure_record_on_blocked_transition(
    session_path, monkeypatch, tmp_path
):
    failures_dir = tmp_path / "failures"
    monkeypatch.setenv("AGENT_FAILURES_DIR", str(failures_dir))
    _write_state(session_path, verification_status="pending")
    write_session_snapshot(str(session_path))
    _write_state(
        session_path,
        verification_status="blocked",
        current_phase="traceability-and-verify",
        task_class="brownfield-improvement",
    )
    _, output = _run_hook(
        posttool,
        {"tool_name": "read_file", "tool_input": {"filePath": "src/main.py"}},
        monkeypatch,
    )
    assert output == {"continue": True}
    records = FailureIndex(failures_dir).recent()
    assert len(records) == 1
    assert "Session blocked" in records[0]["symptom"]


def test_failure_index_recent_handles_missing_dir(tmp_path):
    index = FailureIndex(tmp_path / "missing")
    assert index.recent() == []