# Feature: Single-Entry Agent Architecture

**Status:** Done
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** N/A

---

## Problem
The repository currently documents two different agent operating models: a role-based
specialist pipeline under `.github/agents/` and a seven-step prompt loop in the docs
that references prompt files that do not exist. This creates drift, lowers trust in the
agent setup, and forces users to manually choose between several specialist agents even
when they want one end-to-end chat experience.

The impact is higher setup friction, inconsistent response quality, weak internal
self-critique, and no single default entry point for routine work.

## Success criteria
The agent architecture is successful when a user can handle normal work through one
default agent, the documented workflow matches the files that actually exist, and the
agent consistently applies planning, critique, and verification logic before answering.

---

## Requirements

### Functional
- [x] Add one default single-entry agent that classifies requests, gathers context, creates or updates a spec for non-trivial work, critiques its own plan, revises, and delivers in one conversation.
- [x] Keep the specialist agents available for advanced or fallback usage, but stop documenting them as the default user path.
- [x] Encode a mandatory breadth-first scan followed by full-depth analysis of the highest-risk surfaces.
- [x] Add a reusable adversarial-review skill that challenges assumptions, alternatives, edge cases, regression risk, and quality blind spots.
- [x] Add a reusable requirements-traceability skill that maps the user request or spec to planned work, verification, and remaining gaps.
- [x] Add one single-entry workflow prompt that users can paste into the default agent for almost every task.
- [x] Rewrite the existing greenfield and brownfield prompts so they route through the new single-entry workflow instead of requiring manual agent switching.
- [x] Add sharper prompt entry points for focused bugfix work and repo-wide launch-readiness audits.
- [x] Add one researcher fallback agent for external docs, ecosystem references, and launch-readiness benchmarking.
- [x] Reconcile stale ownership and scoped guidance files outside `.github/` and `docs/` when they would mislead the orchestrator.
- [x] Update AGENTS and setup documentation so every referenced agent, prompt, and skill exists and matches the implemented workflow.

### Non-functional
- [x] Performance: the new workflow must not require repeated manual handoffs for normal tasks.
- [x] Security: the new critique flow must explicitly inspect input validation, secrets hygiene, auth, and query-safety gaps when relevant.
- [x] Accessibility: UI-oriented prompts and critique paths must explicitly consider accessibility checks.
- [x] Observability: service or endpoint work must explicitly consider logging, metrics, tracing, and health checks.

---

## Affected components
- `AGENTS.md`
- `CODEOWNERS`
- `frontend/AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agents/*.agent.md`
- `.github/prompts/*.prompt.md`
- `.github/skills/*/SKILL.md`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`
- `specs/004-studio-runtime-ops/plan.md`
- `specs/004-studio-runtime-ops/tasks.md`

---

## Architecture plan
Introduce a new `@orchestrator` agent as the default interface for normal work. The
orchestrator keeps the user in one conversation and internally follows a bounded phase
machine:

1. Classify the task.
2. Run a breadth-first scan across the relevant repo surfaces.
3. Go full-depth on the highest-risk branches from that scan.
4. Create or update a spec for non-trivial work.
5. Draft a preferred approach and compare it with at least one viable alternative.
6. Run adversarial critique and traceability checks.
7. Revise once or twice, then execute or answer.
8. Summarize verification, residual risks, and next steps.

The existing specialist agents remain available as narrow fallback tools for analysis,
research, planning, implementation, QA, review, and cleanup. Documentation is updated so
the single-entry path is canonical and the specialist path is advanced/manual.

---

## API design

No runtime API changes. This feature changes workspace agent customizations,
instructions, prompts, and documentation only.

---

## Data model changes

No application data model changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the new agent, prompt, and skills; restore the prior docs and routing guidance.
- Breaking change? No application-facing breaking change. There is a workflow change for contributors using the old manual prompt roadmap.

---

## Edge cases

| Edge case | Handling |
|---|---|
| User asks for review only | The orchestrator stays in review mode and reports findings first instead of trying to implement code. |
| User asks a trivial question or one-line fix | The orchestrator can compress phases and skip spec creation if the work is truly trivial. |
| Non-trivial work starts without a spec | The orchestrator must create or update a spec before code changes. |
| Requirements are materially ambiguous | Ask at most one blocking clarification; otherwise state assumptions and proceed. |
| Older plan or spec conflicts with the codebase | Treat the legacy document as input, not authority, until reconciled against the current code. |
| User explicitly wants a specialist agent | Allow the specialist mode, but document it as an advanced/manual path. |
| Domain-specific release checks are needed | The orchestrator should consult the relevant checklist under `skills/` or `.github/skills/` before finalizing. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The new agent instructions become too broad and verbose | Medium | High | Keep the phase machine explicit and bounded; restrict output contracts to non-trivial work. |
| Documentation remains partially inconsistent after the refactor | Medium | High | Update AGENTS, setup guide, and runbook in the same change set and verify every referenced asset exists. |
| Contributors still use legacy prompts as primary entry points | Medium | Medium | Mark legacy prompts as wrappers around the default orchestrator and document the new default clearly. |
| Critique loops become open-ended | Low | Medium | Cap self-critique and revision to two passes before escalation. |

---

## Breaking changes
This does not break runtime code, APIs, or schemas. It does change contributor workflow:
the default guidance moves from multi-agent manual handoffs to a single-entry
orchestrator. Specialist agents remain available as fallback tooling.

---

## Testing strategy
- **Unit:** N/A for product code.
- **Integration:** Verify all referenced agent, prompt, and skill files exist after the refactor.
- **E2E:** Smoke-test representative task types against the new orchestrator guidance.
- **Performance:** Ensure the default workflow reduces manual handoffs for non-trivial tasks.
- **Security:** Verify critique guidance explicitly includes security checks for relevant tasks.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] The single-entry orchestrator agent exists and is documented as the default path.
- [x] The default workflow explicitly does breadth-first discovery before a full-depth pass.
- [x] The adversarial-review and requirements-traceability skills exist and are referenced by the new default workflow.
- [x] The specialist agents remain available but are described as fallback/manual modes.
- [x] The researcher fallback agent exists for external references and benchmark-style work.
- [x] The greenfield and brownfield prompts no longer require manual agent switching.
- [x] Focused prompt wrappers exist for bugfix work and launch-readiness audits.
- [x] `AGENTS.md`, `.github/copilot-instructions.md`, `docs/runbooks/agent-mode.md`, and `docs/copilot-setup.md` all describe the same workflow.
- [x] Stale repo guidance outside `.github/` and `docs/` that would misroute the workflow has been corrected.
- [x] All agent, prompt, and skill references in the updated docs resolve to existing files.
- [x] The new default workflow explicitly addresses planning, critique, verification, observability, security, and testing.
