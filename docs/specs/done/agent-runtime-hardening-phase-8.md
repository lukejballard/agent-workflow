# Feature: Agent Runtime Hardening Phase 8

**Status:** Done
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** `docs/specs/done/agent-runtime-hardening-phase-7.md`

---

## Problem
The repository's custom agents and prompt wrappers still rely on stale VS Code customization conventions.

Prompt files use `mode: agent` instead of the current `agent:` field, and the tool lists do not
consistently expose the current built-in execution and browser tool sets. In practice, that can
leave a session with local file access while dropping the intended terminal execution and browser
automation surfaces.

If this remains unresolved, contributors can inspect and edit the app but still lose the local
verification and UI automation workflow that the repo docs, specs, and test expectations assume.

## Success criteria
This phase is successful when:
- prompt wrappers explicitly target the repo's `orchestrator` custom agent
- execution-oriented workflows expose current local execution tooling consistently
- browser-capable workflows expose integrated browser automation where the workflow expects UI verification
- least-privilege specialist and review paths stay constrained
- the workflow manifest, setup guide, and runbook describe the same capability model honestly

---

## Requirements

### Functional
- [x] Update custom-agent frontmatter to current tool declarations for local read/search/edit access and execution where appropriate.
- [x] Update prompt wrappers to use `agent: orchestrator` instead of stale `mode: agent` frontmatter.
- [x] Add built-in browser automation to the orchestrator, QA path, and relevant prompt wrappers that may need UI verification.
- [x] Keep read-only and review-only entrypoints least-privilege.
- [x] Align the workflow manifest and contributor docs with the effective capability routing after the frontmatter change.

### Non-functional
- [x] Security: do not widen destructive or remote-write approvals; browser and execution access remain subject to editor approvals and existing hooks.
- [x] Reliability: use the current VS Code customization syntax documented by the official docs.
- [x] Documentation: update setup and runbook guidance so capability claims match the actual repo customizations.
- [x] Traceability: capture the external VS Code customization guidance in a reusable research brief.

---

## Affected components
- `docs/specs/active/agent-runtime-hardening-phase-8.md`
- `docs/specs/research/vscode-custom-agent-tooling-research.md`
- `.github/agents/orchestrator.agent.md`
- `.github/agents/implementer.agent.md`
- `.github/agents/qa.agent.md`
- `.github/agents/cleanup.agent.md`
- `.github/agents/researcher.agent.md`
- `.github/agents/reviewer.agent.md`
- `.github/agents/planner.agent.md`
- `.github/agents/analyst.agent.md`
- `.github/prompts/single-entry-workflow.prompt.md`
- `.github/prompts/brownfield-improve.prompt.md`
- `.github/prompts/bugfix-workflow.prompt.md`
- `.github/prompts/greenfield-feature.prompt.md`
- `.github/prompts/generate-tests.prompt.md`
- `.github/prompts/research.prompt.md`
- `.github/prompts/review-code.prompt.md`
- `.github/prompts/launch-readiness-audit.prompt.md`
- `.github/agent-platform/workflow-manifest.json`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
This phase uses the official VS Code customization and tools documentation.
See `docs/specs/research/vscode-custom-agent-tooling-research.md`.

The external guidance materially changes the local implementation because it confirms:
- prompt files should use `agent:`
- built-in execution and browser tool sets should be declared explicitly
- MCP server tool lists should use wildcard server references
- prompt tool lists override agent tool lists

---

## Documentation impact
Update the setup guide and runbook so contributors know:
- prompt wrappers explicitly target the repo's `orchestrator` custom agent
- execution-oriented entrypoints expose the current execution tool surface for local verification
- browser automation is available for UI-sensitive workflows when the editor browser tools are enabled
- approval behavior is still controlled by editor settings and hooks, not by markdown instructions alone

---

## Architecture plan
Modernize the repo customizations rather than adding another workaround layer.

Preferred approach:
- use current built-in tool-set names for local repo work: `read`, `search`, `edit`, `execute`, and `browser`
- use wildcard MCP references for external services already configured in the workspace: `github/*` and `fetch/*`
- keep browser automation focused on the default orchestrator, QA path, and prompt wrappers that plausibly need UI verification
- leave read-only specialist paths constrained to read/search and external context only where appropriate

Alternative considered:
- add more prose to the docs without changing the frontmatter

Why rejected:
- it would preserve the actual capability drift and only make the mismatch more explicit
- the underlying problem is stale customization syntax, not missing contributor explanation alone

---

## API design

No product runtime API changes.
This phase changes workflow metadata, prompt frontmatter, and contributor docs only.

---

## Data model changes

No application schema changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: restore the previous agent and prompt frontmatter, manifest entries, and docs if a compatibility issue is found.
- Breaking change? No product-facing breaking change. Contributor tooling metadata becomes more explicit and current.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Prompt files override agent tools | Update both the prompt wrappers and the custom-agent frontmatter |
| Browser chat tools are disabled in the editor | Keep docs honest that browser automation depends on `workbench.browser.enableChatTools` |
| A tool is unavailable in a given session | Rely on the platform behavior that unavailable tools are ignored rather than causing parse failure |
| Review-only or planning-only workflows accidentally gain execution capability | Keep those agents on read/search-only tool declarations |
| MCP server names drift from the workspace config | Use the current configured server names and wildcard syntax documented by VS Code |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Capability scope widens more than intended | Low | Medium | Keep browser and execution access limited to the orchestrator, QA, and execution-oriented prompts/agents |
| Docs still describe stale behavior after the patch | Medium | Medium | Update `docs/runbooks/agent-mode.md` and `docs/copilot-setup.md` in the same change set |
| A current tool name differs from the repo's existing assumptions | Low | High | Base the change on the current official VS Code customization docs and keep the patch focused |

---

## Breaking changes
No product behavior changes are intended.
This phase only changes contributor workflow customizations and the documentation that describes them.

---

## Testing strategy
- **Integration:** inspect all changed agent and prompt frontmatter for consistent current field names and tool declarations
- **Integration:** verify the workflow manifest and contributor docs match the same capability story
- **Integration:** run `python scripts/agent/sync_agent_platform.py --check` if the local execution environment permits; this phase passed that check in the configured repo virtual environment
- **E2E:** no product Playwright flow is required for this metadata-only change
- **Security:** confirm the approval hook and workspace approval settings remain unchanged

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Prompt wrappers use `agent: orchestrator` where they are intended to wrap the default orchestrator workflow
- [x] Execution-oriented custom agents expose current local execution tooling consistently
- [x] Browser-capable workflows expose built-in browser automation where relevant
- [x] Review-only and planning-only paths remain constrained
- [x] Workflow manifest capability routing reflects the effective browser and execution story
- [x] Setup and runbook docs match the implemented customization behavior
- [x] Official-doc research brief is saved and referenced by this spec
- [x] Metadata validation is run if the local environment permits it, or the verification gap is called out explicitly