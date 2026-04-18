# Feature: Observability IA Reduction

**Status:** In Review
**Created:** 2026-04-12
**Author:** @github-copilot
**Estimate:** M
**Supersedes:** frontend-enterprise-hardening.md (navigation scope only)

---

## Problem
The frontend currently presents too many first-class workflows for a product whose core value is observing and operating company pipelines. Studio, catalog, node authoring, connections, changelog, executive reporting, streaming, and API reference all compete with the operator path in the primary navigation. That dilutes the product story, increases cognitive load, and makes enterprise-readiness gaps in identity, governance, and incident response more visible.

The immediate user need is to make the product feel like an observability control plane rather than a broad demo suite while preserving advanced surfaces that may still be useful for internal or future workflows.

## Success criteria
- The primary navigation is centered on observability and operations, not authoring.
- Runs and executions are presented as one coherent operational surface.
- API Reference no longer uses a route that conflicts with the `/api` dev proxy prefix.
- Studio and adjacent authoring surfaces remain available, but are no longer promoted as the default product path.

---

## Requirements

### Functional
- [ ] The primary sidebar shows only the observability-first pages: Dashboard, Pipelines, Runs, System Health, Alerts, Data Quality, Audit Log, Docs, and Settings.
- [ ] Studio, Catalog, Node Library, Connections, Streaming, Executive, Changelog, Compare Runs, Alert Rules, and API Reference are removed from the primary navigation.
- [ ] The command palette mirrors the reduced primary IA and points dispatch operations to the merged runs surface.
- [ ] The Runs surface exposes two explicit subviews: run history and execution dispatches.
- [ ] Existing `/executions` links remain functional by resolving to the merged runs surface instead of a separate top-level page.
- [ ] API Reference is available at `/docs/api-reference`, and all maintained in-app links use that route.
- [ ] First-run onboarding stops presenting Studio or connections management as the default path for primary personas.
- [ ] The docs hub, walkthroughs, and contextual help distinguish default operator workflows from optional advanced authoring, configuration, and integration surfaces.

### Non-functional
- [ ] Performance: the merged runs surface must not fetch run history when the dispatches subview is active.
- [ ] Security: no new route may bypass the existing authenticated API client conventions.
- [ ] Accessibility: the merged runs/dispatches switch uses keyboard-focusable controls with clear selected state.
- [ ] Observability: dispatch status updates continue to refresh through the existing realtime execution events.

---

