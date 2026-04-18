# Feature: Agent Context Engineering Phase 2

**Status:** Implemented
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** docs/specs/done/agent-context-engineering-phase-1.md

---

## Problem
Phase 1 made the context contract explicit, but the default workflow still leaves two important behaviors under-specified.
First, the run-artifact and `taskLedger` model exists without a default activation rule for real multi-step work.
Second, semantic memory is described as on-demand, but the packet does not yet capture which repo-memory notes were
loaded, why they were loaded, or how that hydrated context changed the current step.

That gap matters on brownfield work, where the agent often needs both a traceable task ledger and targeted repo facts.
Without those behaviors becoming first-class, the architecture still depends too much on prose discipline instead of
the packet and artifact structures that were added in phase 1.

## Success criteria
This phase is successful when non-trivial multi-surface work activates a run artifact by default, semantic-memory
hydration is recorded in the packet contract, and the repo contains a concrete brownfield example pair that validates
the end-to-end flow.

---

## Requirements

### Functional
- [x] Upgrade the `ContextPacket` contract so it records task classification, active run-artifact state, and hydrated
      semantic-memory sources.
- [x] Update the workflow manifest so it defines when a run artifact becomes active and how memory hydration should be
      scoped for repo, session, and user memory.
- [x] Update the default orchestrator and the relevant prompt wrappers so longer multi-step workflows activate a run
      artifact and record hydrated memory sources instead of only retrieval intent.
- [x] Add a concrete brownfield context-packet example that demonstrates repo-memory hydration and an active run-artifact
      path.
- [x] Add a concrete brownfield run-artifact example whose `taskLedger` traces the packet-driven flow across multiple
      atomic subtasks.
- [x] Extend local validation so both new example files and the richer packet fields are checked by
      `python scripts/agent/sync_agent_platform.py --check`.
- [x] Update contributor docs so they describe the activation rule for run artifacts and the limitation that editor-
      managed memory notes are not hard-validated as normal repo files.

### Non-functional
- [x] Reliability: the richer packet remains bounded and does not turn into a full-session dump.
- [x] Security: hydrated memory summaries must not require copying raw secrets or sensitive tool output into the packet.
- [x] Observability: active run artifacts must record task-ledger updates for longer workflows without implying exact
      runtime token accounting that the editor cannot guarantee.
- [x] Documentation: workflow docs must explicitly distinguish repo-local validation from editor-managed memory storage.

---

## Affected components
- `docs/specs/done/agent-context-engineering-phase-2.md`
- `.github/agent-platform/workflow-manifest.json`
- `.github/agent-platform/context-packet.schema.json`
- `.github/agent-platform/examples/context-packet.example.json`
- `.github/agent-platform/examples/brownfield-context-packet.example.json`
- `.github/agent-platform/examples/brownfield-run-artifact.json`
- `.github/agents/orchestrator.agent.md`
- `.github/prompts/single-entry-workflow.prompt.md`
- `.github/prompts/brownfield-improve.prompt.md`
- `.github/prompts/bugfix-workflow.prompt.md`
- `.github/prompts/greenfield-feature.prompt.md`
- `.github/prompts/review-code.prompt.md`
- `.github/prompts/research.prompt.md`
- `.github/prompts/generate-tests.prompt.md`
- `.github/prompts/launch-readiness-audit.prompt.md`
- `scripts/agent/sync_agent_platform.py`
- `AGENTS.md`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
No external context materially changes this phase.
The work remains a brownfield hardening pass over the repository's own agent-platform metadata, prompts, and docs.

---

## Documentation impact
- Document when the default orchestrator should treat a run artifact as active rather than optional.
- Document that semantic-memory hydration may reference editor-managed memory scopes such as `/memories/repo/`, even
  when those notes are not exposed as ordinary workspace files.
- Keep the root guide, runbook, and setup guide aligned on the same packet and artifact story.

---

## Architecture plan
Phase 2 keeps the phase-1 model and makes it operational.

Preferred approach:
- upgrade the packet instead of adding a second side-channel for memory hydration
- activate run artifacts by policy for longer non-trivial workflows instead of leaving them as an optional afterthought
- add a concrete brownfield example pair so the default path is exercised against a real repo-maintenance scenario
- validate the richer contract locally through the existing sync script

Alternative considered:
- introduce a new dedicated memory-hydration artifact separate from the packet and run artifact

Why rejected for this phase:
- it would split one current-step contract into multiple partially overlapping structures
- the repo already has a packet and a run artifact; phase 2 should make those sufficient before adding another layer

---

## API design

No product runtime API changes.
This phase changes repo-local agent metadata, examples, prompts, validation logic, and documentation only.

---

## Data model changes

No application database changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: revert the packet-schema changes, remove the new examples, and restore the prior orchestrator and prompt
  guidance.
- Breaking change? No product-facing breaking change. The repo-local packet contract becomes stricter and moves to a new
  schema version.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Trivial task with no active run artifact needed | Packet marks the run artifact as `not-needed` and skips path emission. |
| Longer task has no repo-backed artifact path | Allow an active in-memory artifact policy and document the limitation. |
| Repo-memory notes are editor-managed rather than workspace files | Record the source path as metadata but do not hard-fail local validation on missing filesystem paths. |
| Hydrated memory becomes stale after the subtask changes | Treat the loaded memory summary as scoped to the current step and refresh it only when needed. |
| Run artifact is active but a task is skipped or blocked | Record the `completionStatus` accurately in `taskLedger` rather than omitting the node. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Packet growth recreates the context-bloat problem | Medium | High | Keep hydrated memory as summaries plus sources, not raw note dumps. |
| Contributors assume `/memories/*` paths are ordinary repo files | Medium | Medium | Document the editor-managed limitation clearly in runbooks and setup docs. |
| Run-artifact activation becomes noisy on small tasks | Low | Medium | Activate it by policy only for multi-surface or multi-subtask non-trivial work. |

---

## Breaking changes
No product behavior changes are intended.
The packet schema becomes stricter for repo-local agent workflow examples and prompt contracts.

---

## Testing strategy
- **Integration:** validate the richer packet schema and all example packets through
  `python scripts/agent/sync_agent_platform.py --check`
- **Integration:** validate the new brownfield run artifact through the same sync check
- **Integration:** inspect the orchestrator, prompts, and docs together to confirm the same run-artifact activation and
  memory-hydration policy
- **E2E:** no product browser flow is required for this metadata-only phase
- **Security:** confirm hydrated memory fields use summaries and source references rather than raw sensitive content

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] The packet schema supports task classification, active run-artifact state, and hydrated semantic-memory sources
- [x] The workflow manifest records both run-artifact activation policy and memory-hydration scope policy
- [x] The orchestrator and the relevant prompt wrappers use the richer packet and active run-artifact contract
- [x] A validated brownfield context-packet example exists
- [x] A validated brownfield run-artifact example exists
- [x] The sync validation script checks the richer packet fields and the new examples
- [x] `AGENTS.md`, `docs/runbooks/agent-mode.md`, and `docs/copilot-setup.md` describe the same activation and
      hydration behavior without overclaiming editor capabilities