# Engineering Contract

This repository is the canonical source for a portable prompt/meta supermind
package. Inside the package boundary, the system behaves as one mind, not a
bundle of specialist agents (see [.github/AGENTS.md](AGENTS.md)).

## Read order (every task)

1. [.github/AGENTS.md](AGENTS.md) — package framing.
2. [.github/agent-platform/workflow-manifest.json](agent-platform/workflow-manifest.json) — canonical policy (phases, task classes, audit, briefs, frontend targets).
3. [.github/agents/orchestrator.agent.md](agents/orchestrator.agent.md) — workflow, structured critique, R1–R15 pre-send checklist.
4. Non-trivial only: episodic memory + `failure_index.search(task_description)`.
5. Surface-scoped guides under [.github/instructions/](instructions/) for the files you will touch.
6. Existing requirements: specs in [docs/specs/active/](../docs/specs/active/), issues, ADRs, plans.
7. Audit-mode runs: [docs/runbooks/adversarial-audit.md](../docs/runbooks/adversarial-audit.md).

## Routing

- All work goes through `@orchestrator`.
- Audit runs as `@orchestrator audit [scope]` and follows the charter at
  [docs/runbooks/adversarial-audit.md](../docs/runbooks/adversarial-audit.md).

## Canonical loop

The phase order is owned by `workflow.phaseOrder` in
[workflow-manifest.json](agent-platform/workflow-manifest.json). It now
includes explicit `self-review` and `critique` phases enforced by the hooks.
Do not restate the loop here.

## Runtime gates (consumer-visible)

These gates live in [.github/hooks/pretool_approval_policy.py](hooks/pretool_approval_policy.py):

- **phase** — edits blocked during read-only phases.
- **scope** — edits outside `allowed_paths` require approval.
- **sensitive-path** — edits to hooks, manifest, audit charter, research dir, secrets-adjacent paths require approval.
- **requirements-lock** — non-trivial classes need `requirements_locked = true` before edits.
- **low-confidence** — edits below 0.4 confidence require approval (non-trivial classes only).
- **critique-fail** — any FAIL in `state.critique_results` blocks edits after the critique phase.
- **token-budget** — estimated session tokens above `AGENT_TOKEN_BUDGET` require approval.
- **tool-call budget** — `AGENT_MAX_TOOL_CALLS` ceiling triggers loop review.

## Stack precedence

Strict order, owned by [workflow-manifest.json](agent-platform/workflow-manifest.json) (`implementationDefaults`):

1. Explicit user requirement.
2. Established host-repo stack evidence.
3. Package default (Python + FastAPI + Pydantic + SQLAlchemy + Alembic for backend; React + TypeScript + Vite + Vitest for frontend).

## Instruction precedence

See [.github/instructions/priority.instructions.md](instructions/priority.instructions.md).

## Hard prohibitions

- Hard-coded secrets — use environment variables.
- `// @ts-ignore` (use `// @ts-expect-error` with rationale only when unavoidable).
- `dangerouslySetInnerHTML` with user or model-derived data.
- Wildcard CORS for authenticated traffic.
- Role-play personas, "Chief X Officer" framing, or specialist-agent ecosystems.
- Success claims without verification evidence in the response.
- Identical retries — every retry must change strategy, inputs, or evidence.
- Edits outside `allowed_paths` for the locked task scope.

If you are running in audit mode, see [docs/runbooks/adversarial-audit.md](../docs/runbooks/adversarial-audit.md).
