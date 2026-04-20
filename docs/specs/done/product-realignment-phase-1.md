# Feature: Product Realignment Phase 1

**Status:** Done
**Created:** 2026-04-14
**Completed:** 2025-01-01
**Author:** GitHub Copilot
**Estimate:** L
**Supersedes:** None

---

## Problem
This repository still contains a large amount of inherited planning,
documentation, automation, and metadata written for specific product identities.
The public surfaces currently mix generic workflow-governance guidance with old
pipeline-observability and other domain-specific language. That mismatch makes the
repo harder to reuse, misleads contributors about what is actually implemented,
and leaves stale scripts, tasks, and CI steps pointing at code that is not in the
workspace.

The current verified state is more limited and more general: this checkout is a
workflow-heavy scaffold with specs, prompts, skills, instructions, and helper
scripts, not a validated concrete application runtime. The cleanup therefore
needs to remove or generalize repo-specific files and wording until the public
surface matches that reality.

## Success criteria
- Top-level contributor docs describe the repo as a generic scaffold for
      agent-assisted software delivery.
- Public docs, active specs, tasks, CI, and helper scripts no longer depend on
      stale product-specific wording or dead runtime paths.
- Clearly inherited product-only files are removed, renamed, or archived behind
      generic replacements.
- Repo metadata is generated from generic source definitions rather than old
      product names.

---

## Requirements

### Functional
- [x] Update top-level docs to describe the repository as a generic scaffold.
- [x] Replace or remove active specs and placeholder pages whose file names or
      contents are tied to a specific inherited product.
- [x] Remove dead product-only helper scripts that point at non-existent runtime code.
- [x] Generalize repo metadata, tasks, and CI so they match the verified workspace shape.
- [x] Keep archival material clearly separated from active contributor guidance.

### Non-functional
- [x] Documentation honesty: no doc should claim validated runtime behavior that is
      not present in the workspace.
- [x] Traceability: all edits should point back to this active spec or the explicit
      user request.
- [x] Regression safety: preserve generic workflow guidance while removing stale,
      misleading product assumptions.
- [x] Maintainability: the source metadata generator should produce the same public
      wording as the checked-in generated artifacts.

---

## Affected components
- `docs/architecture.md`
- `docs/architecture/README.md`
- `docs/quickstart.md`
- `docs/ci-cd.md`
- `docs/product-direction.md`
- `docs/runbooks/agent-mode.md`
- non-workflow documentation pages and placeholders previously kept under `docs/`
- `docs/specs/active/product-realignment-phase-1.md`
- product-specific and non-workflow active specs under `docs/specs/active/`
- non-workflow historical specs under `docs/specs/done/`
- root and scoped `AGENTS.md` files
- repo metadata under `.github/agent-platform/`
- agent-platform source generation under `scripts/agent/`
- `.github/workflows/ci.yml`
- `.vscode/tasks.json`
- repo-visible helper scripts under `scripts/`

---

## External context
No external research is required. The governing inputs are the explicit user
request and the current repository contents.

---

## Documentation impact
This change directly updates the public contributor and planning surfaces listed
above so they present a generic, reusable repository shape.

## API changes
None. This work only changes docs, metadata, and helper automation.

## Data model changes
None.

---

## Architecture plan
1. Rewrite the entry-point docs to describe the repo as a generic workflow and
      governance scaffold.
2. Replace or remove active files whose names or contents are tied to inherited
      product identities.
3. Update tasks, CI, and generated metadata so they validate only what exists.
4. Remove dead scripts that refer to missing runtime modules.

---

## Edge cases

| Edge case | Handling |
|---|---|
| A legacy spec still contains product-specific detail after the rewrite | Replace it with a generic equivalent or delete it if it only preserves stale assumptions |
| Contributors expect runnable backend commands from docs or CI | Replace those commands with metadata and repo-hygiene checks unless the target files exist |
| A future project chooses a concrete product domain | Reintroduce narrow terminology only in the files backed by actual runtime code and current specs |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Removing useful historical context | Medium | Medium | Keep generic workflow guidance and delete only files that are dead or misleading |
| Leaving one source generator stale after updating generated files | Medium | High | Update `scripts/agent/sync_agent_platform.py` and the generated metadata together |
| Missing hidden product-specific references in secondary docs | Medium | Medium | Run targeted searches after the edit pass and clean remaining public surfaces |

---

## Breaking changes
This is a documentation and workflow-asset realignment. It does not introduce
runtime behavior, but it does remove dead scripts and stale task references.

## Rollback plan
If any rewritten documentation proves too aggressive, revert the affected doc or
metadata files as a content-only change. No runtime rollback is required.

---

## Testing strategy
- **Unit:** not applicable.
- **Integration:** validate agent-platform metadata generation and CI/task references.
- **Documentation:** run targeted searches for stale product identifiers in active and public-facing files.
- **Regression:** verify that key docs still point to existing files and directories.

---

## Acceptance criteria
- [x] Top-level docs describe a generic workflow-governance scaffold.
- [x] Product-specific active specs and placeholder pages are removed or generalized.
- [x] Dead product-only scripts are removed.
- [x] CI, tasks, and generated metadata no longer point at missing runtime code.
- [x] Verification confirms the main public surfaces are free of inherited product naming.
