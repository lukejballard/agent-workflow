"""Typed session state with validation and versioned migration."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from session_io_support import read_session_data, write_session_data
from session_log import append_log

SCHEMA_VERSION = 6
VALID_PHASES = (
    "goal-anchor", "classify", "breadth-scan", "depth-dive",
    "lock-requirements", "choose-approach", "adversarial-critique", "revise",
    "execute-or-answer", "self-review", "critique", "traceability-and-verify",
)
VALID_VERIFICATION_STATUSES = ("pending", "in-progress", "verified", "partially-verified", "blocked")

VALID_CRITIQUE_VERDICTS = ("PASS", "WARN", "FAIL")

PHASE_INDEX = {phase: i for i, phase in enumerate(VALID_PHASES)}

def _phase_budget_detail(estimated_tokens_used: int) -> dict[str, float | int]:
    from token_budget import get_budget

    budget = get_budget()
    utilization = (estimated_tokens_used / budget) * 100 if budget > 0 else 0.0
    return {"estimated_tokens_used": estimated_tokens_used, "token_budget": budget, "token_budget_utilization_pct": round(utilization, 1)}

@dataclass
class CritiqueResult:
    check_id: str
    verdict: Literal["PASS", "WARN", "FAIL"]
    rationale: str
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"check_id": self.check_id, "verdict": self.verdict, "rationale": self.rationale, "suggested_fix": self.suggested_fix}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CritiqueResult":
        return cls(
            check_id=str(data.get("check_id", "")),
            verdict=str(data.get("verdict", "PASS")),
            rationale=str(data.get("rationale", "")),
            suggested_fix=str(data.get("suggested_fix", "")),
        )

@dataclass
class SessionState:
    schema_version: int = SCHEMA_VERSION
    current_phase: str = "goal-anchor"
    phase_index: int = 0
    allowed_paths: list[str] = field(default_factory=list)
    tool_call_count: int = 0
    read_files: list[str] = field(default_factory=list)
    edit_count: int = 0
    phase_history: list[dict[str, Any]] = field(default_factory=list)
    bootstrap_complete: bool = False
    requirements_locked: bool = False
    verification_status: str = "pending"
    task_class: str = ""
    scope_justification: str = ""
    subtask_attempt_counts: dict[str, int] = field(default_factory=dict)
    confidence: float = 1.0
    failure_log: list[dict[str, Any]] = field(default_factory=list)
    estimated_tokens_used: int = 0
    critique_results: list[CritiqueResult] = field(default_factory=list)
    phase_token_costs: dict[str, int] = field(default_factory=dict)
    closed_task_count_per_surface: dict[str, int] = field(default_factory=dict)
    last_audit_at_per_surface: dict[str, float] = field(default_factory=dict)
    last_blocked_at: float = 0.0
    audit_due: bool = False
    audit_due_reason: str = ""
    verification_matrix_present: bool = False
    research_brief_required: bool = False
    last_updated: float = 0.0

    def validate(self) -> list[str]:
        """Return list of validation errors. Empty list means valid."""
        errors: list[str] = []
        if self.current_phase not in VALID_PHASES:
            errors.append(f"Invalid phase '{self.current_phase}'; must be one of {VALID_PHASES}")
        for name in ("phase_index", "tool_call_count", "edit_count", "estimated_tokens_used"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                errors.append(f"{name} must be a non-negative int, got {value}")
        for name in ("read_files", "allowed_paths", "failure_log"):
            if not isinstance(getattr(self, name), list):
                errors.append(f"{name} must be a list")
        if self.verification_status not in VALID_VERIFICATION_STATUSES:
            errors.append(f"Invalid verification_status '{self.verification_status}'")
        if not isinstance(self.subtask_attempt_counts, dict):
            errors.append("subtask_attempt_counts must be a dict")
        if not isinstance(self.confidence, (int, float)) or not 0.0 <= float(self.confidence) <= 1.0:
            errors.append(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not isinstance(self.critique_results, list):
            errors.append("critique_results must be a list")
        else:
            for result in self.critique_results:
                if not isinstance(result, CritiqueResult):
                    errors.append("critique_results must contain CritiqueResult entries")
                    break
                if result.verdict not in VALID_CRITIQUE_VERDICTS:
                    errors.append(f"Invalid critique verdict '{result.verdict}'")
                    break
        if not isinstance(self.phase_token_costs, dict):
            errors.append("phase_token_costs must be a dict")
        elif any(not isinstance(value, int) or value < 0 for value in self.phase_token_costs.values()):
            errors.append("phase_token_costs values must be non-negative ints")
        if not isinstance(self.closed_task_count_per_surface, dict):
            errors.append("closed_task_count_per_surface must be a dict")
        elif any(not isinstance(value, int) or value < 0 for value in self.closed_task_count_per_surface.values()):
            errors.append("closed_task_count_per_surface values must be non-negative ints")
        if not isinstance(self.last_audit_at_per_surface, dict):
            errors.append("last_audit_at_per_surface must be a dict")
        elif any(not isinstance(value, (int, float)) or value < 0 for value in self.last_audit_at_per_surface.values()):
            errors.append("last_audit_at_per_surface values must be non-negative numbers")
        if not isinstance(self.last_blocked_at, (int, float)) or self.last_blocked_at < 0:
            errors.append("last_blocked_at must be a non-negative number")
        if not isinstance(self.audit_due, bool):
            errors.append("audit_due must be a bool")
        if not isinstance(self.audit_due_reason, str):
            errors.append("audit_due_reason must be a str")
        if not isinstance(self.verification_matrix_present, bool):
            errors.append("verification_matrix_present must be a bool")
        if not isinstance(self.research_brief_required, bool):
            errors.append("research_brief_required must be a bool")
        if self.phase_index != PHASE_INDEX.get(self.current_phase, -1):
            errors.append(f"phase_index {self.phase_index} does not match current_phase '{self.current_phase}'")
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["critique_results"] = [result.to_dict() for result in self.critique_results]
        data["phase_token_costs"] = dict(self.phase_token_costs)
        return data

    def reset_for_new_task(self, task_class: str, allowed_paths: list[str]) -> None:
        """Reset transient task state while preserving durable counters and history."""
        self.task_class = task_class
        self.allowed_paths = list(allowed_paths)
        self.current_phase = "goal-anchor"
        self.phase_index = 0
        self.requirements_locked = False
        self.verification_status = "pending"
        self.confidence = 1.0
        self.critique_results = []
        self.phase_token_costs = {}
        self.subtask_attempt_counts = {}
        self.audit_due = False
        self.audit_due_reason = ""
        self.verification_matrix_present = False
        self.scope_justification = ""
        self.estimated_tokens_used = 0
        self.tool_call_count = 0
        self.edit_count = 0
        # Preserve: closed_task_count_per_surface, last_audit_at_per_surface,
        # last_blocked_at, failure_log, phase_history, read_files, bootstrap_complete.

    def declare_phase(self, target_phase: str) -> tuple[bool, str]:
        current_idx = PHASE_INDEX.get(self.current_phase)
        target_idx = PHASE_INDEX.get(target_phase)
        if current_idx is None:
            return False, f"Current phase '{self.current_phase}' is invalid."
        if target_idx is None:
            return False, f"Target phase '{target_phase}' is invalid."
        if target_idx <= current_idx:
            return False, f"Phase transition must move forward from '{self.current_phase}' to a later phase; got '{target_phase}'."
        old_phase = self.current_phase
        self.current_phase = target_phase
        self.phase_index = target_idx
        transition = {"from": old_phase, "to": target_phase, "at_tool_call": self.tool_call_count, "read_count": len(self.read_files), "edit_count": self.edit_count, "timestamp": time.time()}
        self.phase_history.append(transition)
        append_log("phase_transition", {**transition, **_phase_budget_detail(self.estimated_tokens_used)})
        return True, f"Phase advanced from '{old_phase}' to '{target_phase}'."

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        if not isinstance(data, dict):
            return cls()
        version = data.get("schema_version", 1)
        if not isinstance(version, int):
            version = 1
        if version < 2:
            for key, value in (("edit_count", 0), ("phase_history", []), ("bootstrap_complete", False), ("requirements_locked", False), ("verification_status", "pending"), ("task_class", ""), ("scope_justification", ""), ("last_updated", 0.0)):
                data.setdefault(key, value)
        if version < 3:
            for key, value in (("subtask_attempt_counts", {}), ("confidence", 1.0), ("failure_log", [])):
                data.setdefault(key, value)
        data.setdefault("estimated_tokens_used", 0)
        if version < 4:
            data.setdefault("critique_results", [])
            data.setdefault("phase_token_costs", {})
        if version < 5:
            data.setdefault("closed_task_count_per_surface", {})
            data.setdefault("last_audit_at_per_surface", {})
            data.setdefault("last_blocked_at", 0.0)
            data.setdefault("audit_due", False)
            data.setdefault("audit_due_reason", "")
            data.setdefault("verification_matrix_present", False)
        if version < 6:
            data.setdefault("research_brief_required", False)
        if version < SCHEMA_VERSION:
            data["schema_version"] = SCHEMA_VERSION
        if not data.get("current_phase"):
            data["current_phase"] = "goal-anchor"
        raw_critique = data.get("critique_results", [])
        if isinstance(raw_critique, list):
            data["critique_results"] = [item if isinstance(item, CritiqueResult) else CritiqueResult.from_dict(item) for item in raw_critique if isinstance(item, (CritiqueResult, dict))]
        else:
            data["critique_results"] = []
        raw_costs = data.get("phase_token_costs", {})
        if isinstance(raw_costs, dict):
            data["phase_token_costs"] = {str(key): value for key, value in raw_costs.items() if isinstance(value, int) and value >= 0}
        else:
            data["phase_token_costs"] = {}
        phase = data.get("current_phase", "goal-anchor")
        data["phase_index"] = PHASE_INDEX.get(phase, 0)
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        try:
            return cls(**filtered)
        except TypeError:
            return cls()


def read_session(path: str | None = None) -> SessionState:
    raw = read_session_data(path)
    if raw is None:
        return SessionState()
    return SessionState.from_dict(raw)


def write_session(state: SessionState, path: str | None = None) -> bool:
    state.last_updated = time.time()
    return write_session_data(state.to_dict(), path)
