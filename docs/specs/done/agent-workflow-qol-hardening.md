# Feature: Agent Workflow QoL Hardening

**Status:** Implemented
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** `docs/specs/active/single-entry-agent-architecture.md`

---

## Problem
The repository now has a credible single-entry orchestrator, but the workflow still
leaves too much quality behavior to manual invocation. Test hardening, regression attack,
documentation completeness, and continuous repo-health auditing are present as isolated
primitives rather than a coherent operating model.

The current research path also stops short of the user's desired breadth: the workflow
can fetch specific URLs and GitHub references, but it does not clearly document that whole-web
search and approval-policy changes are platform-level concerns outside `.github/`.

The spec-source routing is also muddy. The repository already contains Speckit artifacts under
`specs/` and OpenSpec change proposals under `openspec/changes/`, but the workflow does not
clearly prefer Speckit for greenfield work and OpenSpec for brownfield changes.

If left unresolved, the agent stack will stay functional but inconsistent: quality gates will
be unevenly applied, audit behavior will remain mostly ad hoc, documentation drift will recur,
and contributors may assume the workflow supports broader web discovery than the available tools
actually allow.

## Success criteria
The workflow should automatically consider the right quality and audit passes for non-trivial work,
create persistent research artifacts when external context matters, and treat documentation coverage
as part of definition-of-done rather than an optional follow-up.

Contributors should be able to read the orchestrator contract, runbook, setup guide, PR template,
and active spec template and see the same story about:
- multi-angle testing expectations
- continuous audit behavior
- research-first external context behavior
- brownfield OpenSpec versus greenfield Speckit routing
- workspace approval hooks and guarded tool policy
- documentation and traceability requirements
- platform constraints around search and approval behavior

---

## Requirements

### Functional
- [x] Create or refresh one active working spec that defines the QoL hardening architecture and its scope boundaries.
- [x] Update the default orchestrator contract so non-trivial work automatically considers the relevant quality passes by task type.
- [x] Strengthen the QA/test-generation path so it explicitly covers unit, integration, regression, error-path, auth-boundary, accessibility, and performance-sensitive verification when relevant.
- [x] Add one reusable regression-audit skill under `.github/skills/` for brownfield and high-regression-risk work.
- [x] Add one reusable documentation-audit skill under `.github/skills/` for workflow and architecture changes.
- [x] Add one reusable continuous-audit skill under `.github/skills/` to define post-merge repo-health auditing behavior.
- [x] Add one new CI workflow under `.github/workflows/` for scheduled or post-merge continuous audits.
- [x] Extend the PR quality workflow to warn on missing documentation, weak traceability, or missing test intent where feasible without destabilizing contributor flow.
- [x] Update the research workflow so external-context tasks create or reference a reusable brief under `docs/specs/research/`.
- [x] Update the spec template and traceability skill so external research and documentation coverage are first-class tracked artifacts.
- [x] Update the setup and runbook docs so they clearly distinguish in-repo workflow behavior from platform-level capabilities such as web search tooling and tool approvals.
- [x] Add workspace MCP configuration for broader web search so the repo can go beyond fetch-only external context when credentials are supplied.
- [x] Route brownfield workflow guidance to OpenSpec change artifacts under `openspec/changes/` and keep Speckit guidance for greenfield feature work.
- [x] Add workspace approval policy automation via `.github/hooks/` and `.vscode/settings.json` so destructive or sensitive tool usage requires explicit approval.

### Non-functional
- [x] Performance: the new quality and audit rules should preserve the single-entry workflow instead of reintroducing mandatory manual agent handoffs.
- [x] Security: the workflow must not claim whole-web search or autoapproval behavior that the current tool contract cannot enforce.
- [x] Accessibility: UI-focused task paths must explicitly consider accessibility and visual QA rather than treating them as optional polish.
- [x] Observability: continuous audit behavior must define how findings are surfaced, categorized, and kept mostly informational until tuned.
- [x] Security: broader web-search configuration must use environment variables rather than committing credentials.
- [x] Security: approval automation must protect hook files and approval config surfaces from silent agent edits.

---

## Affected components
- `.github/agents/orchestrator.agent.md`
- `.github/agents/qa.agent.md`
- `.github/agents/researcher.agent.md`
- `.github/copilot-instructions.md`
- `.github/prompts/generate-tests.prompt.md`
- `.github/prompts/research.prompt.md`
- `.github/skills/adversarial-review/SKILL.md`
- `.github/skills/requirements-traceability/SKILL.md`
- `.github/skills/test-hardening/SKILL.md`
- `.github/skills/visual-qa/SKILL.md`
- `.github/skills/regression-audit/SKILL.md`
- `.github/skills/documentation-audit/SKILL.md`
- `.github/skills/continuous-audit/SKILL.md`
- `.github/workflows/pr-quality.yml`
- `.github/workflows/continuous-audit.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/hooks/`
- `.vscode/mcp.json`
- `.vscode/settings.json`
- `.env.example`
- `scripts/agent/pretool_approval_policy.py`
- `docs/specs/_template.md`
- `docs/runbooks/agent-mode.md`
- `docs/copilot-setup.md`
- `docs/specs/research/`

---

## Architecture plan
Keep the existing single-entry orchestrator and extend it rather than introducing a new
default agent.

Preferred approach:
1. Encode a quality trigger matrix directly in the orchestrator and always-on instructions.
2. Expand the QA and test-hardening assets so they attack changes from more angles.
3. Introduce a scheduled and post-merge continuous audit layer that is mostly informational at first.
4. Formalize research artifacts and documentation coverage as traceable workflow outputs.
5. Document the hard boundary between what `.github/` can change and what requires platform-level MCP or approval configuration.
6. Configure workspace MCP for search expansion and document that editor approval policy remains separate.
7. Treat OpenSpec as the preferred upstream artifact system for brownfield changes and Speckit as the preferred upstream system for greenfield feature planning.
8. Add deterministic workspace approval hooks so destructive commands and edits to approval-sensitive files are gated even when prompt instructions are ignored.

