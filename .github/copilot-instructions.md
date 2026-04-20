# Engineering Contract

This repository is the canonical source for a portable prompt/meta supermind package.

## Before doing anything
- Read `.github/AGENTS.md`.
- Read `.github/agent-platform/workflow-manifest.json` for task routing.
- If repo requirements already exist in issues, specs, ADRs, or planning docs, read them before writing code.

## Agent routing
- Default for all work → `@orchestrator`
- Use the orchestrator's internal critique and requirement-lock phases; no packaged specialist agents are required.

## Default application generation
- When asked to scaffold or choose an application stack and the user has not specified one, follow the package default stack declared in `.github/agent-platform/workflow-manifest.json`.
- Respect stack precedence strictly: explicit user requirement first, established host-repo stack evidence second, package default third.
- The package default generated backend stack is Python + FastAPI + Pydantic + SQLAlchemy + Alembic.
- The package default generated frontend stack is React + TypeScript + Vite + Vitest.
- These defaults guide generation; they do not justify replacing an already-established repo stack.

## Essentials
- Never hardcode secrets; use environment variables.
- Follow coding standards in `.github/instructions/` when relevant.
- Non-trivial changes require explicit requirement locking before code.
