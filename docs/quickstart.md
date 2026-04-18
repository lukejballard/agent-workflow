# Quickstart

## What You Can Do In This Snapshot

This repository snapshot is best treated as a documentation, planning, and
agent-workflow workspace for a generic application scaffold.

A practical contributor quickstart is:
1. Read `README.md`.
2. Read `docs/product-direction.md`.
3. Read `docs/specs/active/product-realignment-phase-1.md`.
4. Review `AGENTS.md` and `.github/copilot-instructions.md` before making changes.
5. Treat inherited specs under `specs/` and `openspec/` as historical inputs, not active runtime truth.

## What You Cannot Reliably Do Here Yet

This snapshot does not contain a verified backend or frontend runtime, so you
cannot currently rely on it for:
- starting the application
- running the product UI
- exercising a public API
- validating deployment behavior end to end

## Working Safely

When updating docs or plans:
- prefer verified statements over reconstructed product claims
- keep historical material clearly marked as archival
- avoid creating new runtime contracts until real code exists to support them

## Next Restoration Milestones

The next meaningful repo restoration steps are:
1. define the concrete application domain this scaffold should support
2. restore or add backend and frontend runtime code only after that scope is chosen
3. align tests, deployment assets, and docs to those restored surfaces
