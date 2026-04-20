"""Tests for scripts/agent/failure_index.py — structured postmortem store."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.agent.failure_index import FailureIndex


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def idx(tmp_path: Path) -> FailureIndex:
    fi = FailureIndex(failures_dir=tmp_path)
    fi._store = None  # Disable memory_store integration for isolation.
    return fi


def _write(idx: FailureIndex, task_id: str = "t1", **kwargs: str) -> dict:
    defaults = {
        "symptoms": "test fails randomly",
        "root_cause": "race condition in fixture",
        "fix_applied": "added lock",
        "prevention_pattern": "always use thread-safe fixtures",
        "area": "tests",
        "task_class": "bugfix",
    }
    defaults.update(kwargs)
    return idx.write(task_id, **defaults)


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------


def test_write_returns_entry(idx: FailureIndex) -> None:
    entry = _write(idx, "t1")
    assert entry["task_id"] == "t1"
    assert entry["symptoms"] == "test fails randomly"


def test_write_creates_markdown_file(idx: FailureIndex, tmp_path: Path) -> None:
    _write(idx, "bug-001")
    md = tmp_path / "bug-001.md"
    assert md.exists()
    content = md.read_text()
    assert "# Failure Postmortem: bug-001" in content
    assert "race condition" in content


def test_write_creates_index_entry(idx: FailureIndex) -> None:
    _write(idx, "t2")
    index = idx._read_index()
    assert "t2" in index


def test_write_sets_created_at_timestamp(idx: FailureIndex) -> None:
    before = time.time()
    entry = _write(idx, "t3")
    after = time.time()
    assert before <= entry["created_at"] <= after


def test_write_strips_task_id(idx: FailureIndex) -> None:
    entry = _write(idx, "  t4  ")
    assert entry["task_id"] == "t4"


def test_write_overwrites_existing(idx: FailureIndex) -> None:
    _write(idx, "t5", symptoms="original symptom")
    _write(idx, "t5", symptoms="updated symptom")
    entry = idx.get("t5")
    assert entry is not None
    assert entry["symptoms"] == "updated symptom"


def test_write_markdown_includes_prevention_pattern(idx: FailureIndex, tmp_path: Path) -> None:
    _write(idx, "t6", prevention_pattern="use pytest-xdist barriers")
    content = (tmp_path / "t6.md").read_text()
    assert "use pytest-xdist barriers" in content


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_returns_entry(idx: FailureIndex) -> None:
    _write(idx, "t7")
    result = idx.get("t7")
    assert result is not None
    assert result["task_id"] == "t7"


def test_get_unknown_returns_none(idx: FailureIndex) -> None:
    assert idx.get("nobody") is None


# ---------------------------------------------------------------------------
# list_failures / recent
# ---------------------------------------------------------------------------


def test_list_empty_returns_empty(idx: FailureIndex) -> None:
    assert idx.list_failures() == []


def test_list_returns_all(idx: FailureIndex) -> None:
    _write(idx, "a")
    _write(idx, "b")
    assert len(idx.list_failures()) == 2


def test_list_sorted_newest_first(idx: FailureIndex) -> None:
    _write(idx, "a")
    time.sleep(0.01)
    _write(idx, "b")
    entries = idx.list_failures()
    assert entries[0]["task_id"] == "b"


def test_list_respects_n(idx: FailureIndex) -> None:
    for i in range(6):
        _write(idx, f"t{i}")
    assert len(idx.list_failures(n=3)) == 3


def test_recent_is_subset_of_list(idx: FailureIndex) -> None:
    for i in range(5):
        _write(idx, f"t{i}")
    recent = idx.recent(n=2)
    assert len(recent) == 2


# ---------------------------------------------------------------------------
# keyword search
# ---------------------------------------------------------------------------


def test_search_finds_by_symptom_word(idx: FailureIndex) -> None:
    _write(idx, "rc1", symptoms="database deadlock timeout")
    _write(idx, "rc2", symptoms="network timeout only")
    results = idx.search("deadlock")
    assert len(results) == 1
    assert results[0]["task_id"] == "rc1"


def test_search_returns_empty_no_match(idx: FailureIndex) -> None:
    _write(idx, "t1", symptoms="simple crash")
    assert idx.search("quantumflux") == []


def test_search_empty_query_returns_empty(idx: FailureIndex) -> None:
    _write(idx, "t1")
    assert idx.search("") == []


def test_search_ranks_by_token_frequency(idx: FailureIndex) -> None:
    _write(idx, "low", symptoms="timeout once")
    _write(idx, "high", symptoms="timeout timeout timeout repeated timeout")
    results = idx.search("timeout", n=5)
    assert results[0]["task_id"] == "high"


def test_search_matches_root_cause_field(idx: FailureIndex) -> None:
    _write(idx, "t1", root_cause="null pointer dereference in mapper")
    results = idx.search("null pointer")
    assert results[0]["task_id"] == "t1"


def test_search_matches_area_field(idx: FailureIndex) -> None:
    _write(idx, "t1", area="frontend")
    _write(idx, "t2", area="backend")
    results = idx.search("frontend")
    assert any(r["task_id"] == "t1" for r in results)


def test_search_respects_n(idx: FailureIndex) -> None:
    for i in range(8):
        _write(idx, f"e{i}", symptoms=f"common flaky test {i}")
    assert len(idx.search("common", n=3)) <= 3
