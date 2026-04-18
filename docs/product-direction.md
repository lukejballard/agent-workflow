# Product Direction

This repository is for a baseball biomechanics application whose goal is to help
players, coaches, and practitioners make better movement prescriptions.

## What is verified today
The current workspace is strongest in documentation, planning artifacts, agent
workflow assets, and helper scripts, but it now also includes a fresh runtime
bootstrap for the first practitioner workflow. The following areas are present and
actively maintained:

| Area | What is here now |
|---|---|
| `docs/` | contributor guidance, architecture notes, active specs, and legacy planning artifacts |
| `.github/` | agent instructions, workflow metadata, prompts, and quality skills |
| `src/biomechanics_ai/` | FastAPI backend bootstrap for the practitioner review flow |
| `frontend/` | React + TypeScript practitioner workspace bootstrap |
| `tests/` | initial backend and frontend test scaffolding |
| `scripts/` | helper scripts for repo maintenance and demos |
| `specs/`, `openspec/`, `plan/` | inherited planning material that now needs product-specific refresh |

## What is not yet verified
The repo is no longer runtime-empty, but it is still early and intentionally narrow.
The following are not yet verified as mature or complete:
- production-grade persistence beyond the local JSON store
- deployment assets aligned to the new bootstrap runtime
- broader frontend coverage beyond the practitioner workspace
- broader backend domain surfaces beyond the first practitioner workflow

## Current source of truth
Use these files in order when deciding what is current:

1. `README.md` for the one-line repo purpose.
2. `docs/product-direction.md` for current product framing and verified repo state.
3. `docs/specs/active/product-realignment-phase-1.md` for the current cleanup and
   realignment work.
4. `docs/specs/active/practitioner-session-review-and-prescription-v1.md` for the
   first validated practitioner workflow.
5. `docs/specs/active/practitioner-runtime-bootstrap-v1.md` for the current runtime
   implementation slice.
6. `AGENTS.md` and `.github/copilot-instructions.md` for contributor and agent
   workflow rules.

## How to treat inherited pipeline-era material
Many planning artifacts in `docs/`, `specs/`, `openspec/`, and `plan/` were inherited
from a pipeline-observability codebase. Until they are rewritten against validated
biomechanics requirements, treat them as archival context only.

They may still help with:
- workflow structure
- review checklists
- naming patterns for future specs
- examples of how the repo previously organized planning work

They should not be treated as:
- validated product requirements
- accurate API contracts
- accurate data models
- proof that a corresponding runtime surface exists in this workspace

## Near-term direction
The next product-alignment phase should focus on:

1. Hardening the new backend and frontend bootstrap with broader automated coverage.
2. Expanding the athlete, session, and movement-assessment domain model beyond the
   first practitioner flow.
3. Refreshing deployment and operational assets to match the new runtime.
4. Replacing inherited pipeline-platform specs with biomechanics-specific
   requirements and acceptance criteria.

The current replacement planning artifacts for that work are:
- `specs/005-athlete-session-domain-foundation/`
- `specs/006-practitioner-assessment-workspace/`
- `specs/007-prescription-delivery-and-followup/`
- `openspec/changes/practitioner-assessment-workflow/`
