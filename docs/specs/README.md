Specs policy — repo-specific vs technical architecture

This directory contains repository-level technical architecture and product-facing
specifications. To keep the repository's technical architecture clear and portable,
repo-specific agent-workflow or operational specs should not live in this tree.

Policy
- Technical architecture and product specs: keep under `docs/specs/active/` and
  `docs/specs/done/` (this folder).
- Agentic workflow / repo-specific operational specs: store separately outside
  `docs/specs/` in one of the following ways:
  - A dedicated repository (recommended) such as `<repo>-ops-specs` for private
    operational details and runbooks, or
  - A top-level `repo-specific/` folder that is excluded from generic tooling,
    if you must keep them in the same repository (document why in the README).

What I removed
- Per owner instruction, previously repo-specific spec files were removed from
  this repository to avoid mixing operational agent workflows with technical
  architecture documentation.

If you need to preserve the removed files for audit or archival reasons, keep a
separate repository or an external archive (ZIP) outside the main branch.

Templates
- Use `.github/templates/` for agent-facing templates and tokenized copies.

Questions or exceptions
- If you need to keep a specific agent workflow spec in this repo, add an
  explicit justification to this README and get stakeholder sign-off.
