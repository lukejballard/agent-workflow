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
  hooks/                       Tool approval hooks, phase engine, session schema
    pretool_approval_policy.py   PreToolUse gate (phase, scope, safety)
    posttool_validator.py        PostToolUse tracker (reads, edits, phase auto-detect)
    session_schema.py            Typed session state with validation and migration
    phase_engine.py              Phase state machine and edit gates
    session_log.py               JSONL observability log and episodic memory
  instructions/                Optional path-specific coding standards
    priority.instructions.md     Conflict resolution order for all instruction files
```

## Runtime enforcement
The hook system provides real enforcement beyond prompt instructions:
- **Phase gates**: edits are blocked during bootstrap and context-loading phases.
- **Scope gates**: edits outside `allowed_paths` require explicit approval.
- **Session state**: typed, validated, and persisted across tool calls.
- **Episodic memory**: structured JSONL artifact written on phase transitions.
- **Observability**: all gate decisions and phase transitions logged to `.log.jsonl`.

## Key constraints
- Default workflow stays inside one conversation.
- Progressive context loading: read only what the current phase needs.
- Non-trivial work requires explicit requirement locking before code changes begin.
- Keep working memory scoped to the current step and compress completed work into episodic summaries.
- Retries are bounded and must change strategy; do not loop on the same failed step.
- Final claims must be backed by verification evidence, not confidence alone.
- Hyperintelligence comes from runtime semantics, explicit memory, and hard verification loops, not from adding more packaged agents.