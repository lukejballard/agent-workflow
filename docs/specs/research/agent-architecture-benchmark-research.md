# Research Brief: Production Agent Architecture Benchmarks

## Questions asked
1. What patterns do current production coding-agent systems use for task decomposition, tool use, verification, and human control?
2. What do GitHub Copilot-style agent systems do for reusable capabilities, memory, and session management?
3. What do OpenHands and Devin-style systems do for long-running sessions, approval modes, and scaling beyond a single chat loop?
4. What does Aider do for large-repo context handling, plan-to-edit separation, and test/lint repair loops?
5. Which of those patterns should shape future refactors of this repository's agent architecture?

## Sources scanned
- GitHub Copilot docs: agent skills, agentic memory, custom agents, agent management
- OpenHands docs: SDK overview, CLI runtime
- Aider docs: chat modes, repository map, lint/test loop
- Devin docs: task sizing, managed parallel sessions, review/auto-fix, session insights
- Local workflow surfaces:
  - [AGENTS.md](AGENTS.md)
  - [.github/agents/orchestrator.agent.md](.github/agents/orchestrator.agent.md)
  - [.github/skills](.github/skills)
  - [.github/prompts](.github/prompts)
  - [.vscode/mcp.json](.vscode/mcp.json)
  - [docs/runbooks/agent-mode.md](docs/runbooks/agent-mode.md)

## Highest-signal sources analysed deeply
1. GitHub Copilot: agent skills
   - https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
2. GitHub Copilot: agentic memory
   - https://docs.github.com/en/copilot/concepts/agents/copilot-memory
3. GitHub Copilot: agent management
   - https://docs.github.com/en/copilot/concepts/agents/cloud-agent/agent-management
4. OpenHands: Software Agent SDK and CLI
   - https://docs.openhands.dev/sdk
   - https://docs.openhands.dev/openhands/usage/run-openhands/cli-mode
5. Aider: repository map, chat modes, lint/test loop
   - https://aider.chat/docs/repomap.html
   - https://aider.chat/docs/usage/modes.html
   - https://aider.chat/docs/usage/lint-test.html
6. Devin: task sizing, managed sessions, review/auto-fix, session insights
   - https://docs.devin.ai/essential-guidelines/when-to-use-devin

## Verified findings
- GitHub Copilot treats skills as a formal packaging model with instructions, scripts, and resources, not just prose. Skills are an open standard and can exist at project and personal scope.
- GitHub Copilot agentic memory is repository-scoped, citation-backed, validated against the current codebase before reuse, and automatically expired to reduce staleness.
- GitHub Copilot provides centralized agent session management, including multiple concurrent sessions, live logs, and mid-session steering.
- OpenHands positions its SDK as a composable runtime with code-defined agents, tool adapters, automatic context compression, and a production-ready agent server.
- OpenHands CLI exposes explicit confirmation modes, pause/resume controls, and resumable conversations.
- Aider uses a repository map with symbol-level compression and graph-based relevance ranking to stay effective on larger repositories.
- Aider separates discussion and editing through ask/code modes and can optionally use an architect/editor split.
- Aider can automatically run lint and test commands after edits and feed failures back into the repair loop.
- Devin emphasizes strong success criteria, session sizing, parallel task execution, browser plus shell plus IDE verification, and automated iteration on review and CI failures.

## Inference
- Modern coding-agent systems are converging on a few durable patterns:
  - A thin default entry point backed by structured capabilities instead of many free-form personas.
  - Dynamic context compression or indexing for large repositories.
  - Persistent but validated memory with provenance and expiry.
  - Session management outside the prompt itself: logs, resume, steering, concurrency, and review loops.
  - Verification that is integrated into the execution loop, not only documented as a best practice.
  - Capability and approval controls that operate at the runtime layer, not only in prompt text.

## Constraints this adds to the local architecture
- Keep the single-entry orchestrator, but move more behavior out of prose and into structured manifests, tool policies, and executable verification hooks.
- Introduce a repository map or equivalent context index before claiming the architecture scales to very large codebases.
- Treat durable memory as a validated store with citations, recency, and explicit scope boundaries.
- Normalize agent capability declarations so tool access matches the documented workflow, especially for Playwright, Tavily, and any remote-write GitHub actions.
- Add session artifacts or logs that make long-running work resumable and auditable.
- Integrate verification scripts directly into the execution loop with bounded retry and repair behavior.
- Prefer bounded, human-steerable autonomy over open-ended recursive loops.

## Open questions
1. Should the next refactor stay repo-local and markdown-driven, or introduce a code-defined orchestrator runtime and manifests?
2. How much autonomy is actually desired for this repository: assisted IDE workflow, background PR generation, or both?
3. Should long-term memory live inside the repository, in editor-managed memory, or in an external service with citations and TTL?
4. Is parallel subtask orchestration worth the added complexity before a context index and evaluation harness exist?
5. Which agent workflow guarantees should be blocking in CI versus advisory in docs and scheduled audits?
