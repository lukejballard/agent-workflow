# agent-workflow

Canonical source repository for a portable prompt/meta supermind package.

## What this repo is

This repository authors and documents a compact AI workflow package built around:
- one orchestrator
- one workflow policy kernel
- one hook stack
- a small documentation layer

The shipped consumer surface is `.github/` only.

## Source-repo layout

Active top-level surfaces during the package collapse:
- `.github/` — canonical package source
- `docs/` — package architecture, runbooks, specs, and archive

Other top-level folders that may still exist are transitional and subject to removal.

## Package surface

```
.github/
  AGENTS.md                    Primary package context
  copilot-instructions.md      Global engineering contract
  agents/
    orchestrator.agent.md      Single hyperintelligent orchestrator
  agent-platform/
    workflow-manifest.json     Workflow, memory, retry, and verification policy
  hooks/
    pretool-approval-policy.json
    hooks.py
  instructions/                Optional path-specific coding standards
```

## Maintainer workflow

1. Read `AGENTS.md`.
2. Read `.github/AGENTS.md`.
3. Read `.github/agent-platform/workflow-manifest.json`.
4. For non-trivial changes, keep a working spec in `docs/specs/active/`.

## Direction

The repository is being simplified toward as few subfolders as possible without
losing the supermind itself. The supermind lives in the package contracts and
guardrails, not in a runtime backend, frontend UI, or multi-agent bundle.