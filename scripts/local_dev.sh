#!/usr/bin/env bash
# scripts/local_dev.sh — Local development helper for pipeline-observe
# Usage: bash scripts/local_dev.sh [command]
#   start-collector   Start the FastAPI collector service (foreground)
#   run-example       Run the hello_pipeline example
#   test              Run the test suite with pytest
#   lint              Run black/ruff/isort checks
#   format            Auto-format with black and isort
#   install           Install the package in editable mode with dev extras

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

CMD="${1:-help}"

case "${CMD}" in
  start-collector)
    echo ">>> Starting collector on http://127.0.0.1:4318 ..."
    python -m pipeline_observe.collector.server
    ;;

  run-example)
    echo ">>> Running examples/hello_pipeline.py ..."
    python examples/hello_pipeline.py
    ;;

  test)
    echo ">>> Running tests ..."
    pytest tests/ -v
    ;;

  lint)
    echo ">>> Running black (check) ..."
    black --check src/ tests/ examples/

    echo ">>> Running ruff ..."
    ruff check src/ tests/ examples/

    echo ">>> Running isort (check) ..."
    isort --check-only src/ tests/ examples/
    ;;

  format)
    echo ">>> Formatting with black ..."
    black src/ tests/ examples/

    echo ">>> Sorting imports with isort ..."
    isort src/ tests/ examples/
    ;;

  install)
    echo ">>> Installing pipeline-observe[dev] in editable mode ..."
    pip install -e ".[dev]"
    echo ">>> Installing pre-commit hooks ..."
    pre-commit install
    ;;

  help|*)
    echo "Usage: bash scripts/local_dev.sh <command>"
    echo ""
    echo "Commands:"
    echo "  install         Install package + dev deps + pre-commit hooks"
    echo "  start-collector Start the FastAPI collector service (foreground)"
    echo "  run-example     Run examples/hello_pipeline.py"
    echo "  test            Run the test suite"
    echo "  lint            Check formatting and lint rules"
    echo "  format          Auto-format source files"
    ;;
esac
