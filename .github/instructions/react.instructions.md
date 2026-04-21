---
applyTo: "**/*.tsx,**/*.jsx"
---

# React frontend standards

## Default generated frontend stack
- When the user and host repo do not establish a frontend stack, default to React + TypeScript + Vite + react-router-dom + Vitest.
- Prefer React Testing Library and `userEvent` for component and page tests.
- Prefer a Vite SPA layout with `src/main.tsx`, `src/App.tsx`, route/page modules, shared components, API helpers, and shared types.

## Default component and styling stack
- When the user and host repo do not establish a component library, default to shadcn/ui + Tailwind CSS.
- Use Lucide React for icons. Use class-variance-authority (cva) for component variants.
- The frontend-design skill provides detailed standards for layout, typography, color, state completeness, and design spec artifacts.

## Component rules
- Pages and components stay thin. Move network and orchestration logic into hooks,
	context, or page-scoped service modules.
- No direct `fetch()` in components or pages. Use shared API helpers and typed wrappers in hooks, context, or services.
- Prop types via TypeScript interfaces or shared types. Never use PropTypes.
- Extract reusable UI into nearby shared component modules.
- Maximum component length: 200 lines. Extract sub-components or hooks if longer.

## App structure
- Match the router and application-shell patterns already used by the host repo.
- For generated apps without an established structure, prefer `src/pages/`, `src/components/`, `src/api/`, `src/hooks/`, and `src/types/`.
- When the host repo uses Vite, browser-exposed environment variables must use the `VITE_` prefix via `import.meta.env`.
- Prefer route-level or page-level lazy loading when a screen is heavy.

## State management
- Local state for component-scoped data.
- Use existing Context providers for cross-cutting concerns already modeled in the host repo.
- Keep REST calls in shared API helpers; keep shared API types in nearby type modules.
- Prefer hooks or page-local services over introducing a new global state library.

## Performance
- Use `react-window` or a similar existing pattern for long lists or large tables.
- Add `React.memo`, `useMemo`, or `useCallback` only after profiling shows it helps.
- Lazy-load heavy route-sized modules instead of pushing them into the initial bundle.
- Keep expensive transforms out of render paths when they can live in hooks or helpers.

## Styling
- Match the existing CSS and component patterns already used in the host repo.
- No inline styles except for truly dynamic values.

## Elite tier — what good looks like
- Use Suspense for streaming or code-split boundaries where the framework
  supports it; do not roll a custom loading orchestrator.
- Make data-fetching abortable: pass an `AbortSignal` from the effect's
  cleanup or the route's lifecycle into every fetch.
- Use `useTransition` (or the framework equivalent) to mark non-urgent
  updates so input latency stays inside the INP budget defined in
  `performance.instructions.md`.
- Profile before memoizing. `React.memo`, `useMemo`, and `useCallback` are
  not free; add them only after a profile shows the cost.
- **Do not introduce Zustand, Jotai, Redux, or XState** as a new default.
  Local state and Context cover the package-default surface; reach for a
  global store only on explicit user requirement or established host-repo
  evidence.
