"""Shared fixtures for agent runtime eval tests."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

HOOKS_DIR = str(Path(__file__).resolve().parent.parent.parent / ".github" / "hooks")
REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)

# Ensure hooks dir is importable
sys.path.insert(0, HOOKS_DIR)


@pytest.fixture()
def session_file(tmp_path: Path):
    """Create a temp session file and set the env var."""
    path = tmp_path / "session.json"
    old = os.environ.get("AGENT_SESSION_FILE")
    os.environ["AGENT_SESSION_FILE"] = str(path)
    yield path
    if old is None:
        os.environ.pop("AGENT_SESSION_FILE", None)
    else:
        os.environ["AGENT_SESSION_FILE"] = old


@pytest.fixture()
def fresh_state(session_file: Path):
    """Return a fresh SessionState backed by the temp session file."""
    from session_schema import SessionState, write_session

    state = SessionState()
    write_session(state, str(session_file))
    return state


def run_hook(
    hook_script: str,
    payload: dict[str, Any],
    session_file: Path,
) -> dict[str, Any]:
    """Run a hook script as a subprocess, returning the parsed JSON output."""
    env = {**os.environ, "AGENT_SESSION_FILE": str(session_file)}
    result = subprocess.run(
        [sys.executable, hook_script],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Hook failed (rc={result.returncode}): {result.stderr}"
        )
    return json.loads(result.stdout)


def run_pretool(
    payload: dict[str, Any], session_file: Path
) -> dict[str, Any]:
    script = os.path.join(HOOKS_DIR, "pretool_approval_policy.py")
    return run_hook(script, payload, session_file)


def run_posttool(
    payload: dict[str, Any], session_file: Path
) -> dict[str, Any]:
    script = os.path.join(HOOKS_DIR, "posttool_validator.py")
    return run_hook(script, payload, session_file)


def get_decision(result: dict[str, Any]) -> str:
    """Extract the permission decision from a pretool hook response."""
    hook_output = result.get("hookSpecificOutput", {})
    return hook_output.get("permissionDecision", "continue")


def read_session_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
