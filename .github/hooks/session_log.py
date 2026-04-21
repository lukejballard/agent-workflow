"""Append-only session log for observability and episodic memory.

Writes structured JSONL entries alongside the session file.
Each entry captures a phase transition, edit action, gate decision,
or memory summary that persists across tool calls.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from session_io_support import default_session_path

MEMORY_LIST_FIELDS = (
    "facts_learned",
    "assumptions_made",
    "corrections_applied",
)


def _log_path() -> Path:
    return Path(default_session_path()).with_suffix(".log.jsonl")


def _memory_path() -> Path:
    return Path(default_session_path()).with_suffix(".memory.jsonl")


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
    facts_learned: list[str] | None = None,
    assumptions_made: list[str] | None = None,
    corrections_applied: list[str] | None = None,
    next_step_hint: str = "",
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
        "facts_learned": facts_learned or [],
        "assumptions_made": assumptions_made or [],
        "corrections_applied": corrections_applied or [],
        "next_step_hint": next_step_hint,
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
    return sorted(entries, key=lambda entry: entry.get("ts", 0), reverse=True)


def read_memory_recent_first() -> list[dict[str, Any]]:
    """Return all episodic memory entries sorted newest-first."""
    return read_memory()


def _flatten_memory_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat_entries: list[dict[str, Any]] = []
    for entry in entries:
        flat = dict(entry)
        for key in MEMORY_LIST_FIELDS:
            flat[f"_{key}"] = list(entry.get(key) or [])
            flat[key] = " ".join(str(item) for item in entry.get(key) or [])
        flat_entries.append(flat)
    return flat_entries


def _keyword_memory_search(
    entries: list[dict[str, Any]], topic: str, top_k: int
) -> list[dict[str, Any]]:
    keywords = {word.lower() for word in re.findall(r"[A-Za-z0-9_-]+", topic) if len(word) > 3}
    if not keywords:
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in entries:
        search_text = " ".join(
            [
                entry.get("summary", ""),
                entry.get("next_step_hint", ""),
                *entry.get("facts_learned", []),
                *entry.get("corrections_applied", []),
            ]
        ).lower()
        score = sum(1 for keyword in keywords if keyword in search_text)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda item: (-item[0], -item[1].get("ts", 0)))
    return [entry for _, entry in scored[:top_k]]


def get_relevant_memory(topic: str, top_k: int = 3) -> str:
    """Return a formatted string of the top matching episodic memories."""
    entries = read_memory_recent_first()
    if not entries or not topic.strip():
        return ""
    try:
        from tfidf import get_cached_index

        flat_entries = _flatten_memory_entries(entries)
        index = get_cached_index(
            f"memory:{_memory_path()}",
            flat_entries,
            ["summary", "next_step_hint", "decisions", "facts_learned", "corrections_applied"],
        )
        matches = index.search(topic, top_k=top_k)
    except ImportError:
        matches = _keyword_memory_search(entries, topic, top_k)
    if not matches:
        return ""
    lines = ["## Relevant past context", ""]
    for entry in matches:
        lines.append(
            f"**Phase {entry.get('phase', '?')}** — {entry.get('summary', '')}"
        )
        facts = entry.get("_facts_learned") or entry.get("facts_learned") or []
        corrections = entry.get("_corrections_applied") or entry.get("corrections_applied") or []
        for fact in facts:
            lines.append(f"  - Fact: {fact}")
        for correction in corrections:
            lines.append(f"  - Correction: {correction}")
        if entry.get("next_step_hint"):
            lines.append(f"  - Next-step hint: {entry['next_step_hint']}")
    return "\n".join(lines)


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
