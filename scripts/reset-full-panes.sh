#!/bin/bash
# Reset panes with full context (90%+) or stuck on dialogs
# Usage: bash scripts/reset-full-panes.sh [session_name]
# If no session specified, scans all tom_hum* sessions
set -uo pipefail

SESSIONS="${1:-}"
if [[ -z "$SESSIONS" ]]; then
  SESSIONS=$(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep "tom_hum" || true)
fi

[[ -z "$SESSIONS" ]] && echo "No tom_hum sessions found" && exit 0

RESET=0
for session in $SESSIONS; do
  pane_count=$(tmux list-panes -t "$session" -F '#{pane_index}' 2>/dev/null | wc -l | tr -d ' ')
  for ((i=0; i<pane_count; i++)); do
    output=$(tmux capture-pane -t "${session}:0.${i}" -p -S -30 2>/dev/null || echo "")
    [[ -z "$output" ]] && continue

    action=""

    # Detect 90%+ or 100% context → /clear
    if echo "$output" | tail -10 | grep -qE "Context:.*100%|context.*100%|auto-compact|Auto-compacting"; then
      action="/clear"
      reason="context 100%"
    elif echo "$output" | tail -10 | grep -qE "Context:.*9[0-9]%|context.*9[0-9]%"; then
      action="/clear"
      reason="context 90%+"
    # Detect selection dialog (Enter to select, arrow keys)
    elif echo "$output" | tail -5 | grep -qiE "Enter to select|arrow keys|select.*option|choose.*from"; then
      # Send Escape to dismiss dialog
      tmux send-keys -t "${session}:0.${i}" Escape 2>/dev/null
      sleep 1
      tmux send-keys -t "${session}:0.${i}" "q" Enter 2>/dev/null
      echo "  ${session}:${i} — dismissed selection dialog"
      RESET=$((RESET + 1))
      continue
    # Detect low remaining context (<20%)
    elif echo "$output" | tail -10 | grep -qE "Context:.*[89][0-9]%"; then
      action="/clear"
      reason="low remaining context"
    fi

    if [[ -n "$action" ]]; then
      echo "  ${session}:${i} — ${reason} → ${action}"
      tmux send-keys -t "${session}:0.${i}" "$action" Enter 2>/dev/null
      RESET=$((RESET + 1))
      sleep 1
    fi
  done
done

echo "Reset ${RESET} panes"
