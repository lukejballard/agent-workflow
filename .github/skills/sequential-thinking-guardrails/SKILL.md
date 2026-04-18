# Sequential Thinking Guardrails Skill

## When to use
Use this skill when a non-trivial subtask is ambiguous enough that a straight-line pass is likely
to miss an edge case, a safer alternative, or a hidden requirement.

Typical triggers:
- complex plan selection
- adversarial critique of a preferred approach
- multi-branch investigations where several plausible causes or designs compete

Do not use this skill for trivial work, routine lookups, or as a substitute for reading the repo.

## Guardrails
- Treat Sequential Thinking session state as scratch space, not durable repo memory.
- Retain only a short summary of the reasoning outcome in the context packet or run artifact.
- Do not preserve raw thought transcripts in specs, docs, run artifacts, or final answers.
- Avoid `export_session` and `import_session` unless the user explicitly asks for persisted reasoning
  or the task cannot be completed without it.
- Clear prior history before reuse when an old session could contaminate the current subtask.
- Clear history after the needed summary is captured when the previous branch is no longer relevant.

## Process

### Step 1 — Decide if the tool is warranted
- Is the subtask genuinely ambiguous or multi-branch?
- Would a normal breadth scan plus critique be enough?
- Is the extra reasoning likely to change the chosen plan or risk analysis?

If the answer is no, skip the tool.

### Step 2 — Reset state if needed
- If there is any chance an older session could bias the current subtask, clear the history first.
- Start from the active goal anchor and current-step contract rather than replaying prior raw context.

### Step 3 — Use the tool narrowly
- Use Sequential Thinking to compare alternatives, attack assumptions, or structure a branching investigation.
- Keep the reasoning anchored to verified repo facts, not speculative chains.
- Stop once the tool has produced a useful conclusion or exposed the real uncertainty.

### Step 4 — Collapse the result
- Generate a short summary of the useful outcome.
- Record only that summary in the context packet or run artifact.
- Include any resulting risk, decision, or open question in normal workflow artifacts.

### Step 5 — Clean up
- Clear the session history when it is no longer relevant.
- Continue the normal orchestrator workflow with the summary, not the transcript.

## Output
Capture only:
- why Sequential Thinking was used
- the chosen direction or risk it exposed
- the summary-level conclusion that affected the plan, implementation, or review