# baseball-biomechanics-ai Constitution

> Non-negotiable principles for product, UX, architecture, quality, and agent-assisted development in `baseball-biomechanics-ai`.
>
> Note: This constitution still contains inherited platform-oriented workflow language in places and needs a full baseball-biomechanics-specific rewrite. Treat it as governance guidance, not as a validated product description.
>
> This document governs specifications, plans, tasks, implementation prompts, agent behavior, and code changes across this repository.
>
> RFC 2119 semantics apply: **MUST**, **SHOULD**, **MAY**.

---

<!--
SYNC IMPACT REPORT
- Version change: none -> 1.0.0
- Modified principles:
	- Section 4 (Spec-driven development requirements): clarified constitutional gates and required artifacts
	- Section 10 (Agentic workflow governance): reinforced agent asset protection and update justification
- Added sections: Sync Impact Report (this header)
- Removed sections: none
- Templates / files updated (local):
	- .specify/templates/plan-template.md (✅ updated)
	- .specify/templates/spec-template.md (✅ updated)
	- .specify/templates/tasks-template.md (✅ updated)
	- .specify/scripts/validate_constitution.py (✅ added)
	- PRODUCT_AUDIT_REPORT.md (✅ added)
- Templates / files requiring manual follow-up (CI / docs):
	- .github/workflows/ci.yml (⚠ pending) — add step to run `.specify/scripts/validate_constitution.py`
	- README.md (⚠ pending) — optional link to the audit report and constitution gate
- Follow-up TODOs:
	- Commit changes and open PR with audit and governance updates
	- Add the validation script to CI to enforce the constitution gate
	- Expand unit/automation tests for new guided-form components (frontend)
	- Plan security & enterprise-readiness work: auth/RBAC, DB migration + Alembic
	- Confirm `RATIFICATION_DATE` and `CONSTITUTION_VERSION` in release notes if required
-->


## 1. Purpose

`baseball-biomechanics-ai` is a baseball biomechanics application with supporting analysis, workflow, and operational tooling.

It serves multiple user groups:
- **Data engineers** instrumenting and operating pipelines
- **Data scientists** exploring pipeline behavior and validating outputs
- **Platform / reliability teams** monitoring health, alerts, and pipeline execution
- **Technical stakeholders** reviewing quality, risk, and operational readiness

The platform includes:
- a Python SDK for instrumentation,
- a FastAPI collector and analysis backend,
- a React/TypeScript frontend for authoring, observing, and operating pipelines,
- and a set of agentic workflow assets under `.github/` that support AI-assisted development.

This constitution exists to ensure the system evolves as:
- a **coherent product**, not a collection of disconnected features;
- a **trustworthy operational platform**, not just a demo;
- and a **spec-driven, agent-compatible codebase** with clear quality and UX standards.

---

## 2. Scope and precedence

This constitution applies to:
- all specifications,
- plans,
- task breakdowns,
- prompts,
- implementation work,
- architectural changes,
- and agent-produced outputs.

It governs:
- backend development,
- frontend development,
- documentation,
- UX improvements,
- testing,
- and agent workflow assets.

### Precedence
When guidance conflicts:
1. **This constitution**
2. Repository safety / governance instructions under `.github/instructions/`
3. Product/page specs and approved design documents
4. Repository-level coding instructions
5. Local implementation convenience

Agents and contributors MUST prefer the higher-precedence source.

---

## 3. Product identity and design intent

`baseball-biomechanics-ai` MUST be developed as:
1. a **developer-friendly biomechanics analysis and workflow platform**,
2. an **operator-friendly control plane** for health, quality, review, and execution,
3. an **increasingly guided authoring and review experience**,
4. and a **self-hostable, enterprise-credible system**.

The product MUST NOT drift into:
- a collection of disconnected admin pages,
- a JSON-first UI for common workflows,
- or a visually rich but operationally untrustworthy experience.

### Product posture
The platform SHOULD feel:
- guided,
- responsive,
- operationally trustworthy,
- discoverable,
- explicit,
- and enterprise-aware.

It SHOULD NOT feel:
- static,
- opaque,
- overloaded,
- raw-config-driven for common flows,
- or inconsistent from page to page.

---

## 4. Spec-driven development requirements

Major feature work and all high-ambiguity product work MUST follow a spec-driven workflow.

### Work that MUST be spec-driven
The following changes require a written spec, audit, or design brief before implementation:
- multi-page UX redesigns,
- control-plane workflow changes,
- new operational pages,
- Studio / pipeline authoring changes,
- connections, alerts, health, settings, or data quality redesigns,
- major backend-control-plane integrations,
- and any change likely to affect enterprise readiness or user trust.

### Minimum required artifacts
For such work, the repo MUST include at least one of:
- a page spec,
- a feature spec,
- a UX audit,
- a design brief,
- or an approved architecture/refactor plan.

Examples include:
- `STUDIO_AUDIT.md`
- future specs under `specs/`
- product/experience briefs
- page-specific design docs

