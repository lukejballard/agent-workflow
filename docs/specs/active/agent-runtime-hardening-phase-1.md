# Feature: Agent Runtime Hardening Phase 1

**Status:** In Review
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** `docs/specs/active/agent-workflow-qol-hardening.md`

---

## Problem
The repository has a credible single-entry orchestrator and a useful skill vocabulary, but the workflow still depends too heavily on repeated markdown instructions instead of canonical manifests, approval-aware capability routing, and evidence-oriented quality skills.

The recent architecture audit and Vercel Labs benchmark show three practical gaps that most directly hurt quality and reliability for real coding workflows:
- workflow behavior is duplicated across agents, prompts, and docs rather than anchored in one canonical machine-readable source
- PR/spec traceability and approval policy enforcement are weaker than the docs imply
- the skill system is missing battle-tested capability patterns for frontend rigor and debugging evidence capture

If left unresolved, the repo will remain useful for guided IDE work but brittle for long-running, audit-heavy, or high-confidence engineering workflows.

## Success criteria
A contributor should be able to identify one canonical workflow manifest, see which skills and capabilities apply to a task, and trust that the highest-risk workflow surfaces enforce spec traceability and higher-friction approval on destructive or remote-write actions.

The skill system should also better cover battle-tested code quality workflows by adding reusable frontend best-practices and debugging-evidence skills.

---

## Requirements

### Functional
- [x] Add one canonical workflow manifest under `.github/` that defines task classes, phase order, skill triggers, and capability routing.
- [x] Update the orchestrator and workflow docs so the manifest is described as the canonical behavioral source for workflow routing.
- [x] Strengthen PR quality gating so a PR must reference a specific active spec path or a real no-spec exemption, instead of passing when any active spec exists.
- [x] Update the PR template so the spec-reference field matches the stronger gate.
- [x] Extend the pre-tool approval policy so higher-risk remote-write or sensitive automation surfaces require explicit approval.
- [x] Add one reusable `frontend-best-practices` skill inspired by modern agent-skill collections for React/UI quality beyond accessibility-only review.
- [x] Add one reusable `debug-timeline-capture` skill that standardizes how agents collect repro evidence across logs, browser output, screenshots, and test failures.
- [x] Update the orchestrator trigger matrix and public docs to reference the new skills where relevant.
- [x] Capture the Vercel Labs ecosystem research in a reusable brief and reference it from this spec.

### Non-functional
- [x] Performance: keep the single-entry workflow intact and avoid introducing a separate runtime service in this phase.
- [x] Security: do not overclaim sandboxing or durable runtime guarantees that the repo does not actually implement.
- [x] Accessibility: the new frontend quality skill must retain explicit accessibility checks rather than replacing them.
- [x] Observability: the new debugging skill must prefer structured, timestamped evidence and make residual blind spots explicit.
- [x] Documentation: all workflow and skill changes must update the public runbook and setup guide in the same change set.

---

## Affected components
- `docs/specs/active/agent-runtime-hardening-phase-1.md`
- `docs/specs/research/vercel-labs-agent-skills-research.md`
- `.github/agent-platform/workflow-manifest.json` (new)
- `.github/agents/orchestrator.agent.md`
- `.github/skills/frontend-best-practices/SKILL.md` (new)
- `.github/skills/debug-timeline-capture/SKILL.md` (new)
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`
- `.github/workflows/pr-quality.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `scripts/agent/pretool_approval_policy.py`

---

## External context
External context materially changed this design.

Research briefs:
- `docs/specs/research/agent-architecture-benchmark-research.md`
- `docs/specs/research/vercel-labs-agent-skills-research.md`

Key constraints added by research:
- use a canonical manifest rather than more duplicated prose
- add battle-tested skill patterns now, but do not overclaim managed-agent or sandbox features not present in this repo
- prefer minimal tool exposure and approval-aware routing over broad default tool surfaces

---

## Documentation impact
The following docs must change:
- `docs/runbooks/agent-mode.md` to describe the manifest as the canonical workflow source and reference the new skills
- `docs/copilot-setup.md` to reflect the manifest-backed workflow and new skills
- `.github/PULL_REQUEST_TEMPLATE.md` to align with the stronger spec traceability gate

