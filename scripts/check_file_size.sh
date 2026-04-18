#!/usr/bin/env bash
# scripts/check_file_size.sh — pre-commit hook to block files larger than 5 MB.
# Called by .pre-commit-config.yaml with filenames as arguments.

set -euo pipefail

MAX_BYTES=$((5 * 1024 * 1024))  # 5 MB
EXIT_CODE=0

for file in "$@"; do
  if [ -f "${file}" ]; then
    size=$(wc -c < "${file}")
    if [ "${size}" -gt "${MAX_BYTES}" ]; then
      echo "ERROR: File exceeds 5 MB limit: ${file} (${size} bytes)" >&2
      EXIT_CODE=1
    fi
  fi
done

exit "${EXIT_CODE}"
