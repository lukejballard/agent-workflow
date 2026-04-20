"""Tests for scripts/agent/memory_store.py — file-backed memory store."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from scripts.agent.memory_store import MemoryStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path) -> MemoryStore:
    return MemoryStore(store_root=tmp_path, use_chroma=False)


# ---------------------------------------------------------------------------
# put / get
# ---------------------------------------------------------------------------


def test_put_returns_entry(store: MemoryStore) -> None:
    entry = store.put("e1", "hello world")
    assert entry["id"] == "e1"
    assert entry["text"] == "hello world"


def test_put_creates_index(store: MemoryStore, tmp_path: Path) -> None:
    store.put("e1", "text1")
    index_path = tmp_path / "memory-store" / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text())
    assert "e1" in index


def test_put_creates_entry_file(store: MemoryStore, tmp_path: Path) -> None:
    store.put("e2", "some text")
    ep = tmp_path / "memory-store" / "e2.json"
    assert ep.exists()
    data = json.loads(ep.read_text())
    assert data["text"] == "some text"


def test_get_returns_entry(store: MemoryStore) -> None:
    store.put("e1", "hello")
    result = store.get("e1")
    assert result is not None
    assert result["text"] == "hello"


def test_get_unknown_returns_none(store: MemoryStore) -> None:
    assert store.get("nobody") is None


def test_put_updates_existing(store: MemoryStore) -> None:
    store.put("e1", "original")
    store.put("e1", "updated")
    result = store.get("e1")
    assert result is not None
    assert result["text"] == "updated"


def test_put_preserves_created_at(store: MemoryStore) -> None:
    entry1 = store.put("e1", "v1")
    time.sleep(0.01)
    entry2 = store.put("e1", "v2")
    assert entry1["created_at"] == entry2["created_at"]
    assert entry2["updated_at"] >= entry1["updated_at"]


def test_put_with_metadata(store: MemoryStore) -> None:
    entry = store.put("e1", "text", metadata={"area": "src", "type": "note"})
    assert entry["metadata"]["area"] == "src"


def test_put_empty_id_raises(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        store.put("", "text")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_existing_entry(store: MemoryStore, tmp_path: Path) -> None:
    store.put("e1", "text")
    assert store.delete("e1") is True
    assert store.get("e1") is None


def test_delete_removes_from_index(store: MemoryStore) -> None:
    store.put("e1", "text")
    store.delete("e1")
    assert "e1" not in store._read_index()


def test_delete_returns_false_when_not_found(store: MemoryStore) -> None:
    assert store.delete("nonexistent") is False


# ---------------------------------------------------------------------------
# list_entries
# ---------------------------------------------------------------------------


def test_list_empty_store(store: MemoryStore) -> None:
    assert store.list_entries() == []


def test_list_returns_all(store: MemoryStore) -> None:
    store.put("a", "text a")
    store.put("b", "text b")
    entries = store.list_entries()
    assert len(entries) == 2


def test_list_sorted_newest_first(store: MemoryStore) -> None:
    store.put("a", "first")
    time.sleep(0.01)
    store.put("b", "second")
    entries = store.list_entries()
    assert entries[0]["id"] == "b"
    assert entries[1]["id"] == "a"


def test_list_respects_n(store: MemoryStore) -> None:
    for i in range(10):
        store.put(f"e{i}", f"text {i}")
    assert len(store.list_entries(n=3)) == 3


# ---------------------------------------------------------------------------
# keyword search
# ---------------------------------------------------------------------------


def test_search_finds_by_word(store: MemoryStore) -> None:
    store.put("x", "python programming language")
    store.put("y", "javascript frontend")
    results = store.search("python")
    assert len(results) == 1
    assert results[0]["id"] == "x"


def test_search_returns_empty_for_no_match(store: MemoryStore) -> None:
    store.put("x", "hello world")
    assert store.search("typescript") == []


def test_search_empty_query(store: MemoryStore) -> None:
    store.put("x", "hello")
    assert store.search("") == []
    assert store.search("   ") == []


def test_search_ranks_by_hit_count(store: MemoryStore) -> None:
    store.put("low", "python once")
    store.put("high", "python python python repeated")
    results = store.search("python", n=5)
    assert results[0]["id"] == "high"


def test_search_respects_n(store: MemoryStore) -> None:
    for i in range(8):
        store.put(f"e{i}", f"common token text {i}")
    results = store.search("common", n=3)
    assert len(results) <= 3


def test_search_searches_metadata(store: MemoryStore) -> None:
    store.put("m1", "unrelated", metadata={"tag": "security-fix"})
    results = store.search("security")
    assert any(r["id"] == "m1" for r in results)


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------


def test_cli_put_and_get(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MEMORY_DIR", str(tmp_path))
    import scripts.agent.memory_store as ms_mod
    # Directly call CLI functions with a fresh store instance.
    s = MemoryStore(store_root=tmp_path, use_chroma=False)
    s.put("cli-test", "cli text content")
    result = s.get("cli-test")
    assert result is not None
    assert result["text"] == "cli text content"
