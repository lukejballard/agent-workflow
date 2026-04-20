"""PreToolUse and PostToolUse hooks.

Wired via .github/hooks/pretool-approval-policy.json.

PreToolUse: Enforces tool-call limits, blocks destructive commands, requires
            approval for remote writes and sensitive paths, scope enforcement.
PostToolUse: Records file reads in session state for surface-guide enforcement.

Usage:
    python .github/hooks/hooks.py pretool   (reads JSON from stdin, writes decision to stdout)
    python .github/hooks/hooks.py posttool  (reads JSON from stdin, writes continue to stdout)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_TOOL_CALLS = int(os.environ.get("AGENT_MAX_TOOL_CALLS", "50"))
_SESSION_FILE = os.environ.get("AGENT_SESSION_FILE", "/tmp/agent-budget.json")

DENY_COMMAND_PATTERNS = [
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "Destructive git history reset is blocked."),
    (re.compile(r"\bgit\s+clean\b", re.IGNORECASE),
     "Destructive git clean is blocked."),
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
     "Recursive force deletes are blocked."),
    (re.compile(r"\bremove-item\b.*\b-recurse\b.*\b-force\b", re.IGNORECASE),
     "Recursive force deletes are blocked."),
    (re.compile(r"\bshutdown\b|\brestart-computer\b|\bformat\b|\bmkfs\b", re.IGNORECASE),
     "System-destructive commands are blocked."),
]

ASK_COMMAND_PATTERNS = [
    (re.compile(r"\bgit\s+push\b", re.IGNORECASE),
     "Pushing to a remote requires approval."),
    (re.compile(
        r"\b(?:pip|pip3|python(?:\.exe)?\s+-m\s+pip|uv|poetry|npm|pnpm|yarn|bun|cargo)"
        r"\s+(?:install|add|update|upgrade|remove|uninstall)\b", re.IGNORECASE),
     "Dependency changes require approval."),
    (re.compile(r"\b(?:curl|wget|invoke-webrequest|iwr)\b", re.IGNORECASE),
     "Network-fetching commands require approval."),
    (re.compile(r"\bnpx\b", re.IGNORECASE),
     "NPX commands require approval."),
]

ASK_TOOL_NAME_PATTERNS = [
    (re.compile(
        r"(?:^|[._])(create_or_update_file|push_files|delete_file|create_pull_request"
        r"|merge_pull_request|create_issue|add_issue_comment)\b", re.IGNORECASE),
     "Remote mutations require approval."),
]

SENSITIVE_PATH_MARKERS = [
    ".github/hooks/", ".github/workflows/", ".github/agent-platform/",
    ".vscode/mcp.json", ".env",
]

EDIT_TOOL_NAMES = {
    "create_file", "apply_patch", "replace_string_in_file", "insert_into_file",
    "delete_file", "rename_file", "write_file", "edit_file", "move_file",
    "mcp_filesystem_write_file", "mcp_filesystem_edit_file",
}

TERMINAL_TOOL_NAMES = {"run_in_terminal", "terminal"}

READ_TOOL_NAMES = frozenset({
    "read_file", "view_file", "view_image", "mcp_filesystem_read_file",
})

# Map directory prefixes to scoped guide files that must be read before editing.
# Populate with your repo's surfaces, e.g.:
#   "src/": "src/agents.md",
#   "frontend/": "frontend/agents.md",
SURFACE_GUIDE_MAP: dict[str, str] = {}


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


def _normalise_path(raw: str) -> str:
    return raw.replace("\\", "/").lower().rstrip("/")


def emit_pretool_decision(decision: str, reason: str, *, additional_context: str | None = None) -> None:
    payload: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    if additional_context:
        payload["hookSpecificOutput"]["additionalContext"] = additional_context
    sys.stdout.write(json.dumps(payload))


def emit_continue() -> None:
    sys.stdout.write(json.dumps({"continue": True}))


def find_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [s for item in value for s in find_strings(item)]
    if isinstance(value, dict):
        return [s for item in value.values() for s in find_strings(item)]
    return []


def extract_terminal_command(tool_input: dict[str, Any]) -> str:
    for key in ("command", "commandLine", "text", "cmd"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    args = tool_input.get("args")
    if isinstance(args, list):
        return " ".join(str(arg) for arg in args)
    return ""


def extract_edit_target_path(tool_input: dict[str, Any]) -> str | None:
    for key in ("filePath", "file_path", "path", "filename", "target", "destination"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def edit_targets_sensitive(tool_input: dict[str, Any]) -> bool:
    strings = find_strings(tool_input)
    lowered = [item.replace("\\", "/") for item in strings]
    return any(marker in item for item in lowered for marker in SENSITIVE_PATH_MARKERS)


def handle_terminal(tool_input: dict[str, Any]) -> bool:
    command = extract_terminal_command(tool_input)
    if not command:
        return False
    for pattern, reason in DENY_COMMAND_PATTERNS:
        if pattern.search(command):
            emit_pretool_decision("deny", reason)
            return True
    for pattern, reason in ASK_COMMAND_PATTERNS:
        if pattern.search(command):
            emit_pretool_decision("ask", reason)
            return True
    return False


def handle_remote_write(tool_name: str) -> bool:
    for pattern, reason in ASK_TOOL_NAME_PATTERNS:
        if pattern.search(tool_name):
            emit_pretool_decision("ask", reason)
            return True
    return False


def pretool_main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        emit_continue()
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    data = _read_session()
    count = int(data.get("tool_call_count", 0)) + 1
    data["tool_call_count"] = count
    _write_session(data)
    if count >= MAX_TOOL_CALLS:
        emit_pretool_decision("ask", f"Tool call limit reached ({count}/{MAX_TOOL_CALLS}).")
        return 0

    if handle_remote_write(tool_name):
        return 0

    if tool_name in TERMINAL_TOOL_NAMES and handle_terminal(tool_input):
        return 0

    if tool_name in EDIT_TOOL_NAMES and edit_targets_sensitive(tool_input):
        emit_pretool_decision("ask", "Editing sensitive files requires manual approval.")
        return 0

    session_data = _read_session()
    read_files: list[str] = session_data.get("read_files", [])
    if tool_name in EDIT_TOOL_NAMES and read_files:
        edit_target = extract_edit_target_path(tool_input)
        if edit_target:
            norm = _normalise_path(edit_target)
            for prefix, guide in SURFACE_GUIDE_MAP.items():
                if norm.startswith(prefix.rstrip("/")):
                    norm_guide = guide.replace("\\", "/").lower()
                    if not any(r == norm_guide or r.endswith("/" + norm_guide) for r in read_files):
                        emit_pretool_decision("ask", f"Surface guide `{guide}` not yet read.")
                        return 0

    emit_continue()
    return 0


def posttool_main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    if tool_name in READ_TOOL_NAMES:
        for key in ("filePath", "file_path", "path", "filename", "uri"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                norm = _normalise_path(value.strip())
                data = _read_session()
                reads: list[str] = data.get("read_files", [])
                if norm not in reads:
                    reads.append(norm)
                    data["read_files"] = reads
                    _write_session(data)
                break

    sys.stdout.write(json.dumps({"continue": True}))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: hooks.py pretool|posttool", file=sys.stderr)
        return 1
    cmd = sys.argv[1]
    if cmd == "pretool":
        return pretool_main()
    if cmd == "posttool":
        return posttool_main()
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())