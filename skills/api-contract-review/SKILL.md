# Skill: API Contract Review

**Scope:** All collector REST API endpoints (`src/biomechanics_ai/collector/`) and their TypeScript counterparts (`frontend/src/api/`, `frontend/src/types/`).

**Purpose:** Ensure the API contract between the collector and the dashboard is consistent, stable, and well-documented.

---

## Checklist

### Endpoint inventory
For each endpoint in `collector/server.py`, verify:
- [ ] The endpoint is documented in `docs/architecture.md` (method, path, purpose).
- [ ] A corresponding TypeScript type exists in `frontend/src/types/`.
- [ ] A fetch helper exists in `frontend/src/api/`.
- [ ] The response shape matches between the Pydantic model (Python) and the TypeScript type.

### Request / response contracts
- [ ] All endpoints return a typed Pydantic model — no raw dicts or `dict` return annotations.
- [ ] All request bodies are validated with a Pydantic model.
- [ ] Error responses use `HTTPException` with appropriate 4xx/5xx codes and a descriptive `detail` string.
- [ ] Pagination is consistent: endpoints returning lists use the same cursor or offset pattern.

### Backwards compatibility
- [ ] No existing response fields are removed or renamed without a major version bump.
- [ ] New optional fields are added with a `None` default to avoid breaking existing clients.
- [ ] New required fields in request bodies are added with a deprecation notice if the client hasn't been updated yet.

### TypeScript type alignment
- [ ] Every field in the Pydantic response model has a matching optional or required field in the TypeScript interface.
- [ ] Field names match exactly (snake_case on Python side, camelCase or snake_case depending on serialisation settings).
- [ ] Enum values are consistent between Python `str` enum and TypeScript string literal unions.

### SDK contract
- [ ] The event payload posted by `sdk/client.py` matches the schema expected by `collector/server.py`'s `/ingest` endpoint.
- [ ] Any new event fields are optional with safe defaults (for forward compatibility).

### Testing
- [ ] Unit tests in `tests/unit/test_dashboard_api.py` cover every endpoint's happy path.
- [ ] Unit tests cover at least one 4xx error scenario for each endpoint.

---

## How to run

```bash
# Start the collector
uvicorn biomechanics_ai.collector.server:app --host 127.0.0.1 --port 4318

# View the auto-generated OpenAPI schema
curl http://127.0.0.1:4318/openapi.json | python -m json.tool

# Or browse the interactive docs
open http://127.0.0.1:4318/docs
```

Compare the OpenAPI output against `docs/architecture.md` and the TypeScript types in `frontend/src/types/`.

---

## Expected output

Every endpoint is documented, has a typed Pydantic response model, and has a matching TypeScript interface. No undocumented breaking changes. All endpoint unit tests pass.
