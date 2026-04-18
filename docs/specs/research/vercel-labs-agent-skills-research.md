# Research Brief: Vercel Labs Agent Skills and Runtime Concepts

## Questions asked
1. Which skills, concepts, and runtime patterns from the Vercel Labs ecosystem are missing from this repository's agent architecture?
2. Which of those patterns materially improve quality, robustness, and thoroughness for building battle-tested codebases?
3. Which concepts are safe to adopt now in a repo-local architecture, and which require a larger runtime shift?

## Sources scanned
- https://github.com/vercel-labs
- https://github.com/vercel-labs/skills
- https://github.com/vercel-labs/agent-skills
- https://github.com/vercel-labs/agent-browser
- https://github.com/vercel-labs/dev3000
- https://github.com/vercel-labs/portless
- https://github.com/vercel-labs/just-bash
- https://github.com/vercel-labs/github-tools
- https://github.com/vercel-labs/claude-managed-agents-starter
- Local workflow surfaces:
  - [AGENTS.md](AGENTS.md)
  - [.github/agents/orchestrator.agent.md](.github/agents/orchestrator.agent.md)
  - [.github/skills](.github/skills)
  - [.github/prompts](.github/prompts)
  - [.github/workflows/pr-quality.yml](.github/workflows/pr-quality.yml)
  - [scripts/agent/pretool_approval_policy.py](scripts/agent/pretool_approval_policy.py)

## Highest-signal sources analysed deeply
1. `vercel-labs/skills`
2. `vercel-labs/agent-skills`
3. `vercel-labs/agent-browser`
4. `vercel-labs/dev3000`
5. `vercel-labs/github-tools`
6. `vercel-labs/just-bash`
7. `vercel-labs/portless`
8. `vercel-labs/claude-managed-agents-starter`

## Verified findings
- `vercel-labs/skills` treats skills as a portable ecosystem with installation, discovery, updates, internal/private visibility, and compatibility across many coding agents.
- `vercel-labs/agent-skills` packages skills as more than prose: skills can include helper scripts and supporting references, and the collection includes reusable frontend quality skills such as `react-best-practices`, `web-design-guidelines`, and `composition-patterns`.
- `vercel-labs/agent-browser` provides a browser-native agent workflow with deterministic refs, session isolation, saved state, domain allowlists, action policy files, annotated screenshots, traces, console/error capture, HAR capture, and a real-time dashboard.
- `vercel-labs/dev3000` focuses on AI-readable debugging evidence: timestamped timelines of server logs, browser console output, network requests, screenshots, and interactions.
- `vercel-labs/github-tools` exposes GitHub tools through scoped presets, per-tool approval controls, semantic tool selection, and durable workflow execution.
- `vercel-labs/just-bash` demonstrates a safer shell model with filesystem scoping, no-network-by-default execution, allowlisted network access, execution limits, and optional language runtimes gated behind explicit configuration.
- `vercel-labs/portless` solves a real agent ergonomics problem: stable, named local URLs across worktrees and local environments.
- `vercel-labs/claude-managed-agents-starter` shows the architectural jump from repo-local prompts to durable managed agents backed by workflow infrastructure and encrypted credentials.

## Inference
The Vercel Labs ecosystem highlights four gaps in the current repository more sharply than the earlier benchmark pass:

1. Skill packaging gap
   - Current skills are prose-only and not treated as installable capability modules.
   - Missing: scripts, references, metadata, registry/discovery, experimental/internal status.

2. Evidence capture gap
   - Current debugging guidance is weak compared with timeline-first tools like `dev3000` and `agent-browser`.
   - Missing: a reusable debugging-evidence skill for browser/server/network/screenshot capture.

3. Capability routing gap
   - Current agents declare broad tool access directly in markdown.
   - Missing: scoped tool presets, capability classes, approval-aware routing, and minimal tool exposure per task type.

4. Safe runtime gap
   - Current workflow relies on editor approval and prompt discipline.
   - Missing: sandboxed shell concepts, execution limits, browser action policy, session state TTL, and durable background run concepts.

## Missing skills and concepts for this repository
- Frontend best-practices audit skill
  - Purpose: catch performance, architecture, accessibility, composition, and UX issues earlier than the current `visual-qa` skill.
  - Closest Vercel source: `react-best-practices`, `web-design-guidelines`, `composition-patterns`.
- Debug timeline capture skill
  - Purpose: capture structured reproduction evidence for bugs, flaky tests, and launch blockers.
  - Closest Vercel source: `dev3000`, `agent-browser`.
- Capability registry / tool preset model
  - Purpose: expose only the smallest useful tool surface per task class.
  - Closest Vercel source: `github-tools` presets and `toolpick` integration.
- Browser automation safety model
  - Purpose: formalize session handling, action gating, domain restrictions, screenshot refs, and trace capture.
  - Closest Vercel source: `agent-browser`.
- Sandboxed shell execution model
  - Purpose: limit command blast radius for agent automation.
  - Closest Vercel source: `just-bash`.
- Stable local URL convention
  - Purpose: remove environment ambiguity in browser-driven tasks, especially across worktrees.
  - Closest Vercel source: `portless`.
- Durable background agent architecture
  - Purpose: support long-running or concurrent tasks safely.
  - Closest Vercel source: `claude-managed-agents-starter` and durable `github-tools` workflows.

## What can be adopted now
- Add new repo-local skills for frontend best practices and debug timeline capture.
- Add a canonical workflow manifest that expresses capability routing and skill triggers.
- Harden approval guidance for remote-write and high-impact tool surfaces.
- Improve PR/spec traceability.
- Document stable local URL guidance as a recommendation, not a hard dependency.

## What should remain future work
- Full managed background agents.
- A real sandboxed execution runtime.
- Durable workflow execution with crash-safe step replay.
- Browser session dashboards and remote providers.
- Automatic skill install/update tooling in this repo.

## Constraints this adds to the local architecture
- Do not claim sandbox guarantees the repo does not actually implement.
- Do not add browser or shell skills that imply capabilities unavailable in the current workspace without clearly marking them as procedural guidance only.
- Prefer repo-local manifest and skill hardening now; defer managed-agent runtime work to a later spec.

## Open questions
1. Should this repository adopt the open `skills` CLI workflow directly, or remain native to `.github/skills/` only?
2. Is stable local URL tooling worth standardizing here, or should it remain optional guidance?
3. Does this repository want eventual background managed agents, or is the target still an IDE-first orchestration model?
4. Should shell execution remain editor-native, or should a future phase introduce a safer constrained shell runner?