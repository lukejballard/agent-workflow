# Skill: Application Security Review

**Scope:** `src/biomechanics_ai/`, `frontend/src/`, `Dockerfile*`, `docker-compose*.yml`, `.github/workflows/`

**Purpose:** Identify and remediate security risks in baseball-biomechanics-ai before a release or after any change that touches authentication, data handling, external I/O, or infrastructure configuration.

**When to invoke:**
- Before any production release.
- After adding a new collector endpoint, changing auth logic, or modifying a Dockerfile / CI workflow.
- When a dependency audit (`pip-audit`, `npm audit`) surfaces new vulnerabilities.

---

## How to use this skill

1. Open `checklist.md` alongside this file.
2. Work through each section in order.
3. Mark items ✅ (pass), ⚠️ (acceptable risk, documented), or ❌ (must fix before merge).
4. File a tracked issue for every ❌ item; do not merge until resolved or explicitly deferred by a maintainer.
5. Optionally paste the checklist into Copilot Chat and ask it to audit the relevant files.

---

## Checklist summary

| Section | Key question |
|---|---|
| Secrets hygiene | Are there any credentials in source? |
| Input validation | Is all user-supplied data validated before processing? |
| Dependency vulnerabilities | Do `pip-audit` and `npm audit` pass cleanly? |
| SAST | Does `bandit` pass with no HIGH/MEDIUM issues? |
| Container security | Are containers running as non-root with pinned base images? |
| CI/CD security | Are GitHub Actions secrets never logged or echoed? |
| CORS and network exposure | Is the collector not inadvertently exposed to the internet? |

See `checklist.md` for the full procedural checklist.

---

## Definition of done

All checklist items are ✅ or ⚠️ with a documented, maintainer-approved exception. No ❌ items remain open without a tracked issue.
