# Skill: Testing Regression

**Scope:** `tests/unit/` and `tests/integration/`.

**Purpose:** Catch regressions before they reach `main`. Run after any code change.

---

## Checklist

### Pre-run checks
- [ ] All test files follow the naming convention `test_<module>.py`.
- [ ] No tests import from each other (test isolation).
- [ ] No `time.sleep()` calls in unit tests.
- [ ] No real HTTP calls or filesystem writes in unit tests.

### Run the test suite
- [ ] `pytest tests/unit/ -v` — all unit tests pass.
- [ ] `pytest tests/integration/ -v -m integration` — all integration tests pass (requires running services).
- [ ] No `XPASS` (unexpectedly passing) tests — investigate if one appears.

### Coverage
- [ ] `pytest tests/unit/ --cov=src --cov-report=term-missing` shows ≥80% line coverage for any changed module.
- [ ] Coverage has not decreased compared to the base branch.

### Regression signals
After any change, verify the most relevant tests for the changed area are still
green. Keep the regression focus tied to the modules that actually exist in the
repository.

### New tests
- [ ] Every new module has a corresponding test file.
- [ ] Every new public function has at least one unit test.
- [ ] Parametrized tests cover empty input, single item, and multiple items.

---

## How to run

```bash
# Unit tests (fast, no services required)
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Integration tests (requires docker compose up -d)
pytest tests/integration/ -v -m integration

# Full suite
pytest tests/ -v
```

---

## Expected output

All tests pass. Coverage report shows no regression from the base branch. Zero new failures in the regression signal list.
