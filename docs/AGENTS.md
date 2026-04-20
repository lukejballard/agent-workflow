# AGENTS.md — docs/

This file provides agent guidance scoped to `docs/`.

## Document inventory

| File | Update when... |
|---|---|
| `docs/product-direction.md` | The package boundary or repository framing changes |
| `docs/architecture.md` | The package surface or control-plane structure changes |
| `docs/quickstart.md` | Maintainer onboarding or package usage changes |
| `docs/runbooks/agent-mode.md` | The single-entry workflow or maintainer runbook changes |
| `docs/specs/` | Working specs, completions, or spec policy change |

## Agent rules

1. Do not invent package behavior that is not present in `.github/` or an active spec.
2. Keep docs aligned with the current package boundary, not with removed runtime layers.
3. Mark historical material clearly or delete it when it stops helping maintainers.
4. Prefer short, explicit prose over roadmap-style speculation.
5. Update linked docs in the same change set when one source-of-truth document changes.
