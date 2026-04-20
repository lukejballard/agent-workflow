from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

_SESSION_FILE = os.environ.get("AGENT_SESSION_FILE", "/tmp/agent-budget.json")

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

_PATH_KEYS: tuple[str, ...] = ("filePath", "file_path", "path", "filename", "uri")


def _normalise(raw: str) -> str:
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
        pass


def record_read(tool_name: str, tool_input: dict[str, Any]) -> None:
    if tool_name not in READ_TOOL_NAMES:
        return

    raw_path = _extract_path(tool_input)
    if not raw_path:
        return

    norm = _normalise(raw_path)
    data = _read_session()
    reads: list[str] = data.get("read_files", [])
    if norm not in reads:
        reads.append(norm)
        data["read_files"] = reads
        _write_session(data)


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