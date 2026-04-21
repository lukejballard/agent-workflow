"""Failure postmortem index for the agent hook system."""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any


def _failures_dir() -> Path:
    override = os.environ.get("AGENT_FAILURES_DIR")
    return Path(override) if override else Path(__file__).parent / "failures"


def _slug(text: str, max_len: int = 30) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower())[:max_len].strip("-")


def _read_record(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


class FailureIndex:
    def __init__(self, failures_dir: Path | None = None) -> None:
        self._dir = failures_dir or _failures_dir()

    def _ensure_dir(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        *,
        task_class: str,
        phase_at_failure: str,
        symptom: str,
        root_cause: str,
        fix_applied: str = "",
        prevention_pattern: str = "",
        task_summary: str = "",
    ) -> Path:
        """Write a failure postmortem. Returns the intended path."""
        self._ensure_dir()
        ts = time.time()
        entry: dict[str, Any] = {
            "ts": ts,
            "timestamp": ts,
            "task_class": task_class,
            "phase_at_failure": phase_at_failure,
            "symptom": symptom,
            "root_cause": root_cause,
            "fix_applied": fix_applied,
            "prevention_pattern": prevention_pattern,
            "task_summary": task_summary,
        }
        path = self._dir / f"{int(ts)}-{_slug(symptom)}.json"
        try:
            path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        except OSError:
            pass
        return path

    def recent(self, n: int = 5) -> list[dict[str, Any]]:
        """Return the n most recent failure records."""
        self._ensure_dir()
        records: list[dict[str, Any]] = []
        for path in self._dir.glob("*.json"):
            record = _read_record(path)
            if record is not None:
                records.append(record)
        return sorted(records, key=lambda item: item.get("ts", 0), reverse=True)[:n]

    def _keyword_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        keywords = {word.lower() for word in query.split() if len(word) > 3}
        if not keywords:
            return []
        matches: list[dict[str, Any]] = []
        for record in self.recent(1000):
            haystack = " ".join(
                [
                    record.get("symptom", ""),
                    record.get("prevention_pattern", ""),
                    record.get("root_cause", ""),
                ]
            ).lower()
            if any(keyword in haystack for keyword in keywords):
                matches.append(record)
        return matches[:top_k]

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return records relevant to query using TF-IDF scoring."""
        try:
            from tfidf import get_cached_index

            records = self.recent(500)
            if not records:
                return []
            index = get_cached_index(
                f"failure-index:{self._dir}",
                records,
                ["symptom", "root_cause", "prevention_pattern", "task_summary"],
            )
            return index.search(query, top_k=top_k)
        except ImportError:
            return self._keyword_search(query, top_k=top_k)

    def format_for_context(self, records: list[dict[str, Any]]) -> str:
        """Format failure records for prompt injection."""
        if not records:
            return ""
        lines = ["## Past failures relevant to this task", ""]
        for record in records:
            lines.append(f"**Symptom:** {record.get('symptom', '')}")
            lines.append(f"**Root cause:** {record.get('root_cause', '')}")
            if record.get("prevention_pattern"):
                lines.append(f"**Prevention:** {record['prevention_pattern']}")
            lines.append("")
        return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="failure_index.py")
    parser.add_argument("--write", action="store_true", help="Write a sample record")
    parser.add_argument("--search", help="Search stored failures")
    parser.add_argument("--recent", type=int, help="Print recent failures as JSON")
    args = parser.parse_args(argv)
    index = FailureIndex()
    if args.write:
        path = index.write(
            task_class="brownfield-improvement",
            phase_at_failure="execute-or-answer",
            symptom="import error",
            root_cause="missing dependency",
            prevention_pattern="Check imports and dependencies before execution.",
            task_summary="CLI smoke-test sample",
        )
        print(path)
        return 0
    if args.search:
        print(json.dumps(index.search(args.search), indent=2))
        return 0
    if args.recent is not None:
        print(json.dumps(index.recent(args.recent), indent=2))
        return 0
    parser.print_usage()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
