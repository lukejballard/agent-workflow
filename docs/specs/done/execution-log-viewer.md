# Feature: Execution Log Viewer

**Status:** Done (PR #33)
**Created:** 2026-04-11
**Author:** @lukejballard
**Estimate:** S
**Supersedes:** N/A

---

## Problem

The Executions page (`/executions`) displays execution history with cancel and retry actions, but provides **no way to view execution output or logs**. The backend already stores log text in the `execution_history.logs` column and serves it via `GET /executions/{id}/logs/raw` and inline in `GET /executions/{id}`, but no frontend component renders this data.

**Who experiences it:** Platform engineers and data engineers who trigger pipeline executions and need to diagnose failures or verify output.

**Frequency:** Every time a user triggers an execution and wants to see what happened — multiple times per day for active teams.

**Impact of not solving:** Users must leave the dashboard to find logs elsewhere (container logs, SSH, etc.), breaking their workflow and increasing mean-time-to-diagnosis for failed executions.

## Success criteria

- Users can view execution logs without leaving the dashboard
- Log viewing works for completed, failed, and cancelled executions
- Time-to-diagnosis for execution failures is reduced (qualitative — users no longer need to switch tools)
- Zero backend changes required (leverages existing endpoints)

---

## Requirements

### Functional

- [ ] Every execution row with status `success`, `failed`, or `cancelled` shows a "View Logs" button
- [ ] Clicking "View Logs" expands an inline log viewer below the execution row
- [ ] Clicking "View Logs" again (or a "Close" control) collapses the log viewer
- [ ] Only one log viewer is expanded at a time (expanding a new one closes the previous)
- [ ] Log content is fetched lazily — only when the user clicks "View Logs" (not on page load)
- [ ] Loading state is shown while logs are being fetched
- [ ] Empty/null logs display a "No logs available" message
- [ ] Log viewer shows line numbers
- [ ] Log viewer has a "Copy to clipboard" button for the full log text
- [ ] Executions with status `pending` or `running` do not show "View Logs" (logs are incomplete)

### Non-functional

- [ ] Performance: Log fetch completes in < 1s for logs up to 1MB
- [ ] Security: Log endpoint inherits existing auth middleware (no new auth surface)
- [ ] Accessibility: Log viewer is keyboard-navigable; button has accessible label
- [ ] Observability: No new metrics required (existing request logging covers the endpoint)

---

## Affected components

### Backend

No changes. All required endpoints already exist:

| Endpoint | File | Purpose |
|----------|------|---------|
| `GET /executions/{id}/logs/raw` | `server.py:510-536` | Returns raw log text as `text/plain` |
| `GET /executions/{id}` | `execution_routes.py:259-273` | Returns `ExecutionOut` + `logs` field |

### Frontend

| File | Change |
|------|--------|
| `frontend/src/api/executions.ts` | Add `getExecutionLogsRaw(id: number): Promise<string>` |
| `frontend/src/components/CodeBlock.tsx` (line 98) | Add `"text"` to the `language` union type |
| `frontend/src/pages/ExecutionsPage.tsx` | Add "View Logs" button, expandable row, log viewer integration |
| `frontend/src/components/ExecutionLogViewer.tsx` | **New component** — fetches and renders logs |

### Database

No changes. Uses existing `execution_history.logs` column (`Text`, nullable).

---

## Architecture plan

### Data flow

```
User clicks "View Logs" on execution #42
    │
    ▼
ExecutionsPage: sets expandedId = 42
    │
    ▼
<ExecutionLogViewer executionId={42} />  mounts
    │
    ▼
useEffect: getExecutionLogsRaw(42)
    │
    ▼
GET /executions/42/logs/raw  ──►  server.py:execution_logs_raw()
    │                                       │
    ▼                                       ▼
Response: "text/plain"              DB: SELECT logs FROM execution_history WHERE id = 42
    │                                       │
    ▼                                       ▼
setState({ logs: responseText })    Return h.logs or "No logs stored..."
    │
    ▼
<CodeBlock
  code={logs}
  language="text"
  showLineNumbers={true}
  filename={`execution-${42}.log`}
/>
```

### Component hierarchy

```
ExecutionsPage
├── <table>
│   ├── <ExecutionRow>           (existing)
│   │   ├── ... existing columns ...
│   │   └── Actions: Cancel | Retry | [View Logs]   ← new button
│   │
│   ├── {expandedId === row.id && (
│   │     <tr className="log-row">          ← new expandable row
│   │       <td colSpan={9}>
│   │         <ExecutionLogViewer            ← new component
│   │           executionId={row.id}
│   │         />
│   │       </td>
│   │     </tr>
│   │   )}
│   │
│   └── ... more rows ...
```

### Why `GET /executions/{id}/logs/raw` instead of `GET /executions/{id}`?

- The detail endpoint returns the full `ExecutionOut` + logs as a JSON-encoded string. For large logs, this means double-encoding overhead (log text embedded in JSON string).
- The raw endpoint returns `text/plain` — simpler, lighter, and avoids JSON parsing of potentially megabyte-scale text.
- The raw endpoint is purpose-built for this use case.

---

## API design

### Existing: `GET /executions/{exec_id}/logs/raw`

No changes to the backend. Documenting the existing contract for frontend consumption.

- **Auth required:** Inherits existing middleware (no explicit role dependency on this endpoint)
- **Path params:** `exec_id` (int) — execution history primary key
- **Success response (200):**
  - Content-Type: `text/plain`
  - Body: Raw log text string
  ```
  2026-04-11 08:00:01 INFO  Starting pipeline etl_pipeline
  2026-04-11 08:00:02 INFO  Step load_data completed (1234 rows)
  2026-04-11 08:00:05 ERROR Step transform failed: KeyError 'amount'
  ```
- **Empty logs response (200):**
  - Body: `"No logs stored for execution 42."`
- **Error responses:**
  - `404` — Execution ID does not exist

### New frontend function: `getExecutionLogsRaw()`

```typescript
// frontend/src/api/executions.ts

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function getExecutionLogsRaw(id: number): Promise<string> {
  const res = await fetch(`${BASE_URL}/executions/${id}/logs/raw`, {
    headers: getAuthHeaders(),  // reuse existing auth header logic
  });
  if (!res.ok) throw new Error(`Failed to fetch logs: ${res.status}`);
  return res.text();
}
```

Note: This uses `fetch` + `.text()` directly (not `fetchJSON`) because the response is `text/plain`.

---

## Data model changes

None. Uses existing `execution_history.logs` column.

### Migration notes
- No migration needed
- No rollback needed
- Not a breaking change

---

## Edge cases

| Edge case | Handling |
|-----------|----------|
| Logs column is `NULL` in DB | Backend returns `"No logs stored for execution {id}."` — frontend displays this as the log content |
| Logs are very large (> 1MB) | `CodeBlock` renders the full string. No virtualization. For V1 this is acceptable — execution logs are typically < 100KB. If logs > 5MB become common, a follow-up can add `react-window` virtualization or a "Download" link |
| Execution is still running | "View Logs" button is hidden (only shown for terminal statuses: `success`, `failed`, `cancelled`) |
| Execution was retried (new execution created) | Each execution has its own logs. Both the original and retry show independent "View Logs" buttons |
| Network error fetching logs | `ExecutionLogViewer` catches the error and shows an inline error message with a retry button |
| User clicks "View Logs" on two rows rapidly | Only one expanded at a time — the state is `expandedId: number | null`. Second click closes the first |
| User clicks "View Logs" then clicks Cancel/Retry on same row | Cancel/Retry handlers do not affect `expandedId`. Log viewer stays open. After the action completes and the list refreshes, the execution status may change, but the expanded row remains (keyed by `id`, which is stable) |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Large logs cause browser tab to slow down | Low | Medium | For V1, accept the limitation. Add a "Download as file" fallback link. Log a warning in console if content > 500KB |
| `CodeBlock` styling doesn't look good for plain text logs | Low | Low | The `language="text"` option renders without syntax highlighting, which is appropriate for logs. Line numbers and monospace font handle readability |
| Auth header not sent on raw text fetch | Medium | Medium | Reuse the existing `getAuthHeaders()` from `http.ts` or inline the token logic. Test with `BIOMECHANICS_AI_API_KEY` set |

---

## Breaking changes

None. This is a purely additive frontend change with no backend modifications.

---

## Testing strategy

- **Unit:**
  - `ExecutionLogViewer`: Test loading state, content rendering, error state, empty logs message
  - `getExecutionLogsRaw()`: Mock fetch, verify it calls the correct URL and returns text
- **Integration:**
  - Verify `GET /executions/{id}/logs/raw` returns `text/plain` (existing endpoint — verify no regression)
  - Verify the frontend correctly handles the `text/plain` response (not JSON-parsed)
- **E2E (Playwright):**
  - Navigate to `/executions`
  - Find a completed execution row
  - Click "View Logs"
  - Verify log content appears in an expanded row
  - Verify line numbers are visible
  - Click "Copy" and verify clipboard content
  - Click "View Logs" again to collapse
  - Find a `pending` execution — verify no "View Logs" button
- **Performance:** Not required (existing endpoint, small component)
- **Security:** No new auth surface — existing middleware covers the endpoint

---

## Acceptance criteria

- [ ] All functional requirements implemented
- [ ] "View Logs" button appears on success/failed/cancelled execution rows
- [ ] Clicking "View Logs" shows inline log content with line numbers
- [ ] Empty/null logs show "No logs available" message
- [ ] Copy-to-clipboard works on log content
- [ ] Loading state shown while fetching
- [ ] Error state shown on fetch failure
- [ ] Only one log viewer expanded at a time
- [ ] `CodeBlock` accepts `language="text"`
- [ ] All unit tests pass (80%+ coverage on new code)
- [ ] E2E happy path passes in Playwright
- [ ] CI green (lint, typecheck, tests, build)
- [ ] No backend changes required
- [ ] PR linked to this spec
