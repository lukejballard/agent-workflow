"""Integration tests for pretool and posttool hooks running as subprocesses."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import (
    get_decision,
    read_session_file,
    run_posttool,
    run_pretool,
)


class TestPhaseEnforcementE2E:
    """Verify phase gates block edits before context loading."""

    def test_edit_blocked_before_bootstrap(self, session_file: Path):
        result = run_pretool(
            {"tool_name": "create_file", "tool_input": {"filePath": "test.py"}},
            session_file,
        )
        assert get_decision(result) == "ask"

    def test_read_always_allowed(self, session_file: Path):
        result = run_pretool(
            {"tool_name": "read_file", "tool_input": {"filePath": "test.py"}},
            session_file,
        )
        # read_file is not in EDIT_TOOL_NAMES, so it should continue
        decision = get_decision(result)
        assert decision == "continue" or "continue" in json.dumps(result)

    def test_bootstrap_advances_phase(self, session_file: Path):
        for f in [".github/AGENTS.md", ".github/agent-platform/workflow-manifest.json"]:
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f}},
                session_file,
            )
        state = read_session_file(session_file)
        assert state["current_phase"] == "classify"
        assert state["bootstrap_complete"] is True

    def test_edit_blocked_in_classify(self, session_file: Path):
        # Bootstrap first
        for f in [".github/AGENTS.md", ".github/agent-platform/workflow-manifest.json"]:
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f}},
                session_file,
            )
        # Try to edit
        result = run_pretool(
            {"tool_name": "replace_string_in_file", "tool_input": {"filePath": "src/app.py"}},
            session_file,
        )
        assert get_decision(result) == "ask"

    def test_edit_allowed_after_sufficient_reads(self, session_file: Path):
        # Bootstrap
        for f in [".github/AGENTS.md", ".github/agent-platform/workflow-manifest.json"]:
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f}},
                session_file,
            )
        # Many more reads to advance to depth-dive
        for i in range(20):
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f"src/file{i}.py"}},
                session_file,
            )

        state = read_session_file(session_file)
        # Should be at least depth-dive
        assert state["current_phase"] in ("depth-dive", "execute-or-answer")

        # Manually advance state to execute phase for edit test
        state["current_phase"] = "execute-or-answer"
        state["phase_index"] = 8
        session_file.write_text(json.dumps(state), encoding="utf-8")

        result = run_pretool(
            {"tool_name": "create_file", "tool_input": {"filePath": "src/new.py"}},
            session_file,
        )
        # Should not be blocked by phase gate (may still be blocked by other gates like scope)
        decision = get_decision(result)
        assert decision == "continue"


class TestScopeEnforcementE2E:
    """Verify scope constraints block out-of-scope edits."""

    def test_out_of_scope_edit_blocked(self, session_file: Path):
        # Set up state with allowed_paths and execute phase
        state = {
            "schema_version": 2,
            "current_phase": "execute-or-answer",
            "phase_index": 8,
            "allowed_paths": ["src/"],
            "tool_call_count": 5,
            "read_files": [],
            "edit_count": 0,
            "phase_history": [],
            "bootstrap_complete": True,
            "requirements_locked": True,
            "verification_status": "pending",
            "task_class": "",
            "scope_justification": "",
            "last_updated": 0.0,
        }
        session_file.write_text(json.dumps(state), encoding="utf-8")

        result = run_pretool(
            {"tool_name": "create_file", "tool_input": {"filePath": "docs/readme.md"}},
            session_file,
        )
        assert get_decision(result) == "ask"

    def test_in_scope_edit_allowed(self, session_file: Path):
        state = {
            "schema_version": 2,
            "current_phase": "execute-or-answer",
            "phase_index": 8,
            "allowed_paths": ["src/"],
            "tool_call_count": 5,
            "read_files": [],
            "edit_count": 0,
            "phase_history": [],
            "bootstrap_complete": True,
            "requirements_locked": True,
            "verification_status": "pending",
            "task_class": "",
            "scope_justification": "",
            "last_updated": 0.0,
        }
        session_file.write_text(json.dumps(state), encoding="utf-8")

        result = run_pretool(
            {"tool_name": "create_file", "tool_input": {"filePath": "src/module.py"}},
            session_file,
        )
        assert get_decision(result) == "continue"

    def test_empty_allowed_paths_permits_all(self, session_file: Path):
        state = {
            "schema_version": 2,
            "current_phase": "execute-or-answer",
            "phase_index": 8,
            "allowed_paths": [],
            "tool_call_count": 5,
            "read_files": [],
            "edit_count": 0,
            "phase_history": [],
            "bootstrap_complete": True,
            "requirements_locked": True,
            "verification_status": "pending",
            "task_class": "",
            "scope_justification": "",
            "last_updated": 0.0,
        }
        session_file.write_text(json.dumps(state), encoding="utf-8")

        result = run_pretool(
            {"tool_name": "create_file", "tool_input": {"filePath": "anywhere/file.py"}},
            session_file,
        )
        assert get_decision(result) == "continue"


class TestSessionStatePersistence:
    """Verify session state persists across hook calls."""

    def test_tool_count_increments(self, session_file: Path):
        for _ in range(3):
            run_pretool(
                {"tool_name": "read_file", "tool_input": {"filePath": "x.py"}},
                session_file,
            )
        state = read_session_file(session_file)
        assert state["tool_call_count"] == 3

    def test_read_files_accumulate(self, session_file: Path):
        for i in range(3):
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f"file{i}.py"}},
                session_file,
            )
        state = read_session_file(session_file)
        assert len(state["read_files"]) == 3

    def test_duplicate_reads_not_duplicated(self, session_file: Path):
        for _ in range(3):
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": "same.py"}},
                session_file,
            )
        state = read_session_file(session_file)
        assert state["read_files"].count("same.py") == 1

    def test_edit_count_tracks(self, session_file: Path):
        # Set state to execute phase so posttool can record edits
        state = {
            "schema_version": 2,
            "current_phase": "execute-or-answer",
            "phase_index": 8,
            "allowed_paths": [],
            "tool_call_count": 0,
            "read_files": [],
            "edit_count": 0,
            "phase_history": [],
            "bootstrap_complete": True,
            "requirements_locked": True,
            "verification_status": "pending",
            "task_class": "",
            "scope_justification": "",
            "last_updated": 0.0,
        }
        session_file.write_text(json.dumps(state), encoding="utf-8")

        run_posttool(
            {"tool_name": "create_file", "tool_input": {"filePath": "new.py"}},
            session_file,
        )
        state = read_session_file(session_file)
        assert state["edit_count"] == 1


class TestMemoryArtifact:
    """Verify episodic memory is written as JSONL file."""

    def test_phase_transition_creates_memory(self, session_file: Path):
        # Read bootstrap files to trigger phase transition
        for f in [".github/AGENTS.md", ".github/agent-platform/workflow-manifest.json"]:
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f}},
                session_file,
            )
        memory_file = session_file.with_suffix(".memory.jsonl")
        assert memory_file.exists(), "Memory artifact should be created on phase transition"
        entries = [
            json.loads(line)
            for line in memory_file.read_text().strip().splitlines()
        ]
        assert len(entries) >= 1
        assert entries[0]["phase"] == "goal-anchor"

    def test_log_file_created_on_transition(self, session_file: Path):
        for f in [".github/AGENTS.md", ".github/agent-platform/workflow-manifest.json"]:
            run_posttool(
                {"tool_name": "read_file", "tool_input": {"filePath": f}},
                session_file,
            )
        log_file = session_file.with_suffix(".log.jsonl")
        assert log_file.exists(), "Session log should be created"
        entries = [
            json.loads(line)
            for line in log_file.read_text().strip().splitlines()
        ]
        events = [e["event"] for e in entries]
        assert "phase_transition" in events or "bootstrap_complete" in events


class TestDestructiveCommandBlocking:
    """Verify destructive terminal commands are blocked."""

    def test_git_reset_hard_blocked(self, session_file: Path):
        result = run_pretool(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "git reset --hard HEAD~1"},
            },
            session_file,
        )
        assert get_decision(result) == "deny"

    def test_rm_rf_blocked(self, session_file: Path):
        result = run_pretool(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "rm -rf /"},
            },
            session_file,
        )
        assert get_decision(result) == "deny"

    def test_safe_command_allowed(self, session_file: Path):
        result = run_pretool(
            {
                "tool_name": "run_in_terminal",
                "tool_input": {"command": "echo hello"},
            },
            session_file,
        )
        decision = get_decision(result)
        assert decision == "continue"
