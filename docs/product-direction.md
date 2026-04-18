# Product Direction

This repository is intentionally product-neutral. Its current purpose is to
provide a reusable operating model for agent-assisted software delivery rather
than to represent one fixed application domain.

## What Is Verified Today

The strongest verified surfaces in this snapshot are the governance and planning
layers:

| Area | What is here now |
|---|---|
| `docs/` | contributor guidance, architecture notes, active specs, and archival planning artifacts |
| `.github/` | agent instructions, workflow metadata, prompts, and quality skills |
| `scripts/` | helper scripts for repo maintenance and metadata validation |
| `skills/` | supplemental release and audit checklists |
| `src/`, `frontend/`, `tests/` | scoped guidance anchors for future project-specific code |

## What Is Not Yet Verified

The following are intentionally undefined or unverified in this snapshot:
- a concrete product domain
- runnable backend or frontend code
- supported public API or CLI contracts
- deployable infrastructure or release process for an application runtime

## Current Source Of Truth

Use these files in order when deciding what is current:

1. `AGENTS.md` for the repo operating model.
2. `docs/product-direction.md` for current repo framing.
3. `docs/architecture.md` for the verified architecture summary.
4. `docs/specs/active/product-realignment-phase-1.md` for the active cleanup scope.
5. `docs/runbooks/agent-mode.md` and `.github/copilot-instructions.md` for contributor and agent workflow rules.

## How To Treat Inherited Product Material

Some files in the repository were inherited from earlier product directions.
Until they are rewritten as generic guidance or backed by actual checked-in
runtime code, treat them as archival context only.

They may still help with:
- workflow structure
- review checklists
- examples of spec organization
- examples of repo hygiene and governance patterns

They should not be treated as:
- validated product requirements
- accurate API or data contracts
- evidence that a runtime implementation exists in this checkout

## Near-Term Direction

The next alignment phase should focus on:

1. Keeping public docs, specs, scripts, and metadata free of stale product-specific naming.
2. Preserving the repo as a reusable scaffold until maintainers choose a concrete application domain.
3. Restoring runtime surfaces only when there is a validated project-specific requirement to support them.
4. Keeping CI, tasks, and helper scripts honest about the files that actually exist.
