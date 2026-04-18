# Architecture

## Repository Goal

This repository is a generic scaffold for agent-driven software delivery. Its
stable value today is the workflow control plane: instructions, prompts,
skills, specs, and maintenance scripts that help contributors build or restore
an application safely.

## Verified Repo State

The following areas are present and verified in this snapshot:
- `.github/` agent workflows, instructions, prompts, and metadata
- `docs/` contributor, architecture, and planning documentation
- `openspec/`, `specs/`, and `.specify/` planning inputs and templates
- `scripts/` helper and maintenance scripts
- scoped guidance files under `src/`, `frontend/`, and `tests/`

## Current Architectural Truth

The current architecture is best understood as four layers:

1. A workflow-governance layer in `.github/` that defines instructions,
	prompts, agents, approval hooks, and canonical metadata.
2. A documentation and planning layer in `docs/`, `specs/`, `openspec/`, and
	`.specify/` that captures requirements, process, and repo operating rules.
3. A maintenance layer in `scripts/` that validates metadata and supports repo
	hygiene.
4. Reserved application areas in `src/`, `frontend/`, `tests/`, and `deploy/`
	for project-specific runtime code once a concrete product direction is chosen.

## Current Constraints

This snapshot does not currently contain a validated backend or frontend
runtime. As a result:
- CI and task automation should stay scoped to repo hygiene and metadata checks
- docs must not claim concrete API, UI, or deployment behavior
- product-domain naming should remain generic until real application code exists

## Documentation Rules

Docs in this repository should avoid inventing runtime capabilities, including:
- API endpoints
- database schemas
- UI routes
- deployment contracts
- product-domain entities

## Source Of Truth

Use these pages first:
- `docs/product-direction.md`
- `docs/specs/active/product-realignment-phase-1.md`
- `docs/runbooks/agent-mode.md`

Treat inherited or archived product-specific material as historical reference
only.
