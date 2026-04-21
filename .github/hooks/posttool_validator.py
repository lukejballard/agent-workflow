from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import audit_trigger
from failure_index import FailureIndex
from session_io_support import read_session_snapshot, default_session_path
from session_log import append_log, append_memory, read_memory

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

from session_schema import read_session, write_session, PHASE_INDEX
from phase_engine import detect_phase, is_bootstrap_complete

from pathlib import Path


def _workspace_root() -> Path:
    """Return the workspace root derived from the session file path."""
    return Path(default_session_path()).parent.parent


def _find_research_briefs() -> list[str]:
    """Return non-README .md filenames in docs/specs/research/."""
    brief_dir = _workspace_root() / "docs" / "specs" / "research"
    if not brief_dir.is_dir():
        return []
    return [p.name for p in brief_dir.glob("*.md") if p.name.lower() != "readme.md"]


def _memory_payload(state: Any) -> dict[str, Any]:
    """Build richer memory append kwargs from current critique results."""
    facts = [
        f"[{r.check_id}] {r.rationale}"
        for r in state.critique_results
        if r.verdict in ("PASS", "WARN")
    ]
    corrections = [
        f"[{r.check_id}] {r.suggested_fix or r.rationale}"
        for r in state.critique_results
        if r.verdict == "FAIL"
    ]
    artifacts = ", ".join(state.allowed_paths) if state.allowed_paths else ""
    return {
        "facts_learned": facts[:5],
        "corrections_applied": corrections[:3],
        "artifacts": artifacts,
    }


_PATH_KEYS: tuple[str, ...] = ("filePath", "file_path", "path", "filename", "uri")


# Task-class sets shared with pretool gate registry. Duplicated here to avoid
# a runtime import cycle (gate_registry imports several posttool support funcs).
REQUIRES_LOCK_TASK_CLASSES: frozenset[str] = frozenset(
    {
        "brownfield-improvement",
        "greenfield-feature",
        "implement-from-existing-spec",
    }
)
LOW_CONFIDENCE_THRESHOLD = 0.4

# Cap so prevention_pattern stays readable in failure-index records and TF-IDF
# results don't get overwhelmed by a single long entry.
_PREVENTION_PATTERN_MAX_LEN = 200


def _infer_failure_context(state: Any) -> tuple[str, str]:
    """Derive ``(root_cause, prevention_pattern)`` from session state.

    The branches are mutually exclusive and ordered by signal strength:
    explicit critique FAILs > requirements gap > low confidence > unknown.
    """
    fail_results = [r for r in state.critique_results if r.verdict == "FAIL"]
    if fail_results:
        ids = ", ".join(r.check_id for r in fail_results) or "(no ids)"
        root_cause = f"Critique checks failed: {ids}"
        prevention = "Resolve critique FAILs before advancing to verification"
        return root_cause, prevention[:_PREVENTION_PATTERN_MAX_LEN]

    if (
        not state.requirements_locked
        and state.task_class in REQUIRES_LOCK_TASK_CLASSES
    ):
        return (
            "Requirements not locked before execution",
            (
                "Always lock requirements before coding for "
                "brownfield/greenfield tasks"
            )[:_PREVENTION_PATTERN_MAX_LEN],
        )

    confidence = float(getattr(state, "confidence", 1.0))
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return (
            f"Low confidence ({confidence:.2f}) at block",
            (
                "Escalate to user when confidence < 0.4 before making edits"
            )[:_PREVENTION_PATTERN_MAX_LEN],
        )

    return (
        f"Unknown block at phase '{state.current_phase}'",
        "",
    )


# Task 4 — Research brief auto-trigger -----------------------------------------

_RESEARCH_BRIEF_TASK_CLASSES: frozenset[str] = frozenset(
    {
        "greenfield-feature",
        "brownfield-improvement",
        "implement-from-existing-spec",
    }
)
_RESEARCH_BRIEF_PHASE_MIN = "choose-approach"
_RESEARCH_BRIEF_LARGE_WRITE_THRESHOLD = 5000
_RESEARCH_BRIEF_DIR_FRAGMENT = "docs/specs/research/"


def _is_external_read_path(path: str) -> bool:
    """Return True for paths that look like fetched-external context.

    Excludes ``.github/`` so internal bootstrap reads never trip the trigger.
    """
    norm = path.replace("\\", "/").lower()
    if norm.startswith(".github/"):
        return False
    if "/fetch/" in norm or norm.startswith("fetch/"):
        return True
    if "http" in norm:
        return True
    return False


