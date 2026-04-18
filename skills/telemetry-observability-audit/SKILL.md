# Skill: Telemetry / Observability Audit

**Scope:** Observability-related code under `src/`.

**Purpose:** Ensure that backend, SDK, and telemetry surfaces emit correct, complete, and non-fatal observability signals before a release or after a significant change.

**When to invoke:**
- Before a production release of the backend or SDK.
- After adding or modifying a route, service, or analysis module.
- When a user reports missing spans, gaps in metrics, or silent failures in the SDK.

---

## How to use this skill

1. Open `checklist.md` alongside this file.
2. Work through each section in order.
3. Mark items ✅ (pass), ⚠️ (needs attention), or ❌ (fail).
4. File a follow-up issue for every ❌ item before merging.
5. Optionally paste the checklist into Copilot Chat and ask it to audit the relevant files against each item.

---

## Checklist summary

| Section | Key question |
|---|---|
| SDK safety | Does every SDK call survive a collector outage? |
| Metric completeness | Does every collector route increment the right counters? |
| Span coverage | Does every significant operation produce a span? |
| Log quality | Are errors logged with enough context to diagnose without a debugger? |
| Env-var hygiene | Are all observability env vars documented and safe-defaulted? |
| Test coverage | Are observability paths covered by at least one unit test? |

See `checklist.md` for the full procedural checklist.

---

## Definition of done

All checklist items are ✅ or ⚠️ with a documented, accepted risk. No ❌ items remain untracked.