### Spec content requirements
A qualifying spec SHOULD define:
- purpose,
- target users,
- jobs to be done,
- current pain points,
- expected product behavior,
- key UI/system states,
- validation and error behavior,
- acceptance criteria,
- and implementation constraints.

### No-code-first on ambiguous product work
For ambiguous UX or workflow problems, contributors and agents MUST NOT jump directly into implementation without clarifying intended behavior in a spec or design brief.

---

## 5. UX and product experience principles

### 5.1 Common workflows MUST be guided
Common product workflows MUST prioritize guided UX over raw configuration.

This especially applies to:
- Pipeline Studio,
- step configuration,
- connections,
- destinations,
- alert rules,
- alert channels,
- and operational settings.

Advanced or expert editing MAY exist, including JSON or code-oriented modes, but MUST be optional rather than the primary experience for common tasks.

### 5.2 User actions MUST visibly acknowledge state
Every significant user action MUST provide visible feedback for one or more of:
- loading / pending,
- success,
- failure,
- validation warning,
- incomplete configuration,
- or saved / unsaved state.

A UI that accepts input but does not clearly acknowledge action completion is considered deficient.

### 5.3 Control-plane pages MUST be task-oriented
Pages MUST be designed around user jobs, not backend object models.

Examples:
- Connections: create, validate, interpret, reuse
- Alerts: understand, configure, route, trust
- Health: assess, triage, act
- Data Quality: interpret, drill down, prioritize
- Studio: author, validate, preview, execute

### 5.4 Reduce cognitive overload
Forms and panels SHOULD use:
- progressive disclosure,
- tabs/sections,
- grouped actions,
- context-specific help,
- and explicit empty/incomplete states.

Monolithic, multi-concern editing panels SHOULD be decomposed.

### 5.5 The UI MUST teach the product
If a concept is likely to confuse a first-time user, the product SHOULD provide inline explanation, examples, glossary support, helper text, or contextual docs.

### 5.6 Pages MUST feel operationally trustworthy
Operational surfaces MUST not look like placeholders.
Health, alerts, runs, executions, and data quality pages SHOULD help users decide what to do next.

---

## 6. Page-level product expectations

### 6.1 Pipeline Studio
Pipeline Studio is a top-priority workflow and MUST be treated as a core product surface.

It MUST evolve toward:
- modular architecture,
- guided configuration,
- lower JSON dependency,
- strong validation,
- clear preview behavior,
- accessible interactions,
- and strong test coverage.

Approved Studio specs and audits, including `STUDIO_AUDIT.md`, MUST guide Studio work.

### 6.2 Connections
Connections MUST feel like a guided setup experience.
They SHOULD support:
- connector-aware forms,
- field-level validation,
- clear test results,
- next-step guidance,
- and safe reuse.

### 6.3 Alerts
Alerts MUST make the rule → condition → channel → delivery mental model understandable.
Users SHOULD be able to understand what an alert does without reading source code.

### 6.4 Health
Health MUST provide actionable operational insight, not only decorative metrics.
It SHOULD communicate system condition, degraded areas, and recent risk signals.

### 6.5 Data Quality
Data Quality MUST provide interpretation and drilldown, not just metrics cards.
It SHOULD help users identify severity, trends, blast radius, and affected runs/steps.

### 6.6 Compare Runs
Compare Runs MUST make run identity legible.
Human-readable naming, contextual labeling, and deep links SHOULD be preferred over opaque identifiers.

### 6.7 Docs
Docs surfaces MUST be task-oriented, role-aware, and operationally useful.
Documentation MUST explain how to use the product, not only what exists.

### 6.8 Settings
Settings MUST feel intentional, grouped, and platform-like.
Sparse or placeholder settings pages SHOULD be avoided.

### 6.9 Runs and Executions
Runs and Executions are currently stronger surfaces and SHOULD be used as references for trustworthy operational UX.
Contributors SHOULD avoid unnecessary redesign unless a change clearly improves the experience.

---

## 7. Architecture and composability principles

### 7.1 Monoliths MUST be reduced over time
High-risk monolithic components MUST be decomposed into testable, reusable modules.
Large components with mixed concerns SHOULD be treated as refactor candidates.

### 7.2 State MUST have a clear source of truth
Frontend state models SHOULD avoid silent divergence between visual state and persisted state.
Manual multi-surface synchronization SHOULD be minimized where feasible.

### 7.3 Public APIs MUST remain stable unless intentionally changed
Changes to SDK/public APIs and control-plane interfaces MUST be documented and justified.

### 7.4 Backend design MUST remain non-fatal for observability flows
Observability and instrumentation MUST remain non-fatal to user pipelines wherever possible.
Failures in telemetry collection SHOULD not crash the user’s primary workload.

### 7.5 Prefer explicit contracts
Structured data SHOULD use typed models and documented schemas rather than loosely shaped data blobs.

---

