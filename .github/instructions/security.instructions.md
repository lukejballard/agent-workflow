---
applyTo: "**/*.py,**/*.ts,**/*.tsx"
---

# Security baseline

## Input validation
- Validate all inputs at the system boundary (API route layer).
- Python: Pydantic v2 models, `extra="forbid"`.
- TypeScript: Zod schemas, `.strict()`.
- Reject unexpected fields. Never pass raw request body to services or DB.

## Stack-specific defaults
- FastAPI: declare request and response models, keep auth and DB session wiring in dependencies, and avoid returning raw ORM models from handlers.
- FastAPI: configure CORS narrowly for the actual frontend origin set. Never use wildcard origins for authenticated browser traffic.
- React/Vite: browser-exposed configuration must come from `import.meta.env` and only `VITE_` variables may cross the browser boundary.

## Output / rendering
- Sanitize all user-generated content before rendering.
- React: rely on JSX escaping. Never use `dangerouslySetInnerHTML` with user data.
- Never render raw HTML from an API response without explicit sanitization (DOMPurify).

## Authentication and authorisation
- Check authentication before any data access. Return `401` if missing/invalid.
- Check authorisation explicitly: does THIS user own THIS resource? Return `403` if not.
- Never trust client-supplied user IDs for authorisation decisions.
- JWT: validate signature, expiry, issuer, and audience on every request.

## Secrets management
- Never hardcode secrets, tokens, API keys, or passwords in source code.
- Never commit `.env` files containing real values.
- Use environment variables. Validate required env vars at application startup.
- Never log secrets, tokens, or PII. Mask or omit sensitive fields in logs.

## Database
- Parameterised queries always.
- Never concatenate user input into SQL, Cypher, MongoDB queries, or any DSL.
- Use least-privilege DB credentials: read-only users for read-only operations.

## Dependencies
- Run `pip-audit` (Python) and `npm audit` (Node) in CI.
- Do not ignore audit findings without documented justification.
- Pin all production dependencies to exact versions.
