"""Tests for agent_runtime.tool_router."""

from __future__ import annotations

import pytest

from agent_runtime.tool_router import (
    ErrorClass,
    PolicyDecision,
    PolicyError,
    ToolPolicy,
    ToolSensitivity,
    classify_error,
    route,
)


# ---------------------------------------------------------------------------
# route — default approval threshold (HIGH)
# ---------------------------------------------------------------------------


def test_low_sensitivity_tool_is_allowed() -> None:
    result = route("read_file")
    assert result.decision == PolicyDecision.ALLOW


def test_medium_sensitivity_tool_is_allowed_by_default() -> None:
    result = route("create_file")
    assert result.decision == PolicyDecision.ALLOW


def test_high_sensitivity_tool_requires_approval() -> None:
    result = route("run_in_terminal")
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_critical_sensitivity_tool_requires_approval() -> None:
    result = route("github_create_pr")
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_deny_reason_is_none_for_allowed_tool() -> None:
    result = route("read_file")
    assert result.deny_reason is None


def test_deny_reason_is_none_for_require_approval_tool() -> None:
    result = route("run_in_terminal")
    assert result.deny_reason is None


# ---------------------------------------------------------------------------
# route — unknown tools use the default low policy
# ---------------------------------------------------------------------------


def test_unknown_tool_is_allowed_with_low_sensitivity() -> None:
    result = route("some_unknown_tool_xyz_123")
    assert result.decision == PolicyDecision.ALLOW
    assert result.sensitivity == ToolSensitivity.LOW


def test_unknown_tool_carries_default_timeout() -> None:
    result = route("some_unknown_tool_xyz_456")
    assert result.timeout_seconds == 30.0


# ---------------------------------------------------------------------------
# route — always_deny policy
# ---------------------------------------------------------------------------


def test_always_deny_tool_returns_deny_decision() -> None:
    import agent_runtime.tool_router as tr

    original = tr._TOOL_REGISTRY.get("_test_always_deny")
    tr._TOOL_REGISTRY["_test_always_deny"] = ToolPolicy(
        sensitivity=ToolSensitivity.HIGH, always_deny=True
    )
    try:
        result = route("_test_always_deny")
        assert result.decision == PolicyDecision.DENY
        assert result.deny_reason is not None
    finally:
        if original is None:
            tr._TOOL_REGISTRY.pop("_test_always_deny", None)
        else:
            tr._TOOL_REGISTRY["_test_always_deny"] = original


def test_always_deny_overrides_threshold() -> None:
    """An always_deny tool must be denied even when threshold would otherwise allow it."""
    import agent_runtime.tool_router as tr

    tr._TOOL_REGISTRY["_test_always_deny_low"] = ToolPolicy(
        sensitivity=ToolSensitivity.LOW, always_deny=True
    )
    try:
        result = route("_test_always_deny_low", approval_threshold=ToolSensitivity.CRITICAL)
        assert result.decision == PolicyDecision.DENY
    finally:
        tr._TOOL_REGISTRY.pop("_test_always_deny_low", None)


# ---------------------------------------------------------------------------
# route — custom approval threshold
# ---------------------------------------------------------------------------


def test_medium_threshold_makes_medium_tool_require_approval() -> None:
    result = route("create_file", approval_threshold=ToolSensitivity.MEDIUM)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_low_threshold_makes_even_low_tools_require_approval() -> None:
    result = route("read_file", approval_threshold=ToolSensitivity.LOW)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_critical_threshold_allows_high_tool() -> None:
    result = route("run_in_terminal", approval_threshold=ToolSensitivity.CRITICAL)
    assert result.decision == PolicyDecision.ALLOW


def test_critical_threshold_requires_approval_for_critical_tool() -> None:
    result = route("github_create_pr", approval_threshold=ToolSensitivity.CRITICAL)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


# ---------------------------------------------------------------------------
# RoutingResult fields
# ---------------------------------------------------------------------------


def test_routing_result_carries_tool_name() -> None:
    result = route("read_file")
    assert result.tool_name == "read_file"


def test_routing_result_carries_positive_timeout() -> None:
    result = route("read_file")
    assert result.timeout_seconds > 0


def test_routing_result_carries_non_negative_max_retries() -> None:
    result = route("read_file")
    assert result.max_retries >= 0


def test_routing_result_carries_sensitivity() -> None:
    result = route("read_file")
    assert result.sensitivity == ToolSensitivity.LOW


# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------


def test_classify_connection_error_as_transient() -> None:
    assert classify_error(ConnectionError("network blip")) == ErrorClass.TRANSIENT


def test_classify_timeout_error_as_transient() -> None:
    assert classify_error(TimeoutError("timed out")) == ErrorClass.TRANSIENT


def test_classify_os_error_as_transient() -> None:
    assert classify_error(OSError("i/o error")) == ErrorClass.TRANSIENT


def test_classify_permission_error_as_permanent() -> None:
    assert classify_error(PermissionError("access denied")) == ErrorClass.PERMANENT


def test_classify_value_error_as_permanent() -> None:
    assert classify_error(ValueError("bad input")) == ErrorClass.PERMANENT


def test_classify_type_error_as_permanent() -> None:
    assert classify_error(TypeError("type mismatch")) == ErrorClass.PERMANENT


def test_classify_not_implemented_error_as_permanent() -> None:
    assert classify_error(NotImplementedError("not implemented")) == ErrorClass.PERMANENT


def test_classify_policy_error_as_policy() -> None:
    assert classify_error(PolicyError("run_in_terminal", "denied")) == ErrorClass.POLICY


def test_classify_unknown_exception_as_permanent() -> None:
    assert classify_error(Exception("something unexpected")) == ErrorClass.PERMANENT


# ---------------------------------------------------------------------------
# PolicyError attributes
# ---------------------------------------------------------------------------


def test_policy_error_carries_tool_name_and_reason() -> None:
    err = PolicyError("run_in_terminal", "high-risk operation")
    assert err.tool_name == "run_in_terminal"
    assert err.reason == "high-risk operation"


def test_policy_error_message_contains_tool_name() -> None:
    err = PolicyError("github_push", "remote write")
    assert "github_push" in str(err)
