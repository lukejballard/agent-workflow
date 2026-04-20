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

## Maintainer rules

1. Update `.github/` contracts before deleting or reshaping package surfaces.
2. Keep `docs/` aligned with the current package boundary in the same change set.
3. Use `docs/specs/active/` for non-trivial changes to the package source repo.
4. Remove stale package surfaces instead of leaving parallel systems in place.

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
