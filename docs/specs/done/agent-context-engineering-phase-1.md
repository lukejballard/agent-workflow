# Feature: Agent Context Engineering Phase 1

**Status:** Implemented (superseded by docs/specs/done/agent-context-engineering-phase-2.md)
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** N/A

---

## Problem
The repo's agent architecture has a solid phase model, but its working context is still mostly passed as broad prose.
The default orchestrator and prompt wrappers tell the model what to do, yet they do not define a typed step packet,
an explicit memory hierarchy, or a context-budget gate. As a result, the architecture is vulnerable to context rot,
goal drift, and stale tool output lingering longer than one sub-task.

This is most visible in the prompt layer, where wrappers still end in freeform fields such as `Context: {{context}}`,
and in the agent layer, where the orchestrator describes phases but not a bounded per-step context contract.
If this remains unresolved, long or ambiguous tasks will keep accumulating narrative state faster than the architecture
can compress or route it safely.

## Success criteria
This phase is successful when the default orchestration path uses a typed context packet, a bounded rolling-summary
policy, explicit atomic sub-task contracts, and structured task telemetry without forcing a full agent-platform rewrite.

---

## Requirements

### Functional
- [x] Add a canonical `ContextPacket` schema under `.github/agent-platform/` for current-step context passing.
- [x] Add an example `ContextPacket` instance that demonstrates goal anchoring, current-step routing, working memory,
      episodic memory, semantic-memory retrieval policy, and a context-health gate.
- [x] Extend the workflow manifest with explicit context-engineering policy metadata: memory tiers, context budget,
      stale-output trimming, sub-task decomposition, ambiguity handling, and task-level observability.
- [x] Update the default orchestrator instructions so non-trivial work is decomposed into an atomic DAG of sub-tasks,
      each with an input contract, output contract, done condition, and local scratchpad.
- [x] Update the default prompt wrappers so they stop relying on freeform trailing context alone and instead inject
      XML- or JSON-delimited context sections with a goal anchor and typed current-step contract.
- [x] Extend the run-artifact schema to support structured sub-task telemetry for context usage and completion status.
- [x] Update the local validation tooling so the new context packet artifact and the extended run-artifact examples are
      checked by `python scripts/agent/sync_agent_platform.py --check`.
- [x] Update workflow docs so contributors understand the phase-1 context hierarchy and the incremental rollout order.

### Non-functional
- [x] Performance: the default context-health gate should target a soft ceiling of 70% context utilization before the
      architecture requires trimming or compression.
- [x] Security: the new packet and telemetry structures must not require storing secrets or raw sensitive tool output in
      persistent summaries.
- [x] Reliability: completed sub-task state must be compressible into episodic memory without losing the top-level goal,
      active constraints, or verification results.
- [x] Observability: each sub-task can emit structured telemetry including task id, tokens in, tokens out,
      context size, context utilization, and completion status.

---

## Affected components
- `docs/specs/done/agent-context-engineering-phase-1.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agent-platform/workflow-manifest.json`
- `.github/agent-platform/context-packet.schema.json`
- `.github/agent-platform/run-artifact-schema.json`
- `.github/agent-platform/examples/context-packet.example.json`
- `.github/agent-platform/examples/bugfix-run-artifact.json`
- `.github/agent-platform/examples/review-run-artifact.json`
- `.github/agents/orchestrator.agent.md`
- `.github/prompts/*.prompt.md`
- `scripts/agent/sync_agent_platform.py`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
No external context materially changes this phase.
This work is a brownfield hardening pass over the repository's existing agent-platform metadata,
prompt wrappers, and contributor docs.

---

## Documentation impact
Update the root agent guide, the setup guide, and the runbook so they describe the same context model:
- the orchestrator keeps only step-local working memory live
- completed work is compressed into episodic memory
- semantic memory is loaded on demand rather than by default
- context-health trimming is a gate before continuing long multi-step work
- prompt wrappers pass a structured current-step packet instead of an unbounded freeform blob

---

## Architecture plan
Implement this in one incremental phase rather than trying to build a full autonomous memory runtime.

