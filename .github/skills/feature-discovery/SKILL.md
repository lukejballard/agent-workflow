# Feature Discovery Skill

## When to use
Use when a feature idea is vague or stated as a user feeling ("users find X confusing",
"Y is slow", "we should improve Z") rather than a concrete requirement.

## Process

### Step 1 — Identify the real problem
Ask: What specific action is the user unable to perform, or what is causing friction?
Do not jump to solutions. The stated problem is often not the real problem.

### Step 2 — Define the target user
Who experiences this? All users? A specific role or segment?
What is their technical sophistication? What is their goal?

### Step 3 — Quantify the value
Would solving this: reduce support tickets? increase conversion? unblock revenue?
Reduce time-on-task? Estimate: High / Medium / Low impact.

### Step 4 — Survey the existing codebase
Is there existing code that partially addresses this?
What would have to change? What is the blast radius?

### Step 5 — Propose solutions
Option A: Simplest possible solution. Minimum scope. Quick to ship.
Option B: More complete solution. Better UX or performance. Takes longer.

### Step 6 — Evaluate tradeoffs
For each option: implementation complexity, test burden, risk, time estimate.

### Step 7 — Recommend one option with clear rationale

## Output
A structured brief the planner agent can use directly as input:
- Problem statement (one paragraph)
- Target user
- Option A: description, pros, cons, estimate
- Option B: description, pros, cons, estimate
- Recommendation and rationale
- Complexity: S / M / L / XL
- Open questions (if any)
