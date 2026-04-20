# Feature: Agent Runtime Hardening Phase 9

**Status:** Done
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** `docs/specs/active/agent-runtime-hardening-phase-8.md`

---

## Problem
The repo's single-entry workflow already has bounded context, explicit critique, and verification phases,
but it lacks a structured-reasoning MCP tool for the hardest planning and investigation paths.

Adding Sequential Thinking informally would create three problems:
- the workspace would depend on an unpinned external server
- prompt wrappers that override tools would silently lose access to the new MCP surface
- persistent or exportable thought history could drift into the workflow without explicit guardrails

Without a controlled integration, the repo gains another optional tool but not a harder workflow.

## Success criteria
This phase is successful when:
- the workspace config exposes Sequential Thinking through a pinned MCP server entry
- the default orchestrator and selected execution-oriented prompt wrappers can access the MCP tool surface
- review-only and research-only wrappers remain least-privilege unless the repo explicitly widens them later
- workflow metadata and docs explain when the MCP is available and what boundaries still apply
- the workflow adds explicit guardrails so only summary-level outcomes, not raw session logs, survive into repo artifacts

---

## Requirements

### Functional
- [x] Add a pinned `sequential-thinking` server entry to `.vscode/mcp.json` with no committed secrets.
- [x] Expose `sequential-thinking/*` on the default orchestrator agent.
- [x] Expose `sequential-thinking/*` on the default single-entry, greenfield, brownfield, bugfix,
      test-generation, and launch-readiness prompt wrappers whose tool lists override agent defaults.
- [x] Keep research-only and review-only prompt wrappers least-privilege for this phase.
- [x] Save a reusable research brief that captures the external Sequential Thinking MCP contract and pinning decision.
- [x] Add a workflow skill that governs when Sequential Thinking should be used and what summary-only retention rules apply.
- [x] Update the canonical workflow manifest and skill registry so the new skill is discoverable through trigger tags.
- [x] Add summary-only structured-reasoning capture to the context-packet contract instead of treating MCP session state as durable memory.

### Non-functional
- [x] Security: pin the external server to a known commit and forbid routine export/import use in the default workflow.
- [x] Reliability: document the dependency on `uvx` or equivalent local tooling honestly.
- [x] Documentation: update workflow and setup guidance in the same change set as the metadata.
- [x] Traceability: keep the active spec, research brief, manifest, and docs aligned.

---

