"""Gate registry: extensible policy enforcement for the PreToolUse hook.

Each ``Gate`` subclass encapsulates one policy check. ``main()`` in
``pretool_approval_policy.py`` iterates ``GATE_REGISTRY`` in order and emits
the first non-None decision returned by ``Gate.check``.

Per the project hardening contract, ``check()`` returns
``tuple[str, str] | None`` (``(decision, reason)``). Gates that need to surface
``additionalContext`` to the agent set ``self.additional_context`` as part of
``check`` and the registry runner forwards it to ``emit_pretool_decision``.
"""
from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
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
from session_schema import SessionState, write_session
from token_budget import check_budget, get_budget, record_token_usage

# Constants shared across gates -------------------------------------------------

MAX_TOOL_CALLS = int(os.environ.get("AGENT_MAX_TOOL_CALLS", "50"))
TOOL_CALL_DENY_THRESHOLD = MAX_TOOL_CALLS * 2
LOW_CONFIDENCE_THRESHOLD = 0.4
REQUIRES_LOCK_TASK_CLASSES = {
    "brownfield-improvement",
    "greenfield-feature",
    "implement-from-existing-spec",
}
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
CRITIQUE_REQUIRED_TASK_CLASSES = {
    "brownfield-improvement",
    "greenfield-feature",
    "implement-from-existing-spec",
}


