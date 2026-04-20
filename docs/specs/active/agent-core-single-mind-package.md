# Feature: Agent Core Single-Mind Package

**Status:** In Review
**Created:** 2026-04-19
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** N/A

---

## Problem
`agent-core/github/` still presents a small ecosystem of optional subagents, skills, and prompt aliases even though the intended package should feel like one hyperintelligent mind. The extra layers increase conceptual overhead and make the package look like a multi-agent bundle rather than a single, disciplined orchestrator.

## Success criteria
The packaged workflow presents one primary mind with internal planning, critique, and verification. Optional layers that only alias or duplicate orchestrator behavior are removed. The remaining core files still support spec-driven non-trivial work, hard critique loops, and package validation.

---

## Requirements

### Functional
- [x] Keep one primary agent entry point and fold review/spec-validation guidance into it.
- [x] Remove optional layers that do not add unique runtime capability: prompt alias, specialist agents, and standalone skills.
- [x] Update package docs and routing text to describe one hyperintelligent orchestrator rather than multiple cooperating roles.
- [x] Keep the spec scaffold, hook system, manifest, and validator if they still serve the single-mind workflow.

### Non-functional
- [ ] Performance: no new dependencies or runtime steps.
- [ ] Security: hook protections and validation coverage remain intact.
- [ ] Accessibility: not applicable; no UI change.
- [ ] Observability: validation and hook behavior remain documented and operational.

---

## Affected components
- `agent-core/README.md`
- `agent-core/github/AGENTS.md`
- `agent-core/github/copilot-instructions.md`
- `agent-core/github/agents/orchestrator.agent.md`
- `agent-core/github/agent-platform/workflow-manifest.json`
- `agent-core/github/prompts/workflow.prompt.md` (remove)
- `agent-core/github/agents/implementer.agent.md` (remove)
- `agent-core/github/agents/reviewer.agent.md` (remove)
- `agent-core/github/skills/adversarial-review/SKILL.md` (remove)
- `agent-core/github/skills/spec-validation/SKILL.md` (remove)

---

## External context
- `docs/hyperintelligence_plan.md` materially shapes this design.
- Key constraint: “The path to hyperintelligence is not more agents. It is strong runtime semantics + explicit memory + hard verification loops + operator-grade observability.”

---

## Documentation impact
The README, packaged agent guide, and global instructions must change because they currently describe reviewer and implementer roles plus skills/prompt surfaces that the minimized package will no longer ship.

---

## Architecture plan
Retain a single orchestrator as the only packaged agent entry point.

Inline the useful content from the removed optional layers into the orchestrator and top-level package guidance:
- adversarial critique checklist
- spec validation expectations
- implementation discipline

Keep the manifest, spec scaffold, hooks, and validator because they contribute to runtime semantics and verification rather than multiplying agent personas.

Remove prompt aliasing and specialist personas because they add packaging surface without adding unique runtime machinery in this minimized package.

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
| Manifest still references removed skills | Remove skill registry entries and keep phase order only |
| Docs still route users to removed agents | Rewrite all routing text to the single orchestrator |
| Removing specialist files weakens critique discipline | Move critique/spec-validation rules into orchestrator and guidance before deleting files |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Too much minimization removes useful discipline | Medium | High | Keep specs, hooks, validator, and explicit critique rules in the orchestrator |
| Stale references to removed optional files remain | Medium | Medium | Search all `agent-core/**` references before validation |

---

## Breaking changes
This removes previously packaged optional surfaces. Consumers of `agent-core/` must stop relying on `@reviewer`, `@implementer`, `/workflow`, or packaged skill folders from this minimal distribution.

---

## Testing strategy
- **Unit:** none added.
- **Integration:** run the package validator after removing the optional layers.
- **E2E:** not applicable.
- **Performance:** none needed.
- **Security:** confirm hook and validation files remain present and referenced.

---

## Acceptance criteria
- [x] Single orchestrator remains the only packaged agent
- [x] Prompt alias, specialist agents, and standalone skills are removed
- [x] Critique and spec-validation rules remain present in core guidance
- [x] Package docs describe a single hyperintelligent mind
- [x] Package validates successfully after minimization