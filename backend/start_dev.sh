#!/bin/bash

# LocalllmOcrMK2 Development Startup Script
# Starts all services needed for local development:
# 1. Redis (message queue)
# 2. vLLM (GPU inference model server)
# 3. Celery Worker (async task processor)
# 4. FastAPI backend (main API server)
# 5. Frontend/React dev server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🚀 LocalllmOcrMK2 Development Startup"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Cleanup function for Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}Cleaning up processes...${NC}"
    for f in redis.pid vllm.pid celery.pid; do
        if [ -f "$BACKEND_DIR/$f" ]; then
            PID=$(cat "$BACKEND_DIR/$f")
            kill $PID 2>/dev/null || true
            rm "$BACKEND_DIR/$f"
        fi
    done
    redis-cli shutdown 2>/dev/null || true
    exit 0
}

trap cleanup EXIT

# Step 1: Check GPU
echo -e "\n${GREEN}[1/5]${NC} Checking GPU environment..."
cd "$BACKEND_DIR"
python check_gpu.py
GPU_CHECK=$?

case $GPU_CHECK in
    0) echo -e "${GREEN}✓ GPU ready${NC}" ;;
    1) echo -e "${YELLOW}⚠ GPU not available, falling back to CPU${NC}" ;;
    2) echo -e "${RED}✗ GPU check failed${NC}"; exit 1 ;;
esac

# Step 2: Create and activate virtual environment
echo -e "\n${GREEN}[2/5]${NC} Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created new virtual environment"
fi
source venv/bin/activate
pip install -q --upgrade pip setuptools wheel
echo -e "${GREEN}✓ Python environment ready${NC}"

# Step 3: Install dependencies
echo -e "\n${GREEN}[3/5]${NC} Installing backend dependencies..."
pip install -q -r requirements.lock
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Prepare directories
echo -e "\n${GREEN}[4/5]${NC} Preparing directories..."
mkdir -p "$BACKEND_DIR/uploads"
mkdir -p "$BACKEND_DIR/logs"
chmod 755 "$BACKEND_DIR/uploads"
echo -e "${GREEN}✓ Directories ready${NC}"

# Step 5: Start Redis
echo -e "\n${GREEN}[5/5]${NC} Starting services..."
echo "Starting Redis on port 6379..."
redis-server --port 6379 --daemonize yes --pidfile "$BACKEND_DIR/redis.pid"
sleep 2
if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Redis started${NC}"
else
    echo -e "  ${RED}✗ Redis failed to start${NC}"
    exit 1
fi

# Step 6: Start vLLM (if GPU available)
if [ $GPU_CHECK -eq 0 ]; then
    echo "Starting vLLM model server on port 8000..."
    cd "$BACKEND_DIR"
    timeout 90 python -m vllm.entrypoints.openai.api_server \
        --model "cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8" \
        --host 0.0.0.0 \
        --port 8000 \
        --gpu-memory-utilization 0.9 \
        --max-model-len 32768 \
        > logs/vllm.log 2>&1 &
    VLLM_PID=$!
    echo $VLLM_PID > "$BACKEND_DIR/vllm.pid"
    
    # Wait for vLLM to be ready
    echo "  Waiting for vLLM to initialize..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ vLLM ready${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "  ${RED}✗ vLLM failed to start (timeout)${NC}"
            echo "  Check logs: tail -f $BACKEND_DIR/logs/vllm.log"
            exit 1
        fi
    done
else
    echo -e "  ${YELLOW}Skipping vLLM (no GPU available)${NC}"
fi

# Step 7: Start Celery Worker
echo "Starting Celery worker..."
cd "$BACKEND_DIR"
python -m celery -A celery_app worker --loglevel=info --pool=solo \
    > logs/celery.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > "$BACKEND_DIR/celery.pid"
sleep 2
echo -e "  ${GREEN}✓ Celery worker started (PID: $CELERY_PID)${NC}"

# Step 8: Start FastAPI
echo "Starting FastAPI backend on port 8080..."
cd "$BACKEND_DIR"
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload &
FASTAPI_PID=$!

# Wait for FastAPI to be ready
echo "  Waiting for FastAPI to start..."
for i in {1..10}; do
    if curl -s http://localhost:8080/docs > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ FastAPI ready (http://localhost:8080/docs)${NC}"
        break
    fi
    sleep 1
done

# Step 9: Start Frontend (optional)
echo "Starting Frontend dev server on port 5173..."
cd "$FRONTEND_DIR"
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
sleep 3
echo -e "  ${GREEN}✓ Frontend running (http://localhost:5173)${NC}"

# All services running
echo ""
echo "======================================"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo ""
echo "Service URLs:"
echo "  Backend API:    http://localhost:8080"
echo "  API Docs:       http://localhost:8080/docs"
echo "  Frontend:       http://localhost:5173"
if [ $GPU_CHECK -eq 0 ]; then
    echo "  vLLM API:       http://localhost:8000/v1/models"
fi
echo "  Redis:          localhost:6379"
echo ""
echo "View logs:"
echo "  FastAPI:  tail -f $BACKEND_DIR/logs/fastapi.log"
if [ -f "$BACKEND_DIR/logs/vllm.log" ]; then
    echo "  vLLM:     tail -f $BACKEND_DIR/logs/vllm.log"
fi
echo "  Celery:   tail -f $BACKEND_DIR/logs/celery.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================"

# Wait for FastAPI process (keep script running)
wait $FASTAPI_PID
