Title: Remove archived repo-specific spec files and clean references

Summary:
- Permanently removed archived repo-specific spec files from `.github/archived/docs/specs/` and `.github/archived/` per owner instruction.
- Removed the archived reference line from `.github/copilot-instructions.md`.
- Verified no remaining `.github/archived/` references in the repository.

Files removed:
- .github/archived/copilot-instructions.repo.md
- .github/archived/docs/specs/active/agent-workflow-simplification-phase-2.repo.md
- .github/archived/docs/specs/active/enterprise-readiness-95-program.repo.md
- .github/archived/docs/specs/active/frontend-coverage-recovery-wave-1.repo.md
- .github/archived/docs/specs/active/frontend-coverage-recovery-wave-2.repo.md
- .github/archived/docs/specs/active/notifications-surface-followup-hardening.repo.md
- .github/archived/docs/specs/active/runs-surface-followup-hardening.repo.md
- .github/archived/docs/specs/done/repository-verification-summary-2026-04-13.repo.md
- .github/archived/docs/specs/done/verification-recovery-wave-1.repo.md

Files modified:
- .github/copilot-instructions.md — removed reference to archived repo-specific copy

Verification performed:
1. Searched repo for `.github/archived/` references — none found.
2. Searched for known repo-specific spec names and reviewed matches to ensure live specs remain consistent.

Recommended next steps (manual or CI-assisted):
- Create a feature branch (e.g., `cleanup/delete-repo-specific-specs`) and commit these changes.
- Run the repo verification steps locally or in CI before merging:
  - Frontend typecheck: `npm --prefix frontend run typecheck`
  - Frontend build: `npm --prefix frontend run build`
  - Docs link-check (if configured)
- Open a PR with this description and request stakeholder sign-off.

Notes:
- No runtime code was changed.
- If you want an external backup ZIP of the deleted archived files before merging, I can create one now and attach it outside the repo.
