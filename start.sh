#!/usr/bin/env bash
set -e

PORT="${PORT:-10000}"
export PORT
export HOST="0.0.0.0"
export NODE_ENV="${NODE_ENV:-production}"
export AI_SERVICE_TOKEN="${AI_SERVICE_TOKEN:-labclarity_production_internal_token_32chars_secure}"
export AI_SERVICE_URL="${AI_SERVICE_URL:-http://127.0.0.1:8000}"
export CORS_ORIGINS="${CORS_ORIGINS:-*}"
export ALLOW_MEMORY_DB="${ALLOW_MEMORY_DB:-1}"

# Ensure gateway dependencies exist
if [ ! -d "backend/api-gateway/node_modules" ]; then
  echo "Installing API Gateway dependencies..."
  (cd backend/api-gateway && npm install --omit=dev)
fi

# Ensure frontend build exists
if [ ! -d "frontend/dist" ]; then
  echo "Building frontend..."
  (cd frontend && npm install && npm run build)
fi

# Find Python executable
PYTHON_BIN="python3"
if [ -f "./venv/bin/python" ]; then
  PYTHON_BIN="./venv/bin/python"
elif [ -f "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif [ -f "backend/ai-service/.venv/bin/python" ]; then
  PYTHON_BIN="backend/ai-service/.venv/bin/python"
elif command -v python &>/dev/null; then
  PYTHON_BIN="python"
fi

# 1. Start Python AI Service on internal port 8000 in background
echo "Starting LabClarity AI Service on 127.0.0.1:8000 using $PYTHON_BIN..."
$PYTHON_BIN -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --app-dir backend/ai-service &
AI_PID=$!

cleanup() {
  echo "Shutting down LabClarity services..."
  kill -TERM "$AI_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

sleep 2

# 2. Start Gateway on $PORT (publicly accessible)
echo "Starting LabClarity Gateway on 0.0.0.0:$PORT..."
cd backend/api-gateway
if [ -n "$MONGODB_URI" ]; then
  node src/server.js
else
  echo "Notice: MONGODB_URI not provided. Running with in-memory database."
  node scripts/dev-memory-db.js
fi
