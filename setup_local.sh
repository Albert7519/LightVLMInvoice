#!/bin/bash

# LocalllmOcrMK2 - Local Development Setup Script
# 自动安装所有系统依赖和 Python/Node 依赖
#
# 使用：bash setup_local.sh

set -e

echo ""
echo "════════════════════════════════════════════════════════"
echo "🔧 LocalllmOcrMK2 Local Development Setup"
echo "════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

STEP=1
TOTAL_STEPS=6

# Step 1: Check current user
echo -e "${YELLOW}[${STEP}/${TOTAL_STEPS}]${NC} Checking prerequisites..."
STEP=$((STEP+1))

if [ "$EUID" -eq 0 ]; then
   echo -e "${RED}✗ Please do not run this script as root${NC}"
   exit 1
fi

echo "Current user: $(whoami)"
echo "Python version: $(python3 --version)"
echo "Node version: $(node --version)"

# Step 2: Install system dependencies
echo ""
echo -e "${YELLOW}[${STEP}/${TOTAL_STEPS}]${NC} Installing system packages (pip, redis)..."
STEP=$((STEP+1))

# Update package list
echo "  Updating package list..."
sudo apt-get update -qq

# Install pip3
if ! command -v pip3 &> /dev/null; then
    echo "  Installing pip3..."
    sudo apt-get install -y -qq python3-pip
else
    echo "  ✓ pip3 already installed"
fi

# Install Redis
if ! command -v redis-server &> /dev/null; then
    echo "  Installing redis-server..."
    sudo apt-get install -y -qq redis-server
else
    echo "  ✓ redis-server already installed"
fi

# Verify installations
echo ""
echo "  Verifying installations..."
pip3 --version
redis-cli --version 2>/dev/null || echo "  Redis version: $(redis-server --version 2>&1 | head -1)"

# Step 3: Setup Python virtual environment
echo ""
echo -e "${YELLOW}[${STEP}/${TOTAL_STEPS}]${NC} Setting up Python environment..."
STEP=$((STEP+1))

cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

cd "$PROJECT_ROOT/backend"

# Check if venv is complete (has activate script)
if [ ! -f "venv/bin/activate" ]; then
    echo "  Creating virtual environment..."
    # Remove incomplete venv if it exists
    [ -d "venv" ] && rm -rf venv
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "  ${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
else
    echo "  ✓ Virtual environment exists"
fi

# Activate virtual environment
if [ ! -f "venv/bin/activate" ]; then
    echo -e "  ${RED}✗ Failed to create venv/bin/activate${NC}"
    exit 1
fi
source venv/bin/activate

# Upgrade pip
echo "  Upgrading pip..."
pip install -q --upgrade pip setuptools wheel

# Install Python dependencies
echo "  Installing Python dependencies..."
pip install -q -r requirements.txt

echo -e "  ${GREEN}✓ Python environment ready${NC}"

# Step 4: Generate requirements.lock
echo ""
echo -e "${YELLOW}[${STEP}/${TOTAL_STEPS}]${NC} Generating requirements.lock..."
STEP=$((STEP+1))

if [ ! -f "requirements.lock" ]; then
    echo "  Creating requirements.lock..."
    pip freeze > requirements.lock
    echo -e "  ${GREEN}✓ requirements.lock created${NC}"
else
    echo "  ✓ requirements.lock exists"
fi

# Step 5: Setup frontend
echo ""
echo -e "${YELLOW}[${STEP}/${TOTAL_STEPS}]${NC} Setting up Node.js environment..."
STEP=$((STEP+1))

cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install
    echo -e "  ${GREEN}✓ Node modules installed${NC}"
else
    echo "  ✓ Node modules exist"
fi

# Step 6: Initialize .env files
echo ""
echo -e "${YELLOW}[${STEP}/${TOTAL_STEPS}]${NC} Initializing configuration files..."
STEP=$((STEP+1))

cd "$PROJECT_ROOT"

if [ ! -f "backend/.env" ]; then
    echo "  Creating backend/.env..."
    cp backend/.env.example backend/.env
fi

if [ ! -f "frontend/.env" ]; then
    echo "  Creating frontend/.env..."
    cp frontend/.env.example frontend/.env
fi

echo -e "  ${GREEN}✓ Configuration files ready${NC}"

# Step 7: Optional - Start Redis
echo ""
echo -e "${YELLOW}[7/6]${NC} Starting Redis service..."

if ! redis-cli ping > /dev/null 2>&1; then
    echo "  Starting Redis..."
    sudo systemctl start redis-server 2>/dev/null || redis-server --daemonize yes
    sleep 1
fi

if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Redis is running${NC}"
else
    echo -e "  ${YELLOW}⚠ Redis not running (try: redis-cli ping)${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo ""
echo "  1. Verify GPU (optional):"
echo "     python backend/check_gpu.py"
echo ""
echo "  2. Start development services:"
echo "     cd $PROJECT_ROOT"
echo "     make dev"
echo ""
echo "  3. Access the application:"
echo "     Frontend:  http://localhost:5173"
echo "     API Docs:  http://localhost:8080/docs"
echo ""
echo "  4. Stop services:"
echo "     Press Ctrl+C in the terminal"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# Activate backend venv for convenience
source "$PROJECT_ROOT/backend/venv/bin/activate"
echo "Python venv activated (backend/venv)"
echo ""
