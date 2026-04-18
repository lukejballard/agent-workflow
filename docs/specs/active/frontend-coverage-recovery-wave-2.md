# Feature: Frontend Coverage Recovery Wave 2

**Status:** Implemented
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** L
**Supersedes:** docs/specs/active/frontend-coverage-recovery-wave-1.md

---

## Problem
The prior coverage-recovery wave fixed the alerting surface and expanded page coverage, but the verified repo-wide frontend snapshot remains far below the newly raised 90% target.
The current coverage report shows two different classes of risk: several route pages still have no direct page-level regression coverage at all, and several already-imported denominator-heavy modules remain deeply under-covered, especially API helper modules, `components/quality`, and `components/settings`.
If the next tranche only adds more page tests, it will likely repeat the previous denominator problem and can lower the global snapshot instead of raising it.

## Success criteria
This wave should add direct regression coverage for the next missing route surfaces, repair the currently low-covered denominator files that are already depressing the snapshot, and remove the remaining direct-transport violation on the streaming page.
The post-wave frontend coverage snapshot should increase materially over the current baseline while the program target is now tracked against 90% instead of 80%.

---

## Requirements

### Functional
- [x] Add direct page-level regression suites for Connections, Pipeline Catalog, and Streaming.
- [x] Page tests cover meaningful loading, empty, filtering, state-switching, and action flows instead of smoke-only rendering.
- [x] Add direct regression tests for the currently low-covered API helper modules that are already in the coverage denominator, including audit, alerts, runs, settings, and pipeline-definition resource helpers.
- [x] Add direct regression tests for the currently low-covered settings and quality components, especially export/import and drilldown or trend behavior.
- [x] Add direct regression tests for low-covered studio utility surfaces already in the denominator, especially data preview, step-type selection, studio service wrappers, and pipeline studio utility helpers.
- [x] Move streaming page transport out of the page and into `frontend/src/api/` so the page no longer performs direct network access.

### Non-functional
- [x] Accessibility: touched tests use accessible locators and touched UI controls retain accessible names and keyboard-usable behavior.
- [x] Architecture: no new direct `fetch()` calls are introduced in pages or components; the streaming page follows the API-helper boundary.
- [x] Regression safety: the full frontend suite is rerun with coverage and the build is reverified after implementation.
- [x] Documentation: this active spec records the coverage delta and any remaining gaps against the 90% target honestly.

---

## Affected components
- `docs/specs/active/frontend-coverage-recovery-wave-2.md`
- `frontend/src/pages/ConnectionsPage.tsx`
- `frontend/src/pages/PipelineCatalogPage.tsx`
- `frontend/src/pages/StreamingPage.tsx`
- `frontend/src/api/alerts.ts`
- `frontend/src/api/audit.ts`
- `frontend/src/api/pipelineDefinitions.ts`
- `frontend/src/api/runs.ts`
- `frontend/src/api/settings.ts`
- `frontend/src/api/streaming.ts`
- `frontend/src/components/settings/SettingsExportImport.tsx`
- `frontend/src/components/settings/SettingsSection.tsx`
- `frontend/src/components/DataPreview.tsx`
- `frontend/src/components/quality/MetricTooltip.tsx`
- `frontend/src/components/quality/QualityDrilldown.tsx`
- `frontend/src/components/quality/QualityTrendChart.tsx`
- `frontend/src/components/quality/StepQualityCard.tsx`
- `frontend/src/pages/PipelineStudio/components/StepTypePicker.tsx`
- `frontend/src/pages/PipelineStudio/services/studioService.ts`
- `frontend/src/utils/pipelineStudioUtils.ts`
- `frontend/src/__tests__/AlertChannelsTab.test.tsx`
- `frontend/src/__tests__/ConnectionsPage.coverage.test.tsx`
- `frontend/src/__tests__/PipelineCatalogPage.coverage.test.tsx`
- `frontend/src/__tests__/StreamingPage.coverage.test.tsx`
- `frontend/src/__tests__/DataPreview.test.tsx`
- `frontend/src/__tests__/SettingsExportImport.test.tsx`
- `frontend/src/__tests__/SettingsSection.test.tsx`
- `frontend/src/__tests__/MetricTooltip.test.tsx`
- `frontend/src/__tests__/QualityDrilldown.test.tsx`
- `frontend/src/__tests__/QualityTrendChart.test.tsx`
- `frontend/src/__tests__/StepQualityCard.test.tsx`
- `frontend/src/__tests__/StepTypePicker.test.tsx`
- `frontend/src/__tests__/pipelineStudioUtils.test.ts`
- `frontend/src/__tests__/apiResources.coverage.test.ts`
- `frontend/src/__tests__/pipelineDefinitionsResources.test.ts`
- `frontend/src/__tests__/runsApi.coverage.test.ts`
- `frontend/src/__tests__/studioService.test.ts`

---

## External context
No external context materially changed this wave.
The scope and verification strategy were driven by the repository testing standards, the current frontend architecture, and the measured coverage gaps from the previous verified frontend snapshot.

