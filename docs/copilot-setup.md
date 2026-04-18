# Copilot & Agent Setup Guide

This guide explains the GitHub Copilot and coding agent files available in this repository, when to use each one, and how to get the most out of them.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository-wide Copilot instructions](#2-repository-wide-copilot-instructions)
3. [Path-specific instruction files](#3-path-specific-instruction-files)
4. [AGENTS.md files](#4-agentsmd-files)
5. [Prompt files](#5-prompt-files)
6. [Skills](#6-skills)
7. [Issue and PR templates](#7-issue-and-pr-templates)
8. [Quick reference](#8-quick-reference)
9. [Agent-mode operating model](#9-agent-mode-operating-model)
10. [External research limits](#10-external-research-limits)
11. [Starter prompts](#11-starter-prompts)

---

## 1. Overview

This repository uses a layered approach to guide AI coding assistants:

```
.github/copilot-instructions.md              ← Always-on: project context + global rules
.github/instructions/*.md                    ← Path-scoped rules activated by file type
.github/agent-platform/workflow-manifest.json ← Canonical workflow, capability, and skill-routing metadata
.github/agent-platform/repo-map.json          ← Canonical repository topology and verification routes
.github/agent-platform/skill-registry.json   ← Canonical skill inventory and trigger-tag coverage
.github/agent-platform/context-packet.schema.json ← Canonical typed current-step context contract
.github/agent-platform/run-artifact-schema.json ← Lightweight run-artifact format for longer workflows
.github/agents/orchestrator.agent.md         ← Default single-entry agent for most work
.github/hooks/*.json                         ← Deterministic workspace approval and validation hooks
.github/prompts/*.prompt.md                  ← On-demand wrappers for common workflows
.github/skills/*/SKILL.md                    ← Agent-discoverable workflow skills
skills/*/SKILL.md                            ← Supplemental repo checklists and release gates
AGENTS.md / */AGENTS.md                      ← Agent operating model for each directory
docs/runbooks/agent-mode.md                  ← Full single-entry operating model and roadmap
.vscode/mcp.json                             ← Workspace MCP servers, including structured reasoning and optional Tavily search
.vscode/settings.json                        ← Workspace prompt recommendations and terminal auto-approve rules
```

For a complete description of the default orchestrator workflow and fallback specialist path,
see **[docs/runbooks/agent-mode.md](runbooks/agent-mode.md)**.
The canonical workflow metadata lives in `.github/agent-platform/workflow-manifest.json`.
Use `.github/agent-platform/repo-map.json` for repository topology, `.github/agent-platform/skill-registry.json`
for skill discovery, `.github/agent-platform/context-packet.schema.json` for typed current-step context,
and `.github/agent-platform/run-artifact-schema.json` for lightweight run-summary structure on longer workflows.
Agent profiles, prompts, and docs should match these files.
During normal verification, run `python scripts/agent/sync_agent_platform.py --check` to catch
metadata drift. Use `python scripts/agent/sync_agent_platform.py --write` only when the repo map,
skill inventory, or other canonical agent-platform metadata needs to be refreshed. Example
artifacts live in `.github/agent-platform/examples/`.
Workflow control-plane changes under `.github/agent-platform/`, `.github/agents/`,
`.github/prompts/`, `.github/skills/`, `.github/workflows/`, `scripts/agent/`, `.vscode/`,
root or scoped `AGENTS.md`, `.github/copilot-instructions.md`, or `.github/PULL_REQUEST_TEMPLATE.md`
must update both `docs/runbooks/agent-mode.md` and `docs/copilot-setup.md` in the same PR.
The PR-quality lane enforces that companion-doc rule and also runs
`python scripts/agent/sync_agent_platform.py --check` as a blocking governance step.

Execution-oriented entrypoints expose the built-in `execute` tool set so the default workflow can run
local verification commands when needed. Browser-capable entrypoints also expose the built-in
`browser` tool set for integrated UI automation when `workbench.browser.enableChatTools` is enabled.
The default orchestrator and selected execution-oriented prompt wrappers also expose
`sequential-thinking/*` so complex planning, critique, and investigation steps can use the pinned
workspace MCP server when local `uvx` support is available.
Use it as scratch reasoning only: keep raw thought history out of specs, docs, and run artifacts,
prefer summary-level conclusions, and avoid `export_session` / `import_session` unless the user
explicitly asks for persisted reasoning.
Prompt files explicitly target the repo's `orchestrator` custom agent and act as thin task-shaping
wrappers over that default workflow. The repo validates their stable contract with
`python scripts/agent/check_workflow_benchmarks.py`, which checks prompt entrypoints, tool tiers,
and required placeholders against `.github/agent-platform/workflow-benchmarks.json`. That harness
is a deterministic contract check, not an end-to-end model-quality eval. Terminal approvals still
flow through `.github/hooks/pretool-approval-policy.json` and `.vscode/settings.json`.
The workspace only pre-approves the repo's safe verification entrypoints:
`bash scripts/agent/verify-narrow.sh`, `bash scripts/agent/verify-broad.sh`, and
`python scripts/agent/sync_agent_platform.py --check`.
`bash scripts/agent/verify-broad.sh` includes a project-scoped Python dependency audit via
`python scripts/agent/check_python_dependency_audit.py`, which reads pinned dependencies from
`pyproject.toml` instead of auditing whatever extra packages happen to be installed locally.

The default orchestrator path now also uses a bounded context model for non-trivial work:
- a one-line goal anchor stays at the top of each deeper reasoning step
- the active subtask is passed through a typed context packet
- working memory stays local to the current node
- completed work is compressed into episodic memory
- semantic memory is loaded only when the current step actually needs more repo facts, then retained as short source-backed summaries
- editor-managed memory scopes such as `/memories/repo/` can be referenced in packet metadata but are not normal workspace files
- longer multi-surface workflows keep a run artifact active and append `taskLedger` entries after each completed subtask
- stale tool output is trimmed once the subtask that produced it is complete

---

## 2. Repository-wide Copilot instructions

**File:** `.github/copilot-instructions.md`

This file is **always active** when Copilot is working in this repository. It provides:

- Project purpose and architecture overview
- Python and TypeScript coding standards
- Testing expectations
- Documentation requirements
- Automatic quality-trigger expectations for non-trivial work
- Key environment variables
- A list of things Copilot must NOT do

You do not need to do anything to activate it — Copilot reads it automatically.

**When to update it:** When a fundamental project convention changes (new language version target, new linting rule, new architectural pattern).

---

## 3. Path-specific instruction files

**Directory:** `.github/instructions/`

These files are activated automatically when Copilot is working on files that match their `applyTo` pattern.

| File | Applies to | Key focus |
|---|---|---|
| `accessibility.instructions.md` | `frontend/**` | Semantic HTML, ARIA, contrast, keyboard support |
| `api.instructions.md` | collector routes, API models, `frontend/src/api/**` | API boundaries and typed client access |
| `database.instructions.md` | `src/**/storage/**`, `alembic/**` | Schema changes, query safety, migration hygiene |
| `performance.instructions.md` | `**/*.py`, `**/*.ts`, `**/*.tsx` | Profiling-first performance work, hot-path awareness |
| `python.instructions.md` | `**/*.py` | Collector, storage, analysis, SDK, typing, testing, error handling |
| `react.instructions.md` | `frontend/**` | SPA component boundaries, hooks, data flow, accessibility |
| `security.instructions.md` | `**/*.py`, `**/*.ts`, `**/*.tsx` | Input validation, secrets hygiene, auth, unsafe output handling |
| `testing.instructions.md` | test files and test directories | Coverage targets, fixtures, mocking, determinism |
| `typescript.instructions.md` | `**/*.ts`, `**/*.tsx` | Strict typing and maintainable TS patterns matched to local config |

**When to update them:** When conventions for that layer change (e.g. you adopt a new testing library, change the frontend framework).

---

## 4. AGENTS.md files

These files describe the operating model for coding agents (Copilot Workspace, Claude, GPT agents, etc.) scoped to each directory.

| File | Scope |
|---|---|
| `AGENTS.md` (root) | Repository-wide: all components, key commands, prohibited actions |
| `src/AGENTS.md` | Python backend: package responsibilities, SDK rules, analysis patterns |
| `frontend/AGENTS.md` | React dashboard: directory guide, naming conventions, common tasks |
| `tests/AGENTS.md` | Test suite: naming, isolation, coverage targets, fixture patterns |
| `docs/AGENTS.md` | Documentation: document inventory, writing rules, update triggers |

**When to use them:** When asking an agent to work on a specific part of the codebase. Point the agent at the relevant `AGENTS.md` file to orient it quickly.

**When to update them:** When the directory structure or team conventions change.

---

## 5. Prompt files

**Directory:** `.github/prompts/`

These are reusable prompt templates you paste into Copilot Chat or an agent conversation.
They are thin wrappers around the default single-entry orchestrator unless noted otherwise.

| File | Use when… |
|---|---|
| `single-entry-workflow.prompt.md` | Starting almost any non-trivial task |
| `greenfield-feature.prompt.md` | Starting a new feature from an idea or brief using Speckit as the upstream planning path |
| `brownfield-improve.prompt.md` | Improving or extending existing code using OpenSpec changes as the upstream change path |
| `bugfix-workflow.prompt.md` | Investigating and fixing a bug with root-cause focus |
| `research.prompt.md` | External context, library docs, or security/performance research is needed |
| `generate-tests.prompt.md` | Writing or hardening tests for a target module |
| `review-code.prompt.md` | Requesting an independent code review response |
| `launch-readiness-audit.prompt.md` | Requesting a repo-wide launch, onboarding, or readiness audit |

### How to use a prompt file

1. Open the relevant prompt file.
2. Copy the **Prompt** section.
3. Paste it into Copilot Chat (VS Code, GitHub.com, or CLI).
4. Fill in the `[PLACEHOLDER]` values for your specific task.
5. Submit and iterate.

---

## 6. Skills

There are two skill layers in this repository.

### Agent-discoverable skills

**Directory:** `.github/skills/`

The highest-trust routing metadata for these skills now lives in `.github/agent-platform/workflow-manifest.json`.
The skill markdown remains the human-readable guidance layer.

| Skill | Use for… |
|---|---|
| `feature-discovery` | Turning vague requests into concrete briefs |
| `spec-validation` | Validating specs before implementation |
| `adversarial-review` | Challenging plans or answers before finalizing |
| `requirements-traceability` | Verifying request-to-change coverage |
| `observability-inject` | Adding logs, metrics, tracing, and health checks |
| `test-hardening` | Strengthening test coverage and failure-path checks |
| `visual-qa` | UI and accessibility-oriented validation |
| `regression-audit` | Attacking brownfield changes for silent break risk |
| `documentation-audit` | Checking workflow and architecture docs for drift |
| `continuous-audit` | Defining or reviewing scheduled repo-health auditing |
| `adr` | Recording architectural decisions |

### Supplemental repo checklists

**Directory:** `skills/`

| Skill | Use for… |
|---|---|
| `skills/python-quality/` | Pre-PR Python quality checks |
| `skills/testing-regression/` | Test suite health before merging |
| `skills/frontend-accessibility/` | A11y audit before a UI release |
| `skills/api-contract-review/` | API consistency review before release |
| `skills/docs-release-readiness/` | Docs completeness before cutting a release |
| `skills/docker-deploy-validation/` | Docker and deployment validation |
| `skills/telemetry-observability-audit/` | SDK and collector telemetry audits |
| `skills/application-security-review/` | Production-sensitive security review |

### How to use a skill

1. Open the relevant `SKILL.md` file.
2. Work through the checklist item by item.
3. Fix any failing items before proceeding.
4. Optionally, paste the skill into Copilot Chat and ask it to evaluate your changes against the checklist.

---

## 7. Issue and PR templates

**Directory:** `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`

| Template | Use for… |
|---|---|
| `bug-report.yml` | Reproducible bugs with steps, environment, and traceback |
| `feature-request.yml` | New features or improvements |
| `PULL_REQUEST_TEMPLATE.md` | All PRs — includes architecture impact, testing, docs, and rollout sections |

These templates encourage contributors to think about architecture impact, testing discipline, documentation completeness, and rollout safety before submitting.

---

## 8. Quick reference

```
Task                                 → Use this file
─────────────────────────────────────────────────────────────────
Copilot always-on context            → .github/copilot-instructions.md
Workspace MCP server config          → .vscode/mcp.json
Workspace prompt/approval config     → .vscode/settings.json
Deterministic approval policy        → .github/hooks/pretool-approval-policy.json
Path-specific Copilot rules          → .github/instructions/*.instructions.md
Orient a coding agent                → AGENTS.md (root or subdirectory)
Full agent-mode operating model      → docs/runbooks/agent-mode.md
Canonical workflow manifest          → .github/agent-platform/workflow-manifest.json
Canonical repo topology              → .github/agent-platform/repo-map.json
Canonical skill inventory            → .github/agent-platform/skill-registry.json
Canonical context packet             → .github/agent-platform/context-packet.schema.json
Run-artifact schema                  → .github/agent-platform/run-artifact-schema.json
Run-artifact examples                → .github/agent-platform/examples/
Validate agent-platform metadata     → python scripts/agent/sync_agent_platform.py --check
Workflow benchmark manifest          → .github/agent-platform/workflow-benchmarks.json
Validate workflow benchmark contract → python scripts/agent/check_workflow_benchmarks.py
Refresh agent-platform metadata      → python scripts/agent/sync_agent_platform.py --write
Default user-facing agent            → .github/agents/orchestrator.agent.md
Execution-capable workflow agents    → .github/agents/orchestrator.agent.md, implementer.agent.md, qa.agent.md, cleanup.agent.md
Browser-capable workflow entrypoints → .github/agents/orchestrator.agent.md, qa.agent.md, and the single-entry, greenfield, brownfield, bugfix, test-generation, and launch-readiness prompts
Start almost any non-trivial task    → .github/prompts/single-entry-workflow.prompt.md
Start a new feature                  → .github/prompts/greenfield-feature.prompt.md
Improve existing code                → .github/prompts/brownfield-improve.prompt.md
Research before planning             → .github/prompts/research.prompt.md
Write or harden tests                → .github/prompts/generate-tests.prompt.md
Request a code review                → .github/prompts/review-code.prompt.md
Fix a bug with root-cause focus      → .github/prompts/bugfix-workflow.prompt.md
Run a launch-readiness audit         → .github/prompts/launch-readiness-audit.prompt.md
External ecosystem research          → .github/agents/researcher.agent.md
Validate a spec                      → .github/skills/spec-validation/SKILL.md
Run adversarial critique             → .github/skills/adversarial-review/SKILL.md
Check request-to-change coverage     → .github/skills/requirements-traceability/SKILL.md
Attack regression risk               → .github/skills/regression-audit/SKILL.md
Capture bug timeline evidence        → .github/skills/debug-timeline-capture/SKILL.md
Audit frontend architecture + UX     → .github/skills/frontend-best-practices/SKILL.md
Check workflow/doc drift             → .github/skills/documentation-audit/SKILL.md
Define scheduled audit behavior      → .github/skills/continuous-audit/SKILL.md
Pre-PR Python quality gate           → skills/python-quality/SKILL.md
Pre-merge test regression gate       → skills/testing-regression/SKILL.md
Pre-release docs gate                → skills/docs-release-readiness/SKILL.md
Pre-release API contract gate        → skills/api-contract-review/SKILL.md
Pre-deploy Docker validation         → skills/docker-deploy-validation/SKILL.md
UI accessibility audit               → skills/frontend-accessibility/SKILL.md
Telemetry audit (SDK + collector)    → skills/telemetry-observability-audit/SKILL.md
Full security review                 → skills/application-security-review/SKILL.md
Report a bug                         → .github/ISSUE_TEMPLATE/bug-report.yml
Request a feature                    → .github/ISSUE_TEMPLATE/feature-request.yml
Use the PR checklist                 → .github/PULL_REQUEST_TEMPLATE.md
```

---

## 9. Agent-mode operating model

For the full single-entry workflow, fallback specialist guidance, definition of done,
and the current prompt roadmap, see:

**[docs/runbooks/agent-mode.md](runbooks/agent-mode.md)**

---

## 10. External research limits

The current workflow can broaden external context through `fetch` and `github`, can use
`sequential-thinking` for local structured reasoning, and can optionally use Tavily search from
`.vscode/mcp.json` when `TAVILY_API_KEY` is configured. It still does not, by itself, change
tool-approval behavior.

When outside references materially change the answer:

1. Use the research-first prompt or `@researcher` fallback.
2. Save the resulting brief to `docs/specs/research/<slug>-research.md`.
3. Reference that brief from the active spec.
4. Configure `TAVILY_API_KEY` if Tavily-backed web search is needed.
5. Treat autoapproval as separate editor configuration work.

---

## 11. Starter prompts

These examples are copy-paste starting points for the default orchestrator.

### Backend feature prompt

```text
Use the default orchestrator workflow for this backend task.

Goal: add or change backend behavior under src/.
Target area: src/
Context: read AGENTS.md, src/AGENTS.md, docs/architecture.md, and any governing spec in `.specify/`, specs/, plan/, openspec/changes/, or docs/specs/active/.
Constraints: keep collector routes thin, keep storage access in storage/ or service helpers, and update docs/architecture.md if an endpoint changes.
Done when: the spec is current, the code change is implemented, tests are updated, and the final response includes key risks and verification status.
```

### Frontend task prompt

```text
Use the default orchestrator workflow for this frontend task.

Goal: implement or fix a dashboard feature in frontend/.
Target area: frontend/src/
Context: read AGENTS.md, frontend/AGENTS.md, the nearest page/component/api files, and any governing spec before coding.
Constraints: no direct fetch() in pages or components, keep API calls in frontend/src/api/, keep shared types in frontend/src/types/, and check accessibility for new UI.
Done when: the change matches existing Vite + React Router patterns, tests are updated, and the final response is concise and explicit about risks.
```

### Review prompt

```text
Use the default orchestrator workflow in review-only mode.

Goal: review the requested scope and report findings first.
Target: <file path, branch, PR, or feature area>
Context: use the governing spec if one exists and compare the implementation to the actual repo patterns.
Constraints: run adversarial-review and requirements-traceability, do not soften critical issues, and keep the review focused on correctness, regressions, security, performance, accessibility, observability, and tests.
Done when: the response starts with findings or a clear PASS/REJECT decision and lists residual risks or verification gaps.
```

### Bugfix prompt

```text
Use the default orchestrator workflow in bugfix mode.

Goal: diagnose and fix a concrete bug without widening scope.
Target: <symptom, failing test, endpoint, or UI path>
Context: start breadth-first across the reproducer, logs, nearby code, tests, and docs, then go deep on the most likely fault line.
Constraints: prefer a root-cause fix, preserve existing patterns, add or update regression tests, and avoid unrelated refactors.
Done when: the bug is fixed, verification is summarized, and any remaining unknowns are explicit.
```

### Launch-readiness audit prompt

```text
Use the default orchestrator workflow in review-only launch-readiness mode.

Goal: assess whether this repository is ready for launch and whether onboarding is fast enough for a new user or contributor.
Context: start breadth-first across architecture, docs, onboarding, tests, CI/CD, deploy, observability, security, ownership, and the user-facing product surface; then go full-depth on the highest-risk gaps.
Constraints: findings first, ordered by severity; include time-to-value, onboarding friction, and differentiation risks; use external references only if they materially change the conclusion.
Done when: the response clearly lists launch blockers, major risks, quick wins, and residual unknowns.
```