def _should_require_research_brief(
    state: Any, tool_name: str, tool_input: dict[str, Any]
) -> bool:
    """Decide whether to auto-set ``state.research_brief_required = True``.

    Two trigger conditions:

    1. The current task class needs a brief, the workflow has reached
       ``choose-approach`` or later, and at least one previously-recorded
       read path looks external (``fetch/`` or contains ``http``) while not
       being a ``.github/`` bootstrap file.
    2. A large write (``content`` field > 5000 chars) was just made under
       ``docs/specs/research/`` (the brief itself).

    The function is read-only — callers flip the flag.
    """
    if state.task_class not in _RESEARCH_BRIEF_TASK_CLASSES:
        return False

    # Trigger 2 — large research write counts even if phase is early.
    if tool_name in EDIT_TOOL_NAMES:
        content = tool_input.get("content")
        path = _extract_path(tool_input) or ""
        norm_path = path.replace("\\", "/").lower()
        if (
            isinstance(content, str)
            and len(content) > _RESEARCH_BRIEF_LARGE_WRITE_THRESHOLD
            and _RESEARCH_BRIEF_DIR_FRAGMENT in norm_path
        ):
            return True

    # Trigger 1 — external read after planning has begun.
    current_idx = PHASE_INDEX.get(state.current_phase, -1)
    min_idx = PHASE_INDEX.get(_RESEARCH_BRIEF_PHASE_MIN, 0)
    if current_idx < min_idx:
        return False
    return any(_is_external_read_path(p) for p in state.read_files)


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


def persist_state(state: Any, tool_name: str) -> None:
    if write_session(state):
        return
    append_log("session_write_retry", {"tool": tool_name, "phase": state.current_phase})
    if not write_session(state):
        append_log("session_write_failed", {"tool": tool_name, "phase": state.current_phase})


VERIFICATION_REQUIRED_TASK_CLASSES: frozenset[str] = frozenset(
    {
        "brownfield-improvement",
        "greenfield-feature",
        "implement-from-existing-spec",
        "test-only",
    }
)
AUDIT_CADENCE_TASK_CLASSES: frozenset[str] = frozenset(
    {
        "brownfield-improvement",
        "greenfield-feature",
        "implement-from-existing-spec",
    }
)


def _audit_threshold() -> int:
    try:
        return max(1, int(os.environ.get("AGENT_AUDIT_TASK_THRESHOLD", "10")))
    except ValueError:
        return 10


