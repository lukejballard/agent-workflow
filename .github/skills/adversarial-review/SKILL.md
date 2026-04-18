# Adversarial Review Skill

## When to use
Use this on any medium- or high-risk task before finalizing a plan, implementation,
review response, or release recommendation.

The goal is not to defend the current answer.
The goal is to attack it until the weak parts are visible.

## Process

### Step 1 — Attack the framing
- Is the request solving the real problem, or only the stated symptom?
- Is there a smaller or safer change that achieves the same outcome?
- Are any assumptions hidden or unverified?

### Step 2 — Attack the requirements
- Which requirements are implied but not stated?
- Which acceptance criteria are missing, vague, or not independently testable?
- Is there a requirement-to-verification gap?

### Step 3 — Attack the design
- What is the simplest viable alternative?
- What does the chosen approach make harder later?
- Where are the tightest coupling points or migration risks?

### Step 4 — Attack failure modes
- What breaks on invalid input, partial failure, empty states, or concurrency?
- What happens when dependencies are slow, unavailable, or return malformed data?
- Which regressions are most likely in neighboring modules?

### Step 5 — Attack quality blind spots
- Security: validation, auth, secrets, unsafe queries, unsafe output handling
- Performance: obvious hot paths, N+1 patterns, unbounded work, blocking I/O
- Accessibility: semantics, keyboard navigation, naming, contrast, touch targets
- Observability: logs, metrics, tracing, health checks, actionable error context
- Testing: happy path only, missing edge cases, missing integration coverage
- Regression: what existing workflow, endpoint, doc path, or release process is most likely to silently break?
- Documentation: do the setup guide, runbook, spec, and PR checklist still describe reality?
- External context: is the answer relying on unstated outside assumptions or tooling that does not exist in this repo?

### Step 6 — Decide
Classify each issue as PASS, WARN, or FAIL.
Only FAIL items must block the current approach.

## Output
- **PASS:** what survived adversarial review
- **WARN:** concerns worth addressing if time permits
- **FAIL:** gaps that must be fixed before proceeding
- **Recommended revision:** the smallest change that resolves the FAIL items
