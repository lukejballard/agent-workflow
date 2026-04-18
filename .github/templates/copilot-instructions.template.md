# Engineering Contract (template)

Stack: {{BACKEND_STACK}} in {{SRC_DIR}}, frontend in {{FRONTEND_DIR}}, tests in {{TESTS_DIR}}.

## Before doing anything
- Read `AGENTS.md` at the repo root.
- If requirements already exist in `docs/specs/active/`, `specs/`, `.specify/`, or `openspec/changes/`, read them before writing code.

## Agent routing (quick reference)
- Default for almost all work → `@orchestrator`
- Read-only mapping → `@analyst`
- Spec-writing only → `@planner`

## Essentials
- Never hardcode secrets; use environment variables.
- Prefer template tokens: `{{SRC_DIR}}`, `{{FRONTEND_DIR}}`, `{{TESTS_DIR}}`.

(Use this file as the starting point for repo-specific `copilot-instructions.md`.)
