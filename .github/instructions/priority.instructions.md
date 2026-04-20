---
applyTo: "**/*"
---

# Instruction priority resolution

When multiple instruction files apply to the same file or action, resolve conflicts
using this precedence order (highest priority first):

1. **Security** (`security.instructions.md`) — security rules override all other guidance.
2. **Editing discipline** (`editing.instructions.md`) — minimal-diff and read-before-write rules.
3. **Tool contracts** (`tool-contracts.instructions.md`) — tool usage patterns and failure handling.
4. **Domain-specific** (`python.instructions.md`, `typescript.instructions.md`, `react.instructions.md`) — language and framework conventions.
5. **Cross-cutting** (`performance.instructions.md`, `accessibility.instructions.md`, `testing.instructions.md`) — quality standards.
6. **Specialized** (`api.instructions.md`, `database.instructions.md`, `frontend-design.instructions.md`) — narrow domain guidance.

If two instructions at the same priority level conflict, prefer the more specific
file (e.g., `api.instructions.md` over `python.instructions.md` for a route handler).

If the conflict cannot be resolved by specificity, surface the tension explicitly
and choose the option that best satisfies the current requirement lock.
