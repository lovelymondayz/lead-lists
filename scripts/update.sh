#!/bin/bash
# update.sh — Idempotent deploy script for lead-lists
# Works on any machine with Docker and git
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[$(date)] Deploying lead-lists..."

# Fetch latest code
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Already up to date."
    exit 0
fi

git pull origin main

# Rebuild and recreate (never use 'restart' — always force-recreate)
docker compose build --no-cache
docker compose up -d --force-recreate

# Health check
sleep 5
if docker compose ps | grep -q "Up"; then
    echo "[$(date)] ✅ lead-lists deploy successful"
else
    echo "[$(date)] ❌ lead-lists deploy failed — check logs"
    docker compose logs --tail=20
    exit 1
fi
