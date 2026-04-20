"""Typed session state with validation and atomic I/O.

Provides a structured schema for agent session state to replace
ad-hoc dict access with validated, versioned state objects.
Handles migration from v1 (unversioned) format transparently.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2

VALID_PHASES = (
    "goal-anchor",
    "classify",
    "breadth-scan",
    "depth-dive",
    "lock-requirements",
    "choose-approach",
    "adversarial-critique",
    "revise",
    "execute-or-answer",
    "traceability-and-verify",
)

VALID_VERIFICATION_STATUSES = (
    "pending",
    "in-progress",
    "verified",
    "partially-verified",
    "blocked",
)

PHASE_INDEX = {phase: i for i, phase in enumerate(VALID_PHASES)}


def _default_session_path() -> str:
    return os.environ.get(
        "AGENT_SESSION_FILE",
        str(Path.home() / ".agent-session" / "session.json"),
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
    last_updated: float = 0.0

    def validate(self) -> list[str]:
        """Return list of validation errors. Empty list means valid."""
        errors: list[str] = []
        if self.current_phase not in VALID_PHASES:
            errors.append(
                f"Invalid phase '{self.current_phase}'; "
                f"must be one of {VALID_PHASES}"
            )
        if not isinstance(self.phase_index, int) or self.phase_index < 0:
            errors.append(
                f"phase_index must be non-negative int, got {self.phase_index}"
            )
        if not isinstance(self.tool_call_count, int) or self.tool_call_count < 0:
            errors.append(
                f"tool_call_count must be non-negative int, got {self.tool_call_count}"
            )
        if not isinstance(self.read_files, list):
            errors.append("read_files must be a list")
        if not isinstance(self.allowed_paths, list):
            errors.append("allowed_paths must be a list")
        if self.verification_status not in VALID_VERIFICATION_STATUSES:
            errors.append(
                f"Invalid verification_status '{self.verification_status}'"
            )
        if not isinstance(self.edit_count, int) or self.edit_count < 0:
            errors.append(
                f"edit_count must be non-negative int, got {self.edit_count}"
            )
        if self.phase_index != PHASE_INDEX.get(self.current_phase, -1):
            errors.append(
                f"phase_index {self.phase_index} does not match "
                f"current_phase '{self.current_phase}'"
            )
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        """Create from dict with v1-to-v2 migration."""
        if not isinstance(data, dict):
            return cls()

        version = data.get("schema_version", 1)

        # Migrate v1 (unversioned) -> v2
        if version < SCHEMA_VERSION:
            data["schema_version"] = SCHEMA_VERSION
            data.setdefault("phase_index", 0)
            data.setdefault("edit_count", 0)
            data.setdefault("phase_history", [])
            data.setdefault("bootstrap_complete", False)
            data.setdefault("requirements_locked", False)
            data.setdefault("verification_status", "pending")
            data.setdefault("task_class", "")
            data.setdefault("scope_justification", "")
            data.setdefault("last_updated", 0.0)
            # Fix empty or missing current_phase
            if not data.get("current_phase"):
                data["current_phase"] = "goal-anchor"
            # Sync phase_index with current_phase
            phase = data.get("current_phase", "goal-anchor")
            data["phase_index"] = PHASE_INDEX.get(phase, 0)

        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}

        try:
            state = cls(**filtered)
        except TypeError:
            return cls()

        return state


def read_session(path: str | None = None) -> SessionState:
    """Read and validate session state from disk."""
    filepath = Path(path or _default_session_path())
    try:
        raw = json.loads(filepath.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return SessionState()

    return SessionState.from_dict(raw)


def write_session(state: SessionState, path: str | None = None) -> bool:
    """Validate and atomically write session state. Returns success."""
    state.last_updated = time.time()
    filepath = Path(path or _default_session_path())
    tmp = filepath.with_suffix(".tmp")
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(
            json.dumps(state.to_dict(), indent=2), encoding="utf-8"
        )
        tmp.replace(filepath)
        return True
    except OSError:
        return False
