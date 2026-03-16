#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 TỨ ĐẠI CHIẾN — 4 Projects Parallel Swarm
# ═══════════════════════════════════════════════════════════════
#
# Khởi động 4 tmux sessions độc lập cho 4 dự án:
# 1. mekong-cli   — Core engine
# 2. sophia       — AgencyOS
# 3. algo-trader  — Trading platform
# 4. wellnexus    — Health platform
#
# Usage: ./4-project-swarm.sh [start|stop|status]
# ═══════════════════════════════════════════════════════════════

set -e

MEKONG_DIR="${MEKONG_DIR:-/Users/macbookprom1/mekong-cli}"
OPENCLAW_DIR="$MEKONG_DIR/apps/openclaw-worker"
PID_DIR="/tmp/tom_hum_pids"
LOG_DIR="$HOME/.openclaw/logs"

# Projects config (parallel arrays for macOS bash 3.x compatibility)
PROJECT_NAMES="mekong-cli sophia algo-trader wellnexus"
PROJECT_DIRS="$MEKONG_DIR $MEKONG_DIR/apps/sophia-proposal $MEKONG_DIR/apps/algo-trader $MEKONG_DIR/apps/well"
TMUX_SESSIONS="tom-hum-mekong tom-hum-sophia tom-hum-algo tom-hum-well"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[🏯 4-PROJECT]${NC} $1"; }
ok() { echo -e "${GREEN}[✅]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
err() { echo -e "${RED}[❌]${NC} $1"; }

# Get project info by index (1-based)
get_project_dir() {
  echo "$PROJECT_DIRS" | awk -v idx=$1 '{print $idx}'
}

get_tmux_session() {
  echo "$TMUX_SESSIONS" | awk -v idx=$1 '{print $idx}'
}

get_project_name() {
  echo "$PROJECT_NAMES" | awk -v idx=$1 '{print $idx}'
}

# Helper: Start project swarm
start_project() {
  local name=$1
  local project_dir=$2
  local tmux_session=$3
  local log_file="$LOG_DIR/${name}.log"

  if [ ! -d "$project_dir" ]; then
    warn "$name: Directory not found ($project_dir)"
    return 1
  fi

  # Kill existing session
  tmux kill-session -t "$tmux_session" 2>/dev/null || true

  # Create new tmux session
  tmux new-session -d -s "$tmux_session" -c "$project_dir"

  # Start task-watcher in tmux mode
  tmux send-keys -t "$tmux_session" "cd $project_dir && TOM_HUM_BRAIN_MODE=tmux node $OPENCLAW_DIR/task-watcher.js >> $log_file 2>&1" C-m

  ok "$name: Started ($tmux_session) at $project_dir"
}

# Helper: Stop project swarm
stop_project() {
  local name=$1
  local tmux_session=$2

  tmux kill-session -t "$tmux_session" 2>/dev/null && ok "$name: Stopped ($tmux_session)" || warn "$name: Already stopped"
}

# Helper: Check project status
check_project() {
  local name=$1
  local tmux_session=$2

  if tmux has-session -t "$tmux_session" 2>/dev/null; then
    ok "$name: Running ($tmux_session)"
  else
    err "$name: Not running"
  fi
}

# ═══════════════════════════════════════
# Start all 4 projects
# ═══════════════════════════════════════

start_all() {
  log "══════════════════════════════════════"
  log "🚀 Khởi động TỨ ĐẠI CHIẾN..."
  log "══════════════════════════════════════"
  echo ""

  # Create directories
  mkdir -p "$PID_DIR" "$LOG_DIR"

  # Verify project directories
  log "📋 Kiểm tra thư mục dự án..."
  for i in 1 2 3 4; do
    name=$(get_project_name $i)
    dir=$(get_project_dir $i)
    if [ -d "$dir" ]; then
      ok "$name: $dir"
    else
      warn "$name: Missing directory $dir"
    fi
  done
  echo ""

  # Start each project
  log "🔥 Khởi động 4 tmux sessions..."
  for i in 1 2 3 4; do
    name=$(get_project_name $i)
    dir=$(get_project_dir $i)
    session=$(get_tmux_session $i)
    start_project "$name" "$dir" "$session"
    sleep 2
  done

  echo ""
  log "══════════════════════════════════════"
  log "✅ TỨ ĐẠI CHIẾN — ONLINE!"
  log "══════════════════════════════════════"
  echo ""
  log "📋 Attach commands:"
  for i in 1 2 3 4; do
    name=$(get_project_name $i)
    session=$(get_tmux_session $i)
    log "  $name: tmux attach -t $session"
  done
  echo ""
  log "📊 Monitor all:"
  log "  tmux list-sessions"
  echo ""
}

# ═══════════════════════════════════════
# Stop all projects
# ═══════════════════════════════════════

stop_all() {
  log "══════════════════════════════════════"
  log "🛑 Dừng TỨ ĐẠI CHIẾN..."
  log "══════════════════════════════════════"
  echo ""

  for i in 1 2 3 4; do
    name=$(get_project_name $i)
    session=$(get_tmux_session $i)
    stop_project "$name" "$session"
  done

  echo ""
  log "✅ Tất cả projects đã dừng."
}

# ═══════════════════════════════════════
# Status check
# ═══════════════════════════════════════

status_all() {
  log "══════════════════════════════════════"
  log "📊 Kiểm tra quân tình..."
  log "══════════════════════════════════════"
  echo ""

  for i in 1 2 3 4; do
    name=$(get_project_name $i)
    session=$(get_tmux_session $i)
    check_project "$name" "$session"
  done

  echo ""
  log "📋 Sessions:"
  tmux list-sessions 2>/dev/null || echo "  No active sessions"
}

# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

case "${1:-start}" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    sleep 2
    start_all
    ;;
  status)
    status_all
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
