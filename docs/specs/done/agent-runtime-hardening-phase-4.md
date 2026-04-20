# Feature: Agent Runtime Hardening Phase 4

**Status:** In Review
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** `docs/specs/active/agent-runtime-hardening-phase-3.md`

---

## Problem
The canonical workflow manifest already models `terminal-exec` for the main implementation paths,
but the current agent and prompt frontmatter do not consistently expose the built-in terminal tool.

The local verification scripts also assume Python quality tools are available directly on `PATH`.
On Windows and other shells that are not running inside an activated virtual environment, that causes
`verify-narrow.sh` and `verify-broad.sh` to fail before they reach the intended repo checks.

Without aligning the frontmatter and the scripts, the documented workflow says execution should be
available while the practical developer path remains flaky.

## Success criteria
This phase is successful when:
- execution-oriented agents and prompt wrappers expose the built-in terminal tool consistently
- review-only and research-only entrypoints remain least-privilege and do not gain unnecessary execution access
- repo-local verification scripts use the repository Python environment when available instead of assuming shell `PATH`
- contributor docs explain terminal availability and the existing approval boundaries honestly

---

## Requirements

### Functional
- [x] Add the built-in terminal tool to the default orchestrator agent.
- [x] Add the built-in terminal tool to execution-oriented specialist agents that are expected to implement, test, or verify local changes.
- [x] Add the built-in terminal tool to execution-oriented prompt wrappers whose tool lists override agent defaults.
- [x] Keep review-only, research-only, and planning-only entrypoints least-privilege unless the workflow manifest explicitly requires more.
- [x] Update `verify-narrow.sh` and `verify-broad.sh` to detect the repo-local Python executable on Windows and POSIX before falling back to `python`.
- [x] Use module invocation for Python quality tools in the verification scripts so they run from the chosen Python environment.

### Non-functional
- [x] Security: keep the existing approval policy and auto-approval boundaries intact; do not widen risky command approvals.
- [x] Reliability: verification scripts must behave consistently in shells where the virtual environment is not pre-activated.
- [x] Documentation: update workflow and setup docs so agent tool access and approval behavior remain accurate.
- [x] Traceability: keep the workflow manifest as the authority and align markdown guidance to it.

---

## Affected components
- `docs/specs/active/agent-runtime-hardening-phase-4.md`
- `.github/agents/orchestrator.agent.md`
- `.github/agents/implementer.agent.md`
- `.github/agents/qa.agent.md`
- `.github/agents/cleanup.agent.md`
- `.github/prompts/single-entry-workflow.prompt.md`
- `.github/prompts/brownfield-improve.prompt.md`
- `.github/prompts/bugfix-workflow.prompt.md`
- `.github/prompts/greenfield-feature.prompt.md`
- `.github/prompts/generate-tests.prompt.md`
- `scripts/agent/verify-narrow.sh`
- `scripts/agent/verify-broad.sh`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`

---

## External context
No new reusable research brief is required.
This phase aligns existing repo metadata and documentation with the already-defined `terminal-exec`
capability in `.github/agent-platform/workflow-manifest.json` and the existing workspace approval model.

---

## Documentation impact
Update the setup guide and runbook so contributors know:
- which workflow entrypoints expose terminal execution
- that prompt file tool lists can override agent defaults
- that terminal access is still governed by `.github/hooks/pretool-approval-policy.json` and `.vscode/settings.json`

---

## Architecture plan
Keep the capability model conservative.

For workflow entrypoints:
- align execution-oriented agent and prompt frontmatter with the manifest by adding the built-in `terminal` tool
- leave review-only, planner, analyst, and researcher paths unchanged

For verification scripts:
- resolve `PYTHON_BIN` from the repo-local virtual environment first
- prefer `python -m <module>` for Python quality tools so the selected environment provides the executables
- keep frontend commands unchanged because they already run from the local frontend directory

---

## Edge cases

| Edge case | Handling |
|---|---|
| Windows repo with `.venv/Scripts/python.exe` | Use that interpreter automatically |
| POSIX repo with `.venv/bin/python` | Use that interpreter automatically |
| No repo-local virtual environment | Fall back to `python` and fail normally if dependencies are missing |
| Prompt file overrides the agent tool list | Add terminal to the prompt frontmatter as well |
| High-risk terminal commands | Continue to rely on the existing approval hook and workspace settings |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Terminal access is widened too broadly | Low | Medium | Limit the change to execution-oriented agents and prompts only |
| Script changes mask missing dependencies | Low | Low | Use the selected interpreter but still fail clearly when a module is absent |
| Docs overclaim auto-approval behavior | Low | Medium | Describe the approval hook and settings explicitly instead of promising silent execution |

---

## Breaking changes
No product behavior changes are intended.
This phase changes contributor workflow entrypoints and local verification ergonomics only.

---

## Testing strategy
- **Unit:** existing agent-platform sync tests remain the regression check for workflow metadata validation
- **Integration:** run `python scripts/agent/sync_agent_platform.py --check` and the focused sync-tool pytest file
- **E2E:** run `bash scripts/agent/verify-narrow.sh` and `bash scripts/agent/verify-broad.sh`
- **Security:** confirm terminal approval behavior is unchanged and still mediated by the existing hook and workspace settings

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Execution-oriented agents expose terminal access
- [x] Execution-oriented prompt wrappers expose terminal access
- [x] Verification scripts use the repo-local Python interpreter when available
- [x] Verification scripts invoke Python quality tools through the selected interpreter
- [x] Runbook and setup docs stay accurate about terminal access and approval boundaries
- [x] Metadata check passes after the change
- [x] Focused sync-tool unit tests pass after the change
- [x] Narrow and broad verification scripts run past the previous `ruff`-not-found failure