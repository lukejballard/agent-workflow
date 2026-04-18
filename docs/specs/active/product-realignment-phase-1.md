# Feature: Product Realignment Phase 1

**Status:** In Progress
**Created:** 2026-04-14
**Author:** GitHub Copilot
**Estimate:** L
**Supersedes:** None

---

## Problem
This repository still contains a large amount of inherited planning and documentation
written for a pipeline-observability product. The actual stated purpose of this repo
is to help baseball players improve biomechanics and support better prescription
workflows, but the public docs, specs, and planning assets do not consistently say
that. The mismatch misleads contributors, creates false implementation assumptions,
and makes it unclear which assets are authoritative.

A second issue is that the current workspace snapshot does not contain the expected
runtime trees under `src/` or `frontend/`. That means product language and helper
surfaces can be aligned now, but end-to-end runtime migration cannot be completed
inside this workspace unless those trees are restored.

Git history inspection on 2026-04-14 confirmed that the missing runtime trees are not
present in the repository history currently available in this workspace. Runtime
restoration therefore requires an external source or a new aligned implementation,
not a simple local checkout from this repository.

## Success criteria
- Top-level contributor and product docs describe the repo as a baseball biomechanics
  application, not a pipeline-observability platform.
- Inherited pipeline-era specs and planning artifacts are either rewritten at the
  summary level or explicitly marked as archival/non-authoritative.
- Repo-visible scripts, workflow assets, and helper paths use `biomechanics_ai`
  naming consistently.
- The docs stop claiming runnable backend/frontend surfaces that are not present in
  the current workspace snapshot.

---

## Requirements

### Functional
- [ ] Update top-level docs to reflect the baseball biomechanics product direction.
- [ ] Add a current source of truth for contributors describing the verified repo
      state and the intended product direction.
- [ ] Mark inherited planning/spec artifacts as archival where their detailed
      pipeline-oriented behavior cannot be validated.
- [ ] Align repo-visible package names, image names, script references, and env var
      names with `biomechanics_ai` where those files exist in this workspace.
- [ ] Record that runtime migration is blocked until real `src/biomechanics_ai/`
      and `frontend/` trees exist in the workspace.

### Non-functional
- [ ] Documentation honesty: no doc should claim validated runtime behavior that is
      not present in the workspace.
- [ ] Traceability: all edits should point back to this active spec or the explicit
      user request.
- [ ] Regression safety: preserve historical artifacts where useful, but clearly mark
      them as non-authoritative instead of silently deleting context.
- [ ] Maintainability: new docs should direct future contributors toward the active
      spec and product-direction summary instead of scattering disclaimers.

---

## Affected components
- `README.md`
- `docs/architecture.md`
- `docs/architecture/README.md`
- `docs/quickstart.md`
- `docs/ci-cd.md`
- `docs/cli-reference.md`
- `docs/deployment.md`
- `docs/sdk-reference.md`
- `docs/pipeline-studio.md`
- `docs/monitors-as-code.md`
- `docs/integrations/*.md`
- `docs/images/*.md`
- `docs/implementation-wave-1-top5.md`
- `plan/*`
- `specs/*`
- `openspec/changes/*`
- `docs/specs/active/*` and `docs/specs/done/*` where inherited pipeline wording is
  still presented as current product truth
- `docs/specs/active/practitioner-session-review-and-prescription-v1.md`
- `specs/005-athlete-session-domain-foundation/`
- `specs/006-practitioner-assessment-workspace/`
- `specs/007-prescription-delivery-and-followup/`
- `openspec/changes/practitioner-assessment-workflow/`
- repo-visible helper scripts under `scripts/`

---

## External context
No external research is required. The governing inputs are the explicit user request,
current repository contents, and the verified absence of runtime trees under `src/`
and `frontend/` in this workspace snapshot.

---

## Documentation impact
This change directly updates the public contributor and planning surfaces listed
above. It also establishes two new anchor docs:
- `docs/product-direction.md` for current product language
- `docs/specs/active/product-realignment-phase-1.md` for implementation traceability

## API changes
None in this phase. This work does not introduce or modify validated runtime API
contracts because the corresponding runtime surfaces are not present in the current
workspace snapshot.

## Data model changes
None in this phase. No database schema, storage model, or persisted runtime data shape
is changed by this realignment work.

---

## Architecture plan
1. Create one verified product-direction document that states what the repo is, what
   is present today, and what is currently absent.
2. Rewrite top-level docs that currently overclaim runtime behavior so they instead
   reflect the verified repo state and future biomechanics direction.
3. Add archival notes to inherited pipeline-era specs and planning artifacts rather
   than letting them continue as silent defaults.
4. Align helper scripts and workflow assets that still use stale package or env-var
   names, limited to files present in this workspace.
5. Stop short of runtime code migration because the expected runtime trees are not
      available here or in current repository history.

---

## Edge cases

| Edge case | Handling |
|---|---|
| A legacy spec still contains pipeline-era detail after the rewrite | Add a clear archival note at the top and point to this active spec |
| Contributors expect runnable backend commands from docs | Replace those commands with current-state guidance unless the target files exist |
| Runtime trees appear later in another workspace snapshot | Treat this phase as documentation and visible-tooling alignment only; perform runtime migration in a follow-up spec |
| A contributor assumes the missing runtime trees can be restored from local git history | Document that current repository history does not contain those trees and that external restoration is required |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Overwriting useful historical context | Medium | Medium | Preserve files but mark them archival instead of deleting them outright |
| Inventing biomechanics behavior not backed by code | High | High | Use high-level product language only and avoid unverified implementation details |
| Contributors miss the new source of truth | Medium | Medium | Link `docs/product-direction.md` from README and top-level docs |

---

## Breaking changes
This is a documentation and workflow-asset realignment. It does not intentionally
change validated runtime behavior. Some legacy helper commands are removed or
reframed where they referenced missing runtime surfaces.

## Rollback plan
If any rewritten documentation proves too aggressive, revert the affected doc or spec
files as a content-only change. No data migration or runtime rollback procedure is
required because this phase does not modify validated application code or storage.

---

## Testing strategy
- **Unit:** not applicable for documentation-only surfaces.
- **Integration:** validate agent-platform metadata and check edited scripts for
  diagnostics.
- **Documentation:** run targeted searches for stale product identifiers and stale
  pipeline-platform framing in top-level docs.
- **Regression:** verify that workflow docs still point to existing files and
  directories.

---

## Acceptance criteria
- [ ] README and top-level docs use baseball biomechanics language.
- [ ] Product-direction doc exists and is linked from key entry points.
- [ ] Inherited pipeline-era planning/spec files are clearly marked archival or
      refreshed at the summary level.
- [ ] No remaining references to the retired legacy product identifier remain in the
      workspace.
- [ ] Runtime-tree absence is documented explicitly rather than hidden.
- [ ] Runtime restoration blocker is documented as an external-source requirement rather than a local git recovery task.
- [ ] Verification summary distinguishes completed alignment from blocked runtime
      migration.
