# Skill: Docker / Deploy Validation

**Scope:** `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `docker-compose.demo.yml`, `deploy/kubernetes/`, `.github/workflows/ci.yml`.

**Purpose:** Ensure Docker images build correctly, services start cleanly, and Kubernetes manifests are valid before deployment.

---

## Checklist

### Dockerfile quality
- [ ] `Dockerfile.backend` uses a multi-stage build (builder + runtime stages).
- [ ] `Dockerfile.frontend` builds the Vite bundle and serves it with a static file server.
- [ ] Both Dockerfiles pin base image versions (no `latest` tags).
- [ ] Both Dockerfiles run the application as a non-root user.
- [ ] `.dockerignore` excludes `node_modules`, `__pycache__`, `.git`, `tests/`, `*.pyc`.

### Docker Compose
- [ ] `docker compose up -d` starts all services without errors.
- [ ] All services pass their health checks within 60 seconds.
- [ ] Environment variables are documented in `.env.example` and not hard-coded in `docker-compose.yml`.
- [ ] Volume mounts use named volumes for persistent data (not anonymous volumes).
- [ ] Service dependencies use `depends_on` with `condition: service_healthy`.

### Service health
After `docker compose up -d`, verify:
- [ ] `curl http://localhost:4318/health` returns `{"status": "ok"}`.
- [ ] `curl http://localhost:3000` returns the React dashboard HTML.
- [ ] `curl http://localhost:9090/-/ready` returns HTTP 200 (Prometheus ready).
- [ ] `curl http://localhost:4318/metrics` returns Prometheus-format metrics.

### Image build (CI)
- [ ] `docker build -f Dockerfile.backend .` succeeds locally.
- [ ] `docker build -f Dockerfile.frontend .` succeeds locally.
- [ ] CI `docker` job passes in GitHub Actions.
- [ ] Image sizes are reasonable (backend ≤500 MB, frontend ≤200 MB).

### Kubernetes manifests
- [ ] `kubectl apply --dry-run=client -f deploy/kubernetes/` produces no errors.
- [ ] All deployments define `resources.requests` and `resources.limits`.
- [ ] All deployments define `readinessProbe` and `livenessProbe`.
- [ ] Secrets are referenced from Kubernetes `Secret` objects — no plain-text passwords in manifests.

### CI workflow
- [ ] `.github/workflows/ci.yml` uses pinned action versions.
- [ ] All jobs run with `permissions: contents: read` (least privilege).
- [ ] No secrets are echoed or logged in workflow steps.
- [ ] Workflow completes successfully on the default branch.

---

## How to run

```bash
# Build images
docker build -f Dockerfile.backend -t baseball-biomechanics-ai-backend:local .
docker build -f Dockerfile.frontend -t baseball-biomechanics-ai-frontend:local .

# Start all services
docker compose up -d

# Health checks
curl http://localhost:4318/health
curl http://localhost:3000
curl http://localhost:9090/-/ready

# Kubernetes dry-run (requires kubectl)
kubectl apply --dry-run=client -f deploy/kubernetes/

# Stop services
docker compose down
```

---

## Expected output

All Docker builds succeed. All services start and pass health checks. Kubernetes dry-run produces no errors. CI pipeline is green.
