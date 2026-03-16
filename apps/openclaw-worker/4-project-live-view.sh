#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 TỨ ĐẠI CHIẾN — LIVE VIEW (Monitor + Attach)
# ═══════════════════════════════════════════════════════════════
#
# Xem progress real-time của 4 projects
# Chạy từ Terminal, không cần attach tmux
#
# Usage: ./4-project-live-view.sh
#

MEKONG_DIR="${MEKONG_DIR:-/Users/macbookprom1/mekong-cli}"
LOG_DIR="$HOME/.openclaw/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

clear_view() {
  clear
}

print_header() {
  echo -e "${CYAN}════════════════════════════════════════════════════════"
  echo -e "   🏯 TỨ ĐẠI CHIẾN — LIVE MONITOR"
  echo -e "════════════════════════════════════════════════════════${NC}"
  echo ""
}

print_pane_status() {
  local session="tom-hum-master"

  if tmux has-session -t "$session" 2>/dev/null; then
    echo -e "${GREEN}✅ Master View: ONLINE (4 panes)${NC}"
    echo ""

    # Pane info
    tmux list-panes -t "$session" -F "${BLUE}  Pane #{pane_index}:#{pane_current_command} (#{pane_width}x#{pane_height})${NC}" 2>/dev/null
  else
    echo -e "${RED}❌ Master View: OFFLINE${NC}"
    echo ""
    echo "Run: /4-project start"
    return 1
  fi
  echo ""
}

print_mission_queues() {
  echo -e "${YELLOW}────────────────────────────────────────────────────${NC}"
  echo -e "${YELLOW}📊 Mission Queues:${NC}"
  echo ""

  projects="mekong-cli sophia algo-trader wellnexus"
  project_dirs="/Users/macbookprom1/mekong-cli /Users/macbookprom1/mekong-cli/apps/sophia-proposal /Users/macbookprom1/mekong-cli/apps/algo-trader /Users/macbookprom1/mekong-cli/apps/well"

  local idx=1
  for project in $projects; do
    local dir=$(echo "$project_dirs" | awk -v i=$idx '{print $i}')
    local tasks_dir="$dir/tasks"
    local count=0

    if [ -d "$tasks_dir" ]; then
      count=$(ls "$tasks_dir"/*.txt 2>/dev/null | wc -l | tr -d ' ')
    fi

    if [ "$count" -gt 0 ]; then
      echo -e "  ${GREEN}$project: $count pending${NC}"
    else
      echo -e "  ${CYAN}$project: 0 pending${NC}"
    fi

    idx=$((idx + 1))
  done
  echo ""
}

print_recent_logs() {
  echo -e "${YELLOW}────────────────────────────────────────────────────${NC}"
  echo -e "${YELLOW}📋 Recent Activity (last 3 lines per project):${NC}"
  echo ""

  projects="mekong-cli sophia algo-trader wellnexus"

  for project in $projects; do
    local log_file="$LOG_DIR/${project}.log"
    echo -e "${BLUE}[$project]:${NC}"

    if [ -f "$log_file" ]; then
      tail -3 "$log_file" 2>/dev/null | sed 's/^/  /'
    else
      echo "  (no logs yet)"
    fi
    echo ""
  done
}

print_controls() {
  echo -e "${YELLOW}────────────────────────────────────────────────────${NC}"
  echo -e "${CYAN}🎮 Controls:${NC}"
  echo "  tmux attach -t tom-hum-master    # Attach xem 4 panes"
  echo "  /4-project stop                  # Dừng master view"
  echo "  /4-project dispatch all \"msg\"    # Dispatch mission"
  echo "  Ctrl+C                           # Thoát monitor"
  echo ""
}

# Main loop
print_header
print_pane_status
print_mission_queues
print_recent_logs
print_controls

echo -e "${CYAN}📺 Auto-refresh every 5s (Ctrl+C to stop)...${NC}"
echo ""

# Auto-refresh loop
while true; do
  sleep 5
  clear_view
  print_header
  print_pane_status
  print_mission_queues
  print_recent_logs
  print_controls
  echo -e "${CYAN}Last updated: $(date '+%H:%M:%S')${NC}"
done
