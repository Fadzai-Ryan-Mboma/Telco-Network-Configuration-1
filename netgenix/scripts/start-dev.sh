#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8510}"
FRONTEND_PORT="${FRONTEND_PORT:-8511}"

echo "Starting NetGenix backend on ${BACKEND_PORT}"
cd "${ROOT_DIR}"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACKEND_PID=$!

echo "Starting NetGenix frontend on ${FRONTEND_PORT}"
cd "${ROOT_DIR}/frontend"
VITE_API_URL="http://127.0.0.1:${BACKEND_PORT}" VITE_USE_LIVE_PARAMETERS="${VITE_USE_LIVE_PARAMETERS:-false}" npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}" &
FRONTEND_PID=$!

trap 'kill "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null || true' EXIT
wait
