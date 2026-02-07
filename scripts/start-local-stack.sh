#!/bin/bash

# start-local-stack.sh
# Starts the full AgencyOS stack locally (Engine, Worker, API, Redis)
# Useful when Docker is not available.

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directories
PROJECT_ROOT=$(pwd)
LOG_DIR="$PROJECT_ROOT/.logs"

mkdir -p "$LOG_DIR"

echo -e "${BLUE}🚀 Starting AgencyOS Local Stack...${NC}"

# 1. Start Redis
echo -e "${BLUE}📦 Checking Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    if command -v redis-server >/dev/null; then
        redis-server --daemonize yes
        echo -e "${GREEN}✅ Redis started${NC}"
    else
        echo -e "${RED}❌ Redis not found. Please install redis-server.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Redis is already running${NC}"
fi

# 2. Start Engine (Node.js)
echo -e "${BLUE}⚙️  Starting Engine (Port 3000)...${NC}"
cd "$PROJECT_ROOT/apps/engine"
# Ensure dependencies
if [ ! -d "node_modules" ]; then
    npm install
fi
# Start in background
PORT=3000 REDIS_HOST=localhost REDIS_PORT=6379 npm start > "$LOG_DIR/engine.log" 2>&1 &
ENGINE_PID=$!
echo $ENGINE_PID > "$LOG_DIR/engine.pid"
echo -e "${GREEN}✅ Engine started (PID: $ENGINE_PID). Logs: $LOG_DIR/engine.log${NC}"

# 3. Start Worker (Node.js)
echo -e "${BLUE}👷 Starting Worker...${NC}"
cd "$PROJECT_ROOT/apps/worker"
# Ensure dependencies
if [ ! -d "node_modules" ]; then
    npm install
fi
# Start in background
REDIS_HOST=localhost REDIS_PORT=6379 npm start > "$LOG_DIR/worker.log" 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > "$LOG_DIR/worker.pid"
echo -e "${GREEN}✅ Worker started (PID: $WORKER_PID). Logs: $LOG_DIR/worker.log${NC}"

# 4. Start API (Python/FastAPI)
echo -e "${BLUE}💰 Starting Money API (Port 8000)...${NC}"
cd "$PROJECT_ROOT"
# Ensure venv
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run 'python3 -m venv venv'${NC}"
    exit 1
fi
# Start in background
source venv/bin/activate
# Using nohup to ensure it stays running
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!
echo $API_PID > "$LOG_DIR/api.pid"
echo -e "${GREEN}✅ API started (PID: $API_PID). Logs: $LOG_DIR/api.log${NC}"

echo -e "\n${GREEN}✨ Full Stack Running!${NC}"
echo -e "   - Engine: http://localhost:3000"
echo -e "   - API:    http://localhost:8000"
echo -e "   - Redis:  localhost:6379"
echo -e "\nType './scripts/stop-local-stack.sh' to stop."
