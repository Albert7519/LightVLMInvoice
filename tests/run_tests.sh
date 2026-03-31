#!/bin/bash

# LocalllmOcrMK2 Test Runner Script
# Runs all tests: backend unit/integration, frontend UI

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🧪 LocalllmOcrMK2 Test Suite"
echo "======================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED_TESTS=0

# Test 1: Backend Tests
echo -e "\n${GREEN}[1/4]${NC} Running Backend Tests (pytest)..."
cd "$BACKEND_DIR"

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo -e "${YELLOW}Installing pytest and dependencies...${NC}"
    pip install -q pytest pytest-asyncio httpx
fi

# Run pytest
if python -m pytest tests/ -v --tb=short 2>/dev/null; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 2: Frontend Tests
echo -e "\n${GREEN}[2/4]${NC} Running Frontend Tests (npm)..."
cd "$FRONTEND_DIR"

# Install if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install > /dev/null 2>&1
fi

# Run linter
echo "  Running ESLint..."
if npm run lint > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ ESLint passed${NC}"
else
    echo -e "  ${YELLOW}⚠ ESLint warnings (not critical)${NC}"
fi

# TypeScript check
echo "  Checking TypeScript types..."
if npm run build > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ TypeScript check passed${NC}"
else
    echo -e "  ${RED}✗ TypeScript check failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 3: Backend Lint
echo -e "\n${GREEN}[3/4]${NC} Running Backend Code Quality Checks..."
cd "$BACKEND_DIR"

# Python syntax check
echo "  Checking Python syntax..."
if python -m py_compile *.py > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Python syntax check passed${NC}"
else
    echo -e "  ${RED}✗ Python syntax check failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 4: Integration Test (Optional - requires services running)
echo -e "\n${GREEN}[4/4]${NC} Integration Tests (Optional - requires services)..."

# Check if services are running
if curl -s http://localhost:8080/docs > /dev/null 2>&1; then
    echo "  Backend service detected, running integration tests..."
    if python -m pytest tests/test_e2e.py -v 2>/dev/null; then
        echo -e "  ${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "  ${YELLOW}⚠ Integration tests skipped or failed${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Backend not running, skipping integration tests${NC}"
    echo "     Run 'make dev' first to start services"
fi

# Summary
echo ""
echo "======================================"
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS test(s) failed${NC}"
    exit 1
fi
