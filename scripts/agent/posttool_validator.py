"""PostToolUse hook — records file reads in session state for Gate 6 enforcement.

Wired via .github/hooks/pretool-approval-policy.json under PostToolUse.
Fires after every tool call completes. Always continues (cannot block).

Records the normalised path of every successfully read file to the session
file under 'read_files'. Gate 6 in pretool_approval_policy.py uses this list
to verify that a surface-scoped AGENTS.md was read before the first edit
targeting that surface.

VS Code PostToolUse hook contract:
  Input  (stdin):  {"tool_name": "...", "tool_input": {...}, ...}
  Output (stdout): {"continue": true}
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

_SESSION_FILE = os.environ.get("AGENT_SESSION_FILE", "/tmp/agent-budget.json")

# Tool names whose primary effect is reading one file.
READ_TOOL_NAMES: frozenset[str] = frozenset({
    "read_file",
    "view_file",
    "view_image",
    "mcp_filesystem_read_file",
    "read_notebook_cell_output",
    "copilot_getNotebookSummary",
})

# Input keys that hold the primary file path for a read tool call.
_PATH_KEYS: tuple[str, ...] = (
    "filePath",
    "file_path",
    "path",
    "filename",
    "uri",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise(raw: str) -> str:
    """Forward-slash, lowercased, no trailing slash."""
    return raw.replace("\\", "/").lower().rstrip("/")


def _extract_path(tool_input: dict[str, Any]) -> str | None:
    for key in _PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _read_session() -> dict[str, Any]:
    try:
        return json.loads(Path(_SESSION_FILE).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_session(data: dict[str, Any]) -> None:
    path = Path(_SESSION_FILE)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(path)
    except OSError:
        pass  # Non-fatal: session file is advisory.


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def record_read(tool_name: str, tool_input: dict[str, Any]) -> bool:
    """Record a read tool's path in the session file.

    Returns True when a new path was recorded, False otherwise.
    """
    if tool_name not in READ_TOOL_NAMES:
        return False
    raw_path = _extract_path(tool_input)
    if not raw_path:
        return False
    norm = _normalise(raw_path)
    data = _read_session()
    reads: list[str] = data.get("read_files", [])
    if norm in reads:
        return False  # Already recorded.
    reads.append(norm)
    data["read_files"] = reads
    _write_session(data)
    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


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

    record_read(tool_name, tool_input)

    sys.stdout.write(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