Preferred approach:
- add a canonical prompt-facing `ContextPacket` schema and example
- record the policy in `workflow-manifest.json` so prompts, agents, and docs all point at one metadata source
- extend `run-artifact-schema.json` with optional task-level telemetry instead of inventing a separate log format
- update only the default orchestrator and prompt wrappers first, keeping specialist-agent expansion as a later phase

Alternative considered:
- implement deterministic context trimming through hooks or editor-side automation first

Why rejected for this phase:
- the repo cannot guarantee editor-managed token estimates or pre-LLM hooks from `.github/` alone
- a prompt and metadata contract can be introduced immediately and validated locally
- it is safer to make the architecture explicit before attempting stronger automation

---

## API design

No product runtime API changes.
This phase changes agent-platform metadata, prompt contracts, documentation, and local validation logic only.

---

## Data model changes

No application database changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the context packet artifact, restore the prior prompt and agent guidance, and revert the
  run-artifact schema additions.
- Breaking change? No product-facing breaking change. Contributor workflow contracts become more structured.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Trivial request with no decomposition needed | Allow the orchestrator to compress directly to one current-step packet and skip a large task DAG. |
| Long-running task accumulates large tool output | Drop raw output after the active step and compress it into episodic memory plus evidence refs. |
| User provides vague or noisy context | Build the first packet around the goal anchor and the minimum input contract needed for the next sub-task. |
| Current step needs repo facts not already in working memory | Load semantic memory on demand rather than preloading all repository guidance. |
| A sub-task cannot be completed in one LLM call | Split it into smaller DAG nodes before continuing. |
| Context budget cannot be estimated precisely | Use qualitative context-health status and utilization estimates rather than claiming deterministic token counts. |
| Specialist agents are used directly | Leave them available, but scope phase-1 hardening to the default orchestrator path and prompt wrappers first. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The new prompt contract becomes more verbose than the old one | Medium | Medium | Keep the packet minimal and load the schema on demand rather than adding it to the default read order. |
| Contributors treat the packet as a log sink and keep too much state in it | Medium | High | Document stale-output trimming and local scratchpad replacement explicitly. |
| Task-level telemetry implies precision the platform cannot guarantee | Medium | Medium | Mark token and context utilization fields as optional, estimated observability rather than deterministic runtime counters. |
| Docs and manifest drift again | Medium | High | Update docs and local validation in the same change set and keep the workflow manifest authoritative. |

---

## Breaking changes
No product behavior changes are intended.
This phase changes how contributors and prompt wrappers structure agent context for multi-step work.

---

## Testing strategy
- **Integration:** validate the new context packet example and updated run-artifact examples through
  `python scripts/agent/sync_agent_platform.py --check`
- **Integration:** inspect the orchestrator and prompt wrappers together to confirm the same goal anchor,
  memory tiers, context-health gate, and task decomposition story
- **Integration:** confirm docs describe the same canonical metadata and rollout sequence as the workflow manifest
- **E2E:** no product browser flow is required for this metadata-only phase
- **Security:** confirm no docs or example artifacts encourage storing raw secrets or long-lived sensitive tool output

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] A canonical `ContextPacket` schema exists under `.github/agent-platform/`
- [x] A validated context packet example exists and demonstrates the phase-1 packet shape
- [x] The workflow manifest records the context-engineering policy and references the new packet artifact
- [x] The orchestrator instructions define a goal anchor, context-health gate, memory hierarchy, and atomic sub-task DAG policy
- [x] The default prompt wrappers use structured delimiters and typed current-step context instead of unbounded freeform context alone
- [x] The run-artifact schema supports optional task-level context telemetry
- [x] The sync validation script checks the new packet artifact and the updated run-artifact examples
- [x] `AGENTS.md`, `.github/copilot-instructions.md`, `docs/runbooks/agent-mode.md`, and `docs/copilot-setup.md` stay aligned enough to avoid workflow drift
- [x] The rollout remains incremental: default orchestrator and wrappers first, specialist-agent expansion later