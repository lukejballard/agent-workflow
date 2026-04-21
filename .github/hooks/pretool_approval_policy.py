from __future__ import annotations

import json
import os
import sys
from typing import Any
from phase_engine import can_edit_in_phase
from pretool_policy_support import (
    EDIT_TOOL_NAMES,
    TERMINAL_TOOL_NAMES,
    edit_targets_out_of_scope,
    edit_targets_sensitive_surface,
    extract_edit_target_path,
    extract_terminal_command,
    guide_was_read,
    remote_write_policy_reason,
    surface_guide_for,
    terminal_policy_decision,
)
from session_log import append_log
from session_io_support import write_session_snapshot
from session_schema import read_session, write_session
from token_budget import check_budget, get_budget, record_token_usage

MAX_TOOL_CALLS = int(os.environ.get("AGENT_MAX_TOOL_CALLS", "50"))
LOW_CONFIDENCE_THRESHOLD = 0.4
REQUIRES_LOCK_TASK_CLASSES = {"brownfield-improvement", "greenfield-feature", "implement-from-existing-spec"}
CRITIQUE_EXEMPT_PHASES = {
    "goal-anchor",
    "classify",
    "breadth-scan",
    "depth-dive",
    "lock-requirements",
    "choose-approach",
    "adversarial-critique",
    "revise",
    "execute-or-answer",
    "self-review",
    "critique",
}

def check_and_increment_tool_call() -> tuple[bool, int]:
    state = read_session()
    state.tool_call_count += 1
    count = state.tool_call_count
    write_session(state)
    return count >= MAX_TOOL_CALLS, count

def emit_pretool_decision(
    decision: str, reason: str, *, additional_context: str | None = None
) -> None:
    payload: dict[str, Any] = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}}
    if additional_context:
        payload["hookSpecificOutput"]["additionalContext"] = additional_context
    sys.stdout.write(json.dumps(payload))

def emit_continue() -> None:
    sys.stdout.write(json.dumps({"continue": True}))

def handle_terminal(tool_input: dict[str, Any]) -> bool:
    command = extract_terminal_command(tool_input)
    if not command:
        return False
    decision = terminal_policy_decision(command)
    if decision is None:
        return False
    verdict, reason = decision
    emit_pretool_decision(verdict, reason, additional_context=None if verdict == "deny" else "Workspace policy allows normal read-only commands to continue but requires manual confirmation for environment, network, or remote-write operations.")
    return True

def handle_remote_write_tool(tool_name: str) -> bool:
    reason = remote_write_policy_reason(tool_name)
    if reason:
        emit_pretool_decision("ask", reason, additional_context="Remote repository writes, review actions, workflow dispatches, and delegated background tasks should not run silently.")
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

    write_session_snapshot()

    # Gate 0 — Token budget check
    budget_state = read_session()
    record_token_usage(budget_state, tool_name, tool_input)
    budget = get_budget()
    within_budget, utilization, used = check_budget(budget_state, budget=budget)
    write_session(budget_state)
    if not within_budget:
        append_log("token_budget_exceeded", {"estimated_used": used, "budget": budget, "utilization_pct": round(utilization, 1), "tool": tool_name})
        emit_pretool_decision("ask", f"Estimated token usage is ~{used:,} tokens ({utilization:.0f}% of {budget:,} budget). Consider compressing working memory before continuing.", additional_context="This is an approximation (chars/4). Override the ceiling with AGENT_TOKEN_BUDGET env var. Compress episodic summaries and remove stale scratchpad entries to reduce context size.")
        return 0

    limit_reached, call_count = check_and_increment_tool_call()
    if limit_reached:
        append_log("budget_exceeded", {"count": call_count, "tool": tool_name})
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
        append_log("sensitive_edit_blocked", {"tool": tool_name, "target": extract_edit_target_path(tool_input)})
        emit_pretool_decision(
            "ask",
            "Editing hook, policy, or secret-adjacent files requires manual approval.",
            additional_context="Sensitive automation and configuration surfaces should not be changed silently.",
        )
        return 0

    state = read_session()
    if tool_name in EDIT_TOOL_NAMES:
        target = extract_edit_target_path(tool_input) or "(unknown)"
        allowed, reason = can_edit_in_phase(state)
        if not allowed:
            append_log("phase_gate_blocked", {"phase": state.current_phase, "tool": tool_name, "target": target})
            emit_pretool_decision(
                "ask",
                f"Edit to '{target}' blocked: {reason}",
                additional_context=(
                    "The phase state machine requires context loading before edits. "
                    f"Current phase: '{state.current_phase}'. "
                    "Read bootstrap files and advance through planning phases first."
                ),
            )
            return 0
        if state.task_class in REQUIRES_LOCK_TASK_CLASSES and not state.requirements_locked:
            append_log("requirements_lock_gate", {"phase": state.current_phase, "task_class": state.task_class, "tool": tool_name, "target": target})
            emit_pretool_decision(
                "ask",
                f"Edit to '{target}' blocked: requirements not locked for task class '{state.task_class}'.",
                additional_context=(
                    "Set requirements_locked = true in session state after creating an "
                    "explicit requirements contract before beginning implementation."
                ),
            )
            return 0
        if state.confidence < LOW_CONFIDENCE_THRESHOLD and state.task_class not in ("trivial", "docs-only", "research-only"):
            append_log("low_confidence_gate", {"confidence": state.confidence, "phase": state.current_phase, "tool": tool_name})
            emit_pretool_decision(
                "ask",
                f"Confidence is {state.confidence:.2f} (below {LOW_CONFIDENCE_THRESHOLD}). Consider escalating to the user before making changes.",
                additional_context=(
                    "Update session state confidence field as your certainty changes. "
                    "Values below 0.4 trigger this review gate for non-trivial edits."
                ),
            )
            return 0
        if state.current_phase not in CRITIQUE_EXEMPT_PHASES:
            fail_checks = [result for result in state.critique_results if result.verdict == "FAIL"]
            if fail_checks:
                check_ids = ", ".join(result.check_id for result in fail_checks)
                append_log("critique_fail_gate", {"phase": state.current_phase, "failing_checks": [result.to_dict() for result in fail_checks], "tool": tool_name})
                emit_pretool_decision(
                    "ask",
                    f"Edit blocked: {len(fail_checks)} critique check(s) are FAIL: {check_ids}. Resolve these before making further changes.",
                    additional_context=(
                        "Update session state critique_results to PASS or WARN to clear this gate. "
                        "WARN results are allowed through. FAIL results block all edits."
                    ),
                )
                return 0

    allowed_paths: list[str] = state.allowed_paths
    if tool_name in EDIT_TOOL_NAMES and edit_targets_out_of_scope(tool_name, tool_input, allowed_paths):
        target = extract_edit_target_path(tool_input) or "(unknown)"
        append_log("scope_gate_blocked", {"phase": state.current_phase, "tool": tool_name, "target": target, "allowed_paths": allowed_paths})
        emit_pretool_decision(
            "ask",
            f"Edit target '{target}' is outside the task scope set by allowed_paths.",
            additional_context=(
                "Confirm the edit is intentional or update the allowed_paths session metadata. "
                f"Allowed paths: {allowed_paths}"
            ),
        )
        return 0

    read_files: list[str] = state.read_files
    if tool_name in EDIT_TOOL_NAMES and read_files:
        edit_target = extract_edit_target_path(tool_input)
        if edit_target:
            guide = surface_guide_for(edit_target)
            if guide and not guide_was_read(guide, read_files):
                append_log("surface_guide_missing", {"tool": tool_name, "target": edit_target, "guide": guide})
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