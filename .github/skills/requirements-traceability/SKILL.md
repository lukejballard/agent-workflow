# Requirements Traceability Skill

## When to use
Use this before finalizing any non-trivial task.
The purpose is to prove that the request, the plan, the code or docs changes,
and the verification work still line up.

## Process

### Step 1 — Identify the source of truth
Choose the governing input:
- active spec in `docs/specs/active/`
- research brief in `docs/specs/research/` when external context materially shaped the plan
- explicit user request
- review scope or bug report

### Step 2 — Break it into traceable units
Convert the source of truth into concrete units such as:
- requirements
- acceptance criteria
- review goals
- release gates

### Step 3 — Map each unit
For every unit, identify:
- source brief or external reference if one exists
- planned work or actual change
- evidence file or artifact
- verification activity
- documentation impact
- regression coverage
- status: covered / partial / missing

### Step 4 — Find drift
Flag anything that is:
- implemented but not required
- required but not implemented
- unverified
- verified only by assumption or estimated coverage

### Step 5 — Close the loop
Recommend the smallest set of changes needed to remove the missing or partial items.

## Output
A compact table or list with:
- requirement or goal
- source or research brief
- evidence
- verification
- documentation impact
- regression coverage
- status
- follow-up if missing or partial