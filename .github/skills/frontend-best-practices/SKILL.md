# Frontend Best-Practices Skill

## When to use
Use for user-facing frontend work, React component changes, UI reviews, page-level refactors,
new screens, data-heavy views, or any task where a visually correct result can still hide
architecture, performance, or maintainability problems.

This skill complements `visual-qa`.
It does not replace accessibility review, visual validation, or normal frontend tests.

Auto-consider this skill for:
- React or TypeScript UI changes
- new pages, routes, or reusable components
- changed loading, error, or empty states
- changes that move logic between components, hooks, API clients, or context
- performance-sensitive dashboard screens and large lists

## What to check

### Architecture boundaries
- No direct `fetch()` in components or pages.
- Network access stays in `frontend/src/api/` and orchestration stays in hooks, context, or page-local services.
- Reusable UI stays composable instead of growing boolean-prop matrices.
- State ownership is clear: local state local, shared state shared, derived state not duplicated.

### Rendering and data flow
- Avoid render waterfalls caused by chained client-only requests when a simpler load path exists.
- Avoid expensive transforms inside render paths when they belong in helpers or hooks.
- Use route or page boundaries to split heavy work when possible.
- Large lists or tables should consider virtualization or pagination.

### User experience quality
- Loading, empty, error, and retry states are explicit.
- Navigation and filters should be linkable or otherwise resilient to refresh.
- Interactive controls should have predictable disabled, pending, and success states.
- New UI should preserve the established visual language of the repo unless the task is a redesign.

### Accessibility and semantics
- Semantic structure, accessible names, visible focus, and keyboard flows remain required.
- Motion-sensitive UI should consider reduced-motion behavior.
- Form fields need labels, validation feedback, and error recovery paths.

### Testability and regression safety
- Prefer accessible locators in tests.
- Add `data-testid` only when semantic locators are insufficient.
- Existing navigation, empty-state, and error-state behavior should get regression coverage when touched.

## Output
Provide a compact audit with:
- PASS: decisions that match the local frontend architecture well
- WARN: quality, UX, or maintainability concerns worth addressing
- FAIL: issues likely to create regressions, poor UX, or architectural drift
- Required fixes before merge
- Residual risks not covered by tests or screenshots