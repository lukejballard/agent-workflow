# Skill: Docs Release Readiness

**Scope:** `docs/`, `README.md`, `CONTRIBUTING.md`, `.env.example`, inline docstrings.

**Purpose:** Ensure documentation is accurate and complete before a release tag is cut.

---

## Checklist

### README.md
- [ ] Key Features table reflects all currently available features (no removed or missing items).
- [ ] Architecture ASCII diagram matches the current component layout.
- [ ] Quickstart commands are runnable against the current codebase (test them!).
- [ ] Project Structure table is accurate (no orphaned or missing directories).
- [ ] Documentation table links are all valid (no 404s).
- [ ] Version badge reflects the correct release version.

### docs/architecture.md
- [ ] Every collector endpoint is listed in the endpoint table.
- [ ] Every storage table and its columns are described accurately.
- [ ] Every analysis module is listed and described.
- [ ] Environment variable table is complete and matches `.env.example`.
- [ ] Plugin protocol section reflects the current `PipelinePlugin` interface.

### docs/quickstart.md
- [ ] All commands are tested end-to-end.
- [ ] Service URLs (ports) match `docker-compose.yml`.
- [ ] No references to removed scripts or files.

### .env.example
- [ ] Every environment variable used in the codebase is listed.
- [ ] Every variable has a comment explaining its purpose and a safe default.
- [ ] No sensitive defaults (tokens, passwords) are included.

### Docstrings
- [ ] All public symbols in changed modules have Google-style docstrings.
- [ ] No `TODO` or `FIXME` comments in public API symbols.
- [ ] No docstrings that describe the old behaviour after a refactor.

### CONTRIBUTING.md
- [ ] Development setup commands are accurate.
- [ ] PR process description matches the current PR template.
- [ ] Pre-commit hook setup instructions are up to date.

### Release notes
- [ ] PR description summarises all user-visible changes.
- [ ] Breaking changes (if any) are called out explicitly.
- [ ] New environment variables are listed.

---

## How to run

```bash
# Check all markdown links (requires markdown-link-check)
npx markdown-link-check README.md docs/**/*.md

# Verify quickstart commands
docker compose up -d
python scripts/run_demo_pipeline.py
curl http://localhost:4318/health
curl http://localhost:4318/runs
```

---

## Expected output

All documentation is accurate, all links resolve, all commands run successfully. Release notes capture every user-visible change.
