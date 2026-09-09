#!/bin/bash
# update.sh — Pull latest code and redeploy
set -euo pipefail

cd "$(dirname "$0")"

echo ">>> Pulling latest code..."
git pull --ff-only

echo ">>> Building and starting containers..."
docker compose build --no-cache
docker compose up -d --force-recreate

echo ">>> Waiting for healthchecks..."
sleep 5

echo ">>> Verifying..."
docker compose ps
docker compose logs --tail=20

echo ">>> Update complete."
