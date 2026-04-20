# Agent Guide

This repository is the canonical source repo for a portable prompt/meta
supermind package.

## What this repo is
The shipped product is the root `.github/` tree: one orchestrator, one policy
kernel, one hook stack, and only the extension points that still contribute to
that package. `docs/` is the maintainer documentation layer for the source repo.

## Package boundary
- The consumer install surface is `.github/` only.
- `.github/AGENTS.md` is the primary package guide.
- `.github/copilot-instructions.md` is the global package contract.
- `docs/specs/active/` is the maintainer-only working spec area for changing
  the package source repo itself.

## How the agent system works
Single-entry workflow: all real work goes through `@orchestrator`.
The package should feel like one mind, not a bundle of specialist personas.

## Maintainer rules
- Read `.github/AGENTS.md` before changing package behavior.
- Treat `.github/agent-platform/workflow-manifest.json` as the canonical policy
  source.
- For non-trivial repo changes, keep a working spec in `docs/specs/active/`.
- Keep default generated application stack policy inside existing `.github/`
  surfaces and docs rather than reintroducing runtime-oriented root folders.
- Do not reintroduce runtime-product framing, specialist-agent ecosystems,
  prompt wrappers, or packaged skill bundles unless the package boundary is
  explicitly widened again.

## Active top-level surfaces
- `.github/` — canonical package source
- `docs/` — package architecture, runbooks, specs, and archive

Any other top-level surface that still exists during the collapse should be
treated as transitional and subject to removal.
