# Continuous Audit Skill

## When to use
Use when defining or reviewing post-merge, scheduled, or repo-health audit behavior.
This skill is for ongoing confidence and refinement, not for replacing the blocking CI lane.

## Process

### Step 1 — Separate blocking checks from informational audits
- Blocking checks belong in normal CI.
- Informational or trend-based checks belong in scheduled or post-merge audit workflows.

### Step 2 — Choose high-signal audit categories
Prefer a small number of trustworthy audits first:
- test flakiness re-runs
- coverage deltas
- dependency and CVE drift
- docs and link health
- basic repo-health or workflow-drift summaries

### Step 3 — Define result handling
- Which findings are warnings only?
- Which findings should become blockers later if they prove low-noise?
- Where are findings surfaced: workflow summary, artifact, issue, or PR comment?

### Step 4 — Keep the feedback loop actionable
- Every audit should explain what changed, why it matters, and what action is expected.
- Avoid adding audits that produce noisy output with no owner or remediation path.

## Output
- Recommended audit categories
- Blocking vs informational classification
- Surfacing plan for findings
- Follow-up tuning risks