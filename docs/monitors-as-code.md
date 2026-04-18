# Operational Monitoring Notes

## Current State

This repository snapshot does not contain a verified running application surface, so it is
not honest to document concrete monitors, alerts, or service-level objectives as if they
already exist.

## What Should Happen Next

Monitoring guidance should be recreated only after the runtime application is restored and
these questions can be answered from real code and infrastructure:
- what services actually run
- what success and failure states matter most to users
- what metrics are emitted
- what alerts map to actionable operator response

## Interim Guidance

If monitoring requirements need to be planned before runtime restoration, capture them in
working specs as assumptions and proposed targets, not as already-implemented operational
contracts.
