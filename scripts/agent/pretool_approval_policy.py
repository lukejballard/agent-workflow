import json
import re
import sys
from typing import Any

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
    (
        re.compile(
            r"\bshutdown\b|\brestart-computer\b|\bformat\b|\bmkfs\b", re.IGNORECASE
        ),
        "System-destructive commands are blocked by workspace policy.",
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
    (
        re.compile(r"\bgh\s+workflow\s+(?:run|rerun|cancel)\b", re.IGNORECASE),
        "Workflow dispatch or mutation commands require explicit approval.",
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
    ".github/workflows/",
    ".github/agent-platform/",
    "scripts/agent/",
    ".vscode/settings.json",
    ".vscode/mcp.json",
    ".github/copilot-instructions.md",
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

TERMINAL_TOOL_NAMES = {
    "run_in_terminal",
    "terminal",
}


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
                additional_context="Workspace policy allows normal read-only commands to continue but requires manual confirmation for environment, network, workflow, or remote-write operations.",
            )
            return True

    return False


def handle_remote_write_tool(tool_name: str) -> bool:
    for pattern, reason in ASK_TOOL_NAME_PATTERNS:
        if pattern.search(tool_name):
            emit_pretool_decision(
                "ask",
                reason,
                additional_context="Remote repository writes, review actions, workflow dispatches, and delegated background tasks should not run silently.",
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

    if handle_remote_write_tool(tool_name):
        return 0

    if tool_name in TERMINAL_TOOL_NAMES and handle_terminal(tool_input):
        return 0

    if tool_name in EDIT_TOOL_NAMES and edit_targets_sensitive_surface(
        tool_name, tool_input
    ):
        emit_pretool_decision(
            "ask",
            "Editing hook, approval-policy, or secret-adjacent files requires manual approval.",
            additional_context="Sensitive automation and configuration surfaces should not be changed silently, even in an otherwise auto-approved session.",
        )
        return 0

    emit_continue()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
