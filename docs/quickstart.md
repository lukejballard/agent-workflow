# Quickstart

## What You Can Do In This Snapshot

This repository contains a working agent runtime scaffold with a typed Python backend,
React/TypeScript frontend, and full test coverage.

A practical contributor quickstart is:
1. Read `AGENTS.md` — the repo operating model.
2. Read `docs/product-direction.md` — current repo framing and verified surfaces.
3. Read `docs/architecture.md` — architecture overview.
4. Review `.github/copilot-instructions.md` before making changes.

## Starting The Backend

```bash
cd src
uvicorn agent_runtime.app:create_app --factory --reload
```

The API is available at `http://localhost:8000`. See `docs/architecture.md` for
the full route table.

## Running Backend Tests

```bash
pytest tests/unit/ --cov=src --cov-report=term-missing
```

Target: 396 passed, 100% coverage across 19 modules.

## Starting The Frontend

```bash
cd frontend
npm install
npm run dev
```

The SPA is available at `http://localhost:5173`.

## Running Frontend Tests And Lint

```bash
cd frontend
npm run lint
npm test
```

## Working Safely

When updating docs, specs, or plans:
- prefer verified statements over reconstructed product claims
- keep historical material clearly marked as archival
- do not introduce new runtime contracts without code to support them
- run `python scripts/agent/sync_agent_platform.py --check` after editing `.github/agent-platform/` files
