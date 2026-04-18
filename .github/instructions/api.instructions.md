---
applyTo: "src/biomechanics_ai/collector/**,src/biomechanics_ai/models/**,frontend/src/api/**"
---

# Collector and API client standards

## Collector route design
- Match the existing collector route families and prefixes in neighboring files.
- Do not introduce `/v1/` versioning or a brand-new top-level route style unless the spec requires it.
- Keep route modules thin: validate input, call service/storage helpers, and shape responses.
- Reuse or add Pydantic models in `src/biomechanics_ai/models/` or the local route module when small.
- Preserve special response modes where required, including `text/plain` and `text/event-stream`.

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
- Use nouns for resources and match the naming style already used in nearby collector routes.
- For list endpoints, filtering and pagination should match the neighboring route family instead of inventing a new shape.
- New or changed endpoints must be reflected in `docs/architecture.md`.
- Never expose stack traces or raw internal exceptions in API responses.

## Auth
- Follow the existing collector auth and middleware patterns for authenticated endpoints.
- Return `401` when authentication is missing or invalid and `403` when it is valid but insufficient.

## Frontend API clients
- Keep low-level transport in `frontend/src/api/http.ts` or a neighboring shared helper.
- Add one typed function per endpoint or resource group under `frontend/src/api/`.
- Mirror response types in `frontend/src/types/`.
- Components and pages should call these helpers through hooks, context, or page-level services rather than `fetch()` directly.

## Rate limiting
- Apply rate limits at the API gateway or middleware layer.
- Return `429` with `Retry-After: <seconds>` header.
- Include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.
