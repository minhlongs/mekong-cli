#!/bin/bash
# ==============================================================================
# OPUS WATCHDOG: 24/7 Tmux Monitor for Claude Code (macOS specific)
# Automatically triggers audio alerts when Opus is idle, done, or blocked.
# ==============================================================================

LOG_FILE="/tmp/opus_watchdog.log"
echo "[$(date)] Watchdog started monitoring opus_algo:0.0" > "$LOG_FILE"

# Make sure volume is audible
osascript -e 'set volume output volume 75'

while true; do
  # Grab the last 15 lines of the Opus pane
  OUTPUT=$(tmux capture-pane -t opus_algo:0.0 -p 2>/dev/null | tail -n 15)
  
  # If tmux command failed (pane closed), exit softly
  if [ $? -ne 0 ]; then
     echo "[$(date)] Pane opus_algo not found. Exiting." >> "$LOG_FILE"
     exit 0
  fi

  # Check if Claude Code is sitting at the prompt '❯'
  # We do a basic heuristic: it has '❯' but doesn't have 'Running…' or 'Tempering…' or 'Crunching…'
  if echo "$OUTPUT" | grep -q "❯"; then
    if ! echo "$OUTPUT" | grep -q -E "(Running…|Tempering…|Crunching…|Newspapering…|Prestidigitating…|Churned|Brewed|Working)"; then
      echo "[$(date)] ALERT: Opus has stopped and is waiting for input!" >> "$LOG_FILE"
      
      # macOS specific physical alerts
      afplay /System/Library/Sounds/Submarine.aiff
      say -v "Linh" "Sếp ơi, cờ lao đê cột chấm dứt công việc, đang chờ lệnh kìa sếp!" 2>/dev/null || say "Sếp ơi, cờ lao đê cột đang chờ lệnh!"
      afplay /System/Library/Sounds/Submarine.aiff
      
      # Cooldown for 2 minutes so it doesn't spam the speaker infinitely
      sleep 120
    fi
  fi
  
  # Check every 10 seconds (ultra low CPU usage)
  sleep 10
done
