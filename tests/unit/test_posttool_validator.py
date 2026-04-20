"""Tests for scripts/agent/posttool_validator.py — PostToolUse read-tracking hook."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.agent.posttool_validator as pv


@pytest.fixture()
def session_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    sf = tmp_path / "session.json"
    monkeypatch.setattr(pv, "_SESSION_FILE", str(sf))
    return sf


# ---------------------------------------------------------------------------
# _extract_path
# ---------------------------------------------------------------------------


def test_extract_filePath() -> None:
    assert pv._extract_path({"filePath": "/some/file.py"}) == "/some/file.py"


def test_extract_path_key() -> None:
    assert pv._extract_path({"path": "src/foo.py"}) == "src/foo.py"


def test_extract_uri_key() -> None:
    assert pv._extract_path({"uri": "file:///repo/x.ts"}) == "file:///repo/x.ts"


def test_extract_returns_none_when_absent() -> None:
    assert pv._extract_path({"command": "ls"}) is None


def test_extract_ignores_empty_string() -> None:
    assert pv._extract_path({"filePath": "   "}) is None


# ---------------------------------------------------------------------------
# _normalise
# ---------------------------------------------------------------------------


def test_normalise_backslashes() -> None:
    assert pv._normalise("src\\api\\main.py") == "src/api/main.py"


def test_normalise_case() -> None:
    assert pv._normalise("SRC/AGENTS.MD") == "src/agents.md"


def test_normalise_trailing_slash() -> None:
    assert pv._normalise("src/") == "src"


# ---------------------------------------------------------------------------
# record_read
# ---------------------------------------------------------------------------


def test_record_read_ignores_non_read_tool(session_file: Path) -> None:
    result = pv.record_read("run_in_terminal", {"command": "ls"})
    assert result is False
    assert not session_file.exists()


def test_record_read_ignores_missing_path(session_file: Path) -> None:
    result = pv.record_read("read_file", {"command": "ls"})
    assert result is False
    assert not session_file.exists()


def test_record_read_records_path(session_file: Path) -> None:
    result = pv.record_read("read_file", {"filePath": "src/AGENTS.md"})
    assert result is True
    data = json.loads(session_file.read_text())
    assert "src/agents.md" in data["read_files"]


def test_record_read_deduplicates(session_file: Path) -> None:
    pv.record_read("read_file", {"filePath": "src/AGENTS.md"})
    result = pv.record_read("read_file", {"filePath": "src/AGENTS.md"})
    assert result is False  # Already present.
    data = json.loads(session_file.read_text())
    assert data["read_files"].count("src/agents.md") == 1


def test_record_read_normalises_backslash(session_file: Path) -> None:
    pv.record_read("read_file", {"filePath": "src\\AGENTS.md"})
    data = json.loads(session_file.read_text())
    assert "src/agents.md" in data["read_files"]


def test_record_read_appends_multiple(session_file: Path) -> None:
    pv.record_read("read_file", {"filePath": "src/AGENTS.md"})
    pv.record_read("view_file", {"filePath": "frontend/AGENTS.md"})
    data = json.loads(session_file.read_text())
    assert "src/agents.md" in data["read_files"]
    assert "frontend/agents.md" in data["read_files"]


def test_record_read_merges_with_existing_session(session_file: Path) -> None:
    session_file.write_text(json.dumps({"tool_call_count": 7, "read_files": ["docs/agents.md"]}))
    pv.record_read("read_file", {"filePath": "src/AGENTS.md"})
    data = json.loads(session_file.read_text())
    assert data["tool_call_count"] == 7
    assert "docs/agents.md" in data["read_files"]
    assert "src/agents.md" in data["read_files"]


def test_record_read_all_read_tool_names(session_file: Path) -> None:
    for tool in ("read_file", "view_file", "view_image", "mcp_filesystem_read_file"):
        pv.record_read(tool, {"filePath": f"some/{tool}.py"})
    data = json.loads(session_file.read_text())
    assert len(data["read_files"]) == 4


# ---------------------------------------------------------------------------
# main (integration)
# ---------------------------------------------------------------------------


def test_main_always_continues(
    session_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import io, sys as _sys  # noqa: E401
    payload = json.dumps({"tool_name": "read_file", "tool_input": {"filePath": "AGENTS.md"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    captured = io.StringIO()
    monkeypatch.setattr("sys.stdout", captured)
    rc = pv.main()
    assert rc == 0
    output = json.loads(captured.getvalue())
    assert output == {"continue": True}


def test_main_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    captured = io.StringIO()
    monkeypatch.setattr("sys.stdout", captured)
    rc = pv.main()
    assert rc == 0
    assert json.loads(captured.getvalue()) == {"continue": True}
