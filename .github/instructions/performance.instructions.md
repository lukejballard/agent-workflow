---
applyTo: "**/*.py,**/*.ts,**/*.tsx"
---

# Performance standards

## Python (backend)
- Follow the surrounding sync or async model. Do not force async into modules that currently use sync SQLAlchemy sessions.
- Batch database reads: never query inside a loop (N+1 anti-pattern).
- Use `asyncio.gather()` only in modules that are already async.
- Cache expensive computations only when profiling shows a real hot path.
- Move long-running work out of request handlers into the existing execution or worker flows when practical.
- Set timeouts on all outbound HTTP calls. Never allow unbounded waits.
- Paginate collection endpoints and stream large responses incrementally instead of loading everything into memory.
- For SSE or streaming routes, stop upstream work promptly on disconnect and avoid unbounded event buffers.
- Profile before optimising: use `py-spy` or `cProfile` to find real hot spots.

## TypeScript and frontend
- Keep expensive transforms and sorting out of render paths when they can live in hooks or helpers.
- Clean up subscriptions, timers, and realtime listeners in effects.
- Lazy-load heavy route-sized modules instead of pushing them into the initial bundle.
- Virtualise long lists or large tables instead of rendering unbounded DOM.
- Avoid speculative memoization. Add `React.memo`, `useMemo`, or `useCallback` only after profiling.
- For generated Vite apps, keep the initial route light and push admin, editor, or analytics-heavy screens behind route-level splitting.

## Browser performance
- Avoid layout thrashing: batch DOM reads before DOM writes when manipulating complex UI.
- Keep initial bundles lean; do not pull large editor, graph, or preview dependencies into routes that do not need them.
- Prefer existing virtualization and route-splitting patterns in the frontend before introducing new libraries.

## Web performance targets
- Core Web Vitals targets: LCP < 2.5s, CLS < 0.1, INP < 200ms.
- Bundle size: new pages must not increase the initial JS bundle by more than 20kB gzipped.
- API response time targets: p95 < 200ms for reads, p95 < 500ms for writes.
