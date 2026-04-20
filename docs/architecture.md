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
| `.github/agent-platform/workflow-manifest.json` | Canonical workflow, requirement-lock, memory, retry, verification, and default generated stack policy |
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

## Default generation stack

The package remains a prompt/meta control plane, but it still carries a default
application stack for generated work when the user and host repo have not
already established one.

Precedence is:
1. explicit user requirement
2. established host-repo stack evidence
3. package default declared in `.github/agent-platform/workflow-manifest.json`

The current package default is:
- Backend: Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Vite + Vitest

That policy lives entirely inside the existing `.github/` control plane and
does not widen the package boundary or restore runtime-oriented root folders.

## Transitional Surfaces

Runtime, frontend, test, eval, and helper-script layers may still exist in the
source repo for maintainer or workspace reasons, but they are not part of the
intended shipped package boundary unless explicitly retained.

## Source of Truth

- `AGENTS.md` — source-repo operating rules
- `.github/AGENTS.md` — shipped package guide
- `.github/agent-platform/workflow-manifest.json` — canonical package policy
- `docs/specs/active/` — in-flight package requirements
- `docs/runbooks/agent-mode.md` — maintainer operating runbook

