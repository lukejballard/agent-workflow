# Product Direction

This repository is no longer being framed as a runtime product scaffold.
Its direction is a compact prompt/meta supermind package.

## What Is Active

| Area | What it means now |
|---|---|
| `.github/` | Canonical package source: orchestrator, workflow policy, hooks, and optional extension points |
| `docs/` | Human-facing package architecture, runbooks, active specs, and archive |

Other top-level folders that still exist during the collapse are transitional
and should not be treated as the intended steady state.

## Current Source Of Truth

Use these files in order when deciding what is current:

1. `AGENTS.md` for source-repo operating rules.
2. `.github/AGENTS.md` for the shipped package guide.
3. `.github/agent-platform/workflow-manifest.json` for the canonical workflow policy.
4. `docs/architecture.md` for the package architecture summary.
5. `.github/copilot-instructions.md` and `docs/runbooks/agent-mode.md` for maintainer workflow rules.

## How To Treat Historical Material

The repository still contains documents and directories from earlier runtime,
frontend, and evaluation phases. Those materials are historical context only
unless they are explicitly retained in active package docs or in
`docs/specs/active/`.

## Near-Term Direction

1. Make the root `.github/` tree the only canonical package source.
2. Remove duplicate packaging surfaces and runtime-product layers that do not
   contribute to the supermind package.
3. Keep the documentation small, explicit, and aligned with the shipped package.
