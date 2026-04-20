# Feature: Agent Core Ultraminimal Hardened Mind

**Status:** Done
**Created:** 2026-04-19
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** N/A

---

## Problem
The current `agent-core` package still ships a packaged spec scaffold and validator, and its orchestrator still treats file-backed specs as the default requirement lock. That adds package surface and extra folders the user no longer wants. At the same time, the remaining orchestrator is still too soft around memory discipline, bounded retries, and evidence-backed verification for the “hyperintelligent mind” goal.

## Success criteria
The shipped package keeps only the core single-mind surfaces: top-level guidance, one orchestrator, one workflow manifest, and hooks. The packaged spec scaffold and validator are removed. The orchestrator and manifest explicitly encode requirement locking, memory discipline, bounded retry behavior, and verification semantics strongly enough that the package becomes smaller and more operationally intelligent at the same time.

---

## Requirements

### Functional
- [x] Remove the packaged validator from `agent-core/github/agent-platform/`.
- [x] Remove the packaged spec scaffold from `agent-core/github/specs/`.
- [x] Replace “spec required” language with “explicit requirement lock required” across the packaged guidance.
- [x] Strengthen the orchestrator and manifest with explicit policies for memory, retries, and verification.
- [x] Update README architecture and dependency documentation to match the smaller package.

### Non-functional
- [x] Performance: no new dependencies or runtime steps.
- [x] Security: hook protections remain intact and documented.
- [x] Accessibility: not applicable; no UI change.
- [x] Observability: final package guidance still emphasizes evidence, traceability, and explicit state.

---

## Affected components
- `agent-core/README.md`
- `agent-core/github/AGENTS.md`
- `agent-core/github/copilot-instructions.md`
- `agent-core/github/agents/orchestrator.agent.md`
- `agent-core/github/agent-platform/workflow-manifest.json`
- `agent-core/github/agent-platform/validate.py` (remove)
- `agent-core/github/specs/_template.md` (remove)
- `agent-core/github/specs/active/` (remove)

---

## External context
- `docs/hyperintelligence_plan.md` materially shapes this design.
- Key constraints to encode in the minimal package:
  - hyperintelligence comes from strong runtime semantics, explicit memory, hard verification loops, and observability
  - state is the product
  - memory requires lifecycle controls
  - failure recovery and retry must be bounded and evidence-based

---

## Documentation impact
README, AGENTS guidance, and copilot instructions must change because they still describe packaged spec files and validator usage that the ultraminimal package will no longer include.

---

## Architecture plan
Keep the package centered on six shipped files/classes of surfaces:
- `.github/AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/agents/orchestrator.agent.md`
- `.github/agent-platform/workflow-manifest.json`
- `.github/hooks/pretool-approval-policy.json`
- `.github/hooks/hooks.py`

Replace packaged specs with a requirement-lock rule:
- use existing repo requirements when they exist
- otherwise create an inline requirements contract before coding

Strengthen the manifest as the policy kernel by adding memory, retry, and verification policy sections.

Strengthen the orchestrator so it explicitly:
- tracks working vs episodic memory behavior
- classifies failures and retries only when a changed strategy exists
- produces evidence-backed verification and confidence summaries

---

## API design
No API changes.

---

## Data model changes
No data model changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Consuming repo already has its own spec system | Orchestrator reads it as an external requirement source rather than relying on a packaged scaffold |
| Non-trivial task has no pre-existing spec or doc | Orchestrator creates an inline requirements contract before coding |
| Task fails twice for the same reason | Stop retrying and escalate with evidence instead of looping |
| Memory is stale or unverifiable | Treat as weak evidence and avoid grounding decisions on it |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Removing the validator reduces package self-checking | Medium | Medium | Keep manifest simple and validate via JSON parsing + diagnostics during implementation |
| Removing packaged specs weakens planning discipline | Medium | High | Replace spec requirement with explicit requirement-lock rules in core guidance |
| New policy text becomes verbose instead of stronger | Medium | Medium | Keep policy language concise and operational, not aspirational |

---

## Breaking changes
Consumers of `agent-core` can no longer rely on packaged `.github/specs/` or `.github/agent-platform/validate.py`. Requirement locking remains part of the workflow, but the mechanism becomes host-repo requirements or inline requirement contracts.

---

## Testing strategy
- **Unit:** none added.
- **Integration:** verify edited package files have no diagnostics and JSON remains valid.
- **E2E:** not applicable.
- **Performance:** none needed.
- **Security:** confirm hook surfaces remain present and unchanged.

---

## Acceptance criteria
- [x] Packaged validator removed
- [x] Packaged spec scaffold removed
- [x] Package guidance now uses explicit requirement locking instead of packaged specs
- [x] Orchestrator and manifest encode memory, retry, and verification semantics more strongly
- [x] Package structure and docs match the new ultraminimal layout