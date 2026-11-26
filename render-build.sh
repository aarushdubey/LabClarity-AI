#!/usr/bin/env bash
set -e

echo "==> [1/3] Installing Python AI Service dependencies..."
pip install -r requirements.txt

echo "==> [2/3] Installing API Gateway dependencies..."
cd backend/api-gateway
npm install --omit=dev
cd ../..

echo "==> [3/3] Building React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "==> Build complete and verified!"
