# Feature: Agent Workflow Simplification Phase 1

**Status:** In Review
**Created:** 2026-04-14
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** None

---

## Problem
The workflow audit found that the repository's agent control plane has stronger documentation than
enforcement. Workflow metadata can drift without failing the PR lane, and core workflow docs still
contain stale claims about missing workspace surfaces even though those directories exist.

If this remains unchanged, contributors will keep treating the workflow manifest and companion docs
as canonical while the repo allows silent drift between metadata, docs, and actual workflow files.

## Success criteria
This phase is successful when workflow-surface changes fail fast if companion workflow docs are not
updated, metadata sync is blocking in the PR lane, and the workflow docs stop claiming the repo
layout is only a target topology.

---

## Requirements

### Functional
- [x] Add a repo-local workflow traceability checker under `scripts/agent/` that inspects changed
      files and fails when workflow control-plane surfaces change without the companion workflow docs.
- [x] Add unit tests for the new checker that cover compliant workflow changes, missing companion
      docs, docs-only changes, and non-workflow changes.
- [x] Update `.github/workflows/pr-quality.yml` so workflow-surface PRs run the new checker as a
      blocking step.
- [x] Update `.github/workflows/pr-quality.yml` so `python scripts/agent/sync_agent_platform.py --check`
      is a blocking PR-quality step for workflow-surface changes.
- [x] Refresh generated `.github/agent-platform/` metadata so the sync check passes again.
- [x] Remove stale workspace-snapshot disclaimers from `docs/runbooks/agent-mode.md` and
      `docs/copilot-setup.md`.
- [x] Update the runbook and setup guide so they explain the blocking workflow-governance checks and
      when companion workflow docs must change.

### Non-functional
- [x] Performance: keep the solution repo-local and static; do not introduce a service or daemon.
- [x] Security: do not widen tool access, approval policy, or remote-write permissions in this phase.
- [x] Observability: failure output from the new checker must state which companion docs are missing.
- [x] Documentation: workflow docs must describe the actual workspace and enforcement behavior.

---

## Affected components
- `docs/specs/active/agent-workflow-simplification-phase-1.md`
- `docs/specs/research/agent-workflow-simplification-research.md`
- `scripts/agent/check_workflow_traceability.py`
- `tests/unit/test_check_workflow_traceability.py`
- `.github/workflows/pr-quality.yml`
- `.github/agent-platform/repo-map.json`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
This phase reuses external guidance captured in:
- `docs/specs/research/agent-architecture-benchmark-research.md`
- `docs/specs/research/agent-workflow-simplification-research.md`

That guidance materially shapes this phase by favoring simpler control loops, executable workflow
checks, and blocking drift detection over additional prompt or agent complexity.

---

## Documentation impact
The workflow runbook and setup guide must change because this phase alters the contributor-facing PR
governance story and removes stale claims about the workspace layout.

No product-facing docs are required because this work changes contributor workflow enforcement only.

---

## Architecture plan
Add one small, standard-library Python script that receives a changed-file set and enforces a narrow
rule: if workflow control-plane surfaces change, the PR must also update the shared workflow docs.

Wire that script into `pr-quality.yml` alongside the existing spec gate and a blocking metadata-sync
check. Keep the current advisory product-code warnings in place; this phase only hardens the workflow
control plane.

Preferred approach:
- add a dedicated checker script with unit tests
- keep the rule set narrow and explicit
- make sync validation and workflow-doc traceability blocking for workflow-surface changes

Alternative considered:
- encode the workflow-doc requirement directly in inline shell inside the GitHub Actions workflow

Why rejected:
- the logic would be harder to test locally
- the rule set would become another opaque CI-only behavior
- contributors would have no reusable local entry point for debugging failures

---

## API design

No product API changes.
This phase changes workflow scripts, metadata, CI, and contributor docs only.

---

## Data model changes

No application data model changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the checker script, revert the PR-quality changes, and restore the prior docs.
- Breaking change? No product-facing breaking change. Workflow PRs become stricter.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Only workflow docs change | The new checker must pass without requiring more companion files. |
| No workflow surface changes are present | The new checker must pass and stay effectively inert. |
| Workflow files change but only one companion doc is updated | The checker must fail with a clear missing-doc list. |
| Metadata drift already exists before the PR | The blocking sync check must fail and surface the stale artifact. |
| Generated metadata adds legitimate paths after a sync write | Refresh the generated file in the same change set. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The new checker is too strict for low-value workflow edits | Medium | Medium | Keep the workflow surface list narrow and test representative cases. |
| The PR lane blocks on generated metadata churn | Medium | Medium | Refresh the generated metadata in the same patch and keep the sync tool deterministic. |
| Docs drift elsewhere outside the enforced surfaces | Medium | Low | Keep the existing advisory job for broader doc and test hints. |

---

## Breaking changes
No runtime or API breaking changes.
This phase makes workflow governance stricter for contributor-facing control-plane changes.

---

## Testing strategy
- **Unit:** add pytest coverage for the new workflow traceability checker.
- **Integration:** run `python scripts/agent/check_workflow_traceability.py` against representative
  changed-file sets.
- **Integration:** run `python scripts/agent/sync_agent_platform.py --check` after refreshing metadata.
- **E2E:** not required; this is CI and documentation enforcement work.
- **Security:** verify the phase does not widen tools, approvals, or remote-write behavior.

### Verification completed
- `python -m pytest tests/unit/test_check_workflow_traceability.py -q` passed.
- `python scripts/agent/sync_agent_platform.py --check` passed after refreshing generated metadata.
- Editor diagnostics reported no errors in the new script, unit tests, workflow file, docs, and spec.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Workflow traceability checker exists under `scripts/agent/`
- [x] Unit tests cover the checker behavior for workflow and non-workflow change sets
- [x] PR quality runs the checker as a blocking step for workflow-surface changes
- [x] PR quality runs `python scripts/agent/sync_agent_platform.py --check` as a blocking step
- [x] Generated agent-platform metadata is refreshed and the sync check passes
- [x] `docs/runbooks/agent-mode.md` no longer claims key repo surfaces are absent
- [x] `docs/copilot-setup.md` no longer claims key repo surfaces are absent
- [x] Runbook and setup guide explain the blocking workflow-governance behavior accurately