# Feature: Agent Runtime Hardening Phase 3

**Status:** In Review
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** `docs/specs/active/agent-runtime-hardening-phase-2.md`

---

## Problem
Phase 2 introduced canonical workflow metadata for topology, skill discovery, and run-artifact structure,
but the metadata is still maintained manually.

That leaves three remaining operational gaps:
1. `repo-map.json` and `skill-registry.json` can drift from the actual repo state because they are not refreshed by tooling.
2. Contributors do not yet have a repo-local validation command for agent-platform metadata, so verification remains ad hoc.
3. The run-artifact schema exists, but there are no concrete example artifacts that show what a bugfix or review summary should look like.

Without automation and examples, the metadata layer is useful but still too easy to neglect in day-to-day work.

## Success criteria
This phase is successful when:
- a repo-local script can refresh canonical agent-platform metadata deterministically
- that same tool can validate the metadata and fail clearly when files drift or examples are invalid
- at least two concrete run-artifact examples exist and align with the schema
- repo verification docs and routes point at the new validation command
- the solution remains static, local, and honest about not being a managed runtime service

---

## Requirements

### Functional
- [x] Add a repo-local Python script under `scripts/agent/` that can refresh canonical agent-platform metadata.
- [x] The script must regenerate `skill-registry.json` from `workflow-manifest.json` and the actual skill files.
- [x] The script must refresh `repo-map.json` deterministically enough to keep topology, verification routes, and observed subpaths aligned with the real repo.
- [x] The script must support a check mode that validates the current metadata without rewriting files.
- [x] Add at least two example run artifacts under the agent-platform tree: one bugfix-oriented artifact and one review-oriented artifact.
- [x] Validation must cover the run-artifact examples and confirm that referenced metadata files exist.
- [x] Update verification routes and contributor docs to reference the new agent-platform validation command.
- [x] Add unit tests for the new script.

### Non-functional
- [x] Performance: the script must run with the Python standard library and may add optional `jsonschema` validation when available.
- [x] Security: validation must not claim secrets safety or durable storage guarantees.
- [x] Accessibility: documentation changes must keep accessibility review explicit for frontend work.
- [x] Observability: example run artifacts must model concrete evidence, verification outcomes, and residual risk reporting.
- [x] Documentation: setup/runbook guidance must explain when to run refresh vs. check mode.

---

## Affected components
- `docs/specs/active/agent-runtime-hardening-phase-3.md`
- `scripts/agent/sync_agent_platform.py`
- `tests/unit/test_sync_agent_platform.py`
- `.github/agent-platform/repo-map.json`
- `.github/agent-platform/skill-registry.json`
- `.github/agent-platform/run-artifact-schema.json`
- `.github/agent-platform/examples/bugfix-run-artifact.json`
- `.github/agent-platform/examples/review-run-artifact.json`
- `scripts/agent/verify-broad.sh`
- `scripts/agent/verify-narrow.sh`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
No new external research is required.
This phase operationalizes the phase 1 and phase 2 decisions already captured in:
- `docs/specs/research/agent-architecture-benchmark-research.md`
- `docs/specs/research/vercel-labs-agent-skills-research.md`

---

## Documentation impact
Update workflow and setup docs so contributors know:
- where the sync tool lives
- how to run refresh mode versus check mode
- where the example run artifacts live

---

## Architecture plan
Introduce a single repo-local Python tool that handles both refresh and validation.

Refresh mode should rewrite deterministic metadata outputs.
Check mode should compare the current files to regenerated outputs and validate example run artifacts.

Keep the tool conservative:
- `skill-registry.json` should be generated from the workflow manifest and actual skill files.
- `repo-map.json` should be generated from a small curated model plus real directory discovery.
- run-artifact validation should use built-in structural checks and may add schema validation when `jsonschema` is available.

Also add sample run artifacts so the schema is concrete rather than theoretical.

---

## Edge cases

| Edge case | Handling |
|---|---|
| A skill directory exists but the manifest omits it | Validation fails with a clear mismatch message |
| The manifest references a missing skill file | Validation fails with a clear missing-path error |
| `jsonschema` is unavailable locally | Built-in validation still runs; optional schema validation is skipped |
| Repo topology changes later | Refresh mode should rebuild deterministic path lists from the current filesystem |
| Example artifacts drift from the schema | Check mode should fail until they are updated |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Refresh logic overwrites useful curated metadata | Medium | Medium | Keep curated role and note mappings in code and regenerate deterministically |
| Validation becomes too strict for minor repo churn | Medium | Low | Limit checks to canonical metadata and example artifacts, not every file in the repo |
| Optional `jsonschema` creates local friction | Low | Low | Fail with a targeted message and document the command path |

---

## Breaking changes
No product behavior changes are intended.
This phase affects contributor tooling, metadata maintenance, and documentation only.

---

## Testing strategy
- **Unit:** cover registry generation, repo-map generation, and validation failures/successes for example artifacts
- **Integration:** static readback of generated JSON and docs after edits
- **E2E:** not applicable
- **Performance:** not applicable
- **Security:** ensure docs remain honest about platform limits and approval behavior

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Repo-local sync/validation script added under `scripts/agent/`
- [x] `skill-registry.json` is generated from manifest + skill files
- [x] `repo-map.json` is refreshed from deterministic repo-local logic
- [x] Check mode validates metadata drift without rewriting files
- [x] Bugfix and review run-artifact examples exist and validate against the schema
- [x] Verification routes/docs reference the new validation command
- [x] Unit tests cover the new script
- [x] The implementation stays explicit about current platform limits
