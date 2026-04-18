#!/usr/bin/env python3
"""
Small helper to add missing columns to a local SQLite `pipeline_definitions` table
when the Alembic migration hasn't been run. This is intended for quick local
development use only. Prefer running `alembic upgrade head` in normal workflows.

Usage:
  python scripts/add_pipeline_columns.py

It will back up the DB file to <db>.bak before applying ALTERs.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path


def detect_sqlite_path() -> Path:
    # Prefer DATABASE_URL env var when present and pointing to SQLite
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if db_url.startswith("sqlite:///"):
            return Path(db_url.replace("sqlite:///", ""))
        if db_url.startswith("sqlite://"):
            return Path(db_url.replace("sqlite://", ""))
        raise SystemExit("DATABASE_URL is set but not a sqlite URL; aborting.")

    # Fallback to PIPELINE_OBSERVE_DB_PATH (used by the app) or default file
    alt = os.environ.get("PIPELINE_OBSERVE_DB_PATH")
    if alt:
        return Path(alt)

    return Path("./pipeline_observe.db").resolve()


def main() -> int:
    db_path = detect_sqlite_path()
    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        return 2

    backup = db_path.with_suffix(db_path.suffix + ".bak")
    print(f"Backing up {db_path} -> {backup}")
    shutil.copy2(db_path, backup)

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    cur.execute("PRAGMA table_info('pipeline_definitions')")
    cols = [r[1] for r in cur.fetchall()]
    print("Existing columns:", cols)

    applied = []

    if "schema_version" not in cols:
        print("Adding column: schema_version (TEXT)")
        cur.execute("ALTER TABLE pipeline_definitions ADD COLUMN schema_version TEXT;")
        applied.append("schema_version")

    if "setup" not in cols:
        print("Adding column: setup (TEXT)")
        # JSON is represented as text in SQLite; SQLAlchemy maps JSON to TEXT here.
        cur.execute("ALTER TABLE pipeline_definitions ADD COLUMN setup TEXT;")
        applied.append("setup")

    if "source_template_id" not in cols:
        print("Adding column: source_template_id (INTEGER)")
        cur.execute(
            "ALTER TABLE pipeline_definitions ADD COLUMN source_template_id INTEGER;"
        )
        applied.append("source_template_id")

    if applied:
        con.commit()
        print("Applied columns:", applied)
    else:
        print("No columns required; DB schema already contains the expected columns.")

    cur.close()
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
