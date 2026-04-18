Specs policy

This directory contains working and completed specifications that describe
portable repository behavior, agent workflow architecture, and future runtime
requirements that contributors should be able to understand from the checked-in
files.

Policy
- Active implementation or cleanup specs belong under `docs/specs/active/`.
- Completed specs belong under `docs/specs/done/`.
- Product-specific or operational details that are not meant to survive beyond a
  single deployment context should live outside this directory.

Guidance
- Until concrete runtime code exists, keep this directory focused on workflow,
  governance, and repository-operating-model specs.
- Prefer generic, reusable wording unless a concrete implementation in the repo
  already requires narrower terminology.
- Archive or remove stale product-specific specs when they stop matching the
  repository's verified state.
- Use `.github/templates/` for agent-facing templates and tokenized copies.
