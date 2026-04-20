# Agent-Mode Operating Model

This runbook explains how to work on the portable supermind package in this
repository.

## Package model

The package is intentionally small:

```
.github/AGENTS.md
.github/copilot-instructions.md
.github/agents/orchestrator.agent.md
.github/agent-platform/workflow-manifest.json
.github/hooks/
.github/instructions/
```

`@orchestrator` is the default entry point for all meaningful work.
The package should behave like one mind with explicit state and verification,
not a set of role-playing specialist agents.

## Default workflow

The orchestrator uses this internal sequence:

```
goal anchor -> classify -> breadth scan -> depth dive -> requirement lock -> critique -> revise -> execute -> verify
```

For non-trivial work:
- lock requirements before code changes
- keep working memory scoped to the current step
- compress completed work into short episodic summaries
- retry at most twice, and only with a changed strategy
- close with evidence-backed verification

## Default application stack policy

The package may express a default generated application stack without widening
the package boundary.

Use this precedence order whenever generated work needs a stack decision:
1. explicit user requirement
2. established host-repo stack evidence
3. package default in `.github/agent-platform/workflow-manifest.json`

Current package defaults:
- Backend: Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Vite + Vitest

Maintain these defaults inside the existing control plane only:
- declarative policy in `.github/agent-platform/workflow-manifest.json`
- always-loaded behavior in `.github/AGENTS.md`, `.github/copilot-instructions.md`, and `.github/agents/orchestrator.agent.md`
- stack-quality execution guidance in `.github/instructions/`

Do not restore deleted root runtime folders, packaged skill registries, or
specialist-agent bundles just to express stack preferences.

## Maintainer rules

1. Update `.github/` contracts before deleting or reshaping package surfaces.
2. Keep `docs/` aligned with the current package boundary in the same change set.
3. Use `docs/specs/active/` for non-trivial changes to the package source repo.
4. Remove stale package surfaces instead of leaving parallel systems in place.
5. Change default stack policy in the manifest, relevant instructions, and docs together.

## What should not return

Do not reintroduce these as packaged defaults unless the package boundary changes:
- specialist-agent bundles
- prompt-wrapper directories
- packaged skill registries and skill bundles
- runtime backend or frontend product layers
- metadata registries that are not part of the active control plane

## Source of truth

1. `AGENTS.md`
2. `.github/AGENTS.md`
3. `.github/agent-platform/workflow-manifest.json`
4. `docs/architecture.md`
5. `docs/specs/active/`
