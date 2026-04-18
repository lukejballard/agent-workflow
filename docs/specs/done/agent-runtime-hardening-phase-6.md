# Feature: Agent Runtime Hardening Phase 6

**Status:** Done
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** `docs/specs/done/agent-runtime-hardening-phase-5.md`

---

## Problem
After the verification ergonomics and formatting backlog were cleared, `verify-broad.sh`
advanced to the backend security scan and surfaced real `bandit` findings in the execution layer.

The affected surfaces are:
- dynamic execution of user-authored pipeline step code in the pipeline-definition runner
- SSH remote execution defaults and shell command construction in the SSH target

The verification lane should not be blocked by avoidable security findings, but the fixes must also
preserve the intended execution model for user-authored pipelines.

## Success criteria
This phase is successful when:
- the SSH target uses secure host-key verification defaults
- the SSH target constructs remote shell commands defensibly and avoids unsafe path handling
- the dynamic step-execution path is either materially hardened or explicitly suppressed with a narrow, justified rationale where dynamic execution is intrinsic to the feature
- targeted regression tests cover the SSH behavior changes
- `verify-broad.sh` advances past the current `bandit` findings so the next real gate is visible

---

## Requirements

### Functional
- [x] Review and fix the `bandit` findings in `src/execution/ssh_target.py`.
- [x] Use host-key verification that is secure by default for SSH execution.
- [x] Quote or otherwise constrain remote shell command construction for SSH execution.
- [x] Avoid hardcoded insecure remote temp-path handling in the SSH target.
- [x] Review the dynamic `exec` usage in `src/execution/pipeline_definition_runner.py` and choose the smallest defensible mitigation.
- [x] Add regression tests for the SSH target behavior changes.

### Non-functional
- [x] Security: do not widen execution permissions or silently disable host verification by default.
- [x] Reliability: keep existing local pipeline preview behavior intact.
- [x] Regression safety: preserve current runner and SSH execution contracts unless an explicit security default must tighten them.
- [x] Documentation: update contributor docs only if the workflow or supported configuration behavior materially changes.

---

## Affected components
- `docs/specs/done/agent-runtime-hardening-phase-6.md`
- `src/execution/pipeline_definition_runner.py`
- `src/execution/ssh_target.py`
- `tests/unit/test_pipeline_definition_runner.py`
- `tests/unit/test_ssh_target.py`
- `docs/runbooks/agent-mode.md` if workflow guidance changes
- `docs/copilot-setup.md` if contributor guidance changes

---

## External context
No new external research brief is required.
This phase is driven by the repository's own security scan and the local security instructions.

---

## Documentation impact
No contributor-doc changes are expected unless the SSH target's supported configuration contract changes in a way contributors must know about.
If the implementation only tightens internals and defaults while keeping the workflow the same, existing docs remain accurate.

---

## Architecture plan
Use the smallest safe changes that satisfy the security scan without inventing a new execution framework.

For the SSH target:
- switch to a secure host-key policy by default
- build remote paths from a configurable work directory instead of a hardcoded temp path
- quote remote commands with shell-safe primitives

For the pipeline-definition runner:
- keep user-authored step execution working
- if dynamic execution remains intrinsic, isolate it behind a small helper and document the intentional scope with a narrow suppression rather than pretending the feature is static code

---

## Edge cases

| Edge case | Handling |
|---|---|
| SSH config omits host | Fail as before with a clear configuration error |
| SSH config points at an unknown host key | Reject by default rather than auto-trusting |
| SSH python executable includes flags | Split and quote the remote command safely |
| Remote work directory includes shell-sensitive characters | Quote path-bearing commands defensively |
| Pipeline step code is empty or invalid | Preserve existing validation and failure behavior |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Tightening SSH host verification breaks permissive existing setups | Medium | Medium | Use secure defaults and keep any opt-out explicit rather than implicit |
| Over-correcting the runner breaks preview execution | Low | High | Keep the dynamic execution path small and covered by existing runner tests |
| New SSH tests overfit to Paramiko internals | Low | Low | Mock only the SSH client boundary and assert the behavior we own |

---

## Breaking changes
Potentially yes for insecure SSH setups that relied on silently trusting unknown host keys.
If this default changes, note it in the final summary and keep any opt-out explicit.

---

## Testing strategy
- **Unit:** extend runner tests only if the dynamic-exec wrapper behavior changes; add dedicated SSH target tests for host-key policy and command construction
- **Integration:** run `python scripts/agent/sync_agent_platform.py --check`
- **E2E:** run `bash scripts/agent/verify-broad.sh`
- **Security:** confirm the `bandit` findings addressed in this phase no longer block the broad verification lane

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] Current `bandit` findings in the execution layer are addressed or narrowly justified
- [x] SSH target defaults to host-key verification rather than auto-trusting unknown hosts
- [x] SSH remote command construction is safely quoted
- [x] SSH target regression tests exist and pass
- [x] Metadata validation still passes
- [x] Broad verification advances past the current security-scan failures or passes fully