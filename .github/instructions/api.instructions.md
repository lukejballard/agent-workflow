---
applyTo: "**/*route*.py,**/*api*.py,**/*api*.ts,**/*api*.tsx"
---

# API client and route standards

## Default generated API stack
- When the framework choice is open, default to FastAPI route modules backed by Pydantic request and response models.
- Prefer one `APIRouter` per resource family plus an app factory that wires routers, middleware, settings, and dependencies.
- Use typed frontend client helpers that mirror backend request and response models.

## Route design
- Match the existing route families and prefixes in neighboring files.
- Do not introduce `/v1/` versioning or a brand-new top-level route style unless the spec requires it.
- For FastAPI, prefer explicit `prefix`, `tags`, `status_code`, and `response_model` declarations instead of implicit defaults.
- Keep route modules thin: validate input, call service/storage helpers, and shape responses.
- Reuse or add local request/response models when small instead of scattering ad hoc dict shapes.
- Preserve special response modes where required, including `text/plain` and `text/event-stream`. For SSE, use framework-native streaming primitives and typed event payloads.

## HTTP status codes
- `200` — success with body
- `201` — resource created (include `Location` header)
- `204` — success with no body (DELETE, some updates)
- `400` — validation error (include field-level errors in body)
- `401` — not authenticated
- `403` — authenticated but not authorised
- `404` — resource not found
- `409` — conflict (duplicate, stale update)
- `422` — unprocessable entity (business rule violation, not a validation error)
- `429` — rate limited (include `Retry-After` header)
- `500` — internal server error (never expose stack traces)

## Endpoint behavior
- Use nouns for resources and match the naming style already used in nearby route modules.
- For list endpoints, filtering and pagination should match the neighboring route family instead of inventing a new shape.
- New or changed endpoints must be reflected in the local architecture or API docs when that repo maintains them.
- Never expose stack traces or raw internal exceptions in API responses.
- Keep auth, DB session, and settings wiring in route dependencies or middleware, not ad hoc globals inside handlers.

## Auth
- Follow the existing auth and middleware patterns for authenticated endpoints.
- Return `401` when authentication is missing or invalid and `403` when it is valid but insufficient.

## Frontend API clients
- Keep low-level transport in a shared client/helper module instead of duplicating request setup in components.
- Add one typed function per endpoint or resource group in the local API layer.
- Mirror response types in shared type modules when the repo separates transport and UI layers.
- Components and pages should call these helpers through hooks, context, or page-level services rather than `fetch()` directly.
- For generated React/Vite frontends, prefer a shared `http` helper plus resource-group modules and page-level hooks or services.

## Rate limiting
- Apply rate limits at the API gateway or middleware layer.
- Return `429` with `Retry-After: <seconds>` header.
- Include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.