No broad architecture-doc update outside the agent workflow surfaces is required because this phase changes contributor workflow behavior, not the product runtime.

---

## Architecture plan
This phase adds a canonical workflow manifest but does not introduce a new runtime engine.

Preferred approach:
- add one machine-readable manifest under `.github/agent-platform/`
- keep the current orchestrator as the default entry point, but make the manifest the canonical source for task classes, capabilities, skill triggers, and workflow phases
- harden the most misleading control surfaces first: PR traceability and approval policy
- add missing quality skills drawn from the benchmark research without pretending the repo now has a managed-agent platform

Alternative considered:
- jump directly to a code-defined orchestrator runtime with durable state, resumable sessions, and tool adapters

Why rejected:
- that is the right long-term direction, but it is too large for one repo-local brownfield pass
- it would force design decisions about storage, auth, process isolation, and background execution that the current repo is not yet ready to settle
- the highest-value improvements available now are governance hardening and better skills, not a partial pseudo-runtime

---

## API design
No product API changes.
This feature changes workflow files, skill surfaces, and local automation policy only.

---

## Data model changes
No application data model changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the new manifest and skills, restore the prior PR gate and docs wording, and archive this spec
- Breaking change? No product-facing breaking change. Contributor workflow and enforcement become stricter and more explicit.

---

## Edge cases

| Edge case | Handling |
|---|---|
| A PR references a spec path that does not exist | The PR gate must fail with a clear message |
| A small fix intentionally has no spec | Allow explicit `[no-spec]` exemption in the documented format |
| Agents lack browser automation in a given editor environment | The new debugging skill must describe evidence collection patterns without requiring unavailable tools |
| Approval hook sees a new unknown remote-write tool name | Use conservative substring and category matching rather than exact-name matching only |
| New skills overlap with existing `visual-qa` or `test-hardening` skills | Scope the new skills narrowly and document when they complement rather than replace existing skills |
| Contributors treat the manifest as executable runtime behavior | Docs must state that the manifest is canonical metadata, not a durable workflow engine |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The manifest becomes another stale file instead of reducing drift | Medium | High | Make docs explicitly point to it as canonical and keep the first version concise |
| Approval rules become too noisy | Medium | Medium | Gate only high-risk remote-write and sensitive automation surfaces |
| PR gate becomes too brittle | Medium | Medium | Support explicit no-spec exemptions and validate only the referenced path |
| New skills duplicate existing skills confusingly | Medium | Medium | Give each new skill a narrow scope and update the runbook table in the same patch |
| Contributors assume future sandbox or managed-agent guarantees already exist | Low | High | Keep the docs explicit that those remain future work |

---

## Breaking changes
No runtime or API breaking changes.
This phase tightens contributor workflow behavior around spec traceability and higher-risk approvals.

---

## Testing strategy
- **Integration:** verify the new manifest, skills, docs, and workflow references all resolve correctly
- **Integration:** statically review the PR gate logic against valid spec, invalid spec, and no-spec cases
- **Integration:** statically review the approval script against representative terminal, edit, and remote-write tool names
- **E2E:** not required for product runtime, but the workflow docs should stay internally consistent with the live files
- **Security:** verify the new docs do not overclaim sandbox or managed runtime capabilities

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Canonical workflow manifest added under `.github/`
- [x] Orchestrator and public workflow docs describe the manifest as the canonical workflow source
- [x] PR quality workflow validates the referenced spec path or a real no-spec exemption
- [x] PR template matches the stronger traceability behavior
- [x] Pre-tool approval policy covers higher-risk remote-write or sensitive automation surfaces more explicitly
- [x] `frontend-best-practices` skill exists and is documented in the workflow surfaces
- [x] `debug-timeline-capture` skill exists and is documented in the workflow surfaces
- [x] The orchestrator trigger matrix includes the new skills where relevant
- [x] Vercel Labs research is captured in a reusable brief and referenced from this spec
- [x] Docs remain honest about current platform limits and future-work boundaries
