# Feature: Agent Core .github-Only Package

**Status:** In Review
**Created:** 2026-04-19
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** N/A

---

## Problem
`agent-core/` still ships two top-level surfaces, `github/` and `scripts/`, even though the packaging goal is to keep the reusable workflow contained to one non-production folder. That creates extra install steps, extra path references, and continued drift between discovery assets and runtime helpers.

## Success criteria
The package root contains only `github/` and `README.md`. Installing the package requires copying only `agent-core/github/.` into `.github/`. Hook execution and package validation continue to work from the installed `.github/` layout and from the source-package `github/` layout.

---

## Requirements

### Functional
- [x] Move the hook runner into the packaged `.github/` tree and update hook config to call it there.
- [x] Move the metadata validator into the packaged `.github/` tree and keep source-layout and installed-layout validation working.
- [x] Update package documentation and agent guidance so the install model is `.github` only.
- [x] Remove the obsolete top-level `agent-core/scripts/` folder.

### Non-functional
- [ ] Performance: helper behavior remains effectively unchanged; no new external dependencies.
- [ ] Security: sensitive-path approval coverage still includes the moved helper locations.
- [ ] Accessibility: not applicable; no UI change.
- [ ] Observability: existing hook decision/output behavior remains unchanged.

---

## Affected components
- `agent-core/README.md`
- `agent-core/github/AGENTS.md`
- `agent-core/github/hooks/pretool-approval-policy.json`
- `agent-core/github/hooks/hooks.py` (new location)
- `agent-core/github/agent-platform/validate.py` (new location)
- `agent-core/scripts/agent/hooks.py` (remove)
- `agent-core/scripts/agent/validate.py` (remove)

---

## External context
No external context materially changed the design.

---

## Documentation impact
The package README and packaged agent guide must change because the installation instructions, package tree, and helper-script locations all change.

---

## Architecture plan
Keep the package root to a single transferable surface: `agent-core/github/`, which installs directly to `.github/`.

Place the hook runner beside the hook config in `.github/hooks/` so the runtime path becomes self-contained.

Place the validator under `.github/agent-platform/` because it validates workflow metadata and should travel with that metadata.

Retain the validator's dual-layout path resolution so `python .github/agent-platform/validate.py --repo-root <repo>` works after installation and `python agent-core/github/agent-platform/validate.py --repo-root agent-core` works in-source.

---

## API design
No API changes.

---

## Data model changes
No data model changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Hook config uses `.github/...` paths while validating source package | Validator maps `.github/...` references to `github/...` when running in source-package mode |
| Sensitive-path approval logic still references removed `scripts/agent/` paths | Replace obsolete markers with the new `.github/...` helper locations |
| Installed repo runs helper scripts from repo root | Hook commands use `.github/...` paths relative to repo root |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Path update misses one source reference | Medium | Medium | Search all `agent-core/**` references before deleting `scripts/` |
| Hook runner move breaks approval hooks on install | Medium | High | Update hook JSON and validate path resolution before cleanup |

---

## Breaking changes
This changes the package installation layout for consumers of `agent-core/`. The migration path is to stop copying `agent-core/scripts/.` and instead rely on the moved helpers inside `.github/`.

---

## Testing strategy
- **Unit:** not adding new unit tests; preserve existing helper behavior with minimal logic changes.
- **Integration:** run the validator against `agent-core/` after the move.
- **E2E:** not applicable.
- **Performance:** none needed.
- **Security:** verify sensitive path gating still covers moved helper locations.

---

## Acceptance criteria
- [x] All functional requirements implemented
- [x] Package validates successfully from source layout
- [x] README reflects `.github`-only installation
- [x] No remaining `agent-core/scripts` references inside the package