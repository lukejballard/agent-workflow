from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

MAX_TOOL_CALLS = int(os.environ.get("AGENT_MAX_TOOL_CALLS", "50"))
_SESSION_FILE = os.environ.get("AGENT_SESSION_FILE", "/tmp/agent-budget.json")

DENY_COMMAND_PATTERNS = [
    (
        re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
        "Destructive git history reset is blocked by workspace policy.",
    ),
    (
        re.compile(r"\bgit\s+clean\b", re.IGNORECASE),
        "Destructive git clean is blocked by workspace policy.",
    ),
    (
        re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
        "Recursive force deletes are blocked by workspace policy.",
    ),
    (
        re.compile(r"\bremove-item\b.*\b-recurse\b.*\b-force\b", re.IGNORECASE),
        "Recursive force deletes are blocked by workspace policy.",
    ),
    (
        re.compile(r"\bdel\b", re.IGNORECASE),
        "Shell delete commands are blocked by workspace policy.",
    ),
]

ASK_COMMAND_PATTERNS = [
    (
        re.compile(r"\bgit\s+push\b", re.IGNORECASE),
        "Pushing to a remote requires explicit approval.",
    ),
    (
        re.compile(
            r"\b(?:pip|pip3|python(?:\.exe)?\s+-m\s+pip|uv|poetry|npm|pnpm|yarn|bun|cargo)\s+(?:install|add|update|upgrade|remove|uninstall)\b",
            re.IGNORECASE,
        ),
        "Dependency or environment changes require explicit approval.",
    ),
    (
        re.compile(r"\b(?:curl|wget|invoke-webrequest|iwr)\b", re.IGNORECASE),
        "Network-fetching terminal commands require explicit approval.",
    ),
    (
        re.compile(r"\bnpx\b", re.IGNORECASE),
        "NPX commands can execute remote code and require explicit approval.",
    ),
]

ASK_TOOL_NAME_PATTERNS = [
    (
        re.compile(
            r"(?:^|[._])(create_or_update_file|push_files|delete_file|create_pull_request|merge_pull_request|add_pull_request_comment|create_pull_request_review|create_issue|add_issue_comment|close_issue|add_labels|remove_label|create_gist|update_gist|delete_gist|create_gist_comment|trigger_workflow|cancel_workflow_run|rerun_workflow_run|assign_copilot_to_issue|request_copilot_review|create_pull_request_with_copilot)\b",
            re.IGNORECASE,
        ),
        "Remote repository or workflow mutations require explicit approval.",
    ),
]

SENSITIVE_PATH_MARKERS = [
    ".github/hooks/",
    ".github/agent-platform/",
    ".github/AGENTS.md",
    ".github/copilot-instructions.md",
    ".vscode/settings.json",
    ".vscode/mcp.json",
    ".env",
]

