#!/bin/bash

set -e

if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

ADMIN_BACKEND_PORT="${ADMIN_BACKEND_PORT:-8010}"

python -m uvicorn admin_backend.app:app --host 127.0.0.1 --port "$ADMIN_BACKEND_PORT" --reload &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID"
}
trap cleanup EXIT

cd admin
npm run dev
