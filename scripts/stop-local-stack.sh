#!/bin/bash

# stop-local-stack.sh
# Stops the locally running AgencyOS stack

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT=$(pwd)
LOG_DIR="$PROJECT_ROOT/.logs"

echo "🛑 Stopping AgencyOS Stack..."

# Helper function to kill process by pid file
kill_process() {
    SERVICE=$1
    PID_FILE="$LOG_DIR/$SERVICE.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            kill $PID
            echo -e "${GREEN}✅ Stopped $SERVICE (PID: $PID)${NC}"
        else
            echo -e "${RED}⚠️  $SERVICE (PID: $PID) not running${NC}"
        fi
        rm "$PID_FILE"
    else
        echo "No PID file for $SERVICE"
    fi
}

kill_process "api"
kill_process "worker"
kill_process "engine"

# Don't kill Redis generally, as it might be used by others, unless we started it?
# For now, let's leave Redis running or check if we want to stop it.
# echo "To stop redis: redis-cli shutdown"

echo "Done."
