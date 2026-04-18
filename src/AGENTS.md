# AGENTS.md — src/pipeline_observe

This file provides agent guidance scoped to the **Python backend** (`src/pipeline_observe/`).

---

## Package responsibilities

```
src/pipeline_observe/
  sdk/              ← @observe_step decorator + HTTP client (user-facing)
  collector/        ← FastAPI app, routes, startup
  storage/          ← SQLAlchemy models, session factory
  analysis/         ← Anomaly detection, schema drift, lineage, DAG, comparators
  alerts/           ← Webhook-based alert manager
  observability/    ← OTel trace setup, Prometheus metrics
  plugins/          ← Plugin protocol (PipelinePlugin), built-in plugins, registry
  workers/          ← Background task utilities
  config/           ← Configuration loading (env vars)
  models/           ← Shared Pydantic request/response models
  dashboard/        ← Dashboard service entry point (if present)
  execution/        ← Pipeline execution helpers (if present)
```

---

## Before making changes

1. Read the existing module's `__init__.py` and primary source file to understand its scope.
2. Check `tests/unit/test_<module>.py` for examples of how the module is tested.
3. If touching `storage/models.py`, understand that tables are created via `create_all()` at startup — any column additions are automatically applied for SQLite but require a migration for PostgreSQL.
4. If touching `collector/server.py`, review the existing route patterns before adding a new endpoint.

---

## SDK rules (highest caution)

The SDK (`sdk/api.py`, `sdk/client.py`) is imported by user pipeline code. Changes here can break pipelines in production.

- Keep runtime dependencies to the absolute minimum.
- Never raise from the decorator wrapper — all errors must be caught and logged.
- If a new event field is added, it must be optional with a safe default so existing collector versions are not broken.

---

## Analysis module rules

Analysis modules (`analysis/`) are **pure functions** — they accept data and return data. They must:
- Have no database I/O of their own; receive data via function arguments.
- Be testable without a database or HTTP server.
- Have complete type annotations.

---

## Adding a new collector endpoint

1. Add the route function to `collector/server.py` (or a sub-router if the file grows large).
2. Define request/response Pydantic models in `models/` or inline if small.
3. Add the endpoint to the endpoint table in `docs/architecture.md`.
4. Write a unit test using `httpx.AsyncClient` with `ASGITransport`.

---

## Environment variable configuration

- All config is read from environment variables via `config/`.
- New variables must be added to `.env.example` with a description and safe default.
- Validate and parse env vars at import time so startup fails fast if required vars are missing.
