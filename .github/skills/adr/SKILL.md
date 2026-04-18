# Architecture Decision Record (ADR) Skill

## When to use
Use when making a significant architectural decision that:
- Introduces a new technology, library, or framework
- Changes a core pattern (switching from REST to GraphQL, ORM to raw SQL, etc.)
- Establishes a convention that all future code should follow
- Represents a non-obvious trade-off that future engineers need to understand

## What an ADR is
A short document that records: the context (why a decision was needed), the decision
(what was chosen), and the consequences (what this means going forward).
ADRs are permanent records. Once accepted, they are never deleted — only superseded
by a new ADR that explicitly replaces them.

## Process
1. Create a new file: `docs/architecture/decisions/NNNN-short-title.md`
   where NNNN is the next sequential number.
2. Fill out the template below.
3. Link the ADR from the PR description.
4. If the decision supersedes an existing ADR, update the existing ADR's status
   to "Superseded by ADR-NNNN".

## ADR template

```markdown
# ADR-NNNN: <Short descriptive title>

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
**Author:** @github-handle

## Context
What situation or problem required a decision? What constraints exist?
What options were available?

## Decision
What was decided? State it clearly and specifically.

## Considered alternatives
What else was considered? Why was each alternative rejected?

## Consequences

### Positive
What does this decision make easier or better?

### Negative
What does this decision make harder? What technical debt does it introduce?
What will future engineers need to know because of this decision?

### Neutral
What changes as a result of this decision without being clearly good or bad?
```

## Output
The completed ADR file saved to `docs/architecture/decisions/NNNN-<title>.md`.
