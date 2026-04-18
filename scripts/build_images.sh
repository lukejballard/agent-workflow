#!/usr/bin/env bash
# scripts/build_images.sh — Build Docker images for pipeline-observe
#
# Usage:
#   bash scripts/build_images.sh                     # build both images
#   bash scripts/build_images.sh --tag 1.2.3         # tag with a version
#   bash scripts/build_images.sh --push              # push after building
#   bash scripts/build_images.sh --tag 1.2.3 --push  # tag and push

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

# ── Parse arguments ──────────────────────────────────────────────────────────
TAG="latest"
PUSH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      TAG="$2"
      shift 2
      ;;
    --push)
      PUSH=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: bash scripts/build_images.sh [--tag <version>] [--push]"
      exit 1
      ;;
  esac
done

BACKEND_IMAGE="pipeline-observe-backend:${TAG}"
FRONTEND_IMAGE="pipeline-observe-frontend:${TAG}"

# ── Build ────────────────────────────────────────────────────────────────────
echo ">>> Building backend image: ${BACKEND_IMAGE}"
docker build -f Dockerfile.backend -t "${BACKEND_IMAGE}" .

echo ">>> Building frontend image: ${FRONTEND_IMAGE}"
docker build -f Dockerfile.frontend -t "${FRONTEND_IMAGE}" .

echo ""
echo ">>> Build complete:"
echo "    ${BACKEND_IMAGE}"
echo "    ${FRONTEND_IMAGE}"

# ── Push (optional) ──────────────────────────────────────────────────────────
if [ "${PUSH}" = true ]; then
  echo ""
  echo ">>> Pushing ${BACKEND_IMAGE} ..."
  docker push "${BACKEND_IMAGE}"

  echo ">>> Pushing ${FRONTEND_IMAGE} ..."
  docker push "${FRONTEND_IMAGE}"

  echo ">>> Push complete."
fi
