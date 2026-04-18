# Engineering Contract

Stack: Python/FastAPI backend in `src/biomechanics_ai/`, React + TypeScript dashboard in
`frontend/`, shared tests in `tests/`, docs in `docs/`, and deploy assets in `deploy/`.

## Before doing anything
Read `AGENTS.md` at the repo root. It describes the full agent system.
If requirements already exist in `docs/specs/active/`, `specs/`, `.specify/`,
`plan/`, or `openspec/changes/`, read them before writing code. Prefer Speckit
for greenfield work and OpenSpec changes for brownfield work, then refresh a
working spec in `docs/specs/active/` before code.

## Agent routing (quick reference)
- Default for almost all work → `@orchestrator`
- Read-only codebase mapping → `@analyst`
- Explicit external docs, ecosystem, or launch-readiness research → `@researcher`
- Spec-writing only → `@planner`
- Build from approved spec → `@implementer`
- Test-only pass → `@qa`
- Independent review → `@reviewer`
- No-behaviour-change refactor → `@cleanup`

## Response quality
- For non-trivial tasks: classify the work, state assumptions, keep current-step context bounded, and search before concluding
- Start with a breadth-first scan, then go deep on the highest-risk surfaces
- Compare at least one viable alternative before committing to a non-trivial approach
- Run self-critique before finalizing; do not stop at the first plausible answer
- Distinguish verified facts from assumptions and summarize verification status
- Auto-consider the relevant quality passes by task type: regression for brownfield work, visual and accessibility QA for UI work, observability for service surfaces, and documentation audit for workflow or docs changes

## Non-negotiable rules
- Never write placeholder, stub, or TODO implementations in production code
- Never invent requirements not in the spec
- Never hardcode secrets, credentials, or environment values
- Never use `any` in TypeScript without a comment explaining why
- Never concatenate user input into SQL or any query language

## Definition of done
A task is complete only when:
- [ ] Code compiles and runs without errors
- [ ] Unit tests exist and pass (80% line + branch coverage minimum)
- [ ] Integration tests exist and pass
- [ ] All error paths are handled and logged
- [ ] No secrets or PII in code or logs
- [ ] Acceptance criteria in the spec are all checked off
- [ ] External research and documentation updates are captured when they materially affect the outcome

## Architecture rules
- Python backend: keep `collector/` routes thin, keep `analysis/` pure, and keep DB access in
	`storage/` or dedicated service helpers.
- SDK code in `src/biomechanics_ai/sdk/` must never break user pipelines on telemetry failure.
- Frontend: no business logic in pages or components. No direct fetch() in components or pages.
- Frontend API clients live in `frontend/src/api/`; shared API shapes live in `frontend/src/types/`.
- Validate external input at the boundary and match the established patterns in the local module.

## Testing standards
- Python: pytest, 80% coverage minimum, no `unittest.TestCase`.
- TypeScript/React: Vitest, 80% coverage minimum.
- E2E: Playwright, at minimum the happy path for every user-facing feature.
- No sleep() in tests. No hardcoded timestamps. No shared mutable state.
- Brownfield work should explicitly consider regression coverage, not just happy-path tests.

## External-context limits
- This repo ships fetch and GitHub research, structured reasoning via `sequential-thinking`, and optional Tavily search from `.vscode/mcp.json` when `TAVILY_API_KEY` is configured.
- Tool approvals remain editor-controlled, and broader search still depends on MCP credentials or setup outside `.github/`.

## When requirements are unclear
State your assumptions explicitly at the top of your response, then proceed.
