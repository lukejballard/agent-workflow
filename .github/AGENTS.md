# Agent Guide

This is the primary package-context document for the portable supermind.

## What this package is
One packaged mind: a single orchestrator plus workflow policy and hooks.
It intentionally avoids multi-agent role theater.

## How the package works

Single-entry workflow: all tasks go through `@orchestrator`.

```
Input → classify → breadth scan → depth dive → requirement lock → critique → revise → execute → verify
```

The orchestrator carries planning, critique, implementation, and verification
internally.

## Requirement lock

Non-trivial changes require an explicit requirement lock before code begins.
Use existing repo requirements when they exist; otherwise create an inline
requirements contract before editing.

## Default generation stack

When generated application work needs a stack decision and neither the user nor
the host repo has already fixed one, prefer:
- Backend: Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- Frontend: React + TypeScript + Vite + Vitest

Precedence is strict:
1. explicit user requirement
2. established host-repo stack evidence
3. package default above

These defaults guide scaffolding, examples, tests, and architecture choices for
generated work. They do not justify rewriting an existing repo onto a different
stack.

## Where things live

```
.github/
  AGENTS.md                    Primary package context
  copilot-instructions.md      Global engineering contract
  agents/                      Orchestrator
  agent-platform/              Workflow policy kernel and default stack policy
  hooks/                       Tool approval hooks and runner
  instructions/                Optional path-specific coding standards
```

## Key constraints
- Default workflow stays inside one conversation.
- Progressive context loading: read only what the current phase needs.
- Non-trivial work requires explicit requirement locking before code changes begin.
- Keep working memory scoped to the current step and compress completed work into episodic summaries.
- Retries are bounded and must change strategy; do not loop on the same failed step.
- Final claims must be backed by verification evidence, not confidence alone.
- Hyperintelligence comes from runtime semantics, explicit memory, and hard verification loops, not from adding more packaged agents.