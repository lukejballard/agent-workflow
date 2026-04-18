# Telemetry / Observability Audit — Checklist

## 1. SDK safety

- [ ] Every call in `sdk/client.py` that emits an event is wrapped in `try/except Exception`.
- [ ] SDK failures are logged with `logger.warning(...)` — not `print()`, not silently swallowed.
- [ ] SDK is a no-op (no HTTP calls) when `BIOMECHANICS_AI_COLLECTOR_URL` is unset or empty.
- [ ] SDK does not import any `collector`-internal module.
- [ ] Plugin hooks (`on_step_start`, `on_step_end`, `on_step_error`) do not raise under any input.

## 2. Metric completeness

Run: `grep -r "Counter\|Gauge\|Histogram" src/biomechanics_ai/observability/metrics.py`

- [ ] The ingest request counter is incremented on every `/ingest` call.
- [ ] The ingest error counter is incremented on every ingest failure.
- [ ] The anomaly detection counter is incremented when an anomaly is flagged.
- [ ] The alert dispatch counter is incremented on each alert webhook dispatch.
- [ ] No metric is registered inside a request handler (must be module-level).
- [ ] All new routes added since the last audit have corresponding counter increments.

## 3. Span coverage

Run: `grep -r "start_span\|use_span" src/biomechanics_ai/`

- [ ] `/ingest` route starts a span named `collector.ingest`.
- [ ] Analysis functions that are called per-request start a child span.
- [ ] Spans include `run_id` and `pipeline_name` as attributes where available.
- [ ] Spans are ended in a `finally` block (no orphaned spans on exception).
- [ ] OTel exporter is only initialised when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

## 4. Log quality

- [ ] Every `except` block in `src/` logs at least: exception type, message, and one piece of business context (`run_id`, `step_name`, or equivalent).
- [ ] No bare `except: pass` in any observability-related code path.
- [ ] Log level matches severity: `DEBUG` for trace, `INFO` for lifecycle, `WARNING` for recoverable errors, `ERROR` for unrecoverable errors.
- [ ] No `print()` calls in `src/biomechanics_ai/`.

## 5. Env-var hygiene

- [ ] `.env.example` contains entries for: `OTEL_EXPORTER_OTLP_ENDPOINT`, `ANOMALY_THRESHOLD_STDDEV`, `ANOMALY_MIN_SAMPLES`.
- [ ] All three have safe, operational defaults (tracing off, reasonable thresholds).
- [ ] `docs/architecture.md` lists all observability env vars in the configuration table.

## 6. Test coverage

- [ ] At least one unit test exercises the SDK `try/except` path (simulate collector unavailability).
- [ ] At least one unit test verifies a Prometheus counter is incremented on `/ingest`.
- [ ] At least one unit test verifies that SDK emits nothing when `BIOMECHANICS_AI_COLLECTOR_URL` is unset.
- [ ] `pytest tests/unit/ --cov=src/biomechanics_ai/observability --cov-report=term-missing` shows ≥80% coverage.

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
