import time

import pytest

from audit_trigger import (
    increment_closed_task_for_surfaces,
    mark_audit_completed,
    should_trigger_audit,
    surface_for_path,
)
from session_schema import SessionState


def test_surface_for_path_buckets_known_prefixes():
    assert surface_for_path(".github/hooks/foo.py") == ".github/"
    assert surface_for_path("docs/runbooks/x.md") == "docs/"
    assert surface_for_path("src/backend/api.py") == "src/backend/"
    assert surface_for_path("src/frontend/app.tsx") == "src/frontend/"
    assert surface_for_path("tests/test_x.py") == "tests/"


def test_surface_for_path_unknown_returns_other():
    assert surface_for_path("scripts/build.sh") == "other"
    assert surface_for_path("README.md") == "other"


def test_surface_for_path_handles_windows_separators():
    assert surface_for_path(".github\\hooks\\x.py") == ".github/"


def test_increment_closed_task_for_surfaces_accumulates():
    state = SessionState()
    increment_closed_task_for_surfaces(state, {".github/", "docs/"})
    increment_closed_task_for_surfaces(state, {".github/"})
    assert state.closed_task_count_per_surface == {".github/": 2, "docs/": 1}


def test_should_trigger_audit_fires_at_threshold():
    state = SessionState()
    state.closed_task_count_per_surface = {".github/": 10}
    triggered, reason = should_trigger_audit(state, threshold=10)
    assert triggered is True
    assert reason == "cadence"


def test_should_trigger_audit_does_not_fire_below_threshold():
    state = SessionState()
    state.closed_task_count_per_surface = {".github/": 9}
    triggered, reason = should_trigger_audit(state, threshold=10)
    assert triggered is False
    assert reason == ""


def test_should_trigger_audit_fires_on_blocked_state():
    state = SessionState()
    state.last_blocked_at = 1000.0
    state.last_audit_at_per_surface = {".github/": 500.0}
    triggered, reason = should_trigger_audit(state, threshold=10)
    assert triggered is True
    assert reason == "blocked"


def test_should_trigger_audit_blocked_does_not_fire_after_audit():
    state = SessionState()
    state.last_blocked_at = 1000.0
    state.last_audit_at_per_surface = {".github/": 1500.0}
    triggered, reason = should_trigger_audit(state, threshold=10)
    assert triggered is False


def test_mark_audit_completed_clears_cadence_state():
    state = SessionState()
    state.closed_task_count_per_surface = {".github/": 12}
    state.audit_due = True
    state.audit_due_reason = "cadence"
    mark_audit_completed(state, ".github/", ts=2000.0)
    assert state.last_audit_at_per_surface[".github/"] == 2000.0
    assert state.closed_task_count_per_surface[".github/"] == 0
    assert state.audit_due is False
    assert state.audit_due_reason == ""


def test_mark_audit_completed_no_double_fire():
    state = SessionState()
    state.closed_task_count_per_surface = {".github/": 10}
    triggered, _ = should_trigger_audit(state, threshold=10)
    assert triggered is True
    mark_audit_completed(state, ".github/", ts=time.time())
    triggered2, _ = should_trigger_audit(state, threshold=10)
    assert triggered2 is False
