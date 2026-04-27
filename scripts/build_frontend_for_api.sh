#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend-service"
API_STATIC_DIR="$ROOT_DIR/api-service/app/static"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "frontend-service directory was not found." >&2
  exit 1
fi

if [[ ! -d "$ROOT_DIR/api-service" ]]; then
  echo "api-service directory was not found." >&2
  exit 1
fi

(
  cd "$FRONTEND_DIR"
  VITE_API_BASE_URL= npm run build
)

rm -rf "$API_STATIC_DIR"
mkdir -p "$API_STATIC_DIR"
cp -R "$FRONTEND_DIR/dist/." "$API_STATIC_DIR/"

echo "Frontend build copied to $API_STATIC_DIR"
