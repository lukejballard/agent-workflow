# Feature: Server-Side Run Pagination

> Note: This completed spec is inherited run-surface context from a pipeline-focused
> product and should not be treated as a current biomechanics requirement.

**Status:** Done (PR #32)
**Created:** 2026-04-11
**Author:** @lukejballard
**Estimate:** S
**Supersedes:** N/A

---

## Problem

`RunsPage` calls `getAllRuns()` which fetches **every pipeline run** from the collector in a single HTTP request. All filtering (status, search text, date range), sorting, and pagination happen client-side via `useMemo` + `Array.slice()`.

**Who experiences it:** Data engineers and platform operators who use Run Explorer daily.

**Frequency:** Every page load of `/runs`.

**Impact of not solving:** As run history grows past several hundred rows, the initial page load becomes progressively slower (full table scan, full JSON serialization, full network transfer, full client-side processing). At ~1,000+ runs the UX becomes noticeably sluggish; at ~10,000+ it risks browser tab crashes due to memory pressure from sorting/filtering large arrays.

**Root cause:** The backend already has a paginated `/runs` endpoint in `run_routes.py` (with SQL `OFFSET`/`LIMIT`), but a legacy endpoint in `server.py` shadows it and returns a flat list. The frontend calls the legacy endpoint and ignores the paginated one entirely.

## Success criteria

- `/runs` page loads in < 500ms regardless of total run count (network + render)
- Only 25 rows are transferred per request (matching current `PAGE_SIZE`)
- Status filter, text search, and column sort are handled server-side
- Existing WebSocket real-time refresh continues to work
- No regression in Run Explorer functionality

---

## Requirements

### Functional

- [ ] `GET /runs` returns a paginated response `{items, total, page, per_page}` for **all callers** (no flat-list fallback)
- [ ] `GET /runs` accepts query params: `page` (int, default 1), `page_size` (int, default 25, max 100), `pipeline_id` (str, optional), `status` (str, optional), `search` (str, optional), `sort` (str, optional, e.g. `duration_ms`), `sort_dir` (str, `asc`|`desc`, default `desc`)
- [ ] `RunsPage` fetches one page per request using the paginated API
- [ ] Changing page number, status filter, search text, or sort column triggers a fresh API call
- [ ] Page resets to 1 when any filter/sort changes
- [ ] Pagination component shows correct total count from server response
- [ ] WebSocket `run.step_ingested` events refetch the current page (not all runs)
- [ ] Date-range filter (`24h`, `7d`, custom) is applied server-side via `since`/`until` ISO-8601 query params
- [ ] Deep-linkable: page, filters, and sort state are reflected in URL query params (optional, nice-to-have)

### Non-functional

- [ ] Performance: p95 response time for `GET /runs?page=1&page_size=25` < 200ms with 100k runs in SQLite
- [ ] Security: No auth changes required (existing auth middleware applies)
- [ ] Observability: Existing Prometheus `pipeline_runs_total` counter remains accurate

---

## Affected components

### Backend

| File | Change |
|------|--------|
| `src/biomechanics_ai/collector/server.py` (line 300-332) | Remove legacy `@app.get("/runs")` endpoint |
| `src/biomechanics_ai/collector/run_routes.py` (line 153-231) | Remove public-caller short-circuit (line ~184); add `search`, `sort`, `sort_dir`, `since`, `until` query params |
| `src/biomechanics_ai/storage/metadata.py` (line 201-245) | Add `offset`, `limit`, `search`, `sort_key`, `sort_dir`, `since`, `until` params to `list_runs()` |
| `src/biomechanics_ai/models/run_schemas.py` (line 196-203) | Verify `RunListResponse` schema; no changes expected |

### Frontend

| File | Change |
|------|--------|
| `frontend/src/types/run.ts` (line 69-75) | Align `RunListResponse`: rename `page_size` to `per_page`, remove `has_more` (or compute client-side) |
| `frontend/src/api/runs.ts` (line 16-18, 69-80) | Enhance `getRuns()` with `search`, `sort`, `since`, `until` params; deprecate `getAllRuns()` |
| `frontend/src/pages/RunsPage.tsx` | Replace `useFetch(getAllRuns)` with paginated `getRuns()` calls; remove client-side filter/sort `useMemo`; wire `Pagination` to trigger refetch |
| `frontend/src/components/Pagination.tsx` | No changes needed |

### Database

No schema changes. No migrations. Uses existing `pipeline_runs` and `pipeline_steps` tables.

---

## Architecture plan

### Current flow (broken)

```
RunsPage mount
    │
    ▼
getAllRuns() ──── GET /runs ────► server.py legacy endpoint
    │                                     │
    ▼                                     ▼
RunSummary[] (ALL rows)          list_runs(session) → all rows
    │
    ▼
useMemo: filter by status, search, date
    │
    ▼
useMemo: sort by column
    │
    ▼
Array.slice(start, end) ──► render 25 rows
```

### Target flow

```
RunsPage mount / filter change / page change
    │
    ├─ page=1, page_size=25, status="failed", search="etl", sort="duration_ms:desc"
    │
    ▼
getRuns(params) ──── GET /runs?page=1&page_size=25&status=failed&search=etl&sort=duration_ms&sort_dir=desc
    │                                     │
    ▼                                     ▼
RunListResponse                   run_routes.py list_runs()
{                                         │
  items: RunSummary[25],          SQL: SELECT ... WHERE status = 'failed'
  total: 142,                           AND (run_id LIKE '%etl%' OR pipeline_name LIKE '%etl%')
  page: 1,                              ORDER BY duration_ms DESC
  per_page: 25                           LIMIT 25 OFFSET 0
}                                         │
    │                                     ▼
    ▼                              COUNT(*) → total = 142
render 25 rows
Pagination: "1-25 of 142"
```

### WebSocket refresh flow (unchanged pattern)

```
SSE: run.step_ingested
    │
    ▼
refetch() ──► getRuns(currentParams) ──► re-render current page
```

---

## API design

### `GET /runs` (modified — consolidate to single implementation)

- **Auth required:** Inherits existing auth (control-plane key or public, depending on config)
- **Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 25 | Items per page (1-100) |
| `pipeline_id` | str | — | Filter by pipeline ID |
| `status` | str | — | Filter by run status (`success`, `error`, `running`) |
| `search` | str | — | Case-insensitive substring match on `run_id` and `pipeline_name` |
| `sort` | str | `start_time` | Sort column: `pipeline_name`, `run_id`, `status`, `duration_ms`, `steps`, `pipeline_version`, `start_time` |
| `sort_dir` | str | `desc` | Sort direction: `asc` or `desc` |
| `since` | str (ISO-8601) | — | Runs started after this timestamp |
| `until` | str (ISO-8601) | — | Runs started before this timestamp |

- **Success response (200):**
```json
{
  "items": [
    {
      "pipeline_name": "etl_pipeline",
      "run_id": "abc-123",
      "steps": 5,
      "status": "success",
      "duration_ms": 12340,
      "git_sha": "a1b2c3d",
      "pipeline_version": "1.2.0",
      "start_time": "2026-04-11T08:00:00Z"
    }
  ],
  "total": 142,
  "page": 1,
  "per_page": 25
}
```

- **Error responses:**
  - `400` — Invalid query param (e.g. `page_size=0`, unknown `sort` column)
  - `401` — Not authenticated (when API key is required)

---

## Data model changes

No new tables or columns.

### Query changes to `list_runs()` in `metadata.py`

Add optional parameters:

```python
def list_runs(
    session,
    *,
    offset: int = 0,
    limit: int = 25,
    search: str | None = None,
    status: str | None = None,
    sort_key: str = "start_time",
    sort_dir: str = "desc",
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[list[dict], int]:
    """Returns (items, total_count)."""
```

The function applies `WHERE` clauses for `status`, `search` (ILIKE on `run_id` and `pipeline_name`), `since`/`until` (on `timestamp`), then `ORDER BY sort_key sort_dir`, then `LIMIT limit OFFSET offset`. A separate `COUNT(*)` query (with the same `WHERE` clauses) returns the total.

### Migration notes
- No migration needed
- Not a breaking change for internal consumers (new params are all optional with defaults matching current behavior)

---

## Edge cases

| Edge case | Handling |
|-----------|----------|
| `page` exceeds total pages | Return empty `items: []` with correct `total` (not 404) |
| `page_size=0` or negative | Return 400 validation error |
| `search` is empty string | Ignore filter (treat as no search) |
| `sort` column doesn't exist | Return 400 with allowed column list |
| `since` > `until` | Return empty results (valid but logically empty range) |
| No runs exist at all | Return `{items: [], total: 0, page: 1, per_page: 25}` |
| WebSocket refetch during page change | Race condition — latest response wins (React state update) |
| Other pages calling `getAllRuns()` | Audit all callers — `DashboardPage` uses `/dashboard/recent-runs` (separate endpoint, unaffected). No other page calls `getAllRuns()` |
| `RunComparisonPage` uses `getAllRuns()` for the run selector dropdowns | Must either switch to `getRuns()` with large `page_size` or keep `getAllRuns()` as a separate function that also calls the paginated endpoint with a high limit |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legacy endpoint removal breaks other consumers | Low | Medium | Audit all `GET /runs` callers (frontend + tests) before removing |
| `RunComparisonPage` run selector needs all runs for dropdown | Medium | Low | Use `getRuns({page_size: 100})` or add a lightweight `/runs/list-brief` endpoint |
| Server-side search is slower than client-side for small datasets | Low | Low | SQLite `LIKE` is fast for < 100k rows; add index on `pipeline_name` if needed |
| Client-side date filter (`24h`, `7d`, custom) logic orphaned | Low | Low | Convert to `since`/`until` ISO-8601 params passed to API |

---

## Breaking changes

- `GET /runs` response shape changes from `RunSummary[]` (flat array) to `{items, total, page, per_page}` (paginated object). Any external consumer expecting a flat array will break.
- Mitigation: This is an internal API with no documented external consumers. The frontend is the only caller.

---

## Testing strategy

- **Unit:** Test `list_runs()` with various filter/sort/pagination combinations. Test edge cases (empty results, out-of-range page, bad sort column).
- **Integration:** Test `GET /runs` endpoint with query params via `httpx.AsyncClient`. Verify response schema matches `RunListResponse`. Test that pagination math is correct (total, offset, limit).
- **E2E:** Playwright test: load `/runs`, verify table shows 25 rows, click "Next", verify new data loads, apply status filter, verify results change, type in search, verify results filter.
- **Performance:** Not required for S-size, but recommend manual testing with 10k+ seeded runs.
- **Security:** No new auth surface; existing tests cover auth.

---

## Acceptance criteria

- [ ] All functional requirements implemented
- [ ] Legacy `@app.get("/runs")` in `server.py` removed
- [ ] `run_routes.py` handles all `/runs` requests with pagination
- [ ] `metadata.list_runs()` supports offset/limit/search/sort/date filtering
- [ ] Frontend `RunsPage` uses server-side pagination (no client-side `Array.slice`)
- [ ] Frontend `RunListResponse` type aligned with backend response
- [ ] Pagination component shows server-side `total` count
- [ ] All unit tests pass (80%+ coverage on changed code)
- [ ] All integration tests pass
- [ ] E2E happy path passes in Playwright
- [ ] CI green (lint, typecheck, tests, build)
- [ ] No regression in existing Run Explorer features (compare, DAG links, WebSocket refresh)
