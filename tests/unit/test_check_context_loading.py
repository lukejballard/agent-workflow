"""Tests for scripts/agent/check_context_loading.py — Phase 0 contract validator."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from scripts.agent.check_context_loading import check_context_loading


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_agent_file(tmp_path: Path, content: str, name: str = "orchestrator.agent.md") -> str:
    """Write *content* to a temp agent file and return the relative path."""
    target = "target/" + name
    (tmp_path / "target").mkdir(exist_ok=True)
    (tmp_path / target).write_text(textwrap.dedent(content), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Valid cases
# ---------------------------------------------------------------------------


def test_valid_phase0_passes(tmp_path: Path) -> None:
    content = """\
        # Before doing anything

        ## Phase 0 — Bootstrap (always, every task)
        1. Read `AGENTS.md` at the repo root.
        2. Read `.github/agent-platform/workflow-manifest.json` — for task classes.

        ## Phase 1 — Classify, then load for the classified surface
        More stuff here.
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert errors == []


def test_valid_phase0_case_insensitive_heading(tmp_path: Path) -> None:
    content = """\
        ## phase 0 — bootstrap
        1. Read `agents.md` at the repo root.
        2. Read `workflow-manifest.json` — details.

        ## Phase 1
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert errors == []


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_missing_phase0_heading_fails(tmp_path: Path) -> None:
    content = """\
        ## Phase 1 — Classify
        Some content.
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert len(errors) == 1
    assert "Phase 0" in errors[0]


def test_phase0_with_zero_items_fails(tmp_path: Path) -> None:
    content = """\
        ## Phase 0 — Bootstrap
        Just some prose, no numbered list items.

        ## Phase 1
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert any("no numbered list items" in e or "0 numbered" in e for e in errors)


def test_phase0_with_one_item_fails(tmp_path: Path) -> None:
    content = """\
        ## Phase 0 — Bootstrap
        1. Read `AGENTS.md`.

        ## Phase 1
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert any("exactly 2" in e for e in errors)


def test_phase0_with_three_items_fails(tmp_path: Path) -> None:
    content = """\
        ## Phase 0 — Bootstrap
        1. Read `AGENTS.md`.
        2. Read `workflow-manifest.json`.
        3. Read `repo-map.json` — should not be here.

        ## Phase 1
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert any("3" in e and "exactly 2" in e for e in errors)


def test_phase0_wrong_first_item_fails(tmp_path: Path) -> None:
    content = """\
        ## Phase 0 — Bootstrap
        1. Read `repo-map.json`.
        2. Read `workflow-manifest.json`.

        ## Phase 1
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert any("item 1" in e and "AGENTS.md" in e for e in errors)


def test_phase0_wrong_second_item_fails(tmp_path: Path) -> None:
    content = """\
        ## Phase 0 — Bootstrap
        1. Read `AGENTS.md`.
        2. Read `skill-registry.json`.

        ## Phase 1
    """
    target = _write_agent_file(tmp_path, content)
    errors = check_context_loading(tmp_path, target)
    assert any("item 2" in e and "workflow-manifest.json" in e for e in errors)


# ---------------------------------------------------------------------------
# File-not-found
# ---------------------------------------------------------------------------


def test_missing_target_file_fails(tmp_path: Path) -> None:
    errors = check_context_loading(tmp_path, "nonexistent/orchestrator.agent.md")
    assert len(errors) == 1
    assert "not found" in errors[0].lower()


# ---------------------------------------------------------------------------
# Real orchestrator.agent.md
# ---------------------------------------------------------------------------


def test_real_orchestrator_agent_file_passes() -> None:
    """The actual orchestrator.agent.md must satisfy the Phase 0 contract."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    agent_file = ".github/agents/orchestrator.agent.md"
    if not (repo_root / agent_file).exists():
        pytest.skip("orchestrator.agent.md not found — skipping live contract check")

    errors = check_context_loading(repo_root, agent_file)
    assert errors == [], f"Orchestrator Phase 0 contract violations:\n" + "\n".join(errors)
