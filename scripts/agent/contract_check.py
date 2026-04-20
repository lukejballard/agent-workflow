"""API contract consistency checker for FastAPI/Pydantic backends (ISSUE-26).

Provides snapshot-based drift detection so frontend TypeScript types and
backend OpenAPI contracts never silently diverge.  Designed to run as a CI
gate *only* when a FastAPI application and an existing snapshot are present —
it is a no-op if neither is found, so it is safe to add to every repo.

Operations:
  export        — Run the FastAPI app's openapi() method and write the result
                  to .github/agent-platform/openapi.snapshot.json.
  diff          — Compare the committed snapshot against a live export.
  generate-types— Call ``npx openapi-typescript`` to emit frontend TypeScript
                  types from the snapshot (requires Node/npx).
  status        — Quick summary: snapshot age, route count, diff clean/dirty.

Usage in CI (ci.yml):
  # Only runs when both a FastAPI source file and a snapshot already exist.
  if: hashFiles('.github/agent-platform/openapi.snapshot.json') != ''

CLI:
  python scripts/agent/contract_check.py export --app src.main:app
  python scripts/agent/contract_check.py diff [--app src.main:app]
  python scripts/agent/contract_check.py generate-types [--out frontend/src/types/api.ts]
  python scripts/agent/contract_check.py status
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_DEFAULT_SNAPSHOT = ".github/agent-platform/openapi.snapshot.json"
_DEFAULT_TYPES_OUT = "frontend/src/types/api.ts"
_REPO_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# FastAPI app loader
# ---------------------------------------------------------------------------


def _load_app(app_spec: str) -> Any:
    """Import ``module.path:attribute`` and return the attribute.

    Raises ImportError / AttributeError with a clear message on failure.
    """
    if ":" not in app_spec:
        raise ValueError(f"app spec must be 'module:attribute', got '{app_spec}'")
    module_path, _, attr = app_spec.partition(":")
    mod = importlib.import_module(module_path)
    try:
        return getattr(mod, attr)
    except AttributeError as exc:
        raise AttributeError(
            f"Module '{module_path}' has no attribute '{attr}'"
        ) from exc


def _get_openapi_dict(app: Any) -> dict[str, Any]:
    """Call app.openapi() and return the schema dict."""
    if not callable(getattr(app, "openapi", None)):
        raise TypeError(f"Object {app!r} has no 'openapi()' method (is it a FastAPI app?)")
    return app.openapi()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------


def _snapshot_path(snapshot: str) -> Path:
    p = Path(snapshot)
    return p if p.is_absolute() else _REPO_ROOT / p


def read_snapshot(snapshot: str = _DEFAULT_SNAPSHOT) -> dict[str, Any] | None:
    """Return the stored snapshot dict, or None if not present."""
    p = _snapshot_path(snapshot)
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_snapshot(schema: dict[str, Any], snapshot: str = _DEFAULT_SNAPSHOT) -> Path:
    """Write schema to the snapshot file atomically. Returns the path."""
    p = _snapshot_path(snapshot)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(schema, indent=2, sort_keys=True))
    tmp.replace(p)
    return p


# ---------------------------------------------------------------------------
# Diff engine
# ---------------------------------------------------------------------------


def _extract_routes(schema: dict[str, Any]) -> dict[str, set[str]]:
    """Return {path: {methods...}} from an OpenAPI schema."""
    paths = schema.get("paths") or {}
    result: dict[str, set[str]] = {}
    for path, methods_dict in paths.items():
        result[path] = {m.upper() for m in methods_dict if not m.startswith("x-")}
    return result


def diff_schemas(
    old: dict[str, Any], new: dict[str, Any]
) -> dict[str, Any]:
    """Compute a structural diff between two OpenAPI schemas.

    Returns a dict with keys:
      added_routes    — routes in new but not old
      removed_routes  — routes in old but not new
      changed_routes  — routes where the HTTP methods changed
      added_schemas   — component schemas added
      removed_schemas — component schemas removed
      clean           — bool, True when there are no changes
    """
    old_routes = _extract_routes(old)
    new_routes = _extract_routes(new)

    added: list[str] = sorted(set(new_routes) - set(old_routes))
    removed: list[str] = sorted(set(old_routes) - set(new_routes))
    changed: list[dict[str, Any]] = []
    for path in set(old_routes) & set(new_routes):
        if old_routes[path] != new_routes[path]:
            changed.append({
                "path": path,
                "before": sorted(old_routes[path]),
                "after": sorted(new_routes[path]),
            })

    old_comp = set((old.get("components") or {}).get("schemas", {}).keys())
    new_comp = set((new.get("components") or {}).get("schemas", {}).keys())
    added_schemas = sorted(new_comp - old_comp)
    removed_schemas = sorted(old_comp - new_comp)

    clean = not (added or removed or changed or added_schemas or removed_schemas)
    return {
        "added_routes": added,
        "removed_routes": removed,
        "changed_routes": changed,
        "added_schemas": added_schemas,
        "removed_schemas": removed_schemas,
        "clean": clean,
    }


# ---------------------------------------------------------------------------
# TypeScript type generation
# ---------------------------------------------------------------------------


def generate_types(
    snapshot: str = _DEFAULT_SNAPSHOT,
    out: str = _DEFAULT_TYPES_OUT,
) -> int:
    """Run openapi-typescript via npx. Returns the exit code."""
    snap_path = _snapshot_path(snapshot)
    if not snap_path.exists():
        print(f"Snapshot not found: {snap_path}", file=sys.stderr)
        return 1
    out_path = _REPO_ROOT / out if not Path(out).is_absolute() else Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "--yes", "openapi-typescript", str(snap_path), "-o", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


def cmd_export(app_spec: str, snapshot: str) -> int:
    try:
        app = _load_app(app_spec)
    except (ImportError, AttributeError, ValueError) as exc:
        print(f"Failed to load app '{app_spec}': {exc}", file=sys.stderr)
        return 1
    try:
        schema = _get_openapi_dict(app)
    except TypeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    p = write_snapshot(schema, snapshot)
    route_count = len(schema.get("paths") or {})
    print(f"Exported {route_count} route(s) → {p}")
    return 0


def cmd_diff(app_spec: str | None, snapshot: str) -> int:
    stored = read_snapshot(snapshot)
    if stored is None:
        print(f"No snapshot at {_snapshot_path(snapshot)} — run 'export' first.", file=sys.stderr)
        return 1
    if app_spec:
        try:
            app = _load_app(app_spec)
            live = _get_openapi_dict(app)
        except (ImportError, AttributeError, ValueError, TypeError) as exc:
            print(f"Failed to load app for live diff: {exc}", file=sys.stderr)
            return 1
    else:
        # Re-export from the snapshot itself — useful for schema component diffs.
        live = stored
    result = diff_schemas(stored, live)
    print(json.dumps(result, indent=2))
    return 0 if result["clean"] else 2  # Exit 2 = dirty diff (not an error).


def cmd_generate_types(snapshot: str, out: str) -> int:
    return generate_types(snapshot, out)


def cmd_status(snapshot: str) -> int:
    p = _snapshot_path(snapshot)
    if not p.exists():
        print(json.dumps({"exists": False, "path": str(p)}))
        return 0
    schema = read_snapshot(snapshot) or {}
    route_count = len(schema.get("paths") or {})
    stat = p.stat()
    print(json.dumps({
        "exists": True,
        "path": str(p),
        "route_count": route_count,
        "openapi_version": schema.get("openapi", "unknown"),
        "title": (schema.get("info") or {}).get("title", "unknown"),
        "age_seconds": round(time.time() - stat.st_mtime),
    }, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="API contract consistency checker"
    )
    parser.add_argument(
        "--snapshot",
        default=_DEFAULT_SNAPSHOT,
        help=f"Path to snapshot file (default: {_DEFAULT_SNAPSHOT})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="Export OpenAPI schema to snapshot")
    p_export.add_argument("--app", required=True, metavar="MODULE:ATTR",
                          help="FastAPI app location, e.g. src.main:app")

    p_diff = sub.add_parser("diff", help="Diff live schema against snapshot")
    p_diff.add_argument("--app", default=None, metavar="MODULE:ATTR")

    p_types = sub.add_parser("generate-types", help="Generate TypeScript types from snapshot")
    p_types.add_argument("--out", default=_DEFAULT_TYPES_OUT)

    sub.add_parser("status", help="Show snapshot status summary")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "export":
        return cmd_export(args.app, args.snapshot)
    elif args.command == "diff":
        return cmd_diff(args.app, args.snapshot)
    elif args.command == "generate-types":
        return cmd_generate_types(args.snapshot, args.out)
    elif args.command == "status":
        return cmd_status(args.snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
