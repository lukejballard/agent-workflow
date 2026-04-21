"""PreToolUse hook entrypoint.

The actual policy checks live in ``gate_registry.py`` as discrete ``Gate``
classes. This module is a thin runner: it parses the tool payload, snapshots
the session for posttool comparison, iterates the gate registry, and emits the
first non-None decision (or ``{"continue": true}``).

``additional_context`` strings emitted to VS Code are sanitized through
``_sanitize_additional_context`` to defang HTML/XML tags and bound the payload
size before they reach the agent's context channel.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

from gate_registry import (
    GATE_REGISTRY,
    LOW_CONFIDENCE_THRESHOLD,
    MAX_TOOL_CALLS,
    REQUIRES_LOCK_TASK_CLASSES,
    TOOL_CALL_DENY_THRESHOLD,
)
from session_io_support import write_session_snapshot
from session_log import append_log
from session_schema import read_session, write_session

# additionalContext sanitization ----------------------------------------------
# The 500 character limit caps the size of any string forwarded to VS Code's
# agent context channel. This protects against accidental prompt injection
# from gates that derive context from user-controlled or LLM-derived content.
_ADDITIONAL_CONTEXT_MAX_LEN = 500
_TAG_PATTERN = re.compile(r"<[^>]{0,200}>")


def _sanitize_additional_context(text: str) -> str:
    """Strip XML/HTML tags, trim whitespace, and truncate to 500 characters.

    The tag pattern is bounded to 200 characters per token to prevent
    catastrophic backtracking on pathological input.
    """
    cleaned = _TAG_PATTERN.sub("", text)
    cleaned = cleaned.strip()
    if len(cleaned) > _ADDITIONAL_CONTEXT_MAX_LEN:
        cleaned = cleaned[:_ADDITIONAL_CONTEXT_MAX_LEN]
    return cleaned


def emit_pretool_decision(
    decision: str, reason: str, *, additional_context: str | None = None
) -> None:
    """Emit a PreToolUse JSON decision to stdout."""
    if additional_context is not None:
        additional_context = _sanitize_additional_context(additional_context)
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

    write_session_snapshot()
    state = read_session()

    for gate in GATE_REGISTRY:
        result = gate.check(state, tool_name, tool_input)
        if result is None:
            continue
        decision, reason = result
        write_session(state)
        emit_pretool_decision(
            decision, reason, additional_context=gate.additional_context
        )
        return 0

    write_session(state)
    emit_continue()
    return 0


# Re-export so existing callers / tests can keep using ``pretool.<name>``.
__all__ = [
    "GATE_REGISTRY",
    "LOW_CONFIDENCE_THRESHOLD",
    "MAX_TOOL_CALLS",
    "REQUIRES_LOCK_TASK_CLASSES",
    "TOOL_CALL_DENY_THRESHOLD",
    "_sanitize_additional_context",
    "append_log",
    "emit_continue",
    "emit_pretool_decision",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
