# AGENTS.md — src/

This file provides agent guidance scoped to the backend or shared application
code area under `src/`.

---

## Area responsibilities

Treat `src/` as the home for project-specific runtime code when that code exists.
Common patterns may include:
- API routes and request handling
- service orchestration
- storage or repository helpers
- analysis or transformation modules
- shared models and configuration

Keep the file structure driven by the actual checked-in code, not by inherited
product assumptions.

---

## Before making changes

1. Read the module you plan to edit end to end before changing it.
2. Check for an existing test file in `tests/` that exercises the same area.
3. Match the surrounding architecture instead of introducing a new layer or naming scheme in one file.
4. Update `docs/architecture.md` only when the repository actually contains the runtime behavior you are documenting.

---

## General rules

- Keep route or handler files thin.
- Move data access into dedicated helpers instead of mixing it into request code.
- Keep pure analysis or transform modules free of I/O.
- Add new environment variables only when they are required by checked-in code.

---

## Testing expectations

- New modules should have corresponding tests when runtime code exists.
- Prefer unit tests for pure logic and boundary tests for HTTP, storage, and filesystem behavior.
- Avoid examples or docs that imply a runtime layout that is not present in the workspace.
