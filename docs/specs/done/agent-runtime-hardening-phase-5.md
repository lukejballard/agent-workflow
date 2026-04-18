# Feature: Agent Runtime Hardening Phase 5

> Note: This completed spec is historical workflow context. It remains useful for
> agent-platform governance, but any product-facing assumptions inside it come from an
> inherited platform codebase.

**Status:** Done
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** `docs/specs/active/agent-runtime-hardening-phase-4.md`

---

## Problem
Phase 4 made the local verification scripts runnable from the repository Python environment,
but the first full execution exposed two remaining operator-friction issues.

First, the repo-wide verification lane is still blocked by an existing set of mechanical `ruff`
violations across backend and test files. That prevents `verify-narrow.sh` and `verify-broad.sh`
from reaching the later quality gates.

Second, the workflow now exposes the built-in terminal tool for execution-oriented agents, but the
workspace auto-approval rules do not yet explicitly allow the repository's safe verification
entrypoints. That leaves the workflow correct but still more interrupt-driven than necessary.

## Success criteria
This phase is successful when:
- the current repo-wide `ruff` backlog exposed by the verification scripts is cleared without changing behavior
- the safe verification entrypoints can be auto-approved by workspace settings without widening high-risk command approval
- the verification docs describe the new auto-approval scope honestly
- the narrow and broad verification scripts advance beyond the previous `ruff` gate so the next real blockers are visible

---

## Requirements

### Functional
- [x] Fix the current `ruff` findings surfaced by `verify-narrow.sh` and `verify-broad.sh`.
- [x] Limit code changes for lint cleanup to mechanical, no-behavior-change fixes.
- [x] Add terminal auto-approval patterns for the repository verification entrypoints under `.vscode/settings.json`.
- [x] Keep destructive, dependency-mutating, network-fetching, and remote-write commands outside the new auto-approval scope.
- [x] Update contributor docs to explain which verification commands are pre-approved and which still require review or approval.

### Non-functional
- [x] Security: preserve the existing deny and ask patterns in the pretool hook and terminal auto-approval settings.
- [x] Reliability: verification should work from the repo root in the supported local shells without requiring manual environment activation.
- [x] Documentation: runbook and setup docs must stay aligned with the actual workspace approval behavior.
- [x] Regression safety: lint cleanup must not change runtime behavior or test intent.

---

## Affected components
- `docs/specs/done/agent-runtime-hardening-phase-5.md`
- `.vscode/settings.json`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`
- `scripts/agent/verify-narrow.sh`
- `scripts/agent/verify-broad.sh`
- `src/biomechanics_ai/alerts/jira_channel.py`
- `src/biomechanics_ai/cli/commands/runs.py`
- `src/biomechanics_ai/cli/commands/sync.py`
- `src/biomechanics_ai/collector/demo_routes.py`
- `src/biomechanics_ai/collector/pipeline_routes.py`
- `src/biomechanics_ai/collector/run_routes.py`
- `src/biomechanics_ai/collector/sse_routes.py`
- `src/biomechanics_ai/collector/template_routes.py`
- `src/biomechanics_ai/sdk/stream_observer.py`
- `tests/unit/test_alert_grouping.py`
- `tests/unit/test_approval.py`
- `tests/unit/test_external_metadata.py`
- `tests/unit/test_rca_similarity.py`
- `tests/unit/test_run_engine.py`
- `tests/unit/test_sensitivity_scanner.py`

---

## External context
No new external research is required.
This phase follows the existing terminal approval and security guidance already captured in the
repository instructions and the VS Code terminal-tool behavior referenced during phase 4.

---

## Documentation impact
Update workflow docs so contributors know:
- which verification commands are safe and auto-approved
- that those approvals are intentionally narrow and do not cover destructive or mutating commands
- that the pretool approval hook remains the higher-risk guardrail

---

## Architecture plan
Use a narrow, operator-focused approach.

For lint cleanup:
- remove unused imports
- remove redundant `f` prefixes
- rename intentionally unused loop variables with leading underscores
- replace `try/except/pass` cleanup blocks with `contextlib.suppress`
- add the explicit `strict=` argument where `zip()` requires it

For approvals:
- auto-approve only the repo's verification entrypoints such as `bash scripts/agent/verify-narrow.sh`,
  `bash scripts/agent/verify-broad.sh`, and the metadata-check command
- leave destructive and environment-mutating rules unchanged

---

## Edge cases

| Edge case | Handling |
|---|---|
| Verification command is run through `bash` with the repo script path | Allow the exact script entrypoint only |
| Metadata check is run directly | Allow the exact metadata-check command only |
| A file-cleanup lint fix could alter behavior | Restrict the changes to mechanical fixes and re-run tests |
| A broader shell or Python pattern would accidentally approve unrelated commands | Avoid generic `bash` or `python` approvals without the repo command path |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Auto-approval pattern is too broad | Low | High | Match exact repo verification commands rather than generic shells or interpreters |
| Lint cleanup changes behavior accidentally | Low | Medium | Keep the fixes mechanical and verify with the existing test and verification commands |
| Later verification gates expose new unrelated failures | Medium | Low | Treat those as newly surfaced blockers rather than regressions from this change |

---

## Breaking changes
No product behavior changes are intended.
This phase only changes verification ergonomics, docs, and no-behavior-change lint cleanup.

---

## Testing strategy
- **Unit:** run the focused sync-tool test file and the relevant backend test suite reached by `verify-broad.sh`
- **Integration:** run `python scripts/agent/sync_agent_platform.py --check`
- **E2E:** run `bash scripts/agent/verify-narrow.sh` and `bash scripts/agent/verify-broad.sh`
- **Security:** confirm the auto-approval patterns remain narrow and the higher-risk pretool rules are unchanged

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Current repo-wide `ruff` findings from the verification scripts are cleared
- [x] Safe verification entrypoints are auto-approved in workspace settings
- [x] Destructive and mutating terminal approvals remain outside the safe-allow list
- [x] Workflow docs accurately describe the new approval scope
- [x] Metadata validation still passes
- [x] Focused sync-tool tests still pass
- [x] Narrow verification advances past lint and reports the next real gate or passes
- [x] Broad verification advances past lint and reports the next real gate or passes