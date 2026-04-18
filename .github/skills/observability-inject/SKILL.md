# Observability Injection Skill

## When to use
Use on any new service, API endpoint, background job, or significant code path
to ensure it produces enough signal to diagnose issues in production.

## What to add

### Structured logging

Every log entry must include:
- `timestamp` (automatic via the logger or platform)
- `level` (debug / info / warn / error)
- `service` or module context
- `trace_id` (from request context / OpenTelemetry span)
- `message` (human-readable summary of the event)
- Relevant domain context (user_id, resource_id, operation) — never raw PII

Python pattern (current codebase logging style):
```python
import logging

logger = logging.getLogger(__name__)

# In route handler or service
logger.info(
  "order.create.started trace_id=%s order_id=%s user_id=%s",
  request.state.trace_id,
  order_id,
  current_user.id,
)

# On success
logger.info("order.create.completed order_id=%s item_count=%s", order_id, len(items))

# On error
logger.exception("order.create.failed order_id=%s", order_id)
```

TypeScript pattern (frontend or tooling code):
```typescript
// Match the local module's diagnostics pattern.
// Avoid adding ad hoc production logging unless the surrounding code already logs.
```

### OpenTelemetry tracing

Python:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def create_order(data: OrderCreate) -> Order:
    with tracer.start_as_current_span("orders.create") as span:
        span.set_attribute("order.item_count", len(data.items))
        # ... implementation
```

TypeScript:
```typescript
import { trace } from "@opentelemetry/api";

const tracer = trace.getTracer("orders-service");

async function createOrder(data: CreateOrderInput) {
  return tracer.startActiveSpan("orders.create", async (span) => {
    span.setAttribute("order.itemCount", data.items.length);
    // ... implementation
    span.end();
  });
}
```

### Metrics (Prometheus / OpenTelemetry)

For every new API endpoint, add:
- Request counter (labelled by route, method, status code)
- Latency histogram (record p50, p95, p99)

For every background job, add:
- Job start / success / failure counters
- Job duration histogram

### Health check endpoint

Every new service must expose a health endpoint:
- Path: `/health` or `/healthz`
- Response: `{ "status": "ok", "version": "<git-sha>", "uptime": <seconds> }`
- HTTP 200 when healthy, HTTP 503 when degraded

## Output
- Updated source files with logging, tracing, and metrics added.
- List of what was added and at which lines.
- Confirmation that no PII is logged.
