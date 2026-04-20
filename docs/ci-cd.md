# CI/CD Status

## Current State

This repository has a verified Python backend and React/TypeScript frontend with
full test coverage. CI enforces the following:

## What CI Enforces

- **Agent-platform metadata synchronization** — `python scripts/agent/sync_agent_platform.py --check`
- **Backend lint and type checks** — `ruff check src/`, `python -m mypy src/`
- **Backend unit tests** — `pytest tests/unit/ --cov=src --cov-report=term-missing`
- **Frontend lint** — `cd frontend && npm run lint`
- **Frontend tests** — `cd frontend && npm test`

## Recommended Next CI/CD Steps

1. End-to-end workflow validation for the agent runtime lifecycle
2. Frontend type check gate (`npm run build` which runs `tsc --noEmit`)
3. Container image build and health-check validation
4. Environment-specific deployment promotion gates
