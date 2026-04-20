"""In-memory run artifact store."""

from __future__ import annotations

from agent_runtime.schemas import RunArtifact


class InMemoryArtifactStore:
    """In-memory store for ``RunArtifact`` records, keyed by ``run_id``.

    Saving an artifact with an existing ``run_id`` overwrites the previous
    record (upsert semantics).
    """

    def __init__(self) -> None:
        self._store: dict[str, RunArtifact] = {}

    def save(self, artifact: RunArtifact) -> None:
        """Persist *artifact*, replacing any existing entry with the same ``run_id``."""
        self._store[artifact.run_id] = artifact

    def load(self, run_id: str) -> RunArtifact | None:
        """Return the artifact for *run_id*, or ``None`` if not found."""
        return self._store.get(run_id)

    def list_all(self) -> list[RunArtifact]:
        """Return all stored artifacts in insertion order."""
        return list(self._store.values())

    def delete(self, run_id: str) -> bool:
        """Remove the artifact with *run_id*.

        Returns:
            True if the artifact existed and was removed; False otherwise.
        """
        if run_id in self._store:
            del self._store[run_id]
            return True
        return False

    def count(self) -> int:
        """Return the number of stored artifacts."""
        return len(self._store)
