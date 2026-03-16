#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 TỨ ĐẠI CHIẾN — COPY LOGS
# ═══════════════════════════════════════════════════════════════
#
# Copy logs từ 4 projects vào clipboard
#

LOG_DIR="$HOME/.openclaw/logs"

echo "══════════════════════════════════════"
echo "📋 Copy Logs to Clipboard"
echo "══════════════════════════════════════"
echo ""

# Check logs exist
if [ ! -d "$LOG_DIR" ]; then
  echo "❌ No logs found in $LOG_DIR"
  exit 1
fi

# Copy each project log
for project in mekong-cli sophia algo-trader wellnexus; do
  log_file="$LOG_DIR/${project}.log"
  if [ -f "$log_file" ]; then
    lines=$(wc -l < "$log_file" | tr -d ' ')
    echo "📄 $project: $lines lines"
  else
    echo "⚠️  $project: No log file"
  fi
done

echo ""
echo "Commands:"
echo "  cat $LOG_DIR/mekong-cli.log | pbcopy    # Copy mekong-cli"
echo "  cat $LOG_DIR/sophia.log | pbcopy        # Copy sophia"
echo "  cat $LOG_DIR/algo-trader.log | pbcopy   # Copy algo-trader"
echo "  cat $LOG_DIR/wellnexus.log | pbcopy     # Copy wellnexus"
echo ""
echo "Or view with less (scroll + select):"
echo "  less $LOG_DIR/mekong-cli.log"
echo ""

# Auto copy last 50 lines of most recent log
latest_project=""
latest_lines=0

for project in mekong-cli sophia algo-trader wellnexus; do
  log_file="$LOG_DIR/${project}.log"
  if [ -f "$log_file" ]; then
    lines=$(wc -l < "$log_file" | tr -d ' ')
    if [ "$lines" -gt "$latest_lines" ]; then
      latest_lines=$lines
      latest_project=$project
    fi
  fi
done

if [ -n "$latest_project" ]; then
  echo "📋 Copying last 100 lines of $latest_project to clipboard..."
  tail -100 "$LOG_DIR/${latest_project}.log" | pbcopy
  echo "✅ Done! Paste with Cmd+V"
fi
