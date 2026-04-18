# Feature: Agent Runtime Hardening Phase 7

**Status:** Done
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** S
**Supersedes:** `docs/specs/done/agent-runtime-hardening-phase-6.md`

---

## Problem
After the broad verification lane cleared lint, tests, and the execution-layer security scan,
`pip-audit` still reported known vulnerabilities in installed runtime-facing packages:

- `Pygments 2.19.2` with a fix available in `2.20.0`
- `requests 2.32.5` with a fix available in `2.33.0`

Both packages are present in the repository runtime dependency graph, so leaving them only as
environment-local upgrades would not keep future installs aligned with the verified state.

## Success criteria
This phase is successful when:
- the project dependency declarations require non-vulnerable versions of `requests` and `Pygments`
- the local virtual environment is updated to those safe versions
- `pip-audit` no longer blocks the broad verification lane on those findings

---

## Requirements

### Functional
- [x] Add safe minimum versions for `requests` and `Pygments` to the runtime dependency declarations.
- [x] Update the local virtual environment so the verification commands use the fixed versions.
- [x] Re-run the broad verification lane after the dependency upgrade.

### Non-functional
- [x] Security: only upgrade to versions that satisfy the reported fixes.
- [x] Reliability: avoid unrelated dependency churn.
- [x] Documentation: no doc changes unless contributor install guidance changes materially.

---

## Affected components
- `docs/specs/done/agent-runtime-hardening-phase-7.md`
- `pyproject.toml`
- local virtual environment package state used by `verify-broad.sh`

---

## External context
No new external research brief is required.
This phase is driven by the repository's own dependency-audit output.

---

## Documentation impact
No documentation changes are expected if contributor install commands remain the same.

---

## Architecture plan
Keep the change narrow:
- declare the fixed minimum versions in `pyproject.toml`
- install those versions into the active virtual environment
- rerun the broad verification lane to surface the next gate, if any

---

## Edge cases

| Edge case | Handling |
|---|---|
| A newer transitive package still resolves to the vulnerable version | Add the explicit runtime dependency lower bound |
| The active venv remains on the old version after the file change | Upgrade the package in the configured venv before rerunning audit |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dependency upgrade introduces unrelated behavior drift | Low | Medium | Limit the change to the two audited packages and rerun the verification lane |
| The fixed version is unavailable | Low | High | Use the exact fix version reported by `pip-audit` or the next available safe version |

---

## Breaking changes
No intentional breaking changes are expected.

---

## Testing strategy
- **Integration:** rerun `bash scripts/agent/verify-broad.sh`
- **Security:** confirm `pip-audit` no longer reports the current `requests` and `Pygments` CVEs

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] `requests` and `Pygments` minimum versions are updated in the project dependency declarations
- [x] The local virtual environment is upgraded to safe versions
- [x] Broad verification advances past the current dependency-audit failures or passes fully