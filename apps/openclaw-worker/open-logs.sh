#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🏯 TỨ ĐẠI CHIẾN — OPEN LOGS IN TEXTEDIT
# ═══════════════════════════════════════════════════════════════
#
# Mở logs trong TextEdit để dễ bôi đen + copy text
#

LOG_DIR="$HOME/.openclaw/logs"

echo "══════════════════════════════════════"
echo "📖 Open Logs in TextEdit"
echo "══════════════════════════════════════"
echo ""

# Check logs exist
if [ ! -d "$LOG_DIR" ]; then
  echo "❌ No logs found in $LOG_DIR"
  exit 1
fi

# Convert logs to single HTML file for easy viewing
HTML_FILE="/tmp/tu-dai-chien-logs.html"

cat > "$HTML_FILE" << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Tứ Đại Chiến — Logs</title>
  <style>
    body { font-family: Menlo, Monaco, monospace; font-size: 12px; padding: 20px; }
    h2 { color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 5px; }
    .log-section { margin-bottom: 30px; }
    pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
    .mekong { border-left: 4px solid #007AFF; }
    .sophia { border-left: 4px solid #FF9500; }
    .algo { border-left: 4px solid #34C759; }
    .well { border-left: 4px solid #FF2D55; }
  </style>
</head>
<body>
  <h1>🏯 Tứ Đại Chiến — Live Logs</h1>
  <p><i>Refresh page to see latest logs. Select text to copy.</i></p>
HTMLEOF

# Add each log
for project in mekong-cli sophia algo-trader wellnexus; do
  log_file="$LOG_DIR/${project}.log"
  if [ -f "$log_file" ]; then
    color_class=$(echo "$project" | tr '-' '_' | tr -d '_')
    case "$project" in
      mekong-cli) color_class="mekong" ;;
      sophia) color_class="sophia" ;;
      algo-trader) color_class="algo" ;;
      wellnexus) color_class="well" ;;
    esac

    echo "<div class='log-section $color_class'>" >> "$HTML_FILE"
    echo "<h2>$project</h2>" >> "$HTML_FILE"
    echo "<pre>" >> "$HTML_FILE"
    # Escape HTML special chars
    sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' "$log_file" >> "$HTML_FILE"
    echo "</pre>" >> "$HTML_FILE"
    echo "</div>" >> "$HTML_FILE"
    echo "" >> "$HTML_FILE"
  fi
done

cat >> "$HTML_FILE" << 'HTMLEOF'
  <script>
    // Auto refresh every 10 seconds
    setTimeout(() => location.reload(), 10000);
  </script>
</body>
</html>
HTMLEOF

# Open in default browser (easier to select/copy than TextEdit)
open "$HTML_FILE"

echo "✅ Opened in browser: $HTML_FILE"
echo ""
echo "Now you can:"
echo "  • Select text with mouse"
echo "  • Copy: Cmd+C"
echo "  • Auto-refresh every 10s"
echo ""
echo "Or open individual logs:"
echo "  open -a TextEdit $LOG_DIR/mekong-cli.log"
echo "  open -a TextEdit $LOG_DIR/sophia.log"
echo "  open -a TextEdit $LOG_DIR/algo-trader.log"
echo "  open -a TextEdit $LOG_DIR/wellnexus.log"
