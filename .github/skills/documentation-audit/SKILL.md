# Documentation Audit Skill

## When to use
Use when changing agents, prompts, skills, instructions, runbooks, setup guides,
CI workflow expectations, contributor processes, or any architecture surface where
documentation drift would mislead future contributors.

## Process

### Step 1 — Identify public-facing workflow surfaces
Check the relevant set of:
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agents/*.agent.md`
- `.github/prompts/*.prompt.md`
- `.github/skills/*/SKILL.md`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/specs/_template.md`

### Step 2 — Check for behavioral drift
- Does each file still describe the same routing, trigger rules, and constraints?
- Are any files referencing assets that do not exist?
- Are there setup or extension steps that no longer match the repo?

### Step 3 — Check documentation coverage
- Which docs must change because of this implementation?
- Which docs are intentionally unaffected, and why?
- Are examples and starter prompts still correct?

### Step 4 — Verify constraint honesty
- Do the docs claim tooling, search, or approval behavior that is not actually available?
- Are platform-level dependencies clearly separated from in-repo behavior?

## Output
- Files that must be updated
- Files verified as still correct
- Drift or overclaim findings
- Residual documentation risks