EDIT_TOOL_NAMES = {
    "create_file",
    "apply_patch",
    "replace_string_in_file",
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

PRE_CLASSIFICATION_PHASES = {"goal-anchor", "classify"}

SURFACE_GUIDE_MAP: dict[str, str] = {
    ".github/": ".github/agents.md",
    "docs/": "docs/agents.md",
}

TERMINAL_TOOL_NAMES = {
    "run_in_terminal",
    "terminal",
}


def _normalise_path(raw: str) -> str:
    return raw.replace("\\", "/").lower().rstrip("/")


def _surface_guide_for(path: str) -> str | None:
    norm = _normalise_path(path)
    for prefix, guide in SURFACE_GUIDE_MAP.items():
        if norm.startswith(prefix.rstrip("/")):
            return guide
    return None


def _guide_was_read(guide: str, read_files: list[str]) -> bool:
    norm_guide = guide.replace("\\", "/").lower()
    return any(item == norm_guide or item.endswith("/" + norm_guide) for item in read_files)


def _read_session_file() -> dict[str, Any]:
    try:
        return json.loads(Path(_SESSION_FILE).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_session_file(data: dict[str, Any]) -> None:
    path = Path(_SESSION_FILE)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(path)
    except OSError:
        pass


def check_and_increment_tool_call() -> tuple[bool, int]:
    data = _read_session_file()
    count = int(data.get("tool_call_count", 0)) + 1
    data["tool_call_count"] = count
    _write_session_file(data)
    return count >= MAX_TOOL_CALLS, count


def emit_pretool_decision(
    decision: str, reason: str, *, additional_context: str | None = None
) -> None:
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
        results: list[str] = []
        for item in value:
            results.extend(find_strings(item))
        return results
    if isinstance(value, dict):
        results: list[str] = []
        for item in value.values():
            results.extend(find_strings(item))
        return results
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


def edit_targets_sensitive_surface(tool_name: str, tool_input: dict[str, Any]) -> bool:
    strings = find_strings(tool_input)
    if tool_name == "apply_patch":
        patch_blob = "\n".join(strings)
        return any(marker in patch_blob for marker in SENSITIVE_PATH_MARKERS)
    lowered = [item.replace("\\", "/") for item in strings]
    return any(marker in item for item in lowered for marker in SENSITIVE_PATH_MARKERS)


def extract_edit_target_path(tool_input: dict[str, Any]) -> str | None:
    for key in ("filePath", "file_path", "path", "filename", "target", "destination"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def edit_targets_out_of_scope(
    tool_name: str, tool_input: dict[str, Any], allowed_paths: list[str]
) -> bool:
    if not allowed_paths or tool_name == "apply_patch":
        return False

    target = extract_edit_target_path(tool_input)
    if not target:
        return False

    norm_target = _normalise_path(target)
    norm_allowed = [_normalise_path(path) for path in allowed_paths]
    return not any(norm_target.startswith(path) for path in norm_allowed)


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
            emit_pretool_decision(
                "ask",
                reason,
                additional_context=(
                    "Workspace policy allows normal read-only commands to continue but "
                    "requires manual confirmation for environment, network, or remote-write operations."
                ),
            )
            return True

    return False


def handle_remote_write_tool(tool_name: str) -> bool:
    for pattern, reason in ASK_TOOL_NAME_PATTERNS:
        if pattern.search(tool_name):
            emit_pretool_decision(
                "ask",
                reason,
                additional_context=(
                    "Remote repository writes, review actions, workflow dispatches, and delegated "
                    "background tasks should not run silently."
                ),
            )
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        emit_continue()
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    limit_reached, call_count = check_and_increment_tool_call()
    if limit_reached:
        emit_pretool_decision(
            "ask",
            f"Tool call limit reached ({call_count}/{MAX_TOOL_CALLS}). Continuing may indicate an agent retry loop.",
            additional_context=(
                "Override the limit with AGENT_MAX_TOOL_CALLS when the task is genuinely large."
            ),
        )
        return 0

    if handle_remote_write_tool(tool_name):
        return 0

    if tool_name in TERMINAL_TOOL_NAMES and handle_terminal(tool_input):
        return 0

    if tool_name in EDIT_TOOL_NAMES and edit_targets_sensitive_surface(tool_name, tool_input):
        emit_pretool_decision(
            "ask",
            "Editing hook, policy, or secret-adjacent files requires manual approval.",
            additional_context=(
                "Sensitive automation and configuration surfaces should not be changed silently."
            ),
        )
        return 0

    session_data = _read_session_file()
    allowed_paths: list[str] = session_data.get("allowed_paths", [])
    if tool_name in EDIT_TOOL_NAMES and edit_targets_out_of_scope(tool_name, tool_input, allowed_paths):
        target = extract_edit_target_path(tool_input) or "(unknown)"
        emit_pretool_decision(
            "ask",
            f"Edit target '{target}' is outside the task scope set by allowed_paths.",
            additional_context=(
                "Confirm the edit is intentional or update the allowed_paths session metadata."
            ),
        )
        return 0

    current_phase = session_data.get("current_phase", "")
    if tool_name in EDIT_TOOL_NAMES and current_phase in PRE_CLASSIFICATION_PHASES:
        target = extract_edit_target_path(tool_input) or "(unknown)"
        emit_pretool_decision(
            "ask",
            f"Edit to '{target}' requested while still in the '{current_phase}' phase.",
            additional_context=(
                "Progressive context loading expects classification before non-trivial edits begin."
            ),
        )
        return 0

    read_files: list[str] = session_data.get("read_files", [])
    if tool_name in EDIT_TOOL_NAMES and read_files:
        edit_target = extract_edit_target_path(tool_input)
        if edit_target:
            guide = _surface_guide_for(edit_target)
            if guide and not _guide_was_read(guide, read_files):
                emit_pretool_decision(
                    "ask",
                    f"Edit to '{edit_target}' targets a scoped surface but `{guide}` has not been read yet in this session.",
                    additional_context=(
                        f"Load `{guide}` first to apply the surface-specific guidance, then retry the edit."
                    ),
                )
                return 0

    emit_continue()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())