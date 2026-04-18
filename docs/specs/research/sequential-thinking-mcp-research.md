# Sequential Thinking MCP Research

**Date:** 2026-04-12
**Author:** @github-copilot
**Topic:** Sequential Thinking MCP integration constraints for the repo's single-entry workflow

---

## Questions asked
- What MCP server contract does the public Sequential Thinking repo expose?
- How should the repo wire that server into VS Code workspace MCP config?
- Does the tool surface change the least-privilege story for review-only or research-only entrypoints?
- What should be pinned to reduce supply-chain and drift risk?

## Sources scanned
- https://github.com/arben-adm/mcp-sequential-thinking
- https://github.com/arben-adm/mcp-sequential-thinking/commits/master
- `docs/specs/research/vscode-custom-agent-tooling-research.md`

## Highest-signal findings

### Verified
- The public repo `arben-adm/mcp-sequential-thinking` documents VS Code workspace integration through
  `.vscode/mcp.json`.
- The documented tool surface includes `process_thought`, `generate_summary`, `clear_history`,
  `export_session`, and `import_session`.
- The server supports `uv run` and `uvx` launch paths, so a repo-local install is not required.
- The public README explicitly describes persistent session history and JSON import/export behavior.
- The latest visible default-branch commit on the public commits page at time of review is
  `f3727d858769495befaf56e6b4f2e84509dc6456` from 2026-03-06.
- The repo's existing VS Code tooling research confirms that prompt-file tool lists override agent tools
  and that MCP servers should be referenced as `<server-name>/*`.

### Inference
- Because this MCP surface can export and import session files, it is not a purely read-only capability.
- The safest first rollout in this repo is to expose it only on the default orchestrator and selected
  execution-oriented prompt wrappers rather than on review-only and research-only wrappers.
- The workflow should treat the MCP session as scratch space and carry only generated summaries forward.

## Constraints this adds to the local workflow change
- Pin the workspace MCP server to commit `f3727d858769495befaf56e6b4f2e84509dc6456` instead of a floating ref.
- Treat the server as optional workspace tooling that depends on `uvx` availability outside repo markdown.
- Do not treat Sequential Thinking session history as durable repo memory.
- Avoid routine `export_session` and `import_session` use in the default workflow.
- Because prompt tool lists override agent tools, update every selected prompt wrapper explicitly.

## Decision impact
- Add a pinned `sequential-thinking` server entry to `.vscode/mcp.json`.
- Expose `sequential-thinking/*` on the orchestrator and selected execution-oriented prompt wrappers.
- Add guardrails so only summary-level outcomes survive into the context packet or run artifact.