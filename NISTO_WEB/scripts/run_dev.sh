#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.yml"

if ! command -v docker compose >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
  echo "Error: docker compose or docker-compose is required." >&2
  exit 1
fi

echo "Stopping existing containers..."
if command -v docker compose >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" down
else
  docker-compose -f "$COMPOSE_FILE" down
fi

echo "Removing old volumes and images..."
if command -v docker compose >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" rm -fsv || true
else
  docker-compose -f "$COMPOSE_FILE" rm -fsv || true
fi

echo "Starting services..."
if command -v docker compose >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" up --build
else
  docker-compose -f "$COMPOSE_FILE" up --build
fi
