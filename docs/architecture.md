# Architecture

## Repository Goal

This repository is the source repo for a portable prompt/meta supermind
package. The package is defined by a workflow-governance control plane under
`.github/` and explained by a small documentation layer under `docs/`.

## Active Architecture

The active architecture has two layers:

### 1. Package layer (`/.github/`)
Defines the shipped supermind package.

| Surface | Responsibility |
|---|---|
| `.github/AGENTS.md` | Primary package context |
| `.github/copilot-instructions.md` | Global package contract |
| `.github/agents/orchestrator.agent.md` | Single-entry orchestrator behavior |
| `.github/agent-platform/workflow-manifest.json` | Canonical workflow, requirement-lock, memory, retry, and verification policy |
| `.github/hooks/` | Deterministic approval and hook enforcement |
| `.github/instructions/` | Optional path-specific coding standards for consuming repos |

### 2. Documentation layer (`/docs/`)
Explains and governs the package source repo.

| Surface | Responsibility |
|---|---|
| `docs/architecture.md` | Package architecture summary |
| `docs/product-direction.md` | Current repository framing |
| `docs/runbooks/` | Maintainer operating guides |
| `docs/specs/active/` | In-flight package changes |
| `docs/specs/research/` | Supporting research when external context matters |
| `docs/specs/done/` | Historical completed specs |

## Supermind Model

The supermind is intentionally compact:
- one orchestrator rather than specialist-agent bundles
- explicit requirement locking before non-trivial changes
- scoped memory plus episodic compression
- bounded retries with changed strategy requirements
- evidence-backed verification rather than confidence-only summaries

## Transitional Surfaces

Runtime, frontend, test, eval, and helper-script layers may still exist while
the collapse is in progress, but they are not part of the intended steady-state
architecture unless explicitly retained.

## Source of Truth

- `AGENTS.md` — source-repo operating rules
- `.github/AGENTS.md` — shipped package guide
- `.github/agent-platform/workflow-manifest.json` — canonical package policy
- `docs/specs/active/` — in-flight package requirements
- `docs/runbooks/agent-mode.md` — maintainer operating runbook

