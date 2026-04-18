# AGENTS.md — tests/

This file provides agent guidance scoped to the **test suite** (`tests/`).

---

## Layout

```
tests/
  unit/          ← Fast, isolated tests — no external services required
  integration/   ← Tests requiring a running collector, database, or network
  __init__.py
```

---

## Naming conventions

- File: `test_<module_name>.py` (matching `src/pipeline_observe/<module>/`).
- Function: `test_<unit>_<condition>_<expected>` (e.g. `test_anomaly_detector_high_stddev_raises_alert`).
- Fixture: descriptive noun (`db_session`, `mock_client`, `sample_run`).

---

## Agent rules

1. **New module = new test file.** Every new `src/pipeline_observe/` module must have a corresponding `tests/unit/test_<module>.py`.
2. **Pure unit tests must not touch I/O.** If a test needs a database, use an in-memory SQLite URL via a fixture. If it needs HTTP, use `httpx.MockTransport`.
3. **Do not modify existing tests** to make your new code pass — fix the code instead.
4. **Mark integration tests.** Any test that requires a real service must be decorated with `@pytest.mark.integration`.
5. **Cover edge cases.** Use `@pytest.mark.parametrize` for boundary values (empty lists, None inputs, negative numbers).
6. **One assertion per test** where practical — use multiple focused tests rather than one large test.

---

## Fixtures

Fixtures are defined in the test file itself or in `conftest.py` at the relevant level. Common patterns:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pipeline_observe.storage.models import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

---

## Running tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v -m integration

# With coverage
pytest tests/unit/ --cov=src/pipeline_observe --cov-report=term-missing

# Single test file
pytest tests/unit/test_anomaly_detection.py -v
```

---

## What makes a test reviewable

- The test file can be read and understood without opening the source file.
- The test name communicates the scenario being tested.
- The test fails for exactly one reason when the behaviour it verifies is broken.
- No `time.sleep()` calls — use deterministic data instead.
