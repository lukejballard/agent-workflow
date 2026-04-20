"""Agent memory store — file-backed store with optional Chroma vector search.

Provides a key-value store with full-text / semantic search that works without
any optional dependencies and improves to semantic search when ``chromadb`` is
installed (ISSUE-07).

File backend (always available):
  Store root (env AGENT_MEMORY_DIR or ``memories/repo``, resolved relative to
  the workspace root):
    memory-store/index.json   — flat entry index for fast listing + keyword search
    memory-store/{id}.json    — individual entry files

Chroma backend (opt-in, used automatically when ``chromadb`` is importable):
  Persistent collection under ``{store_root}/memory-store-chroma/``.
  Keyword search falls back to the file backend if Chroma is unavailable.

CLI:
  python scripts/agent/memory_store.py put  <id> <text> [--meta key=value ...]
  python scripts/agent/memory_store.py get  <id>
  python scripts/agent/memory_store.py search <query> [--n 5]
  python scripts/agent/memory_store.py list   [--n 20]
  python scripts/agent/memory_store.py delete <id>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Optional Chroma import (graceful fallback)
# ---------------------------------------------------------------------------

try:
    import chromadb  # type: ignore[import-untyped]

    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants & defaults
# ---------------------------------------------------------------------------

_DEFAULT_MEMORY_DIR = "memories/repo"
_STORE_SUBDIR = "memory-store"
_CHROMA_SUBDIR = "memory-store-chroma"
_INDEX_NAME = "index.json"


# ---------------------------------------------------------------------------
# MemoryStore
# ---------------------------------------------------------------------------


class MemoryStore:
    """Persistent key-value store with keyword and optional vector search."""

    def __init__(
        self,
        store_root: str | Path | None = None,
        *,
        use_chroma: bool = True,
    ) -> None:
        if store_root is None:
            base = os.environ.get("AGENT_MEMORY_DIR", _DEFAULT_MEMORY_DIR)
            # Allow absolute or workspace-relative paths.
            base_path = Path(base)
            if not base_path.is_absolute():
                # Resolve relative to the repo root (two levels up from this file).
                repo_root = Path(__file__).parent.parent.parent
                base_path = repo_root / base_path
            store_root = base_path
        self._root: Path = Path(store_root) / _STORE_SUBDIR
        self._root.mkdir(parents=True, exist_ok=True)
        self._index_path = self._root / _INDEX_NAME
        self._chroma_client: Any = None
        self._chroma_collection: Any = None
        if use_chroma and _CHROMA_AVAILABLE:
            self._init_chroma()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_chroma(self) -> None:
        try:
            chroma_path = str(self._root.parent / _CHROMA_SUBDIR)
            self._chroma_client = chromadb.PersistentClient(path=chroma_path)
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                "agent_memory"
            )
        except Exception:  # pragma: no cover  # Chroma errors are non-fatal.
            self._chroma_client = None
            self._chroma_collection = None

    def _read_index(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self._index_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_index(self, index: dict[str, dict[str, Any]]) -> None:
        tmp = self._index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, indent=2))
        tmp.replace(self._index_path)

    def _entry_path(self, entry_id: str) -> Path:
        return self._root / f"{entry_id}.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(
        self,
        entry_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store or update an entry. Returns the stored entry dict."""
        if not entry_id or not entry_id.strip():
            raise ValueError("entry_id must be a non-empty string")
        entry_id = entry_id.strip()
        now = time.time()
        index = self._read_index()
        existing = index.get(entry_id, {})
        entry: dict[str, Any] = {
            "id": entry_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": existing.get("created_at", now),
            "updated_at": now,
        }
        # Write individual file.
        ep = self._entry_path(entry_id)
        tmp = ep.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry, indent=2))
        tmp.replace(ep)
        # Update index.
        index[entry_id] = {k: v for k, v in entry.items() if k != "text"}
        self._write_index(index)
        # Upsert into Chroma if available.
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.upsert(
                    ids=[entry_id],
                    documents=[text],
                    metadatas=[{str(k): str(v) for k, v in (metadata or {}).items()}],
                )
            except Exception:  # pragma: no cover
                pass
        return entry

    def get(self, entry_id: str) -> dict[str, Any] | None:
        """Return a stored entry by ID, or None if not found."""
        ep = self._entry_path(entry_id.strip())
        try:
            return json.loads(ep.read_text())  # type: ignore[no-any-return]
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def delete(self, entry_id: str) -> bool:
        """Delete an entry. Returns True if it existed."""
        entry_id = entry_id.strip()
        ep = self._entry_path(entry_id)
        existed = ep.exists()
        if existed:
            ep.unlink(missing_ok=True)
        index = self._read_index()
        if entry_id in index:
            del index[entry_id]
            self._write_index(index)
            existed = True
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.delete(ids=[entry_id])
            except Exception:  # pragma: no cover
                pass
        return existed

    def list_entries(self, *, n: int = 50) -> list[dict[str, Any]]:
        """Return entries sorted newest-first, limited to n."""
        index = self._read_index()
        entries = list(index.values())
        entries.sort(key=lambda e: e.get("updated_at", 0), reverse=True)
        return entries[:n]

    def search(self, query: str, *, n: int = 5) -> list[dict[str, Any]]:
        """Return up to n entries matching query (vector or keyword)."""
        if not query.strip():
            return []
        # Prefer Chroma vector search.
        if self._chroma_collection is not None:
            return self._chroma_search(query, n)
        return self._keyword_search(query, n)

    def _chroma_search(self, query: str, n: int) -> list[dict[str, Any]]:  # pragma: no cover
        try:
            results = self._chroma_collection.query(
                query_texts=[query], n_results=min(n, max(1, self._chroma_collection.count()))
            )
            ids: list[str] = results.get("ids", [[]])[0]
            entries = []
            for entry_id in ids:
                entry = self.get(entry_id)
                if entry:
                    entries.append(entry)
            return entries
        except Exception:
            return self._keyword_search(query, n)

    def _keyword_search(self, query: str, n: int) -> list[dict[str, Any]]:
        tokens = set(re.split(r"\W+", query.lower()))
        tokens.discard("")
        scored: list[tuple[float, dict[str, Any]]] = []
        for entry_id in self._read_index():
            entry = self.get(entry_id)
            if not entry:
                continue
            text = entry.get("text", "").lower()
            meta_text = json.dumps(entry.get("metadata", {})).lower()
            combined = f"{text} {meta_text}"
            hits = sum(combined.count(t) for t in tokens)
            if hits:
                scored.append((hits, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:n]]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent memory store — file-backed + optional Chroma vector search"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_put = sub.add_parser("put", help="Store an entry")
    p_put.add_argument("id", help="Entry ID (slug)")
    p_put.add_argument("text", help="Entry text")
    p_put.add_argument(
        "--meta",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help="Metadata key=value pairs",
    )

    p_get = sub.add_parser("get", help="Retrieve an entry by ID")
    p_get.add_argument("id", help="Entry ID")

    p_search = sub.add_parser("search", help="Search entries")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--n", type=int, default=5, help="Max results (default 5)")

    p_list = sub.add_parser("list", help="List entries newest-first")
    p_list.add_argument("--n", type=int, default=20, help="Max results (default 20)")

    p_del = sub.add_parser("delete", help="Delete an entry")
    p_del.add_argument("id", help="Entry ID")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    store = MemoryStore()

    if args.command == "put":
        meta: dict[str, str] = {}
        for kv in (args.meta or []):
            if "=" in kv:
                k, _, v = kv.partition("=")
                meta[k.strip()] = v.strip()
        entry = store.put(args.id, args.text, meta if meta else None)
        print(json.dumps(entry, indent=2))

    elif args.command == "get":
        entry = store.get(args.id)
        if entry is None:
            print(f"Not found: {args.id}", file=__import__("sys").stderr)
            return 1
        print(json.dumps(entry, indent=2))

    elif args.command == "search":
        results = store.search(args.query, n=args.n)
        print(json.dumps(results, indent=2))

    elif args.command == "list":
        entries = store.list_entries(n=args.n)
        print(json.dumps(entries, indent=2))

    elif args.command == "delete":
        found = store.delete(args.id)
        print("deleted" if found else "not found")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
