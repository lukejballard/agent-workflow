from __future__ import annotations

import json
import sys
from typing import Any

from session_schema import read_session, write_session
from phase_engine import detect_phase, advance_phase, is_bootstrap_complete
from session_log import append_log, append_memory

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

    # Track reads
    new_read = record_read(tool_name, tool_input, state)

    # Track edits
    first_edit = record_edit(tool_name, state)

    # Check bootstrap completion
    if not state.bootstrap_complete and is_bootstrap_complete(state.read_files):
        state.bootstrap_complete = True
        append_log("bootstrap_complete", {
            "read_count": len(state.read_files),
            "tool_call": state.tool_call_count,
        })

    # Auto-detect and advance phase
    old_phase = state.current_phase
    detected = detect_phase(state)
    if advance_phase(state, detected):
        append_log("phase_transition", {
            "from": old_phase,
            "to": state.current_phase,
            "trigger": "auto-detect",
            "tool": tool_name,
        })
        # Write episodic memory for completed phase
        append_memory(
            phase=old_phase,
            summary=f"Phase '{old_phase}' completed. "
                    f"Reads: {len(state.read_files)}, Edits: {state.edit_count}.",
            verification=state.verification_status,
        )

    # Log first edit
    if first_edit:
        edit_target = _extract_path(tool_input) or "(unknown)"
        append_log("first_edit", {
            "phase": state.current_phase,
            "target": edit_target,
            "tool": tool_name,
        })

    write_session(state)
    sys.stdout.write(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())