# AGENTS.md — frontend/

> **STATUS: RESERVED — Runtime code does not yet exist.**
> Before running any command described here, verify that `frontend/package.json` exists.
> If it does not, this directory is a scaffold only. Do not attempt `npm ci`, `npm run lint`,
> `npm run build`, or any other npm command — they will fail. Scaffold the frontend first
> (create `package.json`, `vite.config.ts`, `tsconfig.json`, and `src/main.tsx`),
> then verify the stack described below.

This file provides agent guidance scoped to the **React TypeScript frontend** (`frontend/`).

---

## Tech stack summary

| Tool | Version | Config file |
|---|---|---|
| React | 19 | `package.json` |
| TypeScript | strict | `tsconfig.app.json` |
| Vite | 8 | `vite.config.ts` |
| ESLint | latest | `eslint.config.js` |
| Vitest | 4 | `vite.config.ts` |

---

## Directory guide

```
frontend/src/
  api/          ← Application API fetch helpers; one file per resource group
  components/   ← Shared/reusable UI components
  context/      ← React Context providers
  hooks/        ← Custom hooks (data fetching, derived state)
  pages/        ← Top-level page components mounted by the router
  types/        ← Shared TypeScript interfaces mirroring collector API responses
  __tests__/    ← Vitest unit + component tests
```

---

## Agent rules

- **Never call the API directly from inside a component**. All data fetching goes through hooks in `hooks/` or context in `context/`.
- **Type everything**. All API response shapes must have a corresponding interface in `types/`.
- **Keep pages thin**. Pages compose components and hooks — they do not contain business logic.
- **Accessibility first**. Every interactive element needs an accessible label. Run the browser's a11y checker before marking work done.
- **No `any` types**. If the shape is unknown, model it with a discriminated union or a generic.

---

## Common tasks

### Add a new API endpoint call
1. Add a typed fetch function to the relevant file in `api/` (create one if needed).
2. Define the response type in `types/`.
3. Create or update a hook in `hooks/` that calls the API function.
4. Use the hook in the relevant page or component.

**Example — plain-text endpoint (`getExecutionLogsRaw`):**
```ts
// api/executions.ts
import { fetchText } from "./http";

export async function getExecutionLogsRaw(id: number): Promise<string> {
  return fetchText(`/executions/${id}/logs/raw`);
}
```
Use `fetchText()` instead of `fetchJSON()` when the backend returns `text/plain`.

### Add a new dashboard page
1. Create `pages/MyPage.tsx`.
2. Register it in the router (if a router is present) or link it from `App.tsx`.
3. Add a link in the navigation component.
4. Write at least one Vitest test for the page's core rendering.

### Add a new reusable component
1. Create `components/MyComponent.tsx`.
2. Export it as a named export.
3. Write a Vitest test in `__tests__/MyComponent.test.tsx`.

---

## Build and lint commands

```bash
cd frontend

# Install deps
npm ci

# Lint
npm run lint

# Build
npm run build

# Test
npm test
```

All three must pass before a frontend PR is ready for review.
