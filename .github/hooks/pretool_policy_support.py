from __future__ import annotations

import re
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
    (re.compile(r"\bdel\b", re.IGNORECASE), "Shell delete commands are blocked by workspace policy."),
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
    ".github/agent-platform/workflow-manifest.json",
    ".github/AGENTS.md",
    ".github/copilot-instructions.md",
    ".vscode/settings.json",
    ".vscode/mcp.json",
    ".env",
    "docs/runbooks/adversarial-audit.md",
    "docs/specs/research/",
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

TERMINAL_TOOL_NAMES = {"run_in_terminal", "terminal"}

SURFACE_GUIDE_MAP: dict[str, str] = {
    ".github/": ".github/agents.md",
    "docs/": "docs/agents.md",
    "src/": ".github/instructions/python.instructions.md",
    "frontend/": ".github/instructions/react.instructions.md",
    "tests/": ".github/instructions/testing.instructions.md",
    "migrations/": ".github/instructions/database.instructions.md",
}


def normalise_path(raw: str) -> str:
    return raw.replace("\\", "/").lower().rstrip("/")


def _matches_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def surface_guide_for(path: str) -> str | None:
    norm = normalise_path(path)
    for prefix, guide in SURFACE_GUIDE_MAP.items():
        if _matches_prefix(norm, normalise_path(prefix)):
            return guide
    return None


def guide_was_read(guide: str, read_files: list[str]) -> bool:
    norm_guide = normalise_path(guide)
    return any(item == norm_guide or item.endswith("/" + norm_guide) for item in read_files)


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


def terminal_policy_decision(command: str) -> tuple[str, str] | None:
    for pattern, reason in DENY_COMMAND_PATTERNS:
        if pattern.search(command):
            return "deny", reason
    for pattern, reason in ASK_COMMAND_PATTERNS:
        if pattern.search(command):
            return "ask", reason
    return None


def remote_write_policy_reason(tool_name: str) -> str | None:
    for pattern, reason in ASK_TOOL_NAME_PATTERNS:
        if pattern.search(tool_name):
            return reason
    return None


def extract_edit_target_path(tool_input: dict[str, Any]) -> str | None:
    for key in ("filePath", "file_path", "path", "filename", "target", "destination"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def edit_targets_sensitive_surface(tool_name: str, tool_input: dict[str, Any]) -> bool:
    strings = find_strings(tool_input)
    if tool_name == "apply_patch":
        return any(marker in "\n".join(strings) for marker in SENSITIVE_PATH_MARKERS)
    lowered = [item.replace("\\", "/") for item in strings]
    return any(marker in item for item in lowered for marker in SENSITIVE_PATH_MARKERS)


def edit_targets_out_of_scope(
    tool_name: str, tool_input: dict[str, Any], allowed_paths: list[str]
) -> bool:
    if not allowed_paths or tool_name == "apply_patch":
        return False
    target = extract_edit_target_path(tool_input)
    if not target:
        return False
    norm_target = normalise_path(target)
    return not any(_matches_prefix(norm_target, normalise_path(path)) for path in allowed_paths)
