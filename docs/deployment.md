# Deployment Status

## Current State

There is no verified deployable application runtime in this repository snapshot. The
backend and frontend trees referenced by inherited documentation are not present, so this
page intentionally avoids claiming a runnable deployment contract.

## What This Means

At the moment, the repository should not be treated as a source of truth for:
- container images
- service ports
- environment variables for production runtime
- managed infrastructure topology
- operational runbooks for a live system

## What A Future Deployment Guide Must Be Based On

A credible deployment guide should only be written after these surfaces are restored and
verified in-repo:
1. backend service entrypoints
2. frontend build and hosting model
3. persistent storage and migrations
4. authentication and secret-management model
5. observability and on-call expectations

## In The Meantime

Use `docs/product-direction.md` and the active realignment spec to understand the product
intent, but do not derive environment or infrastructure decisions from inherited archived
material without first validating them against restored runtime code.
