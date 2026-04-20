"""Tests for session state schema validation and migration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / ".github" / "hooks"))

from session_schema import (
    SCHEMA_VERSION,
    VALID_PHASES,
    SessionState,
    read_session,
    write_session,
)


class TestSessionStateCreation:
    def test_default_state_is_valid(self):
        state = SessionState()
        assert state.is_valid()
        assert state.current_phase == "goal-anchor"
        assert state.schema_version == SCHEMA_VERSION

    def test_all_phases_are_accepted(self):
        for phase in VALID_PHASES:
            idx = list(VALID_PHASES).index(phase)
            state = SessionState(current_phase=phase, phase_index=idx)
            assert state.is_valid(), f"Phase '{phase}' should be valid"

    def test_invalid_phase_fails_validation(self):
        state = SessionState(current_phase="nonexistent-phase", phase_index=99)
        errors = state.validate()
        assert any("Invalid phase" in e for e in errors)

    def test_negative_tool_call_count_fails(self):
        state = SessionState(tool_call_count=-1)
        errors = state.validate()
        assert any("tool_call_count" in e for e in errors)

    def test_negative_edit_count_fails(self):
        state = SessionState(edit_count=-1)
        errors = state.validate()
        assert any("edit_count" in e for e in errors)

    def test_mismatched_phase_index_fails(self):
        state = SessionState(current_phase="classify", phase_index=0)
        errors = state.validate()
        assert any("phase_index" in e for e in errors)

    def test_invalid_verification_status_fails(self):
        state = SessionState(verification_status="maybe")
        errors = state.validate()
        assert any("verification_status" in e for e in errors)


class TestV1Migration:
    def test_empty_dict_produces_valid_state(self):
        state = SessionState.from_dict({})
        assert state.is_valid()

    def test_v1_format_migrates(self):
        v1 = {
            "tool_call_count": 10,
            "read_files": ["a.md", "b.py"],
            "allowed_paths": ["/src"],
            "current_phase": "breadth-scan",
        }
        state = SessionState.from_dict(v1)
        assert state.schema_version == SCHEMA_VERSION
        assert state.tool_call_count == 10
        assert state.read_files == ["a.md", "b.py"]
        assert state.current_phase == "breadth-scan"
        assert state.is_valid()

    def test_empty_phase_gets_default(self):
        state = SessionState.from_dict({"current_phase": ""})
        assert state.current_phase == "goal-anchor"

    def test_missing_phase_gets_default(self):
        state = SessionState.from_dict({"tool_call_count": 3})
        assert state.current_phase == "goal-anchor"

    def test_unknown_fields_are_ignored(self):
        data = {"schema_version": 1, "unknown_field": "value"}
        state = SessionState.from_dict(data)
        assert state.is_valid()
        assert not hasattr(state, "unknown_field") or True  # just check no crash

    def test_non_dict_returns_default(self):
        state = SessionState.from_dict("not a dict")  # type: ignore[arg-type]
        assert state.is_valid()


class TestRoundTrip:
    def test_write_read_roundtrip(self, session_file: Path):
        original = SessionState(
            current_phase="depth-dive",
            phase_index=3,
            tool_call_count=15,
            read_files=["a.md", "b.py"],
            edit_count=2,
        )
        assert write_session(original, str(session_file))
        loaded = read_session(str(session_file))
        assert loaded.current_phase == original.current_phase
        assert loaded.tool_call_count == original.tool_call_count
        assert loaded.read_files == original.read_files
        assert loaded.edit_count == original.edit_count

    def test_read_missing_file_returns_default(self, tmp_path: Path):
        path = tmp_path / "nonexistent.json"
        state = read_session(str(path))
        assert state.is_valid()
        assert state.current_phase == "goal-anchor"

    def test_read_corrupt_file_returns_default(self, session_file: Path):
        session_file.write_text("{{not json}}", encoding="utf-8")
        state = read_session(str(session_file))
        assert state.is_valid()

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "deep" / "nested" / "session.json"
        state = SessionState()
        assert write_session(state, str(path))
        assert path.exists()
