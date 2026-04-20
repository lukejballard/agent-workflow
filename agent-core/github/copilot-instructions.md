# Engineering Contract

Stack: {{BACKEND_STACK}}. Common code surfaces: {{SRC_DIR}}, {{FRONTEND_DIR}}, {{TESTS_DIR}}.

## Before doing anything
- Read `.github/AGENTS.md`.
- Read `.github/agent-platform/workflow-manifest.json` for task routing.
- If repo requirements already exist in issues, specs, ADRs, or planning docs, read them before writing code.

## Agent routing
- Default for all work → `@orchestrator`
- Use the orchestrator's internal critique and spec-validation phases; no packaged specialist agents are included.

## Essentials
- Never hardcode secrets; use environment variables.
- Follow coding standards in `.github/instructions/`.
- Non-trivial changes require explicit requirement locking before code.
