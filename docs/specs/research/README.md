# Research Briefs

This directory stores reusable research briefs for tasks where external docs,
standards, ecosystem references, or competitive context materially changed the
recommended approach.

Use one file per topic:

`docs/specs/research/<slug>-research.md`

Each brief should capture:

1. The questions asked
2. The sources scanned
3. The 3-5 highest-signal sources analysed deeply
4. Verified findings vs inference
5. Constraints or decisions this adds to the local implementation
6. Open questions that still need a human decision

If a non-trivial active spec depends on outside context, reference the brief from that spec.

## When a brief is required

Authoritative source: `researchBriefPolicy.requiredWhen` in
`.github/agent-platform/workflow-manifest.json`. A brief is required when any
of the following is true:

- An external source materially changed a non-trivial plan.
- Conflicting sources had to be reconciled (name what was trusted, what was
  discarded).
- A framework or stack decision needed evidence beyond the package default.
- The orchestrator ran in audit mode (see `## Audit briefs` below).

When a brief is required and was not produced, the posttool hook logs
`research_brief_skipped` so the next audit pass can catch the gap.

## Audit briefs

Audit-mode runs (per
[adversarial-audit.md](../../runbooks/adversarial-audit.md)) write their
output as a brief at:

```
docs/specs/research/audit-<surface>-<YYYYMMDD>.md
```

Audit briefs follow the same 6-field schema as a regular brief plus a final
**Capability classification** table covering every claim made by the system,
mapped to `fully-real`, `partially-real`, or `illusory` per
`auditPolicy.capabilityClassification`.

## Failure wiki vs decision wiki

This directory is the **decision wiki**: durable knowledge about why a
non-trivial decision went the way it did.

The **failure wiki** is separate. It lives in `.github/hooks/failures/`,
managed by `.github/hooks/failure_index.py`, and is queried at Phase 0 by
`FailureIndex.search(task_description)`. Failures are written automatically
by the posttool hook when a session closes with `verification_status =
blocked`. Do not store failure postmortems here, and do not store decision
briefs there.