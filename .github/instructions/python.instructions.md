---
applyTo: "**/*.py"
---

# Python standards

## Style
- PEP 8 enforced via ruff. black for formatting.
- Type hints required on all public functions and methods.
- Use `X | Y` union syntax (Python 3.10+). Never `Optional[X]`.
- Maximum function length: 40 lines. Extract if longer.

## Architecture
- `collector/` and `*_routes.py`: request parsing, auth checks, response shaping, and orchestration only.
- `storage/`: SQLAlchemy models, session factories, and database query helpers.
- `analysis/`: pure, testable transforms with no database or HTTP I/O.
- `sdk/`: never let observability failures break user pipeline execution.
- `alerts/`, `execution/`, `workers/`, and `plugins/`: isolate side effects and log context clearly.

## Validation
- Use Pydantic models for request, response, and event payloads.
- Validate external input at the route or boundary layer before it reaches storage or analysis.
- Match the neighboring model and validation style instead of inventing a new pattern in one file.

## Error handling
- Use `logging.getLogger(__name__)`, which is the current codebase pattern.
- Never swallow exceptions silently. If a failure is intentionally non-fatal, log why.
- Log with enough context to debug the failure without leaking secrets or PII.

## Async and I/O
- Follow the surrounding module's sync or async model. Do not force async into sync SQLAlchemy flows.
- Use `async def` where the surrounding FastAPI route or dependency already relies on async libraries.
- Avoid long-running work in request paths; prefer the existing execution and worker mechanisms when practical.

## Testing
- pytest with fixtures. Never unittest.TestCase.
- Use `pytest.mark.parametrize` for input matrix tests.
- Mock at the network, process, or database-session boundary that the module actually uses.
- Use `pytest-asyncio` for async tests where the code under test is async.
- Minimum 80% line + branch coverage on new code.

## Observability
- Use the standard library logger patterns already present in `src/biomechanics_ai/`.
- No `print()` statements in production code.
- Include relevant IDs and context in logs when available.
- Never log passwords, tokens, or PII.
