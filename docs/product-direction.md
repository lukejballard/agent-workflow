# Product Direction

This repository is intentionally product-neutral. Its purpose is to provide a
reusable operating model for agent-assisted software delivery.

## What Is Verified Today

| Area | What is here now |
|---|---|
| `docs/` | contributor guidance, architecture notes, active specs, and planning artifacts |
| `.github/` | agent instructions, workflow metadata, prompts, and quality skills |
| `scripts/` | helper scripts for repo maintenance and metadata validation |
| `skills/` | supplemental release and audit checklists |
| `src/agent_runtime/` | typed Python runtime — 19 modules, 396 unit tests, 100% coverage |
| `frontend/` | React 19 / TypeScript / Vite SPA — typed API client, hooks, and operator UI |
| `tests/unit/` | 396 passing unit tests covering all backend modules |

## Current Source Of Truth

Use these files in order when deciding what is current:

1. `AGENTS.md` for the repo operating model.
2. `docs/product-direction.md` for current repo framing.
3. `docs/architecture.md` for the verified architecture summary.
4. `docs/runbooks/agent-mode.md` and `.github/copilot-instructions.md` for contributor and agent workflow rules.

## How To Treat Inherited Planning Material

Some files in the repository were written during earlier planning phases for
specific product directions. Those artifacts remain under `docs/specs/done/`
and the archival planning directories as historical context.

They may still help with:
- workflow structure patterns
- review checklist examples
- spec organization templates
- repo hygiene and governance patterns

They should not be treated as active requirements unless they appear in
`docs/specs/active/`.

## Near-Term Direction

1. Keep public docs, specs, scripts, and metadata aligned with the verified runtime.
2. Maintain 100% test coverage across all `src/agent_runtime/` modules.
3. Add the eval harness (`evals/`) to enable measurable benchmarking of agent
   orchestration quality.
