---
applyTo: "**/*.py"
---

# Python standards

## Default generated backend stack
- When the user and host repo do not establish a backend stack, default to Python + FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic.
- Prefer an application factory such as `create_app()` plus thin router modules, service modules, and storage modules.
- Prefer an ASGI-friendly layout that runs cleanly under `uvicorn`.

## Style
- PEP 8 enforced via ruff. black for formatting.
- Type hints required on all public functions and methods.
- Use `X | Y` union syntax (Python 3.10+). Never `Optional[X]`.
- Maximum function length: 40 lines. Extract if longer.

## Architecture
- Route modules parse requests, declare dependencies, enforce auth, and shape responses only.
- Service modules own business logic and multi-step orchestration.
- Storage modules own SQLAlchemy models, sessions, and query helpers.
- Keep API schemas in Pydantic models and persistence schemas in ORM models. Do not return raw ORM models directly from API boundaries.
- Prefer explicit config/settings modules validated at startup.

## Validation
- Use Pydantic v2 models for request, response, and event payloads.
- For generated API boundaries, prefer `ConfigDict(extra="forbid")` unless the host repo already uses a different validation policy.
- Validate external input at the route or boundary layer before it reaches storage or analysis.
- Match the neighboring model and validation style instead of inventing a new pattern in one file.

## Error handling
- Use `logging.getLogger(__name__)`, which is the current codebase pattern.
- Never swallow exceptions silently. If a failure is intentionally non-fatal, log why.
- Log with enough context to debug the failure without leaking secrets or PII.

## Async and I/O
- Follow the surrounding module's sync or async model. Do not mix sync SQLAlchemy sessions into async routes without a clean boundary.
- Use `async def` where the FastAPI route or dependency tree already relies on async libraries; keep sync stacks sync when the DB/session layer is sync.
- Avoid long-running work in request paths; prefer background tasks, workers, or explicit execution flows when practical.

## Testing
- pytest with fixtures. Never unittest.TestCase.
- Use `pytest.mark.parametrize` for input matrix tests.
- Mock at the network, process, or database-session boundary that the module actually uses.
- Use `pytest-asyncio` for async tests where the code under test is async.
- For generated FastAPI services, test the ASGI app through `TestClient` or `httpx.AsyncClient` rather than calling route functions directly.
- Cover request validation, auth boundaries, error responses, and serialization at the route layer.
- Minimum 80% line + branch coverage on new code.

## Observability
- Use the standard library logger or the host repo's established logging pattern.
- No `print()` statements in production code.
- Include relevant IDs and context in logs when available.
- Never log passwords, tokens, or PII.
