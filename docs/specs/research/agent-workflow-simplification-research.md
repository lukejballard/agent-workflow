# Research Brief: Agent Workflow Simplification Constraints

## Questions asked
1. What patterns do Anthropic, OpenAI, and Google emphasize for reliable agent workflows?
2. Which of those patterns matter most for a repo-local coding workflow rather than a managed agent runtime?
3. What do those sources imply should be simplified, enforced, or deferred in this repository?

## Sources scanned
- https://www.anthropic.com/engineering/building-effective-agents
- https://developers.openai.com/api/docs/guides/prompt-engineering
- https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
- https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/
- Local workflow surfaces:
  - `AGENTS.md`
  - `.github/agents/orchestrator.agent.md`
  - `.github/prompts/*.prompt.md`
  - `.github/workflows/pr-quality.yml`
  - `docs/runbooks/agent-mode.md`
  - `docs/copilot-setup.md`

## Highest-signal findings

### Verified
- Anthropic recommends simple, composable workflows first and explicitly says to add complexity only
  when it demonstrably improves outcomes.
- Anthropic distinguishes predictable workflows from more autonomous agents and treats tools,
  stop conditions, and environment feedback as core control surfaces.
- OpenAI recommends strong instruction structure, reusable prompt templates, explicit authority
  boundaries, model pinning, and evals to monitor prompt behavior over time.
- OpenAI's practical agent guide recommends maximizing a single agent with clear tools and
  instructions before splitting into multi-agent orchestration.
- Google’s multi-agent guidance treats specialization as useful only when a single agent stops
  scaling, and it calls out shared-state and debugging costs as real design constraints.

### Inference
- This repository should prefer fewer workflow surfaces with stronger enforcement over more wrapper
  prompts or more specialist personas.
- Repo-local workflow checks that run in CI provide more value than additional prose about packet or
  task-ledger behavior that the runtime does not actually emit.
- The next high-leverage improvement is to make workflow drift observable and blocking before adding
  richer runtime state or agent orchestration.

## Constraints this adds to the local implementation
- Keep the default orchestrator path intact for now.
- Prefer executable workflow checks and deterministic CI gates over additional prompt complexity.
- Do not add a runtime service, durable memory layer, or new default multi-agent pattern in this phase.
- Keep workflow docs honest about what is actually enforced and available in the repo.

## Open questions
1. Should a later phase reduce the number of prompt wrappers, or are some of them still earning their keep?
2. What minimal workflow benchmark set should gate future workflow-control-plane changes?
3. Which parts of the context-packet and run-artifact model should remain as optional debug structure only?