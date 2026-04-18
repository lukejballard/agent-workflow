# Regression Audit Skill

## When to use
Use for brownfield work, bugfixes, refactors with no intended behavior change,
or any change where an existing user journey, contract, or workflow is more
likely to break than a brand-new path.

## Process

### Step 1 — Identify regression surfaces
- Which existing behavior is being modified directly?
- Which adjacent modules or workflows depend on that behavior indirectly?
- Which user-visible or operator-visible outcomes would silently drift first?

### Step 2 — Rank risk
Classify each candidate regression surface as High / Medium / Low risk based on:
- blast radius
- coupling to neighboring modules
- historical brittleness
- whether existing tests already cover it well

### Step 3 — Choose verification strategy
For each High-risk regression surface, require at least one of:
- unit regression test
- integration regression test
- Playwright regression assertion
- documentation or contract verification if the risk is process or workflow drift

### Step 4 — Check neighboring artifacts
- Do specs still match the changed behavior?
- Do docs or prompts describe the old behavior?
- Do CI or release gates assume the old behavior?

### Step 5 — Report residual risk
Call out the regressions that remain plausible even after the chosen tests.

## Output
- Ranked list of regression surfaces
- Verification plan or evidence for each High-risk surface
- Residual regression risks that remain