Alternative considered:
- Add a separate default auditor or tester agent that users must switch into for quality work.

Why rejected:
- It would fragment the single-entry model and reintroduce the same manual workflow sprawl the repo just removed.
- The real need is better automatic trigger behavior, not more top-level chat modes.

---

## API design

No product runtime API changes.
This feature changes workflow architecture, prompts, skills, CI policies, templates, and docs.

---

## Data model changes

No application schema changes.

### Migration notes
- Is this migration reversible? Yes
- Rollback plan: remove the new skills and continuous-audit workflow, restore the previous orchestrator/docs/templates, and archive the QoL spec.
- Breaking change? No application-facing breaking change. Contributor workflow expectations become stricter and more explicit.

---

## Edge cases

| Edge case | Handling |
|---|---|
| Task is trivial | The orchestrator may compress phases, but the docs should still distinguish that from non-trivial multi-gate work. |
| Task touches both frontend and backend | The trigger matrix should allow multiple quality paths to apply at once instead of picking only one. |
| External context is useful but not critical | The orchestrator may do lightweight fetch/github research without creating a full research brief. |
| User asks for whole-web search or autoapproval | The workflow docs must state that this requires platform-level tooling/configuration outside `.github/`. |
| Tavily credentials are absent | The workspace should keep the search MCP entry inert except for fetch/github research, and docs should explain the requirement clearly. |
| Brownfield task has no OpenSpec change yet | The workflow should instruct contributors to create or refresh an OpenSpec change proposal before reconciling it into `docs/specs/active/`. |
| The agent attempts to edit hook or approval-policy files | Workspace hooks and approval settings should force manual review instead of silently auto-approving those edits. |
| Continuous audit produces noisy findings | Keep audit results informational first, document tuning expectations, and avoid blocking merges until signal is trusted. |
| Workflow files change without docs updates | The documentation-audit skill and PR quality gate should flag the drift. |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The trigger matrix becomes too broad and noisy | Medium | High | Keep it task-shaped and document when checks are required vs recommended. |
| Continuous audit workflows produce alert fatigue | Medium | High | Start with informational reporting and tighten only after tuning. |
| Contributors assume new research tooling exists when it does not | Medium | High | Document the MCP and approval boundary explicitly in runbook and setup docs. |
| New skills overlap confusingly with existing ones | Medium | Medium | Give each new skill a narrow role and update the runbook skill table in the same patch. |
| Search MCP is configured but credentials are missing or invalid | Medium | Medium | Use environment variables only, document setup in `.env.example` and setup docs, and keep fetch/github as fallback. |
| Brownfield and greenfield planning paths diverge inconsistently | Medium | High | Update prompts, orchestrator docs, and setup guide in the same patch and keep `docs/specs/active/` as the execution-time reconciliation point. |
| Approval hooks block too aggressively and slow normal work | Medium | Medium | Limit deterministic denials to destructive commands and sensitive config surfaces; use `ask` rather than `deny` for reviewable operations. |

---

## Breaking changes
No runtime API or schema changes.
This does change workflow expectations for contributors: documentation coverage,
regression thinking, and continuous audit awareness become explicit parts of the
agent architecture.

---

## Testing strategy
- **Unit:** N/A for product code.
- **Integration:** Verify that all new skill, prompt, workflow, and doc references resolve to real files and describe the same behavior.
- **Integration:** Verify that `.vscode/mcp.json` and `.env.example` describe the same Tavily setup and that the workflow docs describe the same brownfield/greenfield routing.
- **Integration:** Verify that `.github/hooks/` and `.vscode/settings.json` describe the same approval policy and that the hook script returns valid `PreToolUse` decisions.
- **E2E:** Smoke-test representative orchestrator scenarios for feature work, bugfix, review, research, and audit prompts.
- **Performance:** Ensure the added workflow behavior does not require extra manual handoffs for normal tasks.
- **Security:** Verify the docs and contracts do not overclaim search or approval capabilities.

---

## Acceptance criteria
All must be checked before this spec is considered done.

- [x] The QoL hardening architecture is captured in an active spec with explicit scope boundaries.
- [x] The orchestrator and always-on instructions define a clear task-to-quality trigger matrix.
- [x] QA and test-generation guidance explicitly cover regression and multi-angle verification.
- [x] A regression-audit skill exists and is referenced by the workflow for brownfield work.
- [x] A documentation-audit skill exists and is referenced by the workflow for workflow/docs-sensitive changes.
- [x] A continuous-audit skill and workflow exist for scheduled or post-merge repo-health auditing.
- [x] The PR workflow includes soft warnings for missing docs or traceability coverage where feasible.
- [x] The research workflow persists reusable briefs under `docs/specs/research/` when external context materially shapes the answer.
- [x] The spec template and traceability skill both track external research and documentation coverage.
- [x] The runbook and setup docs clearly distinguish in-repo workflow behavior from platform-level search and approval capabilities.
- [x] All updated workflow, prompt, skill, and documentation references resolve to existing files.
- [x] Workspace MCP configuration includes an optional broader web-search server with credentials supplied by environment variables, not committed secrets.
- [x] Brownfield workflow guidance points to OpenSpec change artifacts, while greenfield workflow guidance keeps Speckit as the preferred planning path.
- [x] Workspace approval policy is enforced by supported editor-side hooks or settings instead of prompt text alone.