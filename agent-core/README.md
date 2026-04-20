# Agent Core — Portable Hyperintelligent Mind Kernel

A minimal, self-contained single-mind workflow kernel for GitHub Copilot agent
mode. The packaged footprint is a single top-level folder: `.github/` for
Copilot discovery, workflow policy, and bundled hook utilities.

## Setup (4 steps)

1. **Copy files to your repo:**
   ```bash
    mkdir -p .github
   cp -r agent-core/github/. ./.github/
   ```

2. **Configure `.github/AGENTS.md`** — Replace `{{REPO_DESCRIPTION}}` with a one-line description of your project.

3. **Configure `.github/copilot-instructions.md`** — Replace template tokens: `{{SRC_DIR}}`, `{{FRONTEND_DIR}}`, `{{TESTS_DIR}}`, `{{BACKEND_STACK}}`.

4. **Add optional coding-standard instructions** — Create `.github/instructions/<lang>.instructions.md` files for your stack when needed.

## Architecture

```
agent-core/
├── README.md
└── github/                            # → .github/ in your repo
    ├── AGENTS.md                      # Primary agent context
    ├── copilot-instructions.md        # Global engineering contract
    ├── agents/
    │   └── orchestrator.agent.md      # Single hyperintelligent orchestrator
    ├── hooks/
    │   ├── pretool-approval-policy.json
    │   └── hooks.py                   # PreTool + PostTool approval hooks
    ├── agent-platform/
    │   └── workflow-manifest.json     # Workflow, memory, retry, verify policy
```

## Core Surface

These files make up the core workflow:

- `.github/AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agents/orchestrator.agent.md`
- `.github/agent-platform/workflow-manifest.json`
- `.github/hooks/pretool-approval-policy.json`
- `.github/hooks/hooks.py`

This minimal distribution intentionally ships no packaged specialist agents,
slash-prompt aliases, standalone skills, spec scaffold, or validator.

## Helpers

| Module | Purpose |
|---|---|
| `.github/hooks/hooks.py` | PreTool/PostTool hooks — blocks destructive commands, requires approval for remote writes and sensitive paths. Wired via `.github/hooks/pretool-approval-policy.json`. |

## Requirement Lock

Non-trivial work still requires locked requirements before code begins, but this
minimal package does not ship a dedicated `.github/specs/` scaffold.

Use one of these sources instead:

- existing repo requirements, issues, ADRs, or planning docs
- an inline requirements contract created by the orchestrator before editing

The lock must define the problem, concrete behaviors, constraints, and how the
result will be verified.

## Workflow Phases

```
goal-anchor → classify → breadth-scan → depth-dive → lock-requirements
→ choose-approach → adversarial-critique → revise → execute-or-answer
→ traceability-and-verify
```

Trivial tasks shortcut: `classify → execute-or-answer`.

The remaining intelligence is concentrated in three policies:

- explicit requirement locking before non-trivial edits
- scoped memory with episodic compression and provenance discipline
- bounded retries plus evidence-backed verification

## Usage

After installation, use GitHub Copilot's agent mode:

```
@orchestrator Fix the pagination bug in the user list endpoint
```

## Extending

- **Add instructions:** Create `.github/instructions/<pattern>.instructions.md`.
- **Configure hooks:** Edit `.github/hooks/hooks.py` to add deny/ask patterns.
- **Add optional extra surfaces later:** If a consuming repo needs prompts, specs, or validators, add them there instead of shipping them in the minimal base package.

## Dependencies

- Python 3.11+ for `.github/hooks/hooks.py`
- No required external packages
