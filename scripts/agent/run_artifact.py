#!/usr/bin/env python3
"""Atomic run-artifact writer with file locking and UUID namespacing.

Run artifacts are written to `docs/runs/{uuid}/artifact.json` to prevent
concurrent-write collisions between agent sessions (ISSUE-18).

Usage as a library
------------------
  from scripts.agent.run_artifact import write_run_artifact, read_run_artifact

  # Write a new artifact (generates a fresh UUID)
  path = write_run_artifact({"goal": "...", "status": "in-progress"})

  # Append to an existing artifact by UUID
  path = write_run_artifact({"status": "done"}, artifact_id="<uuid>")

  # Read back
  data = read_run_artifact("<uuid>")

Usage as a CLI
--------------
  echo '{"goal": "test", "status": "done"}' | python scripts/agent/run_artifact.py write
  python scripts/agent/run_artifact.py read <uuid>
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# File-locking helpers — portable across Windows and Unix.
# ---------------------------------------------------------------------------

try:
    import msvcrt  # Windows

    def _lock(fp) -> None:  # type: ignore[no-untyped-def]
        # Lock the first byte of the file (advisory lock on Windows)
        msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock(fp) -> None:  # type: ignore[no-untyped-def]
        try:
            fp.seek(0)
            msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass

except ImportError:
    try:
        import fcntl  # Unix

        def _lock(fp) -> None:  # type: ignore[no-untyped-def]
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX)

        def _unlock(fp) -> None:  # type: ignore[no-untyped-def]
            fcntl.flock(fp.fileno(), fcntl.LOCK_UN)

    except ImportError:
        # No locking available (rare), degrade gracefully

        def _lock(fp) -> None:  # type: ignore[no-untyped-def]
            pass

        def _unlock(fp) -> None:  # type: ignore[no-untyped-def]
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_RUNS_DIR = _REPO_ROOT / "docs" / "runs"


def _artifact_dir(artifact_id: str) -> Path:
    return _RUNS_DIR / artifact_id


def _artifact_path(artifact_id: str) -> Path:
    return _artifact_dir(artifact_id) / "artifact.json"


def write_run_artifact(
    data: dict[str, Any],
    artifact_id: str | None = None,
    *,
    merge: bool = True,
) -> Path:
    """Write *data* to a UUID-namespaced artifact file and return its path.

    Parameters
    ----------
    data:
        The artifact payload to write (must be JSON-serialisable).
    artifact_id:
        UUID string identifying the artifact. A fresh UUID is generated when
        ``None`` is passed.  Pass the existing UUID to update an artifact.
    merge:
        When *True* (default) and the artifact file already exists, deep-merge
        *data* into the existing contents. When *False*, overwrite entirely.

    Returns
    -------
    Path
        Absolute path to the written artifact file.
    """
    if artifact_id is None:
        artifact_id = str(uuid.uuid4())

    art_path = _artifact_path(artifact_id)
    art_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to a sibling temp file, then rename.
    tmp_path = art_path.with_suffix(".tmp")

    try:
        with tmp_path.open("w", encoding="utf-8") as fp:
            _lock(fp)
            try:
                if merge and art_path.exists():
                    try:
                        existing = json.loads(art_path.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, OSError):
                        existing = {}
                    existing.update(data)
                    payload = existing
                else:
                    payload = data
                json.dump(payload, fp, indent=2, ensure_ascii=False)
                fp.write("\n")
            finally:
                _unlock(fp)

        tmp_path.replace(art_path)
    except OSError as exc:
        raise RuntimeError(f"Failed to write run artifact {art_path}: {exc}") from exc

    return art_path


def read_run_artifact(artifact_id: str) -> dict[str, Any]:
    """Read and return the artifact for *artifact_id*.

    Raises
    ------
    FileNotFoundError
        If no artifact exists for the given ID.
    json.JSONDecodeError
        If the artifact file is corrupted.
    """
    art_path = _artifact_path(artifact_id)
    return json.loads(art_path.read_text(encoding="utf-8"))


def list_run_artifacts() -> list[str]:
    """Return a sorted list of all artifact UUIDs under ``docs/runs/``."""
    if not _RUNS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in _RUNS_DIR.iterdir()
        if d.is_dir() and (_artifact_path(d.name)).exists()
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli_write(args: list[str]) -> int:
    raw = sys.stdin.read().strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: stdin is not valid JSON: {exc}", file=sys.stderr)
        return 1
    artifact_id = args[0] if args else None
    path = write_run_artifact(data, artifact_id=artifact_id)
    print(path)
    return 0


def _cli_read(args: list[str]) -> int:
    if not args:
        print("ERROR: read requires an artifact UUID argument", file=sys.stderr)
        return 1
    try:
        data = read_run_artifact(args[0])
    except FileNotFoundError:
        print(f"ERROR: no artifact found for id '{args[0]}'", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2))
    return 0


def _cli_list() -> int:
    ids = list_run_artifacts()
    if not ids:
        print("(no run artifacts found)")
        return 0
    for art_id in ids:
        print(art_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__)
        return 0
    command, *rest = args
    if command == "write":
        return _cli_write(rest)
    if command == "read":
        return _cli_read(rest)
    if command == "list":
        return _cli_list()
    print(f"ERROR: unknown command '{command}'. Use write, read, or list.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
