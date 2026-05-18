#!/bin/bash

set -e

echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting FastAPI TEST backend..."
uvicorn backend.api:app --reload --port 8001
BACKEND_PID=$!

cleanup() {
  echo "Stopping backend..."
  kill $BACKEND_PID
}
trap cleanup EXIT
