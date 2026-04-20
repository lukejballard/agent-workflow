---
applyTo: "**/storage/**,**/migrations/**,**/*service*.py,**/db.py"
---

# Database standards

## Migrations
- Every schema change must update the owning models and include a migration when the repo uses migration files.
- Never alter the production schema manually.
- Migrations must be reversible when possible. Implement `downgrade()` or document why rollback is not safe.
- Never drop a column or table in the same migration that removes all code references to it.

## Naming conventions
- Match the existing table, column, and index naming already present in the owning storage module.
- Do not normalize unrelated tables or key types opportunistically during a feature change.

## Storage patterns
- Keep database access in `storage/` or in dedicated service helpers that already own that query path.
- Route files should not grow ad hoc SQL or session-management logic.
- Match the existing ORM and session patterns already used in the repo.
- Preserve compatibility across the database environments the repo explicitly supports.

## Query rules
- Parameterised queries always. Never string-concatenate user input into queries.
- Add indices for real query hotspots, especially columns used in filters or ordering.
- Avoid N+1 query patterns in storage helpers and service code.
- Use explicit transactions for multi-step writes or state transitions.
- Match the return-shape conventions already used in the surrounding storage or service module.
