"""Pure-function audit trigger logic for the recurring self-audit cadence.

The orchestrator and posttool hook use these helpers to detect when the
adversarial-audit charter (`docs/runbooks/adversarial-audit.md`) should be
invoked. No I/O — all state lives on the SessionState argument.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pretool_policy_support import normalise_path

if TYPE_CHECKING:
    from session_schema import SessionState

SURFACE_BUCKETS: tuple[tuple[str, str], ...] = (
    (".github/", ".github/"),
    ("docs/", "docs/"),
    ("src/backend/", "src/backend/"),
    ("src/frontend/", "src/frontend/"),
    ("tests/", "tests/"),
)
OTHER_SURFACE = "other"


def surface_for_path(path: str) -> str:
    """Bucket a path into a coarse surface label."""
    norm = normalise_path(path)
    for prefix, label in SURFACE_BUCKETS:
        norm_prefix = normalise_path(prefix)
        if norm == norm_prefix or norm.startswith(norm_prefix + "/"):
            return label
    return OTHER_SURFACE


def increment_closed_task_for_surfaces(
    state: "SessionState", surfaces: set[str]
) -> None:
    """Increment the closed-task counter for each touched surface."""
    counts = dict(state.closed_task_count_per_surface)
    for surface in surfaces:
        counts[surface] = counts.get(surface, 0) + 1
    state.closed_task_count_per_surface = counts


def mark_audit_completed(
    state: "SessionState", surface: str, ts: float
) -> None:
    """Record audit completion for a surface and clear cadence state."""
    audits = dict(state.last_audit_at_per_surface)
    audits[surface] = ts
    state.last_audit_at_per_surface = audits
    counts = dict(state.closed_task_count_per_surface)
    counts[surface] = 0
    state.closed_task_count_per_surface = counts
    state.audit_due = False
    state.audit_due_reason = ""


def should_trigger_audit(
    state: "SessionState", threshold: int = 10
) -> tuple[bool, str]:
    """Return (trigger?, reason). Reason is 'cadence', 'blocked', or ''."""
    audits = state.last_audit_at_per_surface or {}
    last_blocked = float(state.last_blocked_at or 0.0)
    if last_blocked > 0.0 and last_blocked > max(audits.values(), default=0.0):
        return True, "blocked"
    for surface, count in (state.closed_task_count_per_surface or {}).items():
        if count >= threshold:
            return True, "cadence"
    return False, ""
