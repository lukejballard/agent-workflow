# Feature: Dashboard Zero-Pipeline Empty State

**Status:** Done
**Created:** 2026-04-13
**Author:** @copilot
**Estimate:** S
**Supersedes:** None

---

## Problem
Users with zero pipelines can land on a visually blank dashboard after dismissing onboarding.
The dashboard route must remain usable and informative even before any pipeline data exists.

## Success criteria
- Users with zero pipelines always see visible dashboard content.
- Dismissing the onboarding guide does not leave the dashboard route empty.
- The zero-pipeline state is covered by a frontend regression test.

---

## Requirements

### Functional
- [x] The dashboard route renders persistent content when the pipelines list is empty.
- [x] The onboarding guide remains available as an overlay when applicable.
- [x] The empty state provides clear next actions.

### Non-functional
- [x] Accessibility: the empty state and actions remain keyboard accessible and semantically labeled.
- [x] Regression safety: add a test for the dismissed onboarding state.

---

## Affected components
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/__tests__/DashboardPage.test.tsx`

## External context
No external context materially changed the design.

## Documentation impact
No documentation changes are required because this is a bugfix to restore intended dashboard behavior.

## Architecture plan
Keep the dashboard route mounted for all users.
When no pipelines exist, render the onboarding guide as an overlay and render a structured empty state underneath it so dismissing the guide leaves the page usable.

## Edge cases
| Edge case | Handling |
|---|---|
| Zero pipelines and guide visible | Show guide overlay and empty state beneath it |
| Zero pipelines and guide dismissed | Show empty state without overlay |
| Dashboard API calls fail while zero pipelines | Preserve visible page shell and error states |

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Existing onboarding tests assume guide-only rendering | Low | Medium | Update tests to cover both overlay and persistent empty state |

## Testing strategy
- **Unit:** Dashboard zero-pipeline dismissed state.
- **E2E:** Browser verification that dismissing onboarding keeps visible dashboard content.

## Acceptance criteria
- [x] Zero-pipeline dashboard remains visible after dismissing onboarding
- [x] Frontend regression test added
- [x] Browser verification against the running container