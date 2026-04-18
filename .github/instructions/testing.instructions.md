---
applyTo: "**/*.test.ts,**/*.test.tsx,**/*.test.py,**/tests/**,**/test_*.py,**/*_test.py"
---

# Testing standards

## What every test suite must cover
- Happy path (expected successful behaviour)
- All error paths and failure modes
- Edge cases: empty, null/undefined, zero, negative, max values, empty strings
- Auth boundary: unauthenticated → 401, unauthorised → 403
- Concurrent access where applicable

## Test naming
- Use descriptive names that read as sentences:
  `it("returns 404 when the requested user does not exist")`
  `test_returns_validation_error_when_email_is_missing`
- Never: `it("works")`, `test_1`, `it("test")`.

## Assertions
- One logical assertion per test where possible.
- Assert the outcome, not the implementation: test what the code does, not how.

## Mocking rules
- Mock only at the I/O boundary: database, HTTP, file system, time.
- Never mock the unit under test.
- Never mock things you don't own (third-party internals).
- Reset all mocks between tests: `beforeEach` / `autouse` fixtures.

## Python-specific
- pytest with fixtures only. No `unittest.TestCase`.
- `pytest.mark.parametrize` for input matrix tests.
- `pytest-asyncio` with `asyncio_mode = "auto"` for async tests.
- Factory fixtures using `factory_boy` over hardcoded test data.
- Database tests: wrap each test in a transaction rolled back at teardown.

## TypeScript-specific
- Vitest. Use `vi.mock()` at module level (not inside test body).
- `vi.useFakeTimers()` for time-dependent tests.
- `@testing-library/react` for component tests. Never test implementation details.
- `userEvent` over `fireEvent` for interaction simulation.

## Coverage
- Minimum 80% line + branch coverage on all new code.
- Coverage-padding tests (tests that execute code without meaningful assertions) are rejected by the reviewer.
- Do not chase 100% coverage at the expense of test quality.
