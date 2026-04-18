# Agent Guide

This file is the primary context document for all AI agents working in this
repository. Read it completely before taking any action.

## What this repo is
A reusable repository scaffold for agent-driven fullstack delivery.
The verified surfaces in this snapshot are workflow metadata, documentation,
specs, prompts, skills, and helper scripts. Project-specific application code
may live under `src/`, `frontend/`, `tests/`, and `deploy/` when those areas
are populated.

## How the agent system works

The default workflow is single-entry:

```
Input → orchestrator → goal anchor → classify/task DAG → breadth scan → depth dive → spec/plan → adversarial critique → revise → execute/verify → final answer
```

`@orchestrator` is the default entry point for almost every task. It keeps the
user in one conversation and internally applies analyst, planner, implementer,
qa, reviewer, and cleanup thinking as needed.

Specialist agents in `.github/agents/` remain available for advanced or manual
fallback use. Agent-discoverable skills live in `.github/skills/`. Repository
checklists in `skills/` are supplemental domain and release gates. Reusable
prompts are in `.github/prompts/`. Path-specific coding standards are in
`.github/instructions/`.

For non-trivial work, the default path now uses a typed current-step context
packet, a rolling episodic summary, on-demand semantic retrieval recorded as
source-backed packet summaries, and an active run artifact for longer multi-
surface workflows instead of carrying raw history and stale tool output
forward indefinitely.

Canonical machine-readable agent metadata lives in `.github/agent-platform/`.
Use `workflow-manifest.json` for workflow routing, `repo-map.json` for repository
topology, `skill-registry.json` for skill discovery, `context-packet.schema.json`
for typed current-step context, and `run-artifact-schema.json` for lightweight
run summaries on longer investigations or cross-surface work.

## When to use which agent

| Situation | Start with |
|---|---|
| Almost any task: features, bug fixes, brownfield work, reviews, research | `@orchestrator` |
| Explicit read-only codebase mapping | `@analyst` |
| Explicit external docs, ecosystem, competitor, or launch-readiness research | `@researcher` |
| Explicit spec-writing only | `@planner` |
| Build from an approved spec only | `@implementer` |
| Tests only | `@qa` |
| Independent adversarial review only | `@reviewer` |
| No-behaviour-change refactor only | `@cleanup` |

## Spec system (anti-drift)

Every non-trivial implementation change requires a working spec file at
`docs/specs/active/<slug>.md` before code changes begin. Existing product requirements may
already live under `specs/`, `.specify/`, `plan/`, or `openspec/changes/`; the orchestrator
should read those first, reconcile them against the current code, and then create or refresh
an active working spec in `docs/specs/active/`.
For greenfield work, Speckit artifacts in `.specify/` and `specs/` are the preferred upstream
planning path. For brownfield work, OpenSpec change artifacts in `openspec/changes/` are the
preferred upstream change path.
The implementer reads ONLY the active working spec for requirements. The template is at
`docs/specs/_template.md`.
When external docs or standards materially affect the approach, save a reusable brief under
`docs/specs/research/<slug>-research.md` and reference it from the active spec.

## Key constraints
- Copilot cannot rely on autonomous agent-to-agent loops. The default workflow must stay inside one conversation and use internal phases instead of manual handoffs.
- Workspace MCP config includes `github`, `playwright`, `filesystem`, `fetch`, `sequential-thinking`, and optional Tavily web search when `TAVILY_API_KEY` is configured.
- MCP resources and prompts are not supported — only tools.
- Prompt files work in VS Code, Visual Studio, and JetBrains only.
- `.github/copilot-instructions.md` must stay under 4 000 characters.

## Where things live

```
frontend/                     Frontend application area and scoped agent guidance
src/                          Backend or shared application code area and scoped guidance
tests/                        Automated tests and test-specific guidance
docs/                         Architecture, setup, workflow, and planning docs
deploy/                       Deployment manifests and operational assets when present
.specify/                     Speckit templates and scripts for greenfield feature planning
openspec/                     OpenSpec change proposals for brownfield capability evolution

.github/
  copilot-instructions.md     Global rules (all contexts)
  instructions/               Path-specific rules (injected by file match)
  agents/                     Single-entry orchestrator + specialist fallback agents
  agent-platform/             Canonical workflow, topology, skill-registry, and artifact metadata
  hooks/                      Deterministic workspace approval and validation hooks
  skills/                     Agent-discoverable quality modules
  prompts/                    Single-entry and targeted workflow prompts
  workflows/                  CI/CD

skills/                       Supplemental manual release and domain checklists

docs/
  specs/
    _template.md              Spec template
    active/                   In-flight feature specs
    research/                 Reusable external-context briefs
    done/                     Completed specs (archive)
  architecture/
    README.md                 Architectural context
    decisions/                Architecture Decision Records (ADRs)

.vscode/
  mcp.json                    MCP server configuration
```
