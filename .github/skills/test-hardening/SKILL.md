# Test Hardening Skill

## When to use
Use when you want to increase confidence in existing tests, eliminate flakiness,
or add missing coverage to a module that already has some tests.

Auto-consider this skill for:
- brownfield work
- API or auth changes
- incident or bugfix work
- changes where a regression is more likely than a brand-new path failure

## Step 1 — Run tests and audit coverage
- Run the test suite for the target module.
- Generate a coverage report.
- Identify: untested branches, untested error paths, untested edge cases.

## Step 2 — Audit for flakiness sources
Check for and fix:
- `time.sleep()` / `await sleep()` → replace with fake timers or retry logic
- Hardcoded dates or timestamps → inject via fixture or mock
- Network calls in unit tests → mock at the I/O boundary
- Shared mutable state between tests → reset in `beforeEach` / `autouse` fixture
- Non-deterministic ordering → sort results before asserting
- Tests that depend on other tests running first → make each test fully independent

## Step 3 — Add missing edge case tests
For every public function, verify coverage exists for:
- Empty input (empty string, empty list, empty dict)
- Null / None / undefined input
- Zero and negative numbers
- Maximum allowed values
- Inputs with special characters (for string inputs)
- Concurrent invocations (if the function has shared state)

## Step 4 — Add missing failure path tests
- What happens when the database call throws?
- What happens when the external HTTP call times out or returns 500?
- What happens when a required environment variable is missing at startup?
- What happens when the input passes validation but violates a business rule?

## Step 4b — Add missing regression-path tests
- Which previously working path is most likely to break because of this change?
- Which neighboring module or route depends on the changed behavior implicitly?
- Add at least one test that proves the old expected behavior still holds.

## Step 5 — Add auth boundary tests
- Unauthenticated request to protected endpoint → 401
- Authenticated request without required permission → 403
- Valid token for a different user's resource → 403

## Step 6 — Python-specific patterns
- Use `pytest.mark.parametrize` for input matrices
- Use `factory_boy` factories instead of hardcoded test data
- Use `respx` or `httpretty` for mocking outbound HTTP

## Step 7 — TypeScript-specific patterns
- Use `it.each` for parametrized test cases
- Use `vi.setSystemTime()` for date-dependent tests
- Use `msw` (Mock Service Worker) for mocking API calls in React tests

## Output
- New or updated test files
- Coverage delta: before vs after
- List of flaky tests fixed
- List of regression paths covered
- List of coverage gaps that remain (with explanation if not addressable)
