#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 TỨ ĐẠI CHIẾN — AUTO DISPATCH
# ═══════════════════════════════════════════════════════════════
#
# Tự động dispatch missions cho 4 projects
# Chạy ngay từ session hiện tại, không cần attach tmux
#
# Usage: ./4-project-dispatch.sh [mekong-cli|sophia|algo-trader|wellnexus|all] "mission description"
# ═══════════════════════════════════════════════════════════════

set -e

MEKONG_DIR="${MEKONG_DIR:-/Users/macbookprom1/mekong-cli}"

# Project configs (parallel arrays for macOS bash 3.x compatibility)
PROJECT_NAMES="mekong-cli sophia algo-trader wellnexus"
PROJECT_DIRS="/Users/macbookprom1/mekong-cli /Users/macbookprom1/mekong-cli/apps/sophia-proposal /Users/macbookprom1/mekong-cli/apps/algo-trader /Users/macbookprom1/mekong-cli/apps/well"

# Get project directory by name
get_project_dir() {
  local target=$1
  local idx=1
  for name in $PROJECT_NAMES; do
    if [ "$name" = "$target" ]; then
      echo "$PROJECT_DIRS" | awk -v i=$idx '{print $i}'
      return 0
    fi
    idx=$((idx + 1))
  done
  echo ""
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[🏯 DISPATCH]${NC} $1"; }
ok() { echo -e "${GREEN}[✅]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
err() { echo -e "${RED}[❌]${NC} $1"; }

# Create mission file
create_mission() {
  local project=$1
  local mission=$2
  local project_dir=$(get_project_dir "$project")
  local tasks_dir="$project_dir/tasks"
  local timestamp=$(date +%y%m%d-%H%M%S)
  local mission_file="$tasks_dir/mission_${timestamp}_${project}.txt"

  if [ ! -d "$tasks_dir" ]; then
    mkdir -p "$tasks_dir"
    ok "Created tasks directory: $tasks_dir"
  fi

  # Write mission file
  cat > "$mission_file" << EOF
/cook $mission

---
Project: $project
Created: $(date)
Dispatched by: 4-project-dispatch.sh
EOF

  ok "Mission created: $mission_file"
  echo ""
  cat "$mission_file"
  echo ""
}

# Dispatch to single project
dispatch() {
  local project=$1
  local mission=$2
  local project_dir=$(get_project_dir "$project")

  if [ -z "$project_dir" ]; then
    err "Unknown project: $project"
    echo "Valid projects: mekong-cli, sophia, algo-trader, wellnexus"
    return 1
  fi

  log "Dispatching to $project: $mission"
  create_mission "$project" "$mission"
}

# Dispatch to all 4 projects
dispatch_all() {
  local mission=$1

  log "══════════════════════════════════════"
  log "🚀 Dispatching to ALL 4 projects..."
  log "══════════════════════════════════════"
  echo ""

  for project in mekong-cli sophia algo-trader wellnexus; do
    dispatch "$project" "$mission"
    echo "──────────────────────────────────────────"
    sleep 1
  done

  ok "✅ All 4 missions dispatched!"
  log "OpenClaw will process them automatically."
}

# Show queue status
show_status() {
  log "══════════════════════════════════════"
  log "📊 Mission Queue Status"
  log "══════════════════════════════════════"
  echo ""

  for project in mekong-cli sophia algo-trader wellnexus; do
    local project_dir=$(get_project_dir "$project")
    local tasks_dir="$project_dir/tasks"
    if [ -d "$tasks_dir" ]; then
      count=$(ls "$tasks_dir"/*.txt 2>/dev/null | wc -l)
      echo "  $project: $count pending missions"
    else
      echo "  $project: No tasks directory"
    fi
  done
}

# Main
case "${1:-help}" in
  mekong-cli|sophia|algo-trader|wellnexus)
    if [ -z "$2" ]; then
      err "Missing mission description"
      echo "Usage: $0 $project \"mission description\""
      exit 1
    fi
    dispatch "$1" "$2"
    ;;
  all)
    if [ -z "$2" ]; then
      err "Missing mission description"
      echo "Usage: $0 all \"mission description\""
      exit 1
    fi
    dispatch_all "$2"
    ;;
  status)
    show_status
    ;;
  *)
    echo "Usage: $0 {mekong-cli|sophia|algo-trader|wellnexus|all|status} [mission]"
    echo ""
    echo "Examples:"
    echo "  $0 mekong-cli \"Fix parser bug in src/core\""
    echo "  $0 sophia \"Add pricing page component\""
    echo "  $0 algo-trader \"Update RSI strategy parameters\""
    echo "  $0 wellnexus \"Add health assessment table\""
    echo "  $0 all \"Run build and fix any errors\""
    echo "  $0 status"
    ;;
esac
