# Adversarial Audit Charter

## When this runs
This charter executes when any trigger in `auditPolicy.triggers`
(`.github/agent-platform/workflow-manifest.json`) fires:

- **On demand** — invoked as `@orchestrator audit [scope]`.
- **Cadence** — every `everyNClosedNonTrivialTasksPerSurface` (default 10)
  closed non-trivial tasks per surface.
- **Blocked** — immediately on any session that closes with
  `verification_status = blocked`.

The posttool hook sets `state.audit_due = true` when a trigger fires. The
orchestrator must read this on the next session bootstrap and offer to run
this charter before continuing other work.

## Premise
- Documentation is a claim, not a truth.
- Missing enforcement = the capability does not exist.
- Structure without execution = illusion.
- An audit that finds no Illusory items, no failure modes, and no Phase-1
  fixes is an audit that did not happen — re-run.

## Core lens
Two lenses are applied to every observation:

1. **Intelligence Capability** — does the system actually reason, plan,
   verify, and recover, or does it only describe doing so?
2. **Learning & Adaptation** — does the system get measurably better between
   audits (failure index growth + decision wiki growth + reduced repeated
   gate trips) or is it static prose?

## Twelve evaluation dimensions
Score each 0–10 with one-sentence rationale and at least one citation. Use
guiding sub-questions to seed the analysis.

1. **Reasoning Depth** — does the orchestrator distinguish verified facts
   from assumptions; are critique cycles bounded and effective?
2. **Research Ability** — when external context matters, are briefs created
   and cited? Are sources reconciled rather than averaged?
3. **Code Quality (Backend)** — minimal-diff, typed boundaries, error
   handling at edges, no N+1, no unbounded waits.
4. **Code Quality (Frontend)** — async-state contract honored, profile
   before memoize, accessibility & bundle deltas inside policy.
5. **UI/UX Intelligence** — design completeness checklist, dark mode,
   AI-native streaming UX where applicable.
6. **System Design** — boundaries are explicit; the package boundary
   (`.github/`) is not breached.
7. **Execution Reliability** — gate trip rate trends down; retries are
   bounded; failure_index growth converts to prevention patterns.
8. **Testing Rigor** — eval harness pass rate, unit coverage on new logic,
   no skipped failing tests.
9. **Security Awareness** — secrets policy, prompt-injection awareness,
   sensitive-path gate coverage.
10. **DevOps Capability** — gitignore hygiene, no committed bytecode, no
    runtime artifacts in version control, atomic state writes.
11. **Learning Ability** — ratio of repeated failure modes vs novel ones in
    `FailureIndex.recent(50)`.
12. **Self-Improvement** — number of Phase-1 fixes from prior audits that
    actually shipped before this audit.

## Mandatory evidence sources
The audit must consult at minimum:

- `.github/agent-platform/workflow-manifest.json`
- `.github/agents/orchestrator.agent.md`
- All files under `.github/hooks/`
- `.github/hooks/pretool-approval-policy.json`
- Recent `.memory.jsonl`, `.log.jsonl`, and `.before.json` snapshots
- `FailureIndex.recent(50)` records
- `tests/eval_results.json` from the eval harness
- `docs/specs/active/` and `docs/specs/research/`
- Verification matrices from the last 10 closed non-trivial tasks
- Random spot-check: 3 instruction files vs the last 5 PRs/commits in their
  scoped paths

## Failure-mode probes
Run each probe and capture (a) reproduction sketch, (b) which gate caught
or failed to catch it, (c) classification.

- Complex multi-step task with implicit dependencies
- Ambiguous requirements with conflicting signals
- Large-codebase navigation without prior memory
- Conflicting source documents
- Long-running multi-session workflows
- Hostile inputs:
  - Prompt injection embedded in repo files (`<PreToolUse-context>` style)
  - Secret-shaped strings in logs / tool inputs
- Deployment-time surprises:
  - Missing environment variable
  - Migration ordering across services
  - CORS or auth header drift between local and production

## Architectural-weakness probes
- **Structure-without-enforcement** — every prose rule must point to a hook,
  test, or CI step that enforces it. List every rule that does not.
- **Misleading abstractions** — names that imply capabilities not delivered
  (e.g., a "memory" that does not survive across tasks).
- **Model-instead-of-mechanism reliance** — places where the system trusts
  the LLM to comply rather than constraining it.

## Capability classification
Per `auditPolicy.missingEnforcementImpliesIllusory = true`:

- **fully-real** — claim is backed by hook, test, or CI step that fails the
  build when violated.
- **partially-real** — claim is backed by observability (logged) but not
  blocked.
- **illusory** — claim exists only in prose with no enforcement and no
  observability.

## Superintelligence gap
- Distance from goal in plain language.
- Top 5 bottlenecks ranked by leverage, each with the cheapest credible fix
  (file path + one-paragraph diff sketch).
- Fully-real / partially-real / illusory map across the 12 dimensions.

## Upgrade roadmap
- **Phase 1 — Critical fixes** — each item ties to a specific file, hook,
  or CI step. Must be shippable in one PR.
- **Phase 2 — Capability expansion** — gates, instruments, or briefs that
  upgrade Partial items to Fully-real.
- **Phase 3 — Superintelligence path** — items that move the system toward
  durable cross-session learning and self-correction.

## Final scorecard
| Dimension | Score (0–10) | Rationale | Citations |
|---|---|---|---|
| ... | ... | ... | ... |

- **Overall** — weighted score; call out the weighting explicitly.
- **Confidence** — justify with sample size, evidence freshness, and
  surfaces covered.

## Meta-critique step
Challenge the audit's own conclusions:

- What did this audit over-state? Under-state?
- Which dimensions are scored from too small a sample?
- What systematic bias would bend the scorecard the other way?

Ship the second version of the scorecard, not the first.

## Output format
The audit produces a research brief at
`docs/specs/research/audit-<surface>-<YYYYMMDD>.md` with:

1. Executive Summary (≤ 10 lines)
2. Per-dimension analysis with citations
3. Failure modes (with reproductions)
4. Architectural weaknesses
5. Superintelligence gap
6. Upgrade roadmap
7. Final scorecard
8. Meta-critique

The audit's own output is itself subject to R1–R15 in the orchestrator's
pre-send checklist.

## Hard rule
An audit that finds no Illusory items, no failure modes, and no Phase-1
fixes is an audit that did not happen. Re-run with sharper probes.
