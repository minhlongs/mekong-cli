#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 TỨ ĐẠI CHIẾN — MASTER VIEW (4 Panes trong 1 Screen)
# ═══════════════════════════════════════════════════════════════
#
# Tạo 1 tmux session với 4 panes cho 4 projects:
# ┌─────────────┬─────────────┐
# │ mekong-cli  │  sophia     │
# ├─────────────┼─────────────┤
# │ algo-trader │  wellnexus  │
# └─────────────┴─────────────┘
#
# Usage: ./4-project-master.sh [start|stop|status|monitor]
# ═══════════════════════════════════════════════════════════════

set -e

MEKONG_DIR="${MEKONG_DIR:-/Users/macbookprom1/mekong-cli}"
OPENCLAW_DIR="$MEKONG_DIR/apps/openclaw-worker"
LOG_DIR="$HOME/.openclaw/logs"
TMUX_SESSION="tom-hum-master"

# Project configs
PROJECT_1_DIR="$MEKONG_DIR"
PROJECT_1_NAME="mekong-cli"
PROJECT_1_LOG="$LOG_DIR/mekong-cli.log"

PROJECT_2_DIR="$MEKONG_DIR/apps/sophia-proposal"
PROJECT_2_NAME="sophia"
PROJECT_2_LOG="$LOG_DIR/sophia.log"

PROJECT_3_DIR="$MEKONG_DIR/apps/algo-trader"
PROJECT_3_NAME="algo-trader"
PROJECT_3_LOG="$LOG_DIR/algo-trader.log"

