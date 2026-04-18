# agent-workflow Constitution

> Non-negotiable principles for repository governance, specification quality,
> contributor experience, and agent-assisted development in `agent-workflow`.
>
> This document governs specifications, plans, implementation prompts, agent
> behavior, and code changes across this repository.
>
> RFC 2119 semantics apply: **MUST**, **SHOULD**, **MAY**.

---

## 1. Purpose

`agent-workflow` is a reusable repository scaffold for agent-assisted software
delivery. It exists to keep planning, documentation, workflow metadata, and
future runtime work aligned under one coherent operating model.

The repository MUST evolve as:
- a coherent scaffold rather than a pile of disconnected templates,
- a trustworthy contributor workflow rather than a collection of stale prompts,
- and a spec-driven codebase where public docs match checked-in reality.

---

## 2. Scope and precedence

This constitution applies to:
- specifications,
- plans,
- implementation work,
- architecture changes,
- documentation,
- tests,
- and agent workflow assets.

### Precedence
When guidance conflicts:
1. This constitution
2. Repository safety and governance instructions under `.github/instructions/`
3. Active specs and approved design documents
4. Repository-level coding instructions
5. Local implementation convenience

---

## 3. Repository identity

The repository MUST remain product-neutral until maintainers choose a concrete
application domain and back it with checked-in runtime code.

The repository MUST NOT:
- advertise a product identity that is not backed by the workspace,
- keep stale domain language in public entry points,
- or imply APIs, deployments, or UI surfaces that do not exist.

---

## 4. Spec-driven development

Non-trivial work MUST start from a written spec in `docs/specs/active/`.

Specs SHOULD define:
- purpose,
- user or contributor impact,
- expected behavior,
- constraints,
- acceptance criteria,
- and verification expectations.

Contributors and agents MUST NOT jump directly into implementation when the
behavior is ambiguous.

---

## 5. Documentation honesty

Public docs MUST describe only what is verified by the current repository.

Docs SHOULD:
- distinguish verified behavior from future intent,
- link to active specs for in-flight work,
- archive or remove stale product-specific material,
- and use generic wording unless runtime code requires narrower terminology.

---

## 6. UX and interface principles

When a real frontend exists, common workflows SHOULD be guided, task-oriented,
and explicit about loading, success, failure, and incomplete states.

Interfaces MUST:
- acknowledge user actions visibly,
- reduce cognitive overload,
- avoid placeholder-like operational surfaces,
- and meet accessibility expectations for supported features.

---

## 7. Architecture principles

When runtime code exists:
- routes and handlers MUST stay thin,
- business logic SHOULD live in dedicated services or helpers,
- storage access SHOULD stay isolated from request handling,
- and pure analysis or transform code MUST remain free of I/O.

If those layers do not exist in the workspace, docs and prompts MUST NOT pretend they do.

---

## 8. Quality and testing

All meaningful changes SHOULD include the smallest defensible verification set.

When code exists:
- new modules SHOULD have corresponding tests,
- tests MUST cover happy paths, failures, and key edge cases,
- and public behavior changes MUST update docs in the same change set.

---

## 9. Agent workflow governance

Agent assets under `.github/`, `docs/runbooks/`, and `scripts/agent/` are
first-class repository surfaces.

Changes to those surfaces MUST:
- keep prose and generated metadata aligned,
- update companion docs when governance behavior changes,
- and avoid hardcoding product-specific assumptions into generic workflow files.

---

## 10. Change control

Before merging a non-trivial change, contributors SHOULD confirm:
- the active spec still matches the implementation,
- public docs still match the repository,
- generated metadata is in sync with its source definitions,
- and stale product-specific naming has not been reintroduced.

---

When in doubt, do not optimize only for implementation speed.
Optimize for **product coherence, operational trust, and spec-aligned evolution**.

**Version**: 1.0.0 | **Ratified**: 2026-03-19 | **Last Amended**: 2026-03-19