def _surfaces_touched(state: Any, edit_path: str | None) -> set[str]:
    paths: set[str] = set()
    for path in state.read_files:
        paths.add(path)
    if edit_path:
        paths.add(edit_path)
    return {audit_trigger.surface_for_path(path) for path in paths if path}


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
    previous_session = read_session_snapshot() or {}
    old_verification = previous_session.get(
        "verification_status", state.verification_status
    )
    old_phase = previous_session.get("current_phase", state.current_phase)

    record_read(tool_name, tool_input, state)
    first_edit = record_edit(tool_name, state)

    # Task 4 — auto-set research_brief_required when policy conditions trigger.
    # Only flip from False to True; reset_for_new_task is the single point of
    # clearing the flag.
    if not state.research_brief_required and _should_require_research_brief(
        state, tool_name, tool_input
    ):
        state.research_brief_required = True
        append_log(
            "research_brief_required_auto",
            {
                "task_class": state.task_class,
                "phase": state.current_phase,
                "tool": tool_name,
            },
        )

    # Task 4 — auto-set research_brief_required when policy conditions trigger.
    # Only flip from False to True; reset_for_new_task is the single point of
    # clearing the flag.
    if not state.research_brief_required and _should_require_research_brief(
        state, tool_name, tool_input
    ):
        state.research_brief_required = True
        append_log(
            "research_brief_required_auto",
            {
                "task_class": state.task_class,
                "phase": state.current_phase,
                "tool": tool_name,
            },
        )

    if not state.bootstrap_complete and is_bootstrap_complete(state.read_files):
        state.bootstrap_complete = True
        append_log("bootstrap_complete", {
            "read_count": len(state.read_files),
            "tool_call": state.tool_call_count,
        })

    detected = detect_phase(state)
    if detected != state.current_phase:
        if PHASE_INDEX.get(detected, -1) > state.phase_index:
            old = state.current_phase
            state.current_phase = detected
            state.phase_index = PHASE_INDEX[detected]
        root_cause, prevention_pattern = _infer_failure_context(state)
        failure = FailureIndex().write(
            task_class=state.task_class or "unknown",
            phase_at_failure=state.current_phase,
            symptom=(
                f"Session blocked at phase '{state.current_phase}' after "
                f"{state.edit_count} edits and {state.tool_call_count} tool calls."
            ),
            root_cause=root_cause,
            prevention_pattern=prevention_pattern
            append_log("phase_advisory", {
                "current": state.current_phase,
                "suggested": detected,
                "tool": tool_name,
            })

    if state.verification_status == "blocked" and old_verification != "blocked":
        root_cause, prevention_pattern = _infer_failure_context(state)
        failure = FailureIndex().write(
            task_class=state.task_class or "unknown",
            phase_at_failure=state.current_phase,
            symptom=(
                f"Session blocked at phase '{state.current_phase}' after "
                f"{state.edit_count} edits and {state.tool_call_count} tool calls."
            ),
            root_cause=root_cause,
            prevention_pattern=prevention_pattern,
            task_summary=state.scope_justification,
        )
        state.failure_log.append(
            {
                "ts": time.time(),
                "verification_status": "blocked",
                "failure_path": str(failure),
            }
        )
        state.last_blocked_at = time.time()
        previously_due = state.audit_due
        state.audit_due = True
        state.audit_due_reason = "blocked"
        if not previously_due:
            append_log("audit_required", {"reason": "blocked", "phase": state.current_phase})

    entered_verify = (
        state.current_phase == "traceability-and-verify"
        and old_phase != "traceability-and-verify"
    )
    if entered_verify and state.task_class in AUDIT_CADENCE_TASK_CLASSES:
        edit_path = _extract_path(tool_input)
        surfaces = _surfaces_touched(state, edit_path)
        if surfaces:
            audit_trigger.increment_closed_task_for_surfaces(state, surfaces)
        previously_due = state.audit_due
        triggered, reason = audit_trigger.should_trigger_audit(state, _audit_threshold())
        if triggered:
            state.audit_due = True
            state.audit_due_reason = reason
            if not previously_due:
                append_log("audit_due", {"reason": reason, "surfaces": sorted(surfaces)})

    if entered_verify and state.task_class in VERIFICATION_REQUIRED_TASK_CLASSES:
        # Research-brief gate: block verification if a brief was required but not created.
        if state.research_brief_required and not _find_research_briefs():
            state.verification_status = "blocked"
            append_log("research_brief_missing", {
                "task_class": state.task_class,
                "phase": state.current_phase,
            })
        else:
            # Write a richer episodic memory entry on entering verification.
            mp = _memory_payload(state)
            append_memory(
                phase=state.current_phase,
                summary=(
                    f"Entering traceability-and-verify for task_class='{state.task_class}'. "
                    f"{state.edit_count} edits, {state.tool_call_count} tool calls."
                ),
                verification=state.verification_status,
                **mp,
            )
        memories = read_memory()
        if not any((entry.get("verification") or "") for entry in memories):
            append_log("verification_matrix_missing", {
                "task_class": state.task_class,
                "phase": state.current_phase,
            })

    # Task-close trigger: when verification_status transitions to a terminal success state,
    # write a final memory entry and reset transient session state for the next task.
    TERMINAL_SUCCESS = frozenset({"verified", "partially-verified"})
    if (
        state.verification_status in TERMINAL_SUCCESS
        and old_verification not in TERMINAL_SUCCESS
        and state.current_phase == "traceability-and-verify"
    ):
        mp = _memory_payload(state)
        append_memory(
            phase=state.current_phase,
            summary=(
                f"Task closed: task_class='{state.task_class}', "
                f"verification='{state.verification_status}', "
                f"{state.edit_count} edits."
            ),
            verification=state.verification_status,
            next_step_hint="New task — call reset_for_new_task() or session will auto-reset on next task start.",
            **mp,
        )
        append_log("task_closed", {
            "task_class": state.task_class,
            "verification_status": state.verification_status,
            "edit_count": state.edit_count,
            "tool_call_count": state.tool_call_count,
        })
        state.reset_for_new_task("", [])

    if first_edit:
        edit_target = _extract_path(tool_input) or "(unknown)"
        append_log("first_edit", {
            "phase": state.current_phase,
            "target": edit_target,
            "tool": tool_name,
        })

    persist_state(state, tool_name)
    sys.stdout.write(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())