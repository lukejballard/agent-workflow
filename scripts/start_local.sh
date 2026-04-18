#!/usr/bin/env bash
# scripts/start_local.sh — Start pipeline-observe locally using Docker Compose
#
# Usage:
#   bash scripts/start_local.sh            # start all services
#   bash scripts/start_local.sh --build    # rebuild images before starting
#   bash scripts/start_local.sh --stop     # stop all services
#   bash scripts/start_local.sh --logs     # tail logs for all services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

# Ensure .env exists
if [ ! -f .env ]; then
  echo ">>> .env not found – copying .env.example to .env"
  cp .env.example .env
  echo ">>> Please review and edit .env before re-running this script."
  exit 0
fi

CMD="${1:-}"

case "${CMD}" in
  --stop)
    echo ">>> Stopping all services ..."
    docker compose down
    ;;

  --logs)
    echo ">>> Tailing logs (Ctrl-C to exit) ..."
    docker compose logs -f
    ;;

  --build)
    echo ">>> Building images and starting services ..."
    docker compose up --build -d
    echo ""
    echo ">>> Services started:"
    echo "    Backend   : http://localhost:4318"
    echo "    Frontend  : http://localhost:3000"
    echo "    Prometheus: http://localhost:9090"
    ;;

  *)
    echo ">>> Starting services ..."
    docker compose up -d
    echo ""
    echo ">>> Services started:"
    echo "    Backend   : http://localhost:4318"
    echo "    Frontend  : http://localhost:3000"
    echo "    Prometheus: http://localhost:9090"
    ;;
esac
