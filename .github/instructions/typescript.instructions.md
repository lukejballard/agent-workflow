---
applyTo: "**/*.ts,**/*.tsx"
---

# TypeScript standards

## Compiler settings (tsconfig.json)
- `"strict": true` always.
- `"noUncheckedIndexedAccess": true`.
- Never use `// @ts-ignore`. Fix the type.

## Style
- Match the existing ESLint and tsconfig settings in the owning package.
- Prefer consistency with the surrounding file over blanket export rewrites.
- Default exports are acceptable where the local area already uses them (for example, app entry points,
  some page components, and config files).
- `const` over `let`. Never `var`.
- Arrow functions for callbacks. Named functions for exported utilities.

## Types
- Define domain types in `types/` or co-located `*.types.ts`.
- Use `unknown` over `any`. Narrow explicitly with type guards.
- Avoid type assertions (`as X`) — if required, add a comment explaining why.
- Add runtime validation when the module already validates external data or when the spec requires it.

## Modules
- Do not assume a path alias exists. Use the import style configured by the local tsconfig.
- Avoid creating barrel files or package boundaries unless the surrounding area already uses them.
- Keep frontend API shapes aligned with `frontend/src/api/` and `frontend/src/types/`.

## Error handling
- Use typed errors: `class DomainError extends Error { constructor(...) }`.
- Never swallow errors with empty catch blocks.
- Log or surface enough context for debugging before re-throwing or handling.

## Async
- `async/await` over raw Promises.
- Always handle rejection. No unhandled promise rejections.
- Use `Promise.all()` for concurrent operations where order doesn't matter.

## Observability
- No stray `console.log` calls in committed production UI code.
- Match the logging or diagnostics pattern already used in the local area.
- Never log tokens, passwords, or PII.
