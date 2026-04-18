#!/usr/bin/env bash
# scripts/agent/verify-broad.sh
#
# Broad verification: runs all quality gates before opening a PR.
# Corresponds to the verification phase in the default orchestrator workflow.
#
# Requires: bash 4+
# Usage: bash scripts/agent/verify-broad.sh

set -euo pipefail

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
PYTHON_PROJECT_FILE="$PYTHON_REPO_ROOT/pyproject.toml"

echo "=== Backend: ruff ==="
"$PYTHON_BIN" -m ruff check "$PYTHON_SRC_PATH" "$PYTHON_TESTS_PATH"

echo "=== Backend: black (check only) ==="
"$PYTHON_BIN" -m black --check "$PYTHON_SRC_PATH" "$PYTHON_TESTS_PATH"

echo "=== Backend: isort (check only) ==="
"$PYTHON_BIN" -m isort "$PYTHON_SRC_PATH" "$PYTHON_TESTS_PATH" --check-only

echo "=== Backend: bandit ==="
"$PYTHON_BIN" -m bandit -r "$PYTHON_SRC_PATH" -c "$PYTHON_PROJECT_FILE" -ll

echo "=== Backend: unit tests ==="
"$PYTHON_BIN" -m pytest "$PYTHON_TESTS_PATH/unit/" -v --tb=short

echo "=== Backend: dependency audit ==="
"$PYTHON_BIN" -m pip_audit

echo "=== Agent platform metadata ==="
"$PYTHON_BIN" "$PYTHON_SYNC_SCRIPT" --check

echo "=== Frontend: lint ==="
(cd "$REPO_ROOT/frontend" && npm run lint)

echo "=== Frontend: build ==="
(cd "$REPO_ROOT/frontend" && npm run build)

echo "=== Frontend: tests ==="
(cd "$REPO_ROOT/frontend" && npm test -- --run)

echo ""
echo "✅ Broad verification passed. Safe to open a PR."
