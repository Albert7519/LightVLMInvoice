#!/bin/bash

# Docker startup verification script for LocalllmOcrMK2
# - Builds images
# - Starts services
# - Waits for healthchecks
# - Verifies endpoints

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

wait_for_health() {
  local service="$1"
  local timeout="$2"
  local start
  start=$(date +%s)

  echo "Waiting for $service to be healthy..."
  while true; do
    container_id=$(docker-compose ps -q "$service")
    if [[ -z "$container_id" ]]; then
      echo -e "  ${RED}✗ $service container not found${NC}"
      return 1
    fi
    status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "unknown")
    if [[ "$status" == "healthy" ]]; then
      echo -e "  ${GREEN}✓ $service healthy${NC}"
      return 0
    fi
    if [[ "$status" == "unhealthy" ]]; then
      echo -e "  ${RED}✗ $service unhealthy${NC}"
      return 1
    fi
    now=$(date +%s)
    if (( now - start > timeout )); then
      echo -e "  ${RED}✗ $service healthcheck timeout${NC}"
      return 1
    fi
    sleep 3
  done
}

echo -e "${GREEN}Step 1: Build images${NC}"
docker-compose build

echo -e "${GREEN}Step 2: Start services${NC}"
docker-compose up -d --force-recreate

echo -e "${GREEN}Step 3: Wait for healthchecks${NC}"
wait_for_health redis 60
wait_for_health vllm 900
wait_for_health backend 120
wait_for_health frontend 120

echo -e "${GREEN}Step 4: Verify endpoints${NC}"

if curl -fsS http://localhost:8080/docs > /dev/null; then
  echo -e "  ${GREEN}✓ Backend API docs reachable${NC}"
else
  echo -e "  ${RED}✗ Backend API docs unreachable${NC}"
  exit 1
fi

if curl -fsS http://localhost:8000/v1/models > /dev/null; then
  echo -e "  ${GREEN}✓ vLLM models endpoint reachable${NC}"
else
  echo -e "  ${RED}✗ vLLM models endpoint unreachable${NC}"
  exit 1
fi

if curl -fsS http://localhost/ > /dev/null; then
  echo -e "  ${GREEN}✓ Frontend reachable${NC}"
else
  echo -e "  ${RED}✗ Frontend unreachable${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Docker verification completed successfully${NC}"
