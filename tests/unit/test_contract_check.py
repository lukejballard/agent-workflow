"""Tests for scripts/agent/contract_check.py — API contract consistency checker."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import scripts.agent.contract_check as cc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_schema(
    routes: dict[str, list[str]] | None = None,
    components: list[str] | None = None,
) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for path, methods in (routes or {}).items():
        paths[path] = {m.lower(): {"summary": "test"} for m in methods}
    schema: dict[str, Any] = {"openapi": "3.1.0", "paths": paths}
    if components:
        schema["components"] = {"schemas": {c: {} for c in components}}
    return schema


# ---------------------------------------------------------------------------
# _extract_routes
# ---------------------------------------------------------------------------


def test_extract_routes_simple() -> None:
    schema = _make_schema({"/users": ["GET", "POST"]})
    routes = cc._extract_routes(schema)
    assert routes["/users"] == {"GET", "POST"}


def test_extract_routes_empty_paths() -> None:
    assert cc._extract_routes({"paths": {}}) == {}


def test_extract_routes_no_paths_key() -> None:
    assert cc._extract_routes({}) == {}


def test_extract_routes_skips_x_extensions() -> None:
    schema = {"paths": {"/items": {"get": {}, "x-internal": "secret"}}}
    routes = cc._extract_routes(schema)
    assert "X-INTERNAL" not in routes.get("/items", set())
    assert "GET" in routes["/items"]


# ---------------------------------------------------------------------------
# diff_schemas — routes
# ---------------------------------------------------------------------------


def test_diff_clean_identical() -> None:
    s = _make_schema({"/a": ["GET"]})
    result = cc.diff_schemas(s, s)
    assert result["clean"] is True
    assert result["added_routes"] == []
    assert result["removed_routes"] == []
    assert result["changed_routes"] == []


def test_diff_added_route() -> None:
    old = _make_schema({"/a": ["GET"]})
    new = _make_schema({"/a": ["GET"], "/b": ["POST"]})
    result = cc.diff_schemas(old, new)
    assert "/b" in result["added_routes"]
    assert result["clean"] is False


def test_diff_removed_route() -> None:
    old = _make_schema({"/a": ["GET"], "/b": ["DELETE"]})
    new = _make_schema({"/a": ["GET"]})
    result = cc.diff_schemas(old, new)
    assert "/b" in result["removed_routes"]
    assert result["clean"] is False


def test_diff_changed_methods() -> None:
    old = _make_schema({"/a": ["GET"]})
    new = _make_schema({"/a": ["GET", "POST"]})
    result = cc.diff_schemas(old, new)
    assert len(result["changed_routes"]) == 1
    assert result["changed_routes"][0]["path"] == "/a"
    assert result["clean"] is False


# ---------------------------------------------------------------------------
# diff_schemas — component schemas
# ---------------------------------------------------------------------------


def test_diff_added_schema_component() -> None:
    old = _make_schema(components=["User"])
    new = _make_schema(components=["User", "Token"])
    result = cc.diff_schemas(old, new)
    assert "Token" in result["added_schemas"]
    assert result["clean"] is False


def test_diff_removed_schema_component() -> None:
    old = _make_schema(components=["User", "Session"])
    new = _make_schema(components=["User"])
    result = cc.diff_schemas(old, new)
    assert "Session" in result["removed_schemas"]
    assert result["clean"] is False


# ---------------------------------------------------------------------------
# snapshot read/write
# ---------------------------------------------------------------------------


def test_write_and_read_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cc, "_REPO_ROOT", tmp_path)
    schema = _make_schema({"/ping": ["GET"]})
    p = cc.write_snapshot(schema, ".github/agent-platform/openapi.snapshot.json")
    assert p.exists()
    loaded = cc.read_snapshot(".github/agent-platform/openapi.snapshot.json")
    assert loaded is not None
    assert "/ping" in loaded["paths"]


def test_read_snapshot_returns_none_when_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cc, "_REPO_ROOT", tmp_path)
    result = cc.read_snapshot(".github/agent-platform/openapi.snapshot.json")
    assert result is None


# ---------------------------------------------------------------------------
# _load_app
# ---------------------------------------------------------------------------


def test_load_app_invalid_spec_raises() -> None:
    with pytest.raises(ValueError):
        cc._load_app("no_colon")


def test_load_app_missing_module_raises() -> None:
    with pytest.raises((ImportError, ModuleNotFoundError)):
        cc._load_app("nonexistent_module_xyz:app")


def test_load_app_missing_attribute_raises() -> None:
    with pytest.raises(AttributeError):
        cc._load_app("json:nonexistent_attribute_xyz")


def test_load_app_valid_stdlib() -> None:
    loaded = cc._load_app("json:loads")
    assert loaded is json.loads


# ---------------------------------------------------------------------------
# _get_openapi_dict
# ---------------------------------------------------------------------------


def test_get_openapi_dict_calls_method() -> None:
    schema = {"openapi": "3.0.0", "paths": {}}
    mock_app = MagicMock()
    mock_app.openapi.return_value = schema
    result = cc._get_openapi_dict(mock_app)
    assert result == schema


def test_get_openapi_dict_raises_for_non_app() -> None:
    with pytest.raises(TypeError):
        cc._get_openapi_dict({"not": "a fastapi app"})


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------


def test_cmd_status_no_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(cc, "_REPO_ROOT", tmp_path)
    rc = cc.cmd_status(".github/agent-platform/openapi.snapshot.json")
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["exists"] is False


def test_cmd_status_with_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(cc, "_REPO_ROOT", tmp_path)
    schema = _make_schema({"/a": ["GET"], "/b": ["POST"]}, components=["User"])
    schema["info"] = {"title": "My API"}
    cc.write_snapshot(schema, ".github/agent-platform/openapi.snapshot.json")
    rc = cc.cmd_status(".github/agent-platform/openapi.snapshot.json")
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["exists"] is True
    assert out["route_count"] == 2
    assert out["title"] == "My API"


# ---------------------------------------------------------------------------
# cmd_diff
# ---------------------------------------------------------------------------


def test_cmd_diff_no_snapshot_returns_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cc, "_REPO_ROOT", tmp_path)
    rc = cc.cmd_diff(None, ".github/agent-platform/openapi.snapshot.json")
    assert rc == 1


def test_cmd_diff_clean_returns_0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(cc, "_REPO_ROOT", tmp_path)
    schema = _make_schema({"/ping": ["GET"]})
    cc.write_snapshot(schema, ".github/agent-platform/openapi.snapshot.json")
    # diff with no live app — compares snapshot to itself.
    rc = cc.cmd_diff(None, ".github/agent-platform/openapi.snapshot.json")
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["clean"] is True
