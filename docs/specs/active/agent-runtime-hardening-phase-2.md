# Feature: Agent Runtime Hardening Phase 2

**Status:** In Review
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** `docs/specs/active/agent-runtime-hardening-phase-1.md`

---

## Problem
Phase 1 hardened workflow governance, approval handling, and skill triggers, but the repository still
lacks machine-readable topology and discovery metadata for large-codebase work.

That gap shows up in three places:
1. Agents and prompts still have to infer repo structure from prose instead of a canonical repo map.
2. Skills are discoverable only through markdown files and the workflow manifest, which makes inventory
   and trigger coverage harder to inspect at a glance.
3. Evidence and verification for longer investigations have no lightweight artifact format, so traceability
   remains conversational instead of reusable.

Without a second-phase metadata layer, the current system remains better than stock prompts but still
slower and less consistent than battle-tested large-repo workflows.

## Success criteria
This phase is successful when:
- agents can read a canonical repo map for topology, scoped guides, and verification routes
- skills have a canonical registry that mirrors trigger metadata without depending on prose-only discovery
- longer investigations and cross-surface changes have a lightweight run-artifact schema for evidence,
  touched paths, verification, and residual risk
- orchestrator/docs/prompts point to the new metadata so it becomes part of the real workflow
- the repo still does not overclaim durable sessions, sandboxing, or managed background execution

---

## Requirements

### Functional
- [x] Add a canonical repo map under `.github/agent-platform/` describing top-level areas, major product
      surfaces, scoped guides, and common verification routes.
- [x] Add a canonical skill registry under `.github/agent-platform/` that inventories active skills,
      their paths, and their trigger tags.
- [x] Add a lightweight run-artifact schema under `.github/agent-platform/` for evidence, touched files,
      verification status, and residual risks.
- [x] Update the canonical workflow manifest so it references the repo map, skill registry, and run-artifact schema.
- [x] Update the orchestrator so it reads the repo map and skill registry before broad analysis.
- [x] Update the single-entry and brownfield workflow prompts so prompt-driven runs inherit the same metadata layer.
- [x] Update workflow docs and setup docs so contributors know which artifact is authoritative for workflow,
      topology, skill discovery, and run-artifact structure.
- [x] Update the root `AGENTS.md` inventory so the new platform files are part of the documented stack.

### Non-functional
- [x] Performance: keep the new metadata static and repo-local; do not add a background service.
- [x] Security: do not represent the run-artifact schema as a durable secret-safe storage system.
- [x] Accessibility: any documentation updates that mention frontend checks must preserve explicit accessibility review.
- [x] Observability: the run-artifact schema must support concrete evidence and explicit residual risk reporting.
- [x] Documentation: docs must stay aligned with the new metadata in the same change set.

---

## Affected components
- `.github/agent-platform/workflow-manifest.json`
- `.github/agent-platform/repo-map.json`
- `.github/agent-platform/skill-registry.json`
- `.github/agent-platform/run-artifact-schema.json`
- `.github/agents/orchestrator.agent.md`
- `.github/prompts/single-entry-workflow.prompt.md`
- `.github/prompts/brownfield-improve.prompt.md`
- `.github/prompts/bugfix-workflow.prompt.md`
- `AGENTS.md`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
No new external context is required for this phase.
This work reuses the decisions already captured in:
- `docs/specs/research/agent-architecture-benchmark-research.md`
- `docs/specs/research/vercel-labs-agent-skills-research.md`

---

## Documentation impact
Update the root agent guide, the agent-mode runbook, and the Copilot setup guide so the new metadata
layer is discoverable and described honestly.
No separate public product docs are required because this phase changes contributor workflow only.

---

## Architecture plan
Add three new machine-readable artifacts under `.github/agent-platform/`:
1. `repo-map.json` for repository topology, scoped guides, and verification routes.
2. `skill-registry.json` for skill inventory and trigger-tag discovery.
3. `run-artifact-schema.json` for optional lightweight run summaries.

Then extend `workflow-manifest.json` so those artifacts are first-class parts of the platform metadata.
Finally, update the orchestrator, prompts, and docs so they consume the metadata instead of treating it
as an undocumented implementation detail.

This phase remains explicitly static and metadata-driven.
It does not implement a daemon, managed session service, sandbox runtime, or persistent memory store.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Repo structure changes later | Keep the repo map small, explicit, and part of the documented update surface |
| A skill exists in `.github/skills/` but is not auto-triggered | Keep it in the registry and allow empty or narrow trigger tags when needed |
| A task has no meaningful run artifact | The schema remains optional guidance, not a mandatory log file |
| Prompts drift from the new metadata layer | Manifest and docs updates are required in the same change set |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Metadata drifts from repo reality | Medium | Medium | Keep files concise and wire them into orchestrator/docs so they stay visible |
| Registry becomes duplicative of the manifest | Medium | Low | Scope the registry to skill discovery and trigger inventory only |
| Run-artifact schema is mistaken for a runtime feature | Low | Medium | Document it as optional, lightweight, and repo-local |

---

## Breaking changes
No runtime or product breaking changes are intended.
This phase changes contributor workflow metadata and documentation only.

---

## Testing strategy
- **Unit:** not applicable; no application code changes in this phase
- **Integration:** static readback of new JSON and markdown files for consistency
- **E2E:** not applicable
- **Performance:** not applicable
- **Security:** confirm docs do not overclaim approval or runtime guarantees

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Canonical repo map added under `.github/agent-platform/`
- [x] Canonical skill registry added under `.github/agent-platform/`
- [x] Lightweight run-artifact schema added under `.github/agent-platform/`
- [x] Workflow manifest references the new metadata artifacts
- [x] Orchestrator reads the repo map and skill registry before deeper analysis
- [x] Prompt wrappers reference the new metadata layer where relevant
- [x] Root and workflow docs describe the new metadata layer accurately
- [x] The implementation stays explicit about current platform limits
