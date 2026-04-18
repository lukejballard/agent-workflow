#!/usr/bin/env bash
set -euo pipefail

echo "Generating Python models (datamodel-code-generator)..."
if command -v datamodel-codegen >/dev/null 2>&1; then
  mkdir -p generated/python
  datamodel-codegen --input-file-type jsonschema \
    --input specs/ingest-event.schema.json \
    --output generated/python/ingest_event_model.py
else
  echo "datamodel-codegen not installed; skipping Python model generation"
fi

echo "(Optional) Generating TypeScript types from OpenAPI..."
if command -v openapi-generator-cli >/dev/null 2>&1; then
  mkdir -p generated/typescript
  openapi-generator-cli generate \
    -i specs/collector.openapi.yaml \
    -g typescript-fetch \
    -o generated/typescript
elif command -v openapi-generator >/dev/null 2>&1; then
  mkdir -p generated/typescript
  openapi-generator generate \
    -i specs/collector.openapi.yaml \
    -g typescript-fetch \
    -o generated/typescript
else
  echo "openapi-generator-cli not installed; skipping TypeScript generation"
fi
