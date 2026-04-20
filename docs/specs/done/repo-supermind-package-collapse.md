# Feature: Repo Supermind Package Collapse

**Status:** Completed
**Created:** 2026-04-19
**Completed:** 2026-04-20
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** `docs/specs/done/agent-core-github-only-package.md`, `docs/specs/done/agent-core-single-mind-package.md`

---

## Problem
The repository had drifted into two overlapping products: a nested `agent-core/`
package and a larger runtime-oriented scaffold with backend, frontend, tests,
evals, scripts, prompts, skills, and extra metadata registries. That blurred the
boundary around the actual supermind package and created unnecessary folder sprawl.

## Outcome
The repository now presents one canonical prompt/meta supermind package.
The root `.github/` tree is the package source, `docs/` is the maintainer
explanation layer, and the nested/runtime-era surfaces were removed.

---

## Completed requirements

### Functional
- [x] Freeze the repository boundary as a prompt/meta supermind package rather than a runtime product.
- [x] Promote the root `.github/` tree to the canonical package source and remove the duplicate `agent-core/` layer.
- [x] Reduce `.github/` to the surfaces that materially implement the package: orchestrator, workflow metadata, hooks, and instructions.
- [x] Fold specialist-agent and skill behavior into the core package contracts instead of shipping separate prompt, skill, and fallback-agent folders.
- [x] Remove runtime-product directories and dependencies that no longer contribute to the package.
- [x] Reduce `docs/` to package architecture, runbooks, specs, and core maintainer guidance.
- [x] Keep a minimal validation story for the reduced package by retaining hook enforcement and a compact workflow manifest.

### Non-functional
- [x] Performance: no new dependencies or runtime steps were introduced.
- [x] Security: hook protections remain part of the package and now live fully under `.github/hooks/`.
- [x] Accessibility: not applicable; no retained UI surface.
- [x] Observability: the surviving docs and manifest still describe requirement locking, memory discipline, retries, and verification.

---

## Key changes
- Reframed root and package contracts around one shipped `.github/` package.
- Added `.github/AGENTS.md` as the primary package guide.
- Replaced the runtime-heavy orchestrator and workflow manifest with compact package-focused versions.
- Rewrote root docs to describe the package-only boundary.
- Removed specialist agents, prompt wrappers, packaged skills, extra metadata registries, runtime/backend/frontend/test/eval layers, and the nested `agent-core/` directory.
- Moved the hook helper scripts into `.github/hooks/` so the package remains self-contained after removing `scripts/`.

---

## Acceptance criteria
- [x] Root `.github/` is the canonical package source.
- [x] Nested `agent-core/` is removed.
- [x] Runtime-product directories are removed from the active repo.
- [x] Root docs and `.github` guidance consistently describe one prompt/meta supermind package.
- [x] The remaining human-maintained product directories are centered on `.github/` and `docs/`.

---

## Notes
Workspace-managed or developer-local surfaces such as `.git/`, `.vscode/`,
`memories/`, `.venv/`, and cache artifacts were not treated as package product
surfaces.
