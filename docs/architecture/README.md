# Architecture Notes

This directory holds durable architecture references for the repository and
for the agent runtime implemented under `src/agent_runtime/`.

## Current Status

The repository has a verified Python backend runtime (`src/agent_runtime/`) —
19 modules, 396 unit tests, 100% coverage — and a React/TypeScript operator
frontend under `frontend/`.

## Use These Documents First

- `docs/architecture.md` for the current architectural summary.
- `docs/product-direction.md` for repo framing.
- `docs/architecture/decisions/` for accepted ADRs.

## Architecture Decision Records

ADRs capture durable architectural choices. New ADRs should follow the format
in `docs/architecture/decisions/` and be referenced from `docs/architecture.md`.
