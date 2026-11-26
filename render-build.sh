#!/usr/bin/env bash
set -e

echo "==> [1/3] Installing Python AI Service dependencies..."
pip install -r requirements.txt

echo "==> [2/3] Installing API Gateway dependencies & preheating MongoDB binary..."
cd backend/api-gateway
npm install
node -e "import('mongodb-memory-server').then(m => m.MongoMemoryServer.create().then(s => s.stop())).catch(e => console.warn('Preheat note:', e.message))"
cd ../..

echo "==> [3/3] Building React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "==> Build complete and verified!"
