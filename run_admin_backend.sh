#!/bin/bash

set -e

if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

PORT="${ADMIN_BACKEND_PORT:-8010}"

python -m uvicorn admin_backend.app:app --host 127.0.0.1 --port "$PORT" --reload
