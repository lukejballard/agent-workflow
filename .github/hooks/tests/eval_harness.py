"""Eval harness for the agent hook system.

Run standalone: python .github/hooks/tests/eval_harness.py
Writes results to: .github/hooks/tests/eval_results.json
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import pretool_approval_policy as pretool
from session_schema import CritiqueResult, PHASE_INDEX, SessionState, write_session

RESULTS_PATH = Path(__file__).with_name("eval_results.json")


@dataclass
class Scenario:
    name: str
    gate: str
    session_overrides: dict[str, Any]
    payload: dict[str, Any]
    expected_decision: str
    env_overrides: dict[str, str] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    name: str
    gate: str
    expected: str
    actual: str
    passed: bool
    latency_ms: float
    error: str = ""


def _build_state(overrides: dict[str, Any]) -> SessionState:
    state = SessionState()
    for key, value in overrides.items():
        setattr(state, key, value)
    state.phase_index = PHASE_INDEX.get(state.current_phase, 0)
    return state


def _decision(output: dict[str, Any]) -> str:
    if output.get("continue") is True:
        return "continue"
    return output.get("hookSpecificOutput", {}).get("permissionDecision", "error")


def _run_scenario(scenario: Scenario) -> ScenarioResult:
    previous_env = {
        key: os.environ.get(key)
        for key in ["AGENT_SESSION_FILE", *scenario.env_overrides]
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        session_path = Path(tmp_dir) / "session.json"
        os.environ["AGENT_SESSION_FILE"] = str(session_path)
        for key, value in scenario.env_overrides.items():
            os.environ[key] = value
        write_session(_build_state(scenario.session_overrides), str(session_path))
        stdin = io.StringIO(json.dumps(scenario.payload))
        stdout = io.StringIO()
        old_stdin, old_stdout = pretool.sys.stdin, pretool.sys.stdout
        pretool.sys.stdin, pretool.sys.stdout = stdin, stdout
        error = ""
        start = time.perf_counter()
        try:
            exit_code = pretool.main()
            output = json.loads(stdout.getvalue())
            actual = _decision(output)
            if exit_code != 0:
                error = f"exit={exit_code}"
        except Exception as exc:
            actual = "error"
            error = repr(exc)
        finally:
            pretool.sys.stdin, pretool.sys.stdout = old_stdin, old_stdout
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        latency_ms = (time.perf_counter() - start) * 1000
        return ScenarioResult(
            name=scenario.name,
            gate=scenario.gate,
            expected=scenario.expected_decision,
            actual=actual,
            passed=actual == scenario.expected_decision,
            latency_ms=round(latency_ms, 2),
            error=error,
        )


def _scenarios() -> list[Scenario]:
    edit_payload = {"tool_name": "edit_file", "tool_input": {"filePath": "src/main.py"}}
    return [
        Scenario("phase_gate_blocks_breadth_scan_edit", "phase", {"current_phase": "breadth-scan"}, edit_payload, "ask"),
        Scenario("phase_gate_allows_execute_phase_edit", "phase", {"current_phase": "execute-or-answer", "requirements_locked": True, "task_class": "trivial"}, edit_payload, "continue"),
        Scenario("requirements_lock_gate_blocks_unlocked_brownfield", "requirements-lock", {"current_phase": "execute-or-answer", "task_class": "brownfield-improvement", "requirements_locked": False}, edit_payload, "ask"),
        Scenario("requirements_lock_gate_passes_locked_brownfield", "requirements-lock", {"current_phase": "execute-or-answer", "task_class": "brownfield-improvement", "requirements_locked": True}, edit_payload, "continue"),
        Scenario("confidence_gate_blocks_low_confidence_edit", "confidence", {"current_phase": "execute-or-answer", "confidence": 0.2, "task_class": "brownfield-improvement", "requirements_locked": True}, edit_payload, "ask"),
        Scenario("token_budget_gate_blocks_overrun", "token-budget", {"estimated_tokens_used": 999999}, {"tool_name": "read_file", "tool_input": {"filePath": "README.md"}}, "ask", {"AGENT_TOKEN_BUDGET": "100000"}),
        Scenario("destructive_command_denied", "destructive-command", {}, {"tool_name": "run_in_terminal", "tool_input": {"command": "rm -rf /"}}, "deny"),
        Scenario("sensitive_path_blocks_hooks_edit", "sensitive-path", {"current_phase": "execute-or-answer"}, {"tool_name": "edit_file", "tool_input": {"filePath": ".github/hooks/pretool_approval_policy.py"}}, "ask"),
        Scenario("scope_gate_blocks_out_of_scope_edit", "scope", {"allowed_paths": ["src/api/"], "current_phase": "execute-or-answer", "requirements_locked": True}, {"tool_name": "edit_file", "tool_input": {"filePath": "src/models/orm.py"}}, "ask"),
        Scenario("critique_fail_gate_blocks_edit_after_critique", "critique", {"current_phase": "traceability-and-verify", "critique_results": [CritiqueResult("security-review", "FAIL", "SQL injection surface")], "requirements_locked": True}, edit_payload, "ask"),
        Scenario("tool_call_limit_gate_blocks_retry_loop", "tool-call-limit", {"tool_call_count": pretool.MAX_TOOL_CALLS - 1}, {"tool_name": "read_file", "tool_input": {"filePath": "README.md"}}, "ask"),
    ]


def main() -> int:
    results = [_run_scenario(scenario) for scenario in _scenarios()]
    total = len(results)
    passed = sum(result.passed for result in results)
    failed = total - passed
    pass_rate = passed / total if total else 0.0
    mean_latency = sum(result.latency_ms for result in results) / total if total else 0.0
    payload = {
        "scenarios": [asdict(result) for result in results],
        "pass_rate": round(pass_rate, 4),
        "total": total,
        "passed": passed,
        "failed": failed,
        "regression_count": failed,
        "mean_gate_latency_ms": round(mean_latency, 2),
        "run_at": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"{'Scenario':44} {'Gate':18} {'Exp':10} {'Act':10} {'Latency':>8} {'Pass':>5}")
    for result in results:
        print(f"{result.name:44} {result.gate:18} {result.expected:10} {result.actual:10} {result.latency_ms:8.2f} {str(result.passed):>5}")
    print(f"pass_rate={pass_rate:.2%} regressions={failed} mean_latency_ms={mean_latency:.2f}")
    return 0 if pass_rate >= 0.80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