## Documentation impact
No contributor-facing or user-facing documentation changed beyond this active spec because the product behavior remained the same.
This spec is the source of truth for the implemented file set, verification evidence, coverage delta, and remaining recovery backlog.

## API design
No backend API contract changes.
The only frontend boundary change was moving streaming transport behind `frontend/src/api/streaming.ts` so the page consumes an existing typed helper instead of making direct transport calls.

## Data model changes
No data model changes.

## Breaking changes
No breaking changes.

---

## Architecture plan
Use a net-gain coverage strategy instead of a page-only strategy.

- Add the three missing page suites the prior wave identified as the next uncovered route cluster.
- Pair those new page suites with direct coverage of the already-imported low-performing denominator files so the repo-wide snapshot rises instead of falling.
- Extend the same denominator-repair strategy into the existing studio utility and helper modules when the first full rerun still shows them as major uncovered sinks.
- Keep page tests focused on page-visible behavior and mock boundaries where doing so avoids dragging in unrelated implementation trees.
- Fix the streaming transport boundary at the root by moving HTTP access into `frontend/src/api/streaming.ts`.

Alternative considered:
- Add only page-level suites for Connections, Pipeline Catalog, and Streaming.

Why rejected:
- The current coverage report shows that API helpers, settings components, and quality components are already low-covered denominator sinks.
- Adding only page suites would likely import more code than it verifies and can reduce the top-line snapshot.

---

## Edge cases

| Edge case | Handling |
|---|---|
| No pipelines exist for Connections | Page shows the no-pipelines empty state and does not render connection panels |
| Pipeline Catalog filters remove all results | Filtered empty state remains explicit and actionable |
| Pipeline Catalog clone or archive fails | Error toast path remains explicit |
| Streaming endpoints return no topics and no consumers | Streaming page shows the setup empty state |
| Streaming endpoints fail independently | Page degrades to the empty state rather than throwing |
| Settings import receives invalid extension or invalid JSON | Export/import component surfaces the correct error path |
| Quality drilldown has no changed fields or too little history | Empty and insufficient-data states remain explicit |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New page suites lower global coverage by importing large low-covered trees | High | High | Pair page work with denominator repair in API, settings, and quality modules |
| Over-mocked page tests stop reflecting real user-visible behavior | Medium | Medium | Keep assertions on visible outcomes and mock only what is necessary to isolate page behavior |
| The 90% target remains out of reach after this wave | High | Medium | Record the post-wave snapshot honestly and treat 90% as the governing target for subsequent waves, not as an assumed outcome |

---

## Testing strategy
- **Unit/component:** settings export/import, settings section rows, metric tooltip, quality drilldown, quality trend chart, step quality card.
- **Unit/component:** data preview and step-type picker.
- **Page-level:** connections, pipeline catalog, streaming.
- **API-helper:** audit, alerts, runs, settings, pipeline-definition resource helpers, streaming transport helpers.
- **Studio utility/service:** pipeline studio helper utilities and studio service wrappers.
- **Full verification:** rerun the full frontend suite with coverage and rerun the frontend build.

---

## Acceptance criteria
- [x] Connections, Pipeline Catalog, and Streaming page suites added and passing
- [x] Streaming page no longer performs direct transport access
- [x] API helper recovery tests added and passing
- [x] Settings and quality component tests added and passing
- [x] Studio utility and service recovery tests added and passing
- [x] Full frontend suite rerun with updated coverage snapshot against the 90% target
- [x] Residual coverage risks summarized honestly

---

## Outcome
This wave repaired the next uncovered page cluster, moved the streaming page behind a typed API helper boundary, and paired that page work with denominator repair across low-covered API, settings, quality, and studio utility surfaces.
It also extended the recovery strategy into deterministic studio modules after the first full rerun showed those files were still acting as large uncovered sinks.

## Verification summary
- Targeted wave-2 regression tranche passed: 12 files / 33 tests
- Added studio recovery tranche passed: 4 files / 24 tests
- Final full frontend suite passed: 54 files / 278 tests
- Final frontend coverage snapshot: 77.96% statements / 67.40% branches / 76.93% functions / 78.61% lines
- Coverage delta versus wave-1 baseline: +12.24 statements / +11.67 branches / +12.45 functions / +11.85 lines
- High-value repaired sinks now covered strongly: `DataPreview.tsx` 96.66% lines, `StepTypePicker.tsx` 100% lines, `studioService.ts` 100% lines, `pipelineStudioUtils.ts` 100% lines
- Frontend build reverified with `npm.cmd run build`

## Residual risks
- The repo-wide frontend snapshot is still below both the repository 80% line-and-branch expectation and the user-raised 90% target, so further recovery waves are still required.
- The next highest-value uncovered sinks are concentrated in `components/CustomFailure.tsx`, `components/FirstRunGuide.tsx`, `components/HelpPanel.tsx`, `pages/AlertRulesPage.tsx`, `pages/AlertsPage.tsx`, `pages/AuditPage.tsx`, and `pages/RunDetailsPage.tsx`.
- Branch coverage remains the most constrained metric; even where line coverage improved materially, several alerting, page, and context surfaces still have untested decision paths.