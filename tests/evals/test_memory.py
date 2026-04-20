"""Tests for episodic memory and session log artifacts."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / ".github" / "hooks"))

from session_log import append_log, append_memory, read_log, read_memory


@pytest.fixture()
def log_env(tmp_path: Path):
    """Set up session file env var for log/memory paths."""
    session = tmp_path / "session.json"
    old = os.environ.get("AGENT_SESSION_FILE")
    os.environ["AGENT_SESSION_FILE"] = str(session)
    yield tmp_path
    if old is None:
        os.environ.pop("AGENT_SESSION_FILE", None)
    else:
        os.environ["AGENT_SESSION_FILE"] = old


class TestSessionLog:
    def test_append_creates_file(self, log_env: Path):
        append_log("test_event", {"key": "value"})
        entries = read_log()
        assert len(entries) == 1
        assert entries[0]["event"] == "test_event"
        assert entries[0]["key"] == "value"
        assert "ts" in entries[0]

    def test_multiple_appends_accumulate(self, log_env: Path):
        for i in range(5):
            append_log(f"event_{i}", {"index": i})
        entries = read_log()
        assert len(entries) == 5

    def test_empty_log_returns_empty_list(self, log_env: Path):
        entries = read_log()
        assert entries == []


class TestEpisodicMemory:
    def test_append_creates_memory_file(self, log_env: Path):
        append_memory(
            phase="classify",
            summary="Classified task as brownfield.",
            decisions="Will modify existing API routes.",
            unresolved="Auth boundary unclear.",
        )
        entries = read_memory()
        assert len(entries) == 1
        assert entries[0]["phase"] == "classify"
        assert entries[0]["summary"] == "Classified task as brownfield."
        assert entries[0]["decisions"] == "Will modify existing API routes."

    def test_multiple_memories_accumulate(self, log_env: Path):
        for phase in ["classify", "breadth-scan", "execute-or-answer"]:
            append_memory(phase=phase, summary=f"Completed {phase}.")
        entries = read_memory()
        assert len(entries) == 3
        assert [e["phase"] for e in entries] == [
            "classify",
            "breadth-scan",
            "execute-or-answer",
        ]

    def test_memory_has_all_fields(self, log_env: Path):
        append_memory(
            phase="execute-or-answer",
            summary="Implemented feature X.",
            decisions="Used approach A.",
            unresolved="Performance TBD.",
            artifacts="src/feature.py",
            verification="tests pass",
        )
        entry = read_memory()[0]
        assert entry["phase"] == "execute-or-answer"
        assert entry["summary"] == "Implemented feature X."
        assert entry["decisions"] == "Used approach A."
        assert entry["unresolved"] == "Performance TBD."
        assert entry["artifacts"] == "src/feature.py"
        assert entry["verification"] == "tests pass"

    def test_empty_memory_returns_empty_list(self, log_env: Path):
        entries = read_memory()
        assert entries == []
