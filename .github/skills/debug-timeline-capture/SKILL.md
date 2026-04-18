# Debug Timeline Capture Skill

## When to use
Use for bugfixes, flaky tests, CI failures, launch blockers, multi-surface regressions,
or any task where the root cause is not obvious from reading code alone.

This skill is designed to stop agents from guessing.
Capture the evidence first, then reason from the timeline.

Auto-consider this skill for:
- brownfield bugfix work
- failing Playwright or browser-driven flows
- backend plus frontend integration regressions
- startup, readiness, or environment-specific failures
- issues where logs, screenshots, or traces already exist but are not yet correlated

## Process

### Step 1 — Write the repro contract
Record:
- expected behavior
- actual behavior
- exact repro steps
- environment details that matter
- commit, branch, or CI run context if available

### Step 2 — Collect timestamped evidence
Prefer concrete artifacts over paraphrase:
- failing command or test output
- backend logs
- frontend console errors and warnings
- network request failures or unexpected statuses
- screenshots of visible failure states
- traces, HAR files, or browser recordings when available
- seeded data or config values needed to reproduce safely

### Step 3 — Build the timeline
Arrange the evidence in order:
- last known good event
- first bad event
- downstream symptoms
- recovery or retry behavior
- whether the failure is deterministic or flaky

### Step 4 — Isolate the fault line
Classify the most likely fault boundary:
- browser/UI state
- frontend API client or rendering path
- backend route or service
- storage or seed data
- CI or environment bootstrapping
- workflow or approval/policy mismatch

### Step 5 — Preserve residual uncertainty
Call out what is still missing:
- no server logs
- no browser trace
- no stable repro
- environment drift not yet ruled out
- auth or seed state unknown

## Browser-first guidance
If browser automation is available, prefer an agent-browser or Playwright-style evidence loop:
1. open the target flow
2. capture a screenshot or trace before interacting further
3. record console and network failures
4. capture a second screenshot after the failure
5. keep selectors and steps stable enough for reuse

## Output
Provide:
- repro recipe
- evidence inventory
- ordered timeline
- most likely fault line
- highest-confidence next verification step
- residual blind spots that still block certainty