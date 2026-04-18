# VS Code Custom Agent Tooling Research

**Date:** 2026-04-12
**Author:** @github-copilot
**Topic:** Current VS Code custom agent and prompt frontmatter for tools and agent selection

---

## Questions asked
- What frontmatter field should prompt files use to target a custom agent?
- How should current VS Code customizations declare built-in execution and browser tools?
- How should MCP servers be referenced from custom agent and prompt tool lists?
- Does prompt frontmatter override custom-agent tool lists?

## Sources scanned
- https://code.visualstudio.com/docs/copilot/customization/custom-agents
- https://code.visualstudio.com/docs/copilot/customization/prompt-files
- https://code.visualstudio.com/docs/copilot/agents/agent-tools
- https://code.visualstudio.com/docs/copilot/reference/copilot-vscode-features

## Highest-signal findings

### Verified
- Prompt files use the `agent` frontmatter field to select a custom agent. `mode` is not part of the current prompt-file frontmatter described by the VS Code docs.
- Prompt-file `tools` take precedence over tools declared by the referenced custom agent.
- MCP servers should be referenced with the `<server-name>/*` form when the intent is to expose the full server tool surface.
- Current VS Code built-in tool sets include `execute` for local command execution and `browser` for integrated-browser automation.
- Browser chat tools are gated by the editor setting `workbench.browser.enableChatTools`.
- If a configured tool is unavailable, VS Code ignores it rather than failing the customization entirely.

### Inference
- Repositories that still use stale prompt frontmatter such as `mode: agent`, or ambiguous tool names that do not match current built-in tool-set names, can silently lose the intended tool surface and fall back to a narrower session capability set.
- For this repository, the safest compatibility fix is to use current built-in tool-set names for local repo work (`read`, `search`, `edit`, `execute`, `browser`) and wildcard MCP references for external services (`github/*`, `fetch/*`).

## Constraints this adds to the local workflow change
- Prompt wrappers should explicitly target the repo's `orchestrator` custom agent with `agent: orchestrator`.
- Execution-oriented workflows should expose `execute`, not legacy terminal-only naming.
- Browser-capable workflows should expose `browser` only where the workflow genuinely needs UI verification.
- Contributor docs should describe browser automation as conditional on the editor setting and approval model, not as unconditional capability.

## Decision impact
- Update repo prompt and agent frontmatter to current VS Code syntax.
- Align workflow docs with the browser and execution capability model actually exposed by those customizations.