class Gate(ABC):
    """Base class for one PreToolUse policy check."""

    name: str = ""
    additional_context: str | None = None

    @abstractmethod
    def check(
        self,
        state: SessionState,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> tuple[str, str] | None:
        """Return ``(decision, reason)`` to block, or ``None`` to pass through."""

    def reset_context(self) -> None:
        self.additional_context = None


# ---------------------------------------------------------------------------
# Gate 0 — Token budget
# ---------------------------------------------------------------------------


class TokenBudgetGate(Gate):
    name = "token-budget"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        record_token_usage(state, tool_name, tool_input)
        budget = get_budget()
        within_budget, utilization, used = check_budget(state, budget=budget)
        if within_budget:
            return None
        append_log(
            "token_budget_exceeded",
            {
                "estimated_used": used,
                "budget": budget,
                "utilization_pct": round(utilization, 1),
                "tool": tool_name,
            },
        )
        self.additional_context = (
            "This is an approximation (chars/4). Override the ceiling with "
            "AGENT_TOKEN_BUDGET env var. Compress episodic summaries and "
            "remove stale scratchpad entries to reduce context size."
        )
        return (
            "ask",
            (
                f"Estimated token usage is ~{used:,} tokens "
                f"({utilization:.0f}% of {budget:,} budget). "
                "Consider compressing working memory before continuing."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 1 — Tool call limit
# ---------------------------------------------------------------------------


class ToolCallLimitGate(Gate):
    name = "tool-call-limit"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        state.tool_call_count += 1
        count = state.tool_call_count
        if count < MAX_TOOL_CALLS:
            return None
        append_log("budget_exceeded", {"count": count, "tool": tool_name})
        if count >= TOOL_CALL_DENY_THRESHOLD:
            self.additional_context = (
                "Hard limit. The agent has already passed the soft limit and "
                "continued. This session must be closed. Start a new session "
                "or reset the session state."
            )
            return (
                "deny",
                (
                    f"Tool call count ({count}) has exceeded the hard ceiling "
                    f"({TOOL_CALL_DENY_THRESHOLD}). Session appears stuck in a "
                    "retry loop. Declare a final answer or abort."
                ),
            )
        self.additional_context = (
            "Override the limit with AGENT_MAX_TOOL_CALLS when the task is "
            "genuinely large."
        )
        return (
            "ask",
            (
                f"Tool call limit reached ({count}/{MAX_TOOL_CALLS}). "
                "Continuing may indicate an agent retry loop."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 2 — Remote write tools
# ---------------------------------------------------------------------------


class RemoteWriteGate(Gate):
    name = "remote-write"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        reason = remote_write_policy_reason(tool_name)
        if not reason:
            return None
        self.additional_context = (
            "Remote repository writes, review actions, workflow dispatches, "
            "and delegated background tasks should not run silently."
        )
        return ("ask", reason)


# ---------------------------------------------------------------------------
# Gate 3 — Destructive shell commands
# ---------------------------------------------------------------------------


class DestructiveCommandGate(Gate):
    name = "destructive-command"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in TERMINAL_TOOL_NAMES:
            return None
        command = extract_terminal_command(tool_input)
        if not command:
            return None
        decision = terminal_policy_decision(command)
        if decision is None:
            return None
        verdict, reason = decision
        if verdict != "deny":
            self.additional_context = (
                "Workspace policy allows normal read-only commands to "
                "continue but requires manual confirmation for environment, "
                "network, or remote-write operations."
            )
        return (verdict, reason)


# ---------------------------------------------------------------------------
# Gate 4 — Sensitive paths (hooks/policy/secrets)
# ---------------------------------------------------------------------------


class SensitivePathGate(Gate):
    name = "sensitive-path"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if not edit_targets_sensitive_surface(tool_name, tool_input):
            return None
        target = extract_edit_target_path(tool_input)
        append_log("sensitive_edit_blocked", {"tool": tool_name, "target": target})
        self.additional_context = (
            "Sensitive automation and configuration surfaces should not be "
            "changed silently."
        )
        return (
            "ask",
            "Editing hook, policy, or secret-adjacent files requires manual approval.",
        )


# ---------------------------------------------------------------------------
# Gate 5 — Phase state machine
# ---------------------------------------------------------------------------


class PhaseGate(Gate):
    name = "phase"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        target = extract_edit_target_path(tool_input) or "(unknown)"
        allowed, reason = can_edit_in_phase(state)
        if allowed:
            return None
        append_log(
            "phase_gate_blocked",
            {"phase": state.current_phase, "tool": tool_name, "target": target},
        )
        self.additional_context = (
            "The phase state machine requires context loading before edits. "
            f"Current phase: '{state.current_phase}'. "
            "Read bootstrap files and advance through planning phases first."
        )
        return ("ask", f"Edit to '{target}' blocked: {reason}")


# ---------------------------------------------------------------------------
# Gate 6 — Requirements lock
# ---------------------------------------------------------------------------


class RequirementsLockGate(Gate):
    name = "requirements-lock"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if state.task_class not in REQUIRES_LOCK_TASK_CLASSES:
            return None
        if state.requirements_locked:
            return None
        target = extract_edit_target_path(tool_input) or "(unknown)"
        append_log(
            "requirements_lock_gate",
            {
                "phase": state.current_phase,
                "task_class": state.task_class,
                "tool": tool_name,
                "target": target,
            },
        )
        self.additional_context = (
            "Set requirements_locked = true in session state after creating an "
            "explicit requirements contract before beginning implementation."
        )
        return (
            "ask",
            (
                f"Edit to '{target}' blocked: requirements not locked for "
                f"task class '{state.task_class}'."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 7 — Confidence floor
# ---------------------------------------------------------------------------


class ConfidenceGate(Gate):
    name = "confidence"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if state.task_class in ("trivial", "docs-only", "research-only"):
            return None
        if state.confidence >= LOW_CONFIDENCE_THRESHOLD:
            return None
        append_log(
            "low_confidence_gate",
            {
                "confidence": state.confidence,
                "phase": state.current_phase,
                "tool": tool_name,
            },
        )
        self.additional_context = (
            "Update session state confidence field as your certainty changes. "
            "Values below 0.4 trigger this review gate for non-trivial edits."
        )
        return (
            "ask",
            (
                f"Confidence is {state.confidence:.2f} (below "
                f"{LOW_CONFIDENCE_THRESHOLD}). Consider escalating to the user "
                "before making changes."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 8 — Critique FAIL verdicts (post-critique phases only)
# ---------------------------------------------------------------------------


class CritiqueFailGate(Gate):
    name = "critique-fail"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if state.current_phase in CRITIQUE_EXEMPT_PHASES:
            return None
        fail_checks = [r for r in state.critique_results if r.verdict == "FAIL"]
        if not fail_checks:
            return None
        check_ids = ", ".join(r.check_id for r in fail_checks)
        append_log(
            "critique_fail_gate",
            {
                "phase": state.current_phase,
                "failing_checks": [r.to_dict() for r in fail_checks],
                "tool": tool_name,
            },
        )
        self.additional_context = (
            "Update session state critique_results to PASS or WARN to clear "
            "this gate. WARN results are allowed through. FAIL results block "
            "all edits."
        )
        return (
            "ask",
            (
                f"Edit blocked: {len(fail_checks)} critique check(s) are "
                f"FAIL: {check_ids}. Resolve these before making further changes."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 9 — Critique completeness in verification phase (NEW)
# ---------------------------------------------------------------------------


class CritiqueCompletenessGate(Gate):
    """Block edits in traceability-and-verify when no critique was recorded.

    Forces non-trivial task classes to attest critique results before they
    can edit during the verification phase.
    """

    name = "critique-completeness"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if state.current_phase != "traceability-and-verify":
            return None
        if state.task_class not in CRITIQUE_REQUIRED_TASK_CLASSES:
            return None
        if state.critique_results:
            return None
        append_log(
            "critique_completeness_gate",
            {
                "phase": state.current_phase,
                "task_class": state.task_class,
                "tool": tool_name,
            },
        )
        self.additional_context = (
            "Record one CritiqueResult per required check (PASS/WARN/FAIL "
            "with rationale) in session state.critique_results before "
            "advancing past verification."
        )
        return (
            "ask",
            (
                "Critique results are empty in traceability-and-verify for "
                f"task class '{state.task_class}'. Run the structured "
                "critique checkpoint first."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 10 — Scope (allowed_paths)
# ---------------------------------------------------------------------------


class ScopeGate(Gate):
    name = "scope"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if not edit_targets_out_of_scope(tool_name, tool_input, state.allowed_paths):
            return None
        target = extract_edit_target_path(tool_input) or "(unknown)"
        append_log(
            "scope_gate_blocked",
            {
                "phase": state.current_phase,
                "tool": tool_name,
                "target": target,
                "allowed_paths": state.allowed_paths,
            },
        )
        self.additional_context = (
            "Confirm the edit is intentional or update the allowed_paths "
            f"session metadata. Allowed paths: {state.allowed_paths}"
        )
        return (
            "ask",
            (
                f"Edit target '{target}' is outside the task scope set by "
                "allowed_paths."
            ),
        )


# ---------------------------------------------------------------------------
# Gate 11 — Surface guide read
# ---------------------------------------------------------------------------


class SurfaceGuideGate(Gate):
    name = "surface-guide"

    def check(self, state, tool_name, tool_input):
        self.reset_context()
        if tool_name not in EDIT_TOOL_NAMES:
            return None
        if not state.read_files:
            return None
        edit_target = extract_edit_target_path(tool_input)
        if not edit_target:
            return None
        guide = surface_guide_for(edit_target)
        if not guide or guide_was_read(guide, state.read_files):
            return None
        append_log(
            "surface_guide_missing",
            {"tool": tool_name, "target": edit_target, "guide": guide},
        )
        self.additional_context = (
            f"Load `{guide}` first to apply the surface-specific guidance, "
            "then retry the edit."
        )
        return (
            "ask",
            (
                f"Edit to '{edit_target}' targets a scoped surface but "
                f"`{guide}` has not been read yet in this session."
            ),
        )


# ---------------------------------------------------------------------------
# Registry — order is significant. Token budget first, surface guide last.
# ---------------------------------------------------------------------------

GATE_REGISTRY: list[Gate] = [
    TokenBudgetGate(),
    ToolCallLimitGate(),
    RemoteWriteGate(),
    DestructiveCommandGate(),
    SensitivePathGate(),
    PhaseGate(),
    RequirementsLockGate(),
    ConfidenceGate(),
    CritiqueFailGate(),
    CritiqueCompletenessGate(),
    ScopeGate(),
    SurfaceGuideGate(),
]

# Silence "unused" complaints for `time` import (kept for future timing hooks).
_ = time