## 8. Testing and quality requirements

### 8.1 Business logic MUST be tested
Every new Python function containing business logic MUST have at least one unit test.

### 8.2 High-risk UI flows MUST be tested
Critical UI workflows MUST have automated coverage where practical, especially:
- Pipeline Studio
- Connections
- Validation flows
- Preview/test-run flows
- Alerts configuration
- Compare Runs identity behavior
- Health state rendering
- Data quality drilldowns

### 8.3 Complex pages MUST not remain untested indefinitely
The most complex product pages MUST not remain effectively untested.
If major refactors occur, testing work MUST be part of the change plan, not deferred indefinitely.

### 8.4 Accessibility testing is required for key workflows
Keyboard navigation, focus behavior, semantic controls, and actionable labeling SHOULD be validated for major user flows.

### 8.5 Refactors MUST improve or preserve testability
Refactors that make code harder to test violate this constitution.

---

## 9. Documentation requirements

### 9.1 User-visible changes MUST update user-facing docs
If a change alters workflow, behavior, configuration, or usage, relevant docs MUST be updated.

### 9.2 Architectural changes MUST update architecture docs
New or materially changed components, subsystems, or workflows MUST be reflected in architecture documentation.

### 9.3 UX/product work SHOULD leave artifacts
Major UX redesigns SHOULD produce or update:
- audits,
- specs,
- acceptance criteria,
- or implementation summaries.

### 9.4 Documentation MUST support agents as well as humans
When possible, docs SHOULD be structured so that both contributors and agents can use them as implementation guidance.

---

## 10. Agentic workflow governance

This repository includes agent definitions, skills, prompts, instructions, and chatmodes under `.github/`.
These assets are a strategic part of the repo and MUST be treated as governed workflow infrastructure.

### 10.1 Agents and instructions are not casual documentation
Files under:
- `.github/agents/`
- `.github/skills/`
- `.github/instructions/`
- `.github/prompts/`
- `.github/chatmodes/`

MUST be updated carefully and intentionally.

### 10.2 Agent changes require justification
Changes to agent behavior, prompt conventions, routing, safety instructions, or workflow assumptions SHOULD include rationale and MUST respect governance guidance already present in the repo.

### 10.3 Specs SHOULD integrate with agents
Where possible, specs and audits SHOULD be written so agents can consume them directly in VS Code and Copilot workflows.

### 10.4 Prompts MUST reference source-of-truth artifacts
When prompting agents for large or ambiguous work, contributors SHOULD point them to:
- this constitution,
- relevant page specs,
- UX audits,
- repo instructions,
- and acceptance criteria.

---

## 11. Security, enterprise credibility, and operational trust

### 11.1 No secrets in source
Secrets, credentials, tokens, and connection secrets MUST NOT be committed.

### 11.2 Environment-based configuration MUST be documented
New environment variables MUST be documented in `.env.example` and relevant docs.

### 11.3 Enterprise trust signals matter
For enterprise-facing changes, contributors SHOULD consider:
- auth clarity,
- validation quality,
- auditability,
- error clarity,
- resilience,
- and operator trust.

### 11.4 Operational pages MUST not mislead
If a page looks authoritative, it MUST not present weak or ambiguous signals in a way that overstates confidence.

---

## 12. Performance and responsiveness

### 12.1 UI performance matters for trust
Slow, stale, or unclear UI updates damage user trust.
Loading states, refresh behavior, and state synchronization SHOULD be explicit.

### 12.2 Large pages SHOULD be decomposed before heavily extending
Performance and maintainability concerns SHOULD be addressed before layering significant new complexity onto already large components.

---

## 13. Delivery standards for specs, plans, and implementations

A spec/plan/task set is constitutionally compliant only if it:
- clearly identifies the user problem,
- reflects product and UX intent,
- respects repo guardrails,
- includes testing expectations,
- avoids unnecessary ambiguity,
- and keeps work scoped to a coherent increment.

An implementation is constitutionally compliant only if it:
- aligns with the governing spec/audit,
- preserves or improves user trust,
- does not degrade testability,
- respects coding standards,
- updates docs when required,
- and leaves the codebase more coherent than before.

---

## 14. Amendment policy

This constitution SHOULD evolve when:
- product direction becomes clearer,
- a recurring class of mistakes appears,
- enterprise-readiness standards need tightening,
- or agent workflows need more explicit governance.

Amendments SHOULD be deliberate, reviewed, and reflected in related instructions/specs.

---

## 15. Practical interpretation

If unsure how to proceed, choose the option that:
1. improves user trust,
2. reduces ambiguity,
3. makes the workflow more guided,
4. keeps architecture modular,
5. improves testability,
6. and helps both humans and agents understand the intended product behavior.

When in doubt, do not optimize only for implementation speed.
Optimize for **product coherence, operational trust, and spec-aligned evolution**.

**Version**: 1.0.0 | **Ratified**: 2026-03-19 | **Last Amended**: 2026-03-19