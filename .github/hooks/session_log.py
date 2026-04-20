"""Append-only session log for observability and episodic memory.

Writes structured JSONL entries alongside the session file.
Each entry captures a phase transition, edit action, gate decision,
or memory summary that persists across tool calls.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def _log_path() -> Path:
    session = os.environ.get(
        "AGENT_SESSION_FILE",
        str(Path.home() / ".agent-session" / "session.json"),
    )
    return Path(session).with_suffix(".log.jsonl")


def _memory_path() -> Path:
    session = os.environ.get(
        "AGENT_SESSION_FILE",
        str(Path.home() / ".agent-session" / "session.json"),
    )
    return Path(session).with_suffix(".memory.jsonl")


def append_log(
    event_type: str,
    detail: dict[str, Any],
) -> None:
    """Append a structured log entry to the session log."""
    path = _log_path()
    entry = {
        "ts": time.time(),
        "event": event_type,
        **detail,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass


def append_memory(
    phase: str,
    summary: str,
    *,
    decisions: str = "",
    unresolved: str = "",
    artifacts: str = "",
    verification: str = "",
) -> None:
    """Append a structured episodic memory entry."""
    path = _memory_path()
    entry = {
        "ts": time.time(),
        "phase": phase,
        "summary": summary,
        "decisions": decisions,
        "unresolved": unresolved,
        "artifacts": artifacts,
        "verification": verification,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass


def read_memory() -> list[dict[str, Any]]:
    """Read all episodic memory entries for the current session."""
    path = _memory_path()
    entries: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except (FileNotFoundError, OSError):
        pass
    return entries


def read_log() -> list[dict[str, Any]]:
    """Read all log entries for the current session."""
    path = _log_path()
    entries: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except (FileNotFoundError, OSError):
        pass
    return entries
