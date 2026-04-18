# Skill: Python Code Quality

**Scope:** All Python files under `src/`, `tests/`, `examples/`, and `scripts/`.

**Purpose:** Ensure Python code meets the project's quality bar before merging.

---

## Checklist

### Formatting and linting
- [ ] `black src/ tests/ examples/ --check` passes (line length 88).
- [ ] `ruff check src/ tests/ examples/` passes with no errors.
- [ ] `isort src/ tests/ examples/ --check-only` passes (black profile).
- [ ] No `print()` statements in `src/` — use `logging` module.
- [ ] No `# noqa` or `# type: ignore` comments without an explanatory note.

### Type annotations
- [ ] Every public function has a return type annotation.
- [ ] Every function parameter has a type annotation.
- [ ] `Optional[X]` replaced with `X | None`.
- [ ] No bare `Any` unless documented with a comment explaining why.

### Docstrings
- [ ] Every public class, function, and method has a Google-style docstring.
- [ ] Docstring includes `Args:`, `Returns:`, and `Raises:` sections where applicable.
- [ ] One-line summary fits on one line (≤88 chars).

### Error handling
- [ ] No bare `except:` clauses — catch specific exception types.
- [ ] Observability code (SDK client, alert manager, plugin hooks) wraps calls in `try/except Exception`.
- [ ] Errors are logged with `logging.warning()` or `logging.error()` before being swallowed or re-raised.

### Security
- [ ] `bandit -r src/ -c pyproject.toml` passes with no HIGH or MEDIUM issues.
- [ ] No secrets, tokens, or credentials in source code.
- [ ] No hard-coded URLs to external services.

### Dependencies
- [ ] No new top-level imports of packages not listed in `pyproject.toml`.
- [ ] `pip-audit --skip-editable` reports no known vulnerabilities.

---

## How to run

```bash
# All-in-one (via pre-commit)
pre-commit run --all-files

# Individual tools
black src/ tests/ examples/
ruff check src/ tests/ examples/
isort src/ tests/ examples/
bandit -r src/ -c pyproject.toml
pip-audit --skip-editable
```

---

## Expected output

All checks pass with zero errors. Any suppressed warnings are documented inline with a justification comment.
