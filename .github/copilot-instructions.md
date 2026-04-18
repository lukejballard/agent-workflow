# Engineering Contract (templated)

This repository uses a templated agent contract to keep agentic workflow guidance generic and reusable.

Use `.github/templates/copilot-instructions.template.md` as the canonical template and instantiate it for repo-specific needs.

Template tokens available: `{{SRC_DIR}}`, `{{FRONTEND_DIR}}`, `{{TESTS_DIR}}`, `{{BACKEND_STACK}}`.

If you need a repo-specific copy for operational reasons, copy the template to `.github/copilot-instructions.md` and replace tokens accordingly.
