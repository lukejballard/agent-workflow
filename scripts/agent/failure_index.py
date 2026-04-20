"""Failure learning loop — write, search, and retrieve structured postmortems.

Addresses ISSUE-21: every time a task fails or a significant bug is fixed,
write a structured postmortem so future runs can retrieve relevant past failures
before attempting the same type of work.

Storage layout:
  memories/repo/failures/
    {task_id}.md          — human-readable Markdown postmortem
    .index.json           — machine-readable index for fast search

Integrates with memory_store.py when available for optional vector search.

CLI:
  python scripts/agent/failure_index.py write <task_id> \\
      --symptoms "..." --root-cause "..." --fix "..." --pattern "..." \\
      [--area src|frontend|tests|docs] [--task-class bugfix|feature|...]
  python scripts/agent/failure_index.py list [--n 10]
  python scripts/agent/failure_index.py search <query>
  python scripts/agent/failure_index.py recent [--n 5]
  python scripts/agent/failure_index.py show <task_id>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

_DEFAULT_FAILURES_DIR = "memories/repo/failures"
_INDEX_NAME = ".index.json"

# Optional memory_store integration.
try:
    from scripts.agent.memory_store import MemoryStore as _MemoryStore

    _MEMORY_STORE_AVAILABLE = True
except ImportError:
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "memory_store",
            Path(__file__).parent / "memory_store.py",
        )
        if _spec and _spec.loader:
            _ms_mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_ms_mod)   # type: ignore[arg-type]
            _MemoryStore = _ms_mod.MemoryStore   # type: ignore[misc]
            _MEMORY_STORE_AVAILABLE = True
        else:
            _MEMORY_STORE_AVAILABLE = False
    except Exception:
        _MEMORY_STORE_AVAILABLE = False


# ---------------------------------------------------------------------------
# FailureIndex
# ---------------------------------------------------------------------------


class FailureIndex:
    """Write and query structured failure postmortems."""

    def __init__(self, failures_dir: str | Path | None = None) -> None:
        if failures_dir is None:
            base = os.environ.get("AGENT_FAILURES_DIR", _DEFAULT_FAILURES_DIR)
            base_path = Path(base)
            if not base_path.is_absolute():
                repo_root = Path(__file__).parent.parent.parent
                base_path = repo_root / base_path
            failures_dir = base_path
        self._root = Path(failures_dir)
        self._root.mkdir(parents=True, exist_ok=True)
        self._index_path = self._root / _INDEX_NAME

        # Optional memory store for vector search.
        self._store: Any = None
        if _MEMORY_STORE_AVAILABLE:
            try:
                self._store = _MemoryStore()  # type: ignore[misc]
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_index(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self._index_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_index(self, index: dict[str, dict[str, Any]]) -> None:
        tmp = self._index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, indent=2))
        tmp.replace(self._index_path)

    def _pm_path(self, task_id: str) -> Path:
        return self._root / f"{task_id}.md"

    @staticmethod
    def _render_markdown(entry: dict[str, Any]) -> str:
        lines = [
            f"# Failure Postmortem: {entry['task_id']}",
            "",
            f"**Area:** {entry.get('area', 'unspecified')}  ",
            f"**Task class:** {entry.get('task_class', 'unspecified')}  ",
            f"**Date:** {time.strftime('%Y-%m-%d', time.localtime(entry.get('created_at', 0)))}",
            "",
            "## Symptoms",
            "",
            entry.get("symptoms", ""),
            "",
            "## Root cause",
            "",
            entry.get("root_cause", ""),
            "",
            "## Fix applied",
            "",
            entry.get("fix_applied", ""),
            "",
            "## Prevention pattern",
            "",
            entry.get("prevention_pattern", ""),
            "",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(
        self,
        task_id: str,
        *,
        symptoms: str,
        root_cause: str,
        fix_applied: str,
        prevention_pattern: str,
        area: str = "unspecified",
        task_class: str = "unspecified",
    ) -> dict[str, Any]:
        """Write a structured postmortem. Returns the index entry dict."""
        task_id = task_id.strip()
        now = time.time()
        entry: dict[str, Any] = {
            "task_id": task_id,
            "area": area,
            "task_class": task_class,
            "symptoms": symptoms,
            "root_cause": root_cause,
            "fix_applied": fix_applied,
            "prevention_pattern": prevention_pattern,
            "created_at": now,
        }
        # Write Markdown file.
        md_path = self._pm_path(task_id)
        md_path.write_text(self._render_markdown(entry))
        # Update index.
        index = self._read_index()
        index[task_id] = entry
        self._write_index(index)
        # Index in memory store for vector search.
        if self._store is not None:
            try:
                combined_text = " ".join([
                    symptoms, root_cause, fix_applied, prevention_pattern
                ])
                self._store.put(
                    f"failure:{task_id}",
                    combined_text,
                    {
                        "task_id": task_id,
                        "area": area,
                        "task_class": task_class,
                        "type": "failure",
                    },
                )
            except Exception:
                pass
        return entry

    def get(self, task_id: str) -> dict[str, Any] | None:
        """Return a postmortem entry by task ID, or None."""
        index = self._read_index()
        return index.get(task_id.strip())

    def list_failures(self, *, n: int = 20) -> list[dict[str, Any]]:
        """Return entries sorted newest-first, limited to n."""
        index = self._read_index()
        entries = list(index.values())
        entries.sort(key=lambda e: e.get("created_at", 0), reverse=True)
        return entries[:n]

    def recent(self, *, n: int = 5) -> list[dict[str, Any]]:
        """Return the n most recent postmortems."""
        return self.list_failures(n=n)

    def search(self, query: str, *, n: int = 5) -> list[dict[str, Any]]:
        """Return up to n entries matching query (vector or keyword)."""
        if not query.strip():
            return []
        # Prefer memory_store vector search.
        if self._store is not None:
            try:
                results = self._store.search(f"failure {query}", n=n)
                found = []
                for r in results:
                    meta = r.get("metadata", {})
                    if meta.get("type") == "failure":
                        tid = meta.get("task_id", "")
                        entry = self.get(tid)
                        if entry:
                            found.append(entry)
                if found:
                    return found
            except Exception:
                pass
        return self._keyword_search(query, n)

    def _keyword_search(self, query: str, n: int) -> list[dict[str, Any]]:
        tokens = set(re.split(r"\W+", query.lower()))
        tokens.discard("")
        index = self._read_index()
        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in index.values():
            combined = " ".join([
                str(entry.get(k, "")) for k in
                ("symptoms", "root_cause", "fix_applied", "prevention_pattern", "area", "task_class")
            ]).lower()
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
        description="Failure learning loop — write and retrieve structured postmortems"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_write = sub.add_parser("write", help="Write a postmortem")
    p_write.add_argument("task_id", help="Unique task/bug identifier")
    p_write.add_argument("--symptoms", required=True, help="Observable failure symptoms")
    p_write.add_argument("--root-cause", required=True, dest="root_cause")
    p_write.add_argument("--fix", required=True, dest="fix_applied", help="Fix applied")
    p_write.add_argument(
        "--pattern", required=True, dest="prevention_pattern",
        help="Actionable prevention pattern"
    )
    p_write.add_argument("--area", default="unspecified")
    p_write.add_argument("--task-class", dest="task_class", default="unspecified")

    p_list = sub.add_parser("list", help="List postmortems newest-first")
    p_list.add_argument("--n", type=int, default=10)

    p_search = sub.add_parser("search", help="Search postmortems")
    p_search.add_argument("query")
    p_search.add_argument("--n", type=int, default=5)

    p_recent = sub.add_parser("recent", help="Most recent postmortems")
    p_recent.add_argument("--n", type=int, default=5)

    p_show = sub.add_parser("show", help="Show a postmortem")
    p_show.add_argument("task_id")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    idx = FailureIndex()

    if args.command == "write":
        entry = idx.write(
            args.task_id,
            symptoms=args.symptoms,
            root_cause=args.root_cause,
            fix_applied=args.fix_applied,
            prevention_pattern=args.prevention_pattern,
            area=args.area,
            task_class=args.task_class,
        )
        print(json.dumps(entry, indent=2))

    elif args.command == "list":
        print(json.dumps(idx.list_failures(n=args.n), indent=2))

    elif args.command == "search":
        print(json.dumps(idx.search(args.query, n=args.n), indent=2))

    elif args.command == "recent":
        print(json.dumps(idx.recent(n=args.n), indent=2))

    elif args.command == "show":
        entry = idx.get(args.task_id)
        if entry is None:
            print(f"Not found: {args.task_id}", file=sys.stderr)
            return 1
        # Also show the Markdown if it exists.
        md = idx._pm_path(args.task_id)
        if md.exists():
            print(md.read_text())
        else:
            print(json.dumps(entry, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
