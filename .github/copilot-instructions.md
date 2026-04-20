# Engineering Contract

This repository is the canonical source for a portable prompt/meta supermind package.

## Before doing anything
- Read `.github/AGENTS.md`.
- Read `.github/agent-platform/workflow-manifest.json` for task routing.
- If repo requirements already exist in issues, specs, ADRs, or planning docs, read them before writing code.

## Agent routing
- Default for all work → `@orchestrator`
- Use the orchestrator's internal critique and requirement-lock phases; no packaged specialist agents are required.

## Essentials
- Never hardcode secrets; use environment variables.
- Follow coding standards in `.github/instructions/` when relevant.
- Non-trivial changes require explicit requirement locking before code.
