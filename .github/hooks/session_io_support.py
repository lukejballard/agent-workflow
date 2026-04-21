from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def default_session_path() -> str:
    return os.environ.get(
        "AGENT_SESSION_FILE",
        str(Path.home() / ".agent-session" / "session.json"),
    )


def read_session_data(path: str | None = None) -> dict[str, Any] | None:
    filepath = Path(path or default_session_path())
    try:
        return json.loads(filepath.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def session_snapshot_path(path: str | None = None) -> Path:
    return Path(path or default_session_path()).with_suffix(".before.json")


def read_session_snapshot(path: str | None = None) -> dict[str, Any] | None:
    snapshot = session_snapshot_path(path)
    try:
        return json.loads(snapshot.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_session_snapshot(path: str | None = None) -> None:
    snapshot = session_snapshot_path(path)
    data = read_session_data(path)
    try:
        if data is None:
            snapshot.unlink(missing_ok=True)
            return
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def write_session_data(data: dict[str, Any], path: str | None = None) -> bool:
    filepath = Path(path or default_session_path())
    tmp = filepath.with_suffix(".tmp")
    lock_file = filepath.with_suffix(".lock")
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_file, "w", encoding="utf-8") as lf:
            lf.write("0")
            lf.flush()
            lf.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(lf.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
                tmp.replace(filepath)
            finally:
                lf.seek(0)
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(lf.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
        return True
    except OSError:
        return False