## Affected components
- `docs/specs/active/agent-runtime-hardening-phase-9.md`
- `docs/specs/research/sequential-thinking-mcp-research.md`
- `.vscode/mcp.json`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agents/orchestrator.agent.md`
- `.github/prompts/single-entry-workflow.prompt.md`
- `.github/prompts/greenfield-feature.prompt.md`
- `.github/prompts/brownfield-improve.prompt.md`
- `.github/prompts/bugfix-workflow.prompt.md`
- `.github/prompts/generate-tests.prompt.md`
- `.github/prompts/launch-readiness-audit.prompt.md`
- `.github/agent-platform/workflow-manifest.json`
- `.github/agent-platform/skill-registry.json`
- `.github/agent-platform/context-packet.schema.json`
- `.github/skills/`
- `docs/copilot-setup.md`
- `docs/runbooks/agent-mode.md`

---

## External context
This phase uses external context from the public Sequential Thinking MCP repository and the existing
VS Code customization research already stored in this repo.

See `docs/specs/research/sequential-thinking-mcp-research.md`.

The external guidance materially changes the local design because it confirms:
- the server is configured through `.vscode/mcp.json`
- the public tool surface includes persistent and export/import-capable operations
- the safest repo integration should pin the dependency and treat MCP history as scratch state, not repo memory

---

## Documentation impact
Update the setup guide and runbook so contributors know:
- the workspace now includes a Sequential Thinking MCP server
- only the orchestrator and selected execution-oriented prompt wrappers expose it by default
- prompt tool lists still override agent tool lists
- `uvx` availability and editor MCP support remain platform dependencies outside markdown alone

---

## Architecture plan
Roll this out in two steps.

Preferred approach:
1. Add the pinned MCP server entry and expose it on the default orchestrator path plus the selected
   execution-oriented prompt wrappers.
2. Add workflow guardrails so the tool is used only for ambiguous or high-complexity reasoning, and
   only summary-level results flow back into the context packet or run artifact.

Alternative considered:
- configure the MCP server only and rely on ad hoc user prompting

Why rejected:
- prompt wrappers that override agent tools would silently miss the capability
- the repo would gain persistence-capable reasoning state without documented constraints
- the workflow would remain enhanced only accidentally, not systematically

---

## API design

No product runtime API changes.
This phase changes workspace MCP configuration, workflow metadata, prompt frontmatter, and docs.

---

## Data model changes

No product schema changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the MCP server entry, tool exposure, skill, and packet schema extension if the
  dependency proves unstable or too permissive.
- Breaking change? No product-facing breaking change. Contributor workflow gains an optional reasoning tool.

---

## Edge cases

| Edge case | Handling |
|---|---|
| `uvx` is unavailable on a contributor machine | Keep docs honest that MCP availability depends on local tooling outside repo markdown. |
| Prompt wrappers override agent tools | Add the MCP tool to the selected wrappers explicitly. |
| Review-only or research-only workflows widen unexpectedly | Keep those wrappers unchanged for this phase. |
| Sequential Thinking session state persists between uses | Add clear-before and clear-after guardrails in the workflow skill. |
| Raw thought logs leak into repo artifacts | Restrict retained output to summary-level packet fields only. |
| The public repo moves after integration | Pin the dependency to a commit instead of a floating branch. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Unpinned external dependency drifts under us | Medium | High | Pin the MCP server to a known commit in `.vscode/mcp.json`. |
| Persistent reasoning state is mistaken for repo memory | Medium | High | Add summary-only retention rules and explicit clear-history guidance. |
| Least-privilege review and research workflows widen too early | Low | Medium | Limit prompt exposure to the selected execution-oriented wrappers. |
| Docs overclaim what the editor can do | Medium | Medium | Separate in-repo config from editor/tooling prerequisites. |

---

## Breaking changes
No product behavior changes are intended.
This phase changes contributor workflow metadata and documentation only.

---

## Testing strategy
- **Integration:** run `python scripts/agent/sync_agent_platform.py --check` after each phase.
- **Integration:** validate changed JSON and markdown files through the editor error surface.
- **Integration:** verify `uvx` availability locally if the environment permits, and document the gap if not.
- **Security:** confirm the MCP entry is pinned and that review-only / research-only wrappers remain constrained.
- **Docs:** verify `AGENTS.md`, `.github/copilot-instructions.md`, `docs/copilot-setup.md`, and
  `docs/runbooks/agent-mode.md` describe the same availability story.

### Verification completed
- `python scripts/agent/sync_agent_platform.py --check` passed after phase 1 and again after phase 2.
- `python scripts/agent/sync_agent_platform.py --write` reported the generated agent-platform artifacts were already up to date.
- Editor diagnostics reported no errors for the changed JSON, markdown, schema, and prompt files.
- Local prerequisite check confirmed `uvx` is on `PATH` and `.github/copilot-instructions.md` remains under the 4,000-character limit.
- Prompt exposure search confirmed `sequential-thinking/*` is present only on the intended six prompt wrappers and the orchestrator agent.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Sequential Thinking MCP is configured in `.vscode/mcp.json` with a pinned commit
- [x] The default orchestrator exposes `sequential-thinking/*`
- [x] Selected execution-oriented prompt wrappers expose `sequential-thinking/*`
- [x] Review-only and research-only wrappers stay constrained
- [x] A reusable research brief captures the external MCP contract and pinning decision
- [x] A dedicated guardrail skill exists for Sequential Thinking usage and retention
- [x] Workflow manifest and skill registry include the new skill and trigger routing
- [x] Context-packet rules only retain summary-level structured-reasoning output
- [x] Setup and runbook docs match the implemented capability and boundary story
- [x] Metadata validation passes after the change