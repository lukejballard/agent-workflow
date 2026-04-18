# Architecture

## Product Goal

baseball-biomechanics-ai is intended to support baseball practitioners and athletes with
better biomechanics assessment, review, and prescription workflows.

## Verified Repo State

The repository is still documentation- and workflow-heavy, but it now also includes a
minimal aligned application runtime. The following areas are present and verified:
- `.github/` agent workflows, instructions, and repo metadata
- `docs/` contributor, architecture, and planning documentation
- `openspec/`, `specs/`, and `plan/` inherited planning artifacts
- `scripts/` helper and maintenance scripts
- `src/biomechanics_ai/` FastAPI runtime bootstrap
- `frontend/` React + TypeScript + Vite practitioner workspace bootstrap
- `tests/` initial Python API coverage

## Current Architectural Truth

The current bootstrap architecture is best understood as four layers:

1. A FastAPI collector layer in `src/biomechanics_ai/collector/` that owns transport,
	auth, error shaping, and route registration.
2. A service and storage layer in `src/biomechanics_ai/services/` and
	`src/biomechanics_ai/storage/` that keeps workflow orchestration separate from
	file-backed persistence.
3. A React frontend in `frontend/src/` that keeps API transport in `api/`, shared types
	in `types/`, and workflow state in hooks instead of in page components.
4. Documentation, planning, and governance surfaces that define product direction and
	contributor workflow.

## Bootstrap Runtime Shape

The current runtime implements the first practitioner flow:
- athlete creation and listing
- session registration and listing
- assessment draft creation, updates, and reviewer finalization
- baseline comparison between sessions
- prescription generation
- shareable report links with revoke support
- health and Prometheus metrics endpoints

Current constraints:
- persistence is a local JSON store, not a relational database
- auth is env-configured bearer-token role mapping
- frontend coverage is limited to the practitioner workspace bootstrap
- deployment assets for this new runtime have not been refreshed yet

## Documentation Rules

Docs in this repository should avoid inventing capabilities beyond the bootstrap runtime,
including:
- API endpoints
- database schemas
- UI routes
- deployment contracts
- SDK behavior

## Source Of Truth

Use these pages first:
- `docs/product-direction.md`
- `docs/specs/active/product-realignment-phase-1.md`
- `docs/specs/active/practitioner-runtime-bootstrap-v1.md`

Treat inherited files under `specs/`, `openspec/`, and archived docs/specs as historical
reference only.
