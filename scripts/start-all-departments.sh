#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DOANH TRẠI TÔM HÙM — Start All Departments
# Usage: bash scripts/start-all-departments.sh [eng|sales|mktg|docs|ops|design|all]
# Each department = tmux session running cto-daemon.sh with role-specific tasks
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DAEMON="${PROJECT_ROOT}/cto-daemon.sh"
DEPT_ARG="${1:-all}"

GREEN='\033[32m' YELLOW='\033[33m' NC='\033[0m'

# Department definitions: session_name|pane_count|description
declare -A DEPT_SESSION DEPT_PANES DEPT_DESC
DEPT_SESSION[eng]="tom_hum"
DEPT_SESSION[sales]="tom_hum_sales"
DEPT_SESSION[mktg]="tom_hum_mktg"
DEPT_SESSION[docs]="tom_hum_docs"
DEPT_SESSION[ops]="tom_hum_ops"
DEPT_SESSION[design]="tom_hum_design"

DEPT_PANES[eng]=3; DEPT_PANES[sales]=2; DEPT_PANES[mktg]=2
DEPT_PANES[docs]=2; DEPT_PANES[ops]=2; DEPT_PANES[design]=2

DEPT_DESC[eng]="CTO Engineering"
DEPT_DESC[sales]="Sales+BD"
DEPT_DESC[mktg]="Marketing"
DEPT_DESC[docs]="Documentation"
DEPT_DESC[ops]="Operations+DevOps"
DEPT_DESC[design]="Design+UX"

start_department() {
  local dept=$1
  local session="${DEPT_SESSION[$dept]}"
  local panes="${DEPT_PANES[$dept]}"
  local desc="${DEPT_DESC[$dept]}"

  # Skip engineering — already managed by existing cto-daemon.sh
  if [[ "$dept" == "eng" ]]; then
    if tmux has-session -t "$session" 2>/dev/null; then
      echo -e "  ${GREEN}✅${NC} ${desc} (${session}) — already running"
    else
      echo -e "  ${YELLOW}⚠️${NC}  ${desc} (${session}) — not running. Start with: bash cto-daemon.sh"
    fi
    return
  fi

  # Check if session already exists
  if tmux has-session -t "$session" 2>/dev/null; then
    echo -e "  ${GREEN}✅${NC} ${desc} (${session}) — already running"
    return
  fi

  # Create tmux session with panes
  tmux new-session -d -s "$session" -x 200 -y 50
  for ((i=1; i<panes; i++)); do
    tmux split-window -t "${session}" -h
  done
  tmux select-layout -t "${session}" even-horizontal

  # Launch CC CLI in each pane
  for ((i=0; i<panes; i++)); do
    tmux send-keys -t "${session}:0.${i}" \
      "cd ${PROJECT_ROOT} && claude --dangerously-skip-permissions" Enter
  done

  echo -e "  ${GREEN}✅${NC} ${desc} (${session}) — started with ${panes} panes"

  # Start daemon for this department in background
  CTO_SESSION="$session" nohup bash "$DAEMON" >> "${PROJECT_ROOT}/.mekong/${dept}-daemon.log" 2>&1 &
  echo -e "     Daemon PID: $!"
}

echo "═══════════════════════════════════════════════════════"
echo "  DOANH TRẠI TÔM HÙM — Multi-Department Launcher"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ "$DEPT_ARG" == "all" ]]; then
  for dept in eng sales mktg docs ops design; do
    start_department "$dept"
  done
elif [[ -n "${DEPT_SESSION[$DEPT_ARG]:-}" ]]; then
  start_department "$DEPT_ARG"
else
  echo "Usage: $0 [eng|sales|mktg|docs|ops|design|all]"
  echo ""
  echo "Departments:"
  for dept in eng sales mktg docs ops design; do
    echo "  ${dept}  — ${DEPT_DESC[$dept]} (${DEPT_SESSION[$dept]})"
  done
  exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Active sessions:"
tmux list-sessions 2>/dev/null | grep "tom_hum" || echo "  (none)"
echo "═══════════════════════════════════════════════════════"
