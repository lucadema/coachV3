#!/bin/bash

set -e

echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting FastAPI backend..."
python -m uvicorn backend.api:app --reload &
BACKEND_PID=$!

cleanup() {
  echo "Stopping backend..."
  kill $BACKEND_PID
}
trap cleanup EXIT

echo "Starting Streamlit frontend..."
streamlit run frontend/app.py
