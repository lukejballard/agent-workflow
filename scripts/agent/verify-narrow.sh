#!/usr/bin/env bash
# scripts/agent/verify-narrow.sh
#
# Narrow verification: runs only the fast unit-test and lint gates.
# Use this during the implement/repair loop for quick feedback.
# Run verify-broad.sh before opening a PR.
#
# Requires: bash 4+
# Usage: bash scripts/agent/verify-narrow.sh [--backend-only] [--frontend-only]

set -euo pipefail

BACKEND=true
FRONTEND=true

for arg in "$@"; do
  case "$arg" in
    --backend-only)  FRONTEND=false ;;
    --frontend-only) BACKEND=false ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $0 [--backend-only] [--frontend-only]" >&2
      exit 1
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/Scripts/python.exe"
elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python"
fi

to_python_path() {
  local path="$1"

  if [[ "$PYTHON_BIN" == *.exe ]]; then
    if command -v wslpath >/dev/null 2>&1; then
      wslpath -w "$path"
      return
    fi
    if command -v cygpath >/dev/null 2>&1; then
      cygpath -w "$path"
      return
    fi
  fi

  printf '%s\n' "$path"
}

PYTHON_REPO_ROOT="$(to_python_path "$REPO_ROOT")"
PYTHON_SRC_PATH="$PYTHON_REPO_ROOT/src"
PYTHON_TESTS_PATH="$PYTHON_REPO_ROOT/tests"
PYTHON_SYNC_SCRIPT="$PYTHON_REPO_ROOT/scripts/agent/sync_agent_platform.py"

if $BACKEND; then
  echo "=== Backend: ruff ==="
  "$PYTHON_BIN" -m ruff check "$PYTHON_SRC_PATH" "$PYTHON_TESTS_PATH"

  echo "=== Backend: black (check only) ==="
  "$PYTHON_BIN" -m black --check "$PYTHON_SRC_PATH" "$PYTHON_TESTS_PATH"

  echo "=== Backend: unit tests ==="
  "$PYTHON_BIN" -m pytest "$PYTHON_TESTS_PATH/unit/" -v --tb=short -q
fi

if $FRONTEND; then
  echo "=== Frontend: lint ==="
  (cd "$REPO_ROOT/frontend" && npm run lint)

  echo "=== Frontend: build ==="
  (cd "$REPO_ROOT/frontend" && npm run build)
fi

echo "=== Agent platform metadata ==="
"$PYTHON_BIN" "$PYTHON_SYNC_SCRIPT" --check

echo ""
echo "✅ Narrow verification passed."