PROJECT_4_DIR="$MEKONG_DIR/apps/well"
PROJECT_4_NAME="wellnexus"
PROJECT_4_LOG="$LOG_DIR/wellnexus.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[🏯 MASTER]${NC} $1"; }
ok() { echo -e "${GREEN}[✅]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
err() { echo -e "${RED}[❌]${NC} $1"; }

# ═══════════════════════════════════════
# Start master view with 4 panes
# ═══════════════════════════════════════

start_master() {
  log "══════════════════════════════════════"
  log "🚀 Khởi động MASTER VIEW (4 Panes)..."
  log "══════════════════════════════════════"
  echo ""

  # Create log directory
  mkdir -p "$LOG_DIR"

  # Kill existing session
  tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true
  sleep 1

  # Verify project directories
  for dir in "$PROJECT_1_DIR" "$PROJECT_2_DIR" "$PROJECT_3_DIR" "$PROJECT_4_DIR"; do
    if [ ! -d "$dir" ]; then
      warn "Directory not found: $dir"
    fi
  done

  # Create master session with pane 1 (top-left: mekong-cli)
  log "📍 Creating master session..."
  tmux new-session -d -s "$TMUX_SESSION" -c "$PROJECT_1_DIR"
  tmux rename-window -t "$TMUX_SESSION" "4-Projects"

  # Split horizontally (creates right pane: sophia)
  tmux split-window -h -t "$TMUX_SESSION" -c "$PROJECT_2_DIR"

  # Split vertically from top-left (creates bottom-left: algo-trader)
  tmux split-window -v -t "$TMUX_SESSION:0.0" -c "$PROJECT_3_DIR"

  # Split vertically from top-right (creates bottom-right: wellnexus)
  tmux split-window -v -t "$TMUX_SESSION:0.1" -c "$PROJECT_4_DIR"

  # Select top-left pane
  tmux select-pane -t "$TMUX_SESSION:0.0"

  # Start task-watcher in each pane
  log "🔥 Khởi động task-watchers trong 4 panes..."

  # Pane 0: mekong-cli
  tmux send-keys -t "$TMUX_SESSION:0.0" "echo '🏯 $PROJECT_1_NAME' && TOM_HUM_BRAIN_MODE=tmux node $OPENCLAW_DIR/task-watcher.js >> $PROJECT_1_LOG 2>&1" C-m

  # Pane 1: sophia
  tmux send-keys -t "$TMUX_SESSION:0.1" "echo '🏯 $PROJECT_2_NAME' && TOM_HUM_BRAIN_MODE=tmux node $OPENCLAW_DIR/task-watcher.js >> $PROJECT_2_LOG 2>&1" C-m

  # Pane 2: algo-trader
  tmux send-keys -t "$TMUX_SESSION:0.2" "echo '🏯 $PROJECT_3_NAME' && TOM_HUM_BRAIN_MODE=tmux node $OPENCLAW_DIR/task-watcher.js >> $PROJECT_3_LOG 2>&1" C-m

  # Pane 3: wellnexus
  tmux send-keys -t "$TMUX_SESSION:0.3" "echo '🏯 $PROJECT_4_NAME' && TOM_HUM_BRAIN_MODE=tmux node $OPENCLAW_DIR/task-watcher.js >> $PROJECT_4_LOG 2>&1" C-m

  sleep 3

  # Add status bar showing project names
  tmux set-window-option -t "$TMUX_SESSION" window-status-format "#T"
  tmux set-window-option -t "$TMUX_SESSION" window-status-current-format "#T [ACTIVE]"

  ok "Master view started!"
  echo ""
  log "══════════════════════════════════════"
  log "✅ TỨ ĐẠI CHIẾN MASTER — ONLINE!"
  log "══════════════════════════════════════"
  echo ""
  log "📋 Attach command:"
  log "  tmux attach -t $TMUX_SESSION"
  echo ""
  log "🎮 Controls:"
  log "  Ctrl+b, Arrow keys — Switch panes"
  log "  Ctrl+b, q — Show pane numbers"
  log "  Ctrl+b, z — Zoom current pane"
  log "  Ctrl+b, x — Kill current pane"
  log "  Ctrl+b, d — Detach session"
  echo ""
  log "📊 Layout:"
  log "  ┌────────────────┬────────────────┐"
  log "  │ mekong-cli (0) │ sophia (1)     │"
  log "  ├────────────────┼────────────────┤"
  log "  │ algo-trader(2) │ wellnexus (3)  │"
  log "  └────────────────┴────────────────┘"
  echo ""
}

# ═══════════════════════════════════════
# Stop master view
# ═══════════════════════════════════════

stop_master() {
  log "══════════════════════════════════════"
  log "🛑 Dừng MASTER VIEW..."
  log "══════════════════════════════════════"
  echo ""

  tmux kill-session -t "$TMUX_SESSION" 2>/dev/null && ok "Master session stopped" || warn "No master session found"

  echo ""
  log "✅ Master view đã dừng."
}

# ═══════════════════════════════════════
# Status check
# ═══════════════════════════════════════

status_master() {
  log "══════════════════════════════════════"
  log "📊 Kiểm tra MASTER VIEW..."
  log "══════════════════════════════════════"
  echo ""

  if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    PANE_COUNT=$(tmux list-panes -t "$TMUX_SESSION" | wc -l)
    ok "Session: $TMUX_SESSION ($PANE_COUNT panes)"

    # Show each pane status
    tmux list-panes -t "$TMUX_SESSION" -F "  #{pane_index}: #{pane_current_command} (#{pane_width}x#{pane_height})"
  else
    err "Session: Not running"
  fi

  echo ""
  log "📋 Logs:"
  for log_file in "$PROJECT_1_LOG" "$PROJECT_2_LOG" "$PROJECT_3_LOG" "$PROJECT_4_LOG"; do
    if [ -f "$log_file" ]; then
      lines=$(tail -1 "$log_file" 2>/dev/null | head -c 60)
      echo "  $log_file: $lines..."
    fi
  done
}

# ═══════════════════════════════════════
# Monitor mode (auto-refresh status)
# ═══════════════════════════════════════

monitor_master() {
  log "📺 Monitor mode (Ctrl+C to stop)..."
  echo ""
  while true; do
    clear
    echo "══════════════════════════════════════"
    echo "🏯 TỨ ĐẠI CHIẾN — LIVE MONITOR"
    echo "══════════════════════════════════════"
    echo ""

    for i in 0 1 2 3; do
      if tmux has-pane -t "$TMUX_SESSION:0.$i" 2>/dev/null; then
        cmd=$(tmux display-message -p -t "$TMUX_SESSION:0.$i" "#{pane_current_command}" 2>/dev/null)
        title=$(tmux display-message -p -t "$TMUX_SESSION:0.$i" "#{pane_title}" 2>/dev/null)
        echo "Pane $i: $title ($cmd)"
      else
        echo "Pane $i: [OFFLINE]"
      fi
    done

    echo ""
    echo "Last logs (5 lines each):"
    echo "──────────────────────────────────────────"
    for log_file in "$PROJECT_1_LOG" "$PROJECT_2_LOG" "$PROJECT_3_LOG" "$PROJECT_4_LOG"; do
      name=$(basename "$log_file" .log)
      echo "[$name]:"
      tail -3 "$log_file" 2>/dev/null | sed 's/^/  /'
      echo ""
    done

    sleep 5
  done
}

# ═══════════════════════════════════════
# Restart
# ═══════════════════════════════════════

restart_master() {
  stop_master
  sleep 2
  start_master
}

# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

case "${1:-start}" in
  start)
    start_master
    ;;
  stop)
    stop_master
    ;;
  restart)
    restart_master
    ;;
  status)
    status_master
    ;;
  monitor)
    monitor_master
    ;;
  attach)
    tmux attach -t "$TMUX_SESSION"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|monitor|attach}"
    exit 1
    ;;
esac
