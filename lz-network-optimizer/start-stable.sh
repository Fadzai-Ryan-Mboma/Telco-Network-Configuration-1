#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_SRC="$PROJECT_DIR/frontend"
FRONTEND_RUN_DIR="/private/tmp/lz-network-optimizer-frontend"
BACKEND_PORT="${BACKEND_PORT:-8503}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

copy_frontend() {
  rm -rf "$FRONTEND_RUN_DIR"
  mkdir -p "$FRONTEND_RUN_DIR"

  cp "$FRONTEND_SRC"/package.json \
     "$FRONTEND_SRC"/package-lock.json \
     "$FRONTEND_SRC"/vite.config.ts \
     "$FRONTEND_SRC"/tsconfig.json \
     "$FRONTEND_SRC"/tsconfig.app.json \
     "$FRONTEND_SRC"/tsconfig.node.json \
     "$FRONTEND_SRC"/tailwind.config.js \
     "$FRONTEND_SRC"/postcss.config.js \
     "$FRONTEND_SRC"/index.html \
     "$FRONTEND_SRC"/eslint.config.js \
     "$FRONTEND_RUN_DIR"/

  cp -R "$FRONTEND_SRC"/src "$FRONTEND_RUN_DIR"/src
  cp -R "$FRONTEND_SRC"/public "$FRONTEND_RUN_DIR"/public
}

cleanup() {
  echo
  echo "Stopping lz-network-optimizer..."
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Preparing frontend in local temp storage..."
copy_frontend

echo "Installing frontend dependencies..."
(cd "$FRONTEND_RUN_DIR" && npm ci)

echo "Starting backend on http://127.0.0.1:$BACKEND_PORT..."
(cd "$PROJECT_DIR" && python3 -m uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload) &
BACKEND_PID=$!

echo "Starting frontend on http://127.0.0.1:$FRONTEND_PORT..."
(cd "$FRONTEND_RUN_DIR" && VITE_API_URL="http://127.0.0.1:$BACKEND_PORT" npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
FRONTEND_PID=$!

echo
echo "NetGenix is starting:"
echo "  Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "  Backend:  http://127.0.0.1:$BACKEND_PORT"
echo
echo "Press Ctrl+C to stop both services."

wait
