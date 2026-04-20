"""Tool routing policy — classifies tool call requests into allow / deny / require_approval.

The router is pure (no I/O, no side effects).  Callers are responsible for
emitting events and enforcing the returned decision.

Usage
-----
    from agent_runtime.tool_router import route, classify_error, PolicyDecision

    result = route("run_in_terminal")
    if result.decision == PolicyDecision.REQUIRE_APPROVAL:
        # emit approval_required event and pause
        ...
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ToolSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class ErrorClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    POLICY = "POLICY"


# Ordered list used for threshold comparison — index reflects severity rank.
_SENSITIVITY_ORDER: list[ToolSensitivity] = [
    ToolSensitivity.LOW,
    ToolSensitivity.MEDIUM,
    ToolSensitivity.HIGH,
    ToolSensitivity.CRITICAL,
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PolicyError(Exception):
    """Raised when a tool call is blocked by routing policy."""

    def __init__(self, tool_name: str, reason: str) -> None:
        super().__init__(f"Policy blocked {tool_name!r}: {reason}")
        self.tool_name = tool_name
        self.reason = reason


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ToolPolicy(BaseModel):
    """Per-tool routing configuration stored in the registry."""

    model_config = ConfigDict(extra="forbid")

    sensitivity: ToolSensitivity = ToolSensitivity.LOW
    timeout_seconds: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    always_deny: bool = False


class RoutingResult(BaseModel):
    """Immutable output of the route() function."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    decision: PolicyDecision
    sensitivity: ToolSensitivity
    timeout_seconds: float
    max_retries: int
    deny_reason: str | None = None


# ---------------------------------------------------------------------------
# Default tool registry
# ---------------------------------------------------------------------------

_DEFAULT_POLICY = ToolPolicy()

_TOOL_REGISTRY: dict[str, ToolPolicy] = {
    # Read-only / low-risk tools
    "read_file": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=10.0),
    "file_search": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=15.0),
    "grep_search": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=15.0),
    "semantic_search": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=30.0),
    "list_dir": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=10.0),
    "get_errors": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=15.0),
    "vscode_listCodeUsages": ToolPolicy(sensitivity=ToolSensitivity.LOW, timeout_seconds=15.0),
    # Local-write tools — medium risk
    "create_file": ToolPolicy(sensitivity=ToolSensitivity.MEDIUM, timeout_seconds=30.0),
    "replace_string_in_file": ToolPolicy(sensitivity=ToolSensitivity.MEDIUM, timeout_seconds=30.0),
    "multi_replace_string_in_file": ToolPolicy(sensitivity=ToolSensitivity.MEDIUM, timeout_seconds=30.0),
    "edit_notebook_file": ToolPolicy(sensitivity=ToolSensitivity.MEDIUM, timeout_seconds=30.0),
    # High-risk: remote writes, shell execution, destructive local ops
    "run_in_terminal": ToolPolicy(sensitivity=ToolSensitivity.HIGH, timeout_seconds=120.0, max_retries=1),
    "delete_file": ToolPolicy(sensitivity=ToolSensitivity.HIGH, timeout_seconds=30.0, max_retries=0),
    "github_push": ToolPolicy(sensitivity=ToolSensitivity.HIGH, timeout_seconds=60.0, max_retries=1),
    # Critical: irreversible or shared-system mutations
    "github_create_pr": ToolPolicy(
        sensitivity=ToolSensitivity.CRITICAL, timeout_seconds=60.0, max_retries=0
    ),
    "github_merge_pr": ToolPolicy(
        sensitivity=ToolSensitivity.CRITICAL, timeout_seconds=60.0, max_retries=0
    ),
    "github_force_push": ToolPolicy(
        sensitivity=ToolSensitivity.CRITICAL, timeout_seconds=60.0, max_retries=0, always_deny=True
    ),
}

# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

_TRANSIENT_TYPES: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)

_PERMANENT_TYPES: tuple[type[Exception], ...] = (
    PermissionError,
    ValueError,
    TypeError,
    NotImplementedError,
)


def classify_error(exc: Exception) -> ErrorClass:
    """Classify an exception for retry decisions.

    Returns:
        POLICY    — blocked by routing policy (PolicyError)
        TRANSIENT — transient network / I/O failure; exponential-backoff retry is safe
        PERMANENT — permanent failure; do not retry

    Note: PERMANENT is checked before TRANSIENT so that specific OSError
    subclasses (PermissionError, FileNotFoundError, etc.) are correctly
    classified as PERMANENT before the broader OSError transient match fires.
    """
    if isinstance(exc, PolicyError):
        return ErrorClass.POLICY
    if isinstance(exc, _PERMANENT_TYPES):
        return ErrorClass.PERMANENT
    if isinstance(exc, _TRANSIENT_TYPES):
        return ErrorClass.TRANSIENT
    # Unknown exception types default to PERMANENT to avoid silent retry storms.
    return ErrorClass.PERMANENT


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def route(
    tool_name: str,
    *,
    approval_threshold: ToolSensitivity = ToolSensitivity.HIGH,
) -> RoutingResult:
    """Evaluate routing policy for a tool call and return a decision.

    Args:
        tool_name: Name of the tool being invoked.
        approval_threshold: Tools with sensitivity at or above this level
            require operator approval.  Defaults to HIGH.

    Returns:
        RoutingResult with decision, timeout, retry budget, and optional deny reason.
    """
    policy = _TOOL_REGISTRY.get(tool_name, _DEFAULT_POLICY)

    if policy.always_deny:
        return RoutingResult(
            tool_name=tool_name,
            decision=PolicyDecision.DENY,
            sensitivity=policy.sensitivity,
            timeout_seconds=policy.timeout_seconds,
            max_retries=policy.max_retries,
            deny_reason="Tool policy has always_deny=True.",
        )

    tool_rank = _SENSITIVITY_ORDER.index(policy.sensitivity)
    threshold_rank = _SENSITIVITY_ORDER.index(approval_threshold)
    decision = (
        PolicyDecision.REQUIRE_APPROVAL
        if tool_rank >= threshold_rank
        else PolicyDecision.ALLOW
    )

    return RoutingResult(
        tool_name=tool_name,
        decision=decision,
        sensitivity=policy.sensitivity,
        timeout_seconds=policy.timeout_seconds,
        max_retries=policy.max_retries,
        deny_reason=None,
    )
