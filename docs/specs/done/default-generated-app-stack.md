# Feature: Default Generated Application Stack

**Status:** Completed
**Created:** 2026-04-19
**Completed:** 2026-04-20
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** `docs/specs/done/hyperintelligence-tier-1.md`, `docs/specs/done/hyperintelligence-tier-2b-routes-frontend.md`, `docs/specs/done/hyperintelligence-tier-3a-app-sse-vitest.md`

---

## Problem
The package no longer carried the previously recommended implementation stack
for generated application work. That made framework selection driftier than
intended and discarded useful prior decisions about backend and frontend
defaults.

The goal was to restore those defaults without reintroducing deleted runtime
folders, packaged skill registries, prompt-wrapper directories, or
specialist-agent surfaces.

## Outcome
The package now declares and applies a default generated application stack from
the existing control plane.

When the user and host repo have not already established a different path, the
workflow defaults to:
- Backend: Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Vite + Vitest

The policy lives entirely inside the existing `.github/` and `docs/` surfaces,
so the repo remains package-first and root-flat.

---

## Completed requirements

### Functional
- [x] Declare the package default generated backend stack as Python + FastAPI + Pydantic + SQLAlchemy + Alembic.
- [x] Declare the package default generated frontend stack as React + TypeScript + Vite + Vitest.
- [x] Make stack precedence explicit: user requirement first, host-repo evidence second, package default third.
- [x] Update the orchestrator and package guides so greenfield or repo-agnostic generation follows the default stack.
- [x] Strengthen the existing instruction files so generated work is high quality in the default stack.
- [x] Absorb useful deleted skill and specialist-agent behavior into existing package surfaces rather than restoring deleted folders.
- [x] Keep the default stack policy inside existing `.github/` and `docs/` surfaces only.

### Non-functional
- [x] Performance: do not add new runtime dependencies or new root folders to the package source repo.
- [x] Security: preserve the package-only boundary and keep security guidance explicit for the default backend and frontend stack.
- [x] Accessibility: keep frontend defaults accessible by default through the retained instruction set.
- [x] Observability: document where stack defaults live and how maintainers should update or override them.

---

## Key changes
- Added `implementationDefaults` to `.github/agent-platform/workflow-manifest.json` with explicit precedence and stack-family defaults.
- Updated `.github/AGENTS.md`, `.github/copilot-instructions.md`, and `.github/agents/orchestrator.agent.md` so the single orchestrator applies the default stack only when user requirements and host-repo evidence do not already decide it.
- Strengthened `.github/instructions/` so the package is concretely good at FastAPI, Pydantic, SQLAlchemy, Alembic, React, TypeScript, Vite, Vitest, React Testing Library, and related cross-cutting expectations.
- Documented the default-stack policy in `docs/architecture.md`, `docs/runbooks/agent-mode.md`, and root `AGENTS.md`.
- Preserved the reduced package boundary: no deleted root runtime folders, packaged skills, prompts, or specialist agents were restored.
- Normalized task-class wording around `implement-from-existing-spec` so the orchestrator text matches the workflow manifest.

---

## Acceptance criteria
- [x] The workflow manifest declares the default generated application stack and precedence rules.
- [x] The package guides and orchestrator consistently describe when to use the default stack.
- [x] The retained instruction files explicitly support the default backend and frontend stack.
- [x] No deleted skill folders, prompt folders, specialist agents, or runtime root folders are restored.
- [x] `docs/architecture.md` and `docs/runbooks/agent-mode.md` document the new default-stack policy.
- [x] Diagnostics pass on all edited package files.
- [x] Live package surfaces contain no stale references implying the deleted folder-based stack system returned.

---

## Notes
- A dry review of the live package surfaces found no remaining stack-steering gaps beyond the task-class wording mismatch fixed in this change.
- The old package metadata validation task is no longer runnable because the earlier package collapse intentionally removed the `scripts/agent/` surface it referenced.