## Affected components
- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/components/CommandPalette.tsx`
- `frontend/src/components/FirstRunGuide.tsx`
- `frontend/src/components/HelpPanel.tsx`
- `frontend/src/components/connections/FormParts.tsx`
- `frontend/src/components/connections/PipelineSelectionSection.tsx`
- `frontend/src/components/operations/ExecutionDispatchesPanel.tsx`
- `frontend/src/pages/ConnectionsPage.tsx`
- `frontend/src/pages/ExecutiveDashboardPage.tsx`
- `frontend/src/pages/NodesLibraryPage.tsx`
- `frontend/src/pages/PipelineCatalogPage.tsx`
- `frontend/src/pages/ExecutionsPage.tsx`
- `frontend/src/pages/RunsPage.tsx`
- `frontend/src/pages/PipelineStudio/PipelineStudioEditor.tsx`
- `frontend/src/pages/DocsPage.tsx`
- `frontend/src/pages/DocsTopicPage.tsx`
- `frontend/src/pages/docsContent.ts`
- `frontend/src/pages/GettingStartedPage.tsx`
- `frontend/src/routes/prefetch.ts`
- `frontend/src/components/docs/TaskGuide.tsx`
- `frontend/src/components/docs/docsContent.ts`
- `frontend/src/__tests__/RunsPage.test.tsx`
- `frontend/src/__tests__/CommandPalette.test.tsx`
- `frontend/src/__tests__/ConnectionsPage.coverage.test.tsx`
- `frontend/src/__tests__/DocsPage.test.tsx`
- `frontend/src/__tests__/DocsTopicPage.test.tsx`
- `frontend/src/__tests__/ExecutiveDashboardPage.test.tsx`
- `frontend/src/__tests__/NodesLibraryPage.test.tsx`
- `frontend/src/__tests__/PipelineCatalogPage.coverage.test.tsx`

---

## External context
- No external research materially changed this design. The approach is driven by repository evidence and the current product goal stated by the user.

---

## Documentation impact
- This working spec becomes the source of truth for the IA reduction.
- Long-form docs, contextual help, and onboarding content must classify Studio, connections, CLI/API, and secondary reporting paths as advanced rather than default.
- Advanced surfaces still exist and remain documented, but they should live in clearly labeled secondary or advanced sections.

---

## Architecture plan
The change preserves all advanced product surfaces but removes them from the primary navigation contract. The app shell becomes explicitly operator-first. The runs route becomes the canonical operational evidence surface by owning both historical run analysis and execution dispatch status. The existing executions UI is extracted into a reusable panel and embedded under the runs route, while `/executions` becomes a compatibility path that resolves to the merged surface.

API Reference is moved under the docs hierarchy because `/api-reference` conflicts with the frontend dev proxy prefix and is conceptually a support artifact, not a primary workflow.

### Page classification

| Classification | Pages |
|---|---|
| Primary | Dashboard, Pipelines, Runs, System Health, Alerts, Data Quality, Audit Log, Docs, Settings |
| Secondary / advanced | Studio, Catalog, Node Library, Connections, Executive, Streaming, Changelog, API Reference, Compare Runs, Alert Rules |
| Supporting utilities | Notifications, Getting Started, Login |

### Documentation classification

| Classification | Guidance |
|---|---|
| Default operator guidance | Overview, operations, alerts, quality, security/governance, role quick starts, runbooks |
| Advanced workflow guidance | Walkthrough, Studio, Node Library, Connections, API Reference, CLI Reference, advanced task guides |
| Secondary support context | Executive summaries, changelog, streaming, release-note links |

### Enterprise gaps this change is making room for
- Org/workspace/environment model and enterprise identity integration
- Pipeline portfolio metadata: owner, team, criticality, environment, SLA/SLO
- Incident workflow surfaces: maintenance windows, acknowledgement ownership, escalation, suppression
- Stronger global search across runs, pipelines, alerts, and docs
- First-class external orchestration integrations rather than deeper authoring-first expansion

---

## API design
- No backend API contracts change in this work.
- Existing execution and run endpoints remain unchanged.

---

## Data model changes
- No database or storage changes.
- Migration notes: Not applicable.
- Breaking change? No backend or schema breaking change. UI navigation changes are intentional product-scope changes.

---

## Edge cases

| Edge case | Handling |
|---|---|
| User opens `/executions` from an old link | Route resolves to the merged runs surface with the dispatches subview active |
| User opens `/api-reference` from an old in-app link | Client-side route redirects to `/docs/api-reference`; maintained links are updated to the new route |
| Dispatches view is active | Run-history API fetch and run-history realtime refresh are skipped |
| No dispatches exist | Surface shows a neutral empty state without referring users back to Studio as the primary path |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hidden links or docs still point to deprecated primary routes | Medium | Medium | Preserve compatibility route for `/executions`; update maintained API reference links |
| Merged runs page becomes harder to scan | Medium | Medium | Keep the subviews explicit and preserve existing Runs table behavior unchanged |
| Users relying on Studio discoverability are surprised | Medium | Low | Keep direct routes functional and preserve advanced links in contextual docs/help |
| Docs still frame advanced surfaces as the default product story | Medium | Medium | Split docs content into primary and advanced lanes and update onboarding/help copy in the same change |

---

## Breaking changes
- The primary navigation and command palette no longer advertise authoring and secondary support surfaces.
- `/api-reference` is no longer the canonical API Reference route.
- No backend, data, or SDK consumer contract changes are introduced.

---

## Testing strategy
- **Unit:** runs surface subview switching, command palette item set, existing executions panel behavior.
- **Integration:** route compatibility for `/executions` and API reference docs route via router-level checks or manual browser validation.
- **E2E:** verify desktop navigation, merged runs surface, and `/docs/api-reference` deep-link behavior in the dev app.
- **Performance:** confirm the runs API is not called while dispatches subview is active.
- **Security:** verify the dispatches subview continues to use the existing authenticated execution APIs only.

---

## Acceptance criteria
- [ ] Primary navigation is observability-first and excludes Studio-adjacent surfaces
- [ ] Command palette mirrors the reduced primary navigation
- [ ] Runs exposes a dispatches subview and remains the canonical operations route
- [ ] `/executions` compatibility path lands on the merged runs surface
- [ ] API Reference is reachable through `/docs/api-reference`
- [ ] Maintained API Reference links use the new docs route
- [ ] Onboarding no longer presents Studio as a default primary path
- [ ] Docs and contextual help label Studio, connections, API/CLI, and secondary reporting pages as advanced or secondary workflows
- [ ] Frontend regression tests cover the merged runs surface and reduced nav contract