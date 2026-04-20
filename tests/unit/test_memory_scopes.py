"""Tests for agent_runtime.memory_service — scoped storage and retrieval."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from agent_runtime.memory_service import InMemoryMemoryService
from agent_runtime.schemas import MemoryEntry, MemoryScope


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _entry(
    summary: str = "default summary",
    scope: MemoryScope = MemoryScope.WORKING,
    memory_id: str | None = None,
) -> MemoryEntry:
    return MemoryEntry(
        memory_id=memory_id or str(uuid.uuid4()),
        scope=scope,
        summary=summary,
        source="test",
        confidence=0.8,
        created_at=_now(),
    )


# ---------------------------------------------------------------------------
# write / read
# ---------------------------------------------------------------------------


def test_write_and_read_roundtrip() -> None:
    svc = InMemoryMemoryService()
    entry = _entry(memory_id="m-1")
    svc.write(entry)
    result = svc.read("m-1")
    assert result is not None
    assert result.memory_id == "m-1"


def test_read_nonexistent_returns_none() -> None:
    assert InMemoryMemoryService().read("does-not-exist") is None


def test_write_overwrites_existing_entry() -> None:
    svc = InMemoryMemoryService()
    original = _entry(summary="original", memory_id="m-1")
    updated = _entry(summary="updated", memory_id="m-1")
    svc.write(original)
    svc.write(updated)
    assert svc.read("m-1").summary == "updated"  # type: ignore[union-attr]


def test_write_multiple_entries_each_readable() -> None:
    svc = InMemoryMemoryService()
    for i in range(5):
        svc.write(_entry(memory_id=f"m-{i}"))
    for i in range(5):
        assert svc.read(f"m-{i}") is not None


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_existing_entry_returns_true() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(memory_id="to-delete"))
    assert svc.delete("to-delete") is True


def test_delete_existing_entry_removes_it() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(memory_id="gone"))
    svc.delete("gone")
    assert svc.read("gone") is None


def test_delete_nonexistent_returns_false() -> None:
    assert InMemoryMemoryService().delete("nonexistent") is False


# ---------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------


def test_count_returns_zero_when_empty() -> None:
    assert InMemoryMemoryService().count() == 0


def test_count_returns_total_entries() -> None:
    svc = InMemoryMemoryService()
    for i in range(3):
        svc.write(_entry(memory_id=f"m-{i}"))
    assert svc.count() == 3


def test_count_with_scope_filter() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(scope=MemoryScope.WORKING, memory_id="w-1"))
    svc.write(_entry(scope=MemoryScope.WORKING, memory_id="w-2"))
    svc.write(_entry(scope=MemoryScope.EPISODIC, memory_id="e-1"))
    assert svc.count(MemoryScope.WORKING) == 2
    assert svc.count(MemoryScope.EPISODIC) == 1
    assert svc.count(MemoryScope.SEMANTIC) == 0


# ---------------------------------------------------------------------------
# search — scope isolation
# ---------------------------------------------------------------------------


def test_search_scope_filters_to_matching_scope() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(summary="planner output", scope=MemoryScope.WORKING, memory_id="w-1"))
    svc.write(_entry(summary="planner archived", scope=MemoryScope.EPISODIC, memory_id="e-1"))

    results = svc.search("planner", scope=MemoryScope.WORKING)
    assert len(results) == 1
    assert results[0].scope == MemoryScope.WORKING


def test_search_without_scope_returns_all_matching() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(summary="context window", scope=MemoryScope.WORKING, memory_id="w-1"))
    svc.write(_entry(summary="context history", scope=MemoryScope.EPISODIC, memory_id="e-1"))

    results = svc.search("context")
    assert len(results) == 2


def test_search_scope_returns_empty_when_no_match_in_scope() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(summary="some text", scope=MemoryScope.EPISODIC, memory_id="e-1"))
    results = svc.search("some text", scope=MemoryScope.WORKING)  # wrong scope
    assert results == []


# ---------------------------------------------------------------------------
# search — case insensitivity
# ---------------------------------------------------------------------------


def test_search_is_case_insensitive() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(summary="MixedCase Summary", memory_id="m-1"))
    assert len(svc.search("mixedcase")) == 1
    assert len(svc.search("MIXEDCASE")) == 1
    assert len(svc.search("mixedcase summary")) == 1


# ---------------------------------------------------------------------------
# search — limit
# ---------------------------------------------------------------------------


def test_search_limit_restricts_results() -> None:
    svc = InMemoryMemoryService()
    for i in range(10):
        svc.write(_entry(summary="relevant item", memory_id=f"m-{i}"))
    results = svc.search("relevant", limit=3)
    assert len(results) == 3


def test_search_limit_zero_returns_empty() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(summary="something"))
    assert svc.search("something", limit=0) == []


def test_search_non_matching_query_returns_empty() -> None:
    svc = InMemoryMemoryService()
    svc.write(_entry(summary="something else"))
    assert svc.search("zzz_no_match") == []
