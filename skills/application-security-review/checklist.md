# Application Security Review — Checklist

## 1. Secrets hygiene

- [ ] `git grep -rn "password\|secret\|token\|api_key\|apikey" src/ frontend/src/` returns only test fixtures and safe env-var references.
- [ ] No literal secret values in `docker-compose.yml`, `docker-compose.demo.yml`, or any Kubernetes manifest.
- [ ] `.env.example` uses `<REPLACE_ME>` placeholders — no real credentials.
- [ ] `ALERT_WEBHOOK_URL` is only logged by its host portion, not the full URL (which may embed a token).
- [ ] `gitleaks` / `git-secrets` pre-commit hook passes on the latest commit.

## 2. Input validation

- [ ] Every FastAPI route that accepts a request body uses a Pydantic model — no `dict` or raw `request.json()`.
- [ ] Path and query parameters use `Annotated` types with explicit constraints (e.g. `Annotated[str, Query(max_length=256)]`).
- [ ] File upload endpoints (if any) validate MIME type and enforce a maximum file size.
- [ ] SQL queries use SQLAlchemy parameterization — no string concatenation in queries.

## 3. Dependency vulnerabilities

```bash
# Python
pip-audit

# JavaScript
cd frontend && npm audit --audit-level=high
```

- [ ] `pip-audit` returns no HIGH or CRITICAL vulnerabilities.
- [ ] `npm audit --audit-level=high` returns no HIGH or CRITICAL vulnerabilities.
- [ ] Any exceptions are documented with CVE number, affected version, and mitigation rationale.

## 4. Static application security testing (SAST)

```bash
bandit -r src/ -c pyproject.toml -ll
```

- [ ] `bandit` reports no HIGH severity issues.
- [ ] `bandit` reports no MEDIUM severity issues (or each is documented with accepted-risk justification).
- [ ] No use of `eval()`, `exec()`, `subprocess.shell=True`, or `pickle.loads()` without explicit review.
- [ ] No use of `md5` or `sha1` for password hashing — use `bcrypt` or `argon2`.

## 5. Container security

- [ ] `Dockerfile.backend` and `Dockerfile.frontend` use non-`latest` base image tags.
- [ ] Both Dockerfiles end with `USER appuser` (non-root).
- [ ] `.dockerignore` excludes `.git`, `__pycache__`, `node_modules`, `*.pyc`, test fixtures.
- [ ] No `COPY . .` without a corresponding `.dockerignore` that excludes sensitive files.
- [ ] Container health-check endpoints do not expose internal state or credentials.

## 6. CI/CD security

- [ ] GitHub Actions workflows use `permissions: contents: read` by default.
- [ ] Secrets are referenced as `${{ secrets.MY_SECRET }}` — never echoed in `run:` steps.
- [ ] Third-party actions are pinned to a full SHA or immutable version tag.
- [ ] No `pull_request_target` trigger that could expose secrets to untrusted PRs.
- [ ] CI does not push Docker images to a registry without an explicit, gated release workflow.

## 7. CORS and network exposure

- [ ] `ALLOWED_ORIGINS` env var controls CORS; no wildcard `*` in production configuration.
- [ ] Sensitive ingest and metrics endpoints are not intended to be publicly reachable; document the expected network boundary in the active architecture or operations docs when those runtime surfaces exist.
- [ ] Health endpoints (`/health`) return only `{"status": "ok"}` — no version strings, dependency lists, or internal paths.
- [ ] Prometheus `/metrics` endpoint is not exposed outside the internal cluster network.

## Result

| Section | Status | Notes |
|---|---|---|
| Secrets hygiene | | |
| Input validation | | |
| Dependency vulnerabilities | | |
| SAST | | |
| Container security | | |
| CI/CD security | | |
| CORS and network exposure | | |

**Overall:** ✅ Pass / ⚠️ Pass with caveats / ❌ Fail

**Open issues filed:**
- (list any ❌ items with issue numbers)
