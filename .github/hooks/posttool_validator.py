from __future__ import annotations

import json
import sys
import time
from typing import Any

from failure_index import FailureIndex
from session_schema import read_session, write_session
from phase_engine import detect_phase, is_bootstrap_complete
from session_io_support import read_session_snapshot
from session_log import append_log

READ_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "read_file",
        "view_file",
        "view_image",
        "mcp_filesystem_read_file",
        "read_notebook_cell_output",
        "copilot_getNotebookSummary",
    }
)

EDIT_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "create_file",
        "apply_patch",
        "replace_string_in_file",
        "multi_replace_string_in_file",
        "insert_into_file",
        "delete_file",
        "rename_file",
        "write_file",
        "edit_file",
        "move_file",
        "mcp_filesystem_write_file",
        "mcp_filesystem_edit_file",
        "mcp_filesystem_move_file",
    }
)

_PATH_KEYS: tuple[str, ...] = ("filePath", "file_path", "path", "filename", "uri")


def _normalise(raw: str) -> str:
    return raw.replace("\\", "/").lower().rstrip("/")


def _extract_path(tool_input: dict[str, Any]) -> str | None:
    for key in _PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def record_read(tool_name: str, tool_input: dict[str, Any], state: Any) -> bool:
    """Record a file read. Returns True if a new file was added."""
    if tool_name not in READ_TOOL_NAMES:
        return False

    raw_path = _extract_path(tool_input)
    if not raw_path:
        return False

    norm = _normalise(raw_path)
    if norm not in state.read_files:
        state.read_files.append(norm)
        return True
    return False


def record_edit(tool_name: str, state: Any) -> bool:
    """Record an edit action. Returns True if this is the first edit."""
    if tool_name not in EDIT_TOOL_NAMES:
        return False
    was_zero = state.edit_count == 0
    state.edit_count += 1
    return was_zero


def persist_state(state: Any, tool_name: str) -> None:
    if write_session(state):
        return
    append_log("session_write_retry", {"tool": tool_name, "phase": state.current_phase})
    if not write_session(state):
        append_log("session_write_failed", {"tool": tool_name, "phase": state.current_phase})


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    state = read_session()
    previous_session = read_session_snapshot() or {}
    old_verification = previous_session.get(
        "verification_status", state.verification_status
    )

    record_read(tool_name, tool_input, state)
    first_edit = record_edit(tool_name, state)

    if not state.bootstrap_complete and is_bootstrap_complete(state.read_files):
        state.bootstrap_complete = True
        append_log("bootstrap_complete", {
            "read_count": len(state.read_files),
            "tool_call": state.tool_call_count,
        })

    detected = detect_phase(state)
    if detected != state.current_phase:
        append_log("phase_advisory", {
            "current": state.current_phase,
            "suggested": detected,
            "tool": tool_name,
        })

    if state.verification_status == "blocked" and old_verification != "blocked":
        failure = FailureIndex().write(
            task_class=state.task_class or "unknown",
            phase_at_failure=state.current_phase,
            symptom=(
                f"Session blocked at phase '{state.current_phase}' after "
                f"{state.edit_count} edits and {state.tool_call_count} tool calls."
            ),
            root_cause="",
            prevention_pattern="",
            task_summary=state.scope_justification,
        )
        state.failure_log.append(
            {
                "ts": time.time(),
                "verification_status": "blocked",
                "failure_path": str(failure),
            }
        )

    if first_edit:
        edit_target = _extract_path(tool_input) or "(unknown)"
        append_log("first_edit", {
            "phase": state.current_phase,
            "target": edit_target,
            "tool": tool_name,
        })

    persist_state(state, tool_name)
    sys.stdout.write(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())