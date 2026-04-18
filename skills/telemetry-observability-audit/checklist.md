# Telemetry / Observability Audit — Checklist

## 1. SDK safety

- [ ] Every call in `sdk/client.py` that emits an event is wrapped in `try/except Exception`.
- [ ] SDK failures are logged with `logger.warning(...)` — not `print()`, not silently swallowed.
- [ ] SDK is a no-op (no HTTP calls) when its backend URL environment variable is unset or empty.
- [ ] SDK does not import any `collector`-internal module.
- [ ] Plugin hooks (`on_step_start`, `on_step_end`, `on_step_error`) do not raise under any input.

## 2. Metric completeness

Run: inspect the metrics module under `src/` if one exists.

- [ ] Request counters are incremented on every relevant API call.
- [ ] Error counters are incremented on every relevant failure path.
- [ ] Domain-specific counters are incremented when their corresponding signals occur.
- [ ] Alert or notification counters are incremented on each dispatch.
- [ ] No metric is registered inside a request handler (must be module-level).
- [ ] All new routes added since the last audit have corresponding counter increments.

## 3. Span coverage

Run: inspect span usage under `src/` if tracing is implemented.

- [ ] Each high-value route starts a span with a stable name.
- [ ] Analysis functions that are called per-request start a child span.
- [ ] Spans include relevant entity identifiers where available.
- [ ] Spans are ended in a `finally` block (no orphaned spans on exception).
- [ ] OTel exporter is only initialised when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

## 4. Log quality

- [ ] Every `except` block in `src/` logs at least: exception type, message, and one piece of business context (`run_id`, `step_name`, or equivalent).
- [ ] No bare `except: pass` in any observability-related code path.
- [ ] Log level matches severity: `DEBUG` for trace, `INFO` for lifecycle, `WARNING` for recoverable errors, `ERROR` for unrecoverable errors.
- [ ] No `print()` calls in `src/`.

## 5. Env-var hygiene

- [ ] `.env.example` contains entries for the observability variables required by checked-in code.
- [ ] Those variables have safe operational defaults where possible.
- [ ] `docs/architecture.md` documents observability variables only when the corresponding runtime exists.

## 6. Test coverage

- [ ] At least one unit test exercises the SDK `try/except` path (simulate collector unavailability).
- [ ] At least one unit test verifies a relevant counter is incremented on the main instrumented path.
- [ ] At least one unit test verifies that SDK emits nothing when its backend URL env var is unset.
- [ ] `pytest tests/unit/ --cov=src --cov-report=term-missing` shows ≥80% coverage for changed observability modules.

## Result

| Section | Status | Notes |
|---|---|---|
| SDK safety | | |
| Metric completeness | | |
| Span coverage | | |
| Log quality | | |
| Env-var hygiene | | |
| Test coverage | | |

**Overall:** ✅ Pass / ⚠️ Pass with caveats / ❌ Fail
