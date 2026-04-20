"""In-memory memory service with scope-aware storage and retrieval."""

from __future__ import annotations

from agent_runtime.schemas import MemoryEntry, MemoryScope


class InMemoryMemoryService:
    """Thread-safe (under the GIL) in-memory store for ``MemoryEntry`` objects.

    Entries are keyed by ``memory_id``.  Writing an entry with an existing
    ``memory_id`` replaces the previous entry (upsert semantics).

    Scope isolation is enforced in ``search()``: when *scope* is provided, only
    entries with a matching scope are returned.
    """

    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}

    def write(self, entry: MemoryEntry) -> None:
        """Persist *entry*, overwriting any existing entry with the same ``memory_id``."""
        self._store[entry.memory_id] = entry

    def read(self, memory_id: str) -> MemoryEntry | None:
        """Return the entry for *memory_id*, or ``None`` if not found."""
        return self._store.get(memory_id)

    def search(
        self,
        query: str,
        scope: MemoryScope | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """Return entries whose ``summary`` contains *query* (case-insensitive).

        Args:
            query: Substring to search for in ``summary``.
            scope: If supplied, restrict results to this scope only.
            limit: Maximum number of results to return.  Must be ≥ 1.

        Returns:
            A list of matching ``MemoryEntry`` objects, capped at *limit*.
        """
        if limit <= 0:
            return []
        query_lower = query.lower()
        results = [
            e
            for e in self._store.values()
            if (scope is None or e.scope == scope)
            and query_lower in e.summary.lower()
        ]
        return results[:limit]

    def delete(self, memory_id: str) -> bool:
        """Remove the entry with *memory_id*.

        Returns:
            True if the entry existed and was removed; False otherwise.
        """
        if memory_id in self._store:
            del self._store[memory_id]
            return True
        return False

    def count(self, scope: MemoryScope | None = None) -> int:
        """Return the total stored entries, optionally filtered by *scope*."""
        if scope is None:
            return len(self._store)
        return sum(1 for e in self._store.values() if e.scope == scope)
