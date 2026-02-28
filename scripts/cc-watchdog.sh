#!/usr/bin/env bash
# Watchdog for CC CLI Compaction Stalls (0%)
TARGET_PANE="tom_hum_brain:0.0"
echo "Starting CC CLI Watchdog for $TARGET_PANE..."

while true; do
  OUTPUT=$(tmux capture-pane -t $TARGET_PANE -p -S -10)
  
  # Check if stalled at 0%
  if echo "$OUTPUT" | grep -iq "Compacting conversation" && echo "$OUTPUT" | grep -iq "0%"; then
    echo "$(date): Detected 0% compaction stall! Applying emergency recovery..."
    tmux send-keys -t $TARGET_PANE C-c
    sleep 3
    tmux send-keys -t $TARGET_PANE "/clear"
    sleep 1
    tmux send-keys -t $TARGET_PANE Enter
    sleep 1
    tmux send-keys -t $TARGET_PANE Enter
    sleep 2
    echo "$(date): Recovery applied. Context cleared."
    
    # Wait longer before next check to avoid loops
    sleep 30
  fi
  
  sleep 10
done
