"""Tests for app.py — verifies the FastAPI application factory.

These tests confirm the ASGI entry-point is importable and has all expected
routes registered without needing a live HTTP round-trip.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_runtime.app import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXPECTED_PATHS = {
    "/api/tasks",
    "/api/tasks/{task_id}",
    "/api/tasks/{task_id}/transitions",
    "/api/tasks/{task_id}/plan",
    "/api/tasks/{task_id}/events",
}


def _registered_paths(app: FastAPI) -> set[str]:
    return {route.path for route in app.routes if hasattr(route, "path")}  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app()
    assert isinstance(app, FastAPI)


def test_create_app_has_correct_title() -> None:
    app = create_app()
    assert app.title == "Agent Runtime API"


def test_create_app_registers_all_expected_routes() -> None:
    app = create_app()
    paths = _registered_paths(app)
    for expected in _EXPECTED_PATHS:
        assert expected in paths, f"Missing route: {expected}"


def test_create_app_instances_are_independent() -> None:
    app1 = create_app()
    app2 = create_app()
    assert app1 is not app2


# ---------------------------------------------------------------------------
# CORS origins helper
# ---------------------------------------------------------------------------


def test_cors_origins_defaults_to_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    from agent_runtime import app as app_module

    origins = app_module._cors_origins()
    assert origins == ["*"]


def test_cors_origins_parses_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, https://preview.example.com")
    from agent_runtime import app as app_module

    os.environ["CORS_ORIGINS"] = "https://app.example.com, https://preview.example.com"
    origins = app_module._cors_origins()
    assert "https://app.example.com" in origins
    assert "https://preview.example.com" in origins


def test_cors_origins_ignores_blank_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example.com, , https://b.example.com")
    from agent_runtime import app as app_module

    os.environ["CORS_ORIGINS"] = "https://a.example.com, , https://b.example.com"
    origins = app_module._cors_origins()
    assert "" not in origins
    assert len(origins) == 2


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


def test_module_level_app_is_fastapi() -> None:
    from agent_runtime.app import app

    assert isinstance(app, FastAPI)


def test_module_level_app_is_same_as_singleton() -> None:
    from agent_runtime.app import app
    from agent_runtime.app import app as app2

    assert app is app2


# ---------------------------------------------------------------------------
# Smoke test via TestClient
# ---------------------------------------------------------------------------


def test_list_tasks_returns_200_via_test_client() -> None:
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_lifespan_context_executes_without_error() -> None:
    """Entering the TestClient context triggers the app lifespan."""
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/api/tasks")
    assert resp.status_code == 200


def test_lifespan_wires_sql_store_when_database_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When DATABASE_URL is set the lifespan replaces the default store with SQLRuntimeStore."""
    import agent_runtime.routes as _routes

    # Record original store so monkeypatch restores it automatically after the test.
    monkeypatch.setattr(_routes, "_default_store", _routes._default_store)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from agent_runtime.storage.store import SQLRuntimeStore

    app = create_app()
    with TestClient(app):
        # The lifespan has fired; check the store type without making route
        # calls (sqlite:///:memory: drops tables between connections).
        assert isinstance(_routes._default_store, SQLRuntimeStore)


def test_lifespan_wires_temporal_runner_when_temporal_host_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When TEMPORAL_HOST is set the lifespan creates a TemporalPlanRunner on app.state."""
    monkeypatch.setenv("TEMPORAL_HOST", "localhost:7233")

    mock_client = MagicMock()
    mock_worker = MagicMock()
    mock_worker.__aenter__ = AsyncMock(return_value=mock_worker)
    mock_worker.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("temporalio.client.Client.connect", AsyncMock(return_value=mock_client)),
        patch("temporalio.worker.Worker", return_value=mock_worker),
    ):
        app = create_app()
        with TestClient(app):
            from agent_runtime.temporal_runner import TemporalPlanRunner

            assert hasattr(app.state, "temporal_runner")
            assert isinstance(app.state.temporal_runner, TemporalPlanRunner)

        # Verify the worker was shut down cleanly on exit.
        mock_worker.__aexit__.assert_called_once_with(None, None, None)
