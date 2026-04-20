# Persistence Stage 1 — SQLAlchemy Core Backing Store

**Status:** Done
**Slug:** persistence-stage-1
**ADR:** [ADR-002](../../architecture/decisions/ADR-002-durability-roadmap.md)

## Goal

Replace the in-memory `RuntimeStore` with an injectable SQLAlchemy Core-backed
implementation so that task, plan, and event state survives process restarts.

## Requirements

- [x] `src/agent_runtime/storage/` package with `db.py`, `tables.py`, `store.py`.
- [x] SQLAlchemy Core table definitions for `tasks`, `plans`, `events`.
- [x] `SQLRuntimeStore` exposing `tasks`, `plans`, `events` as `MutableMapping`
      views backed by SQLite (dev) or PostgreSQL (production).
- [x] All writes idempotent (UPDATE → INSERT if 0 rows).
- [x] `configure_store()` function in `routes.py` for startup wiring.
- [x] `_lifespan` in `app.py` wires SQL store when `DATABASE_URL` env var is set.
- [x] Alembic initial migration creates all three tables.
- [x] `pyproject.toml` gains `sqlalchemy>=2.0,<3.0` and `alembic>=1.13,<2.0`.
- [x] `tests/unit/test_sql_store.py` covering all views and idempotency (≥15 tests).
- [x] Existing 327 backend tests continue to pass.

## Out of Scope

- Run artifact persistence (follow-up spec).
- Async SQLAlchemy.
- Stage 2 executor checkpoints.
