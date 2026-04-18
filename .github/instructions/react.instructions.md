---
applyTo: "frontend/**"
---

# React + Vite frontend standards

## Component rules
- Pages and components stay thin. Move network and orchestration logic into hooks,
	context, or page-scoped service modules.
- No direct `fetch()` in components or pages. Use `frontend/src/api/` helpers and
	typed wrappers in hooks, context, or services.
- Prop types via TypeScript interfaces or shared types. Never use PropTypes.
- Extract reusable UI into `frontend/src/components/`.
- Maximum component length: 200 lines. Extract sub-components or hooks if longer.

## App structure
- This frontend is a React + Vite SPA, not a Next.js app.
- Use the existing `react-router-dom` patterns in `frontend/src/App.tsx` and `frontend/src/pages/`.
- Browser-exposed environment variables must use the `VITE_` prefix via `import.meta.env`.
- Prefer route-level or page-level lazy loading when a screen is heavy.

## State management
- Local state for component-scoped data.
- Use existing Context providers for cross-cutting concerns already modeled in `frontend/src/context/`.
- Keep REST calls in `frontend/src/api/`; keep shared API types in `frontend/src/types/`.
- Prefer hooks or page-local services over introducing a new global state library.

## Performance
- Use `react-window` or a similar existing pattern for long lists or large tables.
- Add `React.memo`, `useMemo`, or `useCallback` only after profiling shows it helps.
- Lazy-load heavy route-sized modules instead of pushing them into the initial bundle.
- Keep expensive transforms out of render paths when they can live in hooks or helpers.

## Styling
- Match the existing CSS and component patterns already used in `frontend/src/`.
- No inline styles except for truly dynamic values.
