#!/bin/zsh
# ═══════════════════════════════════════════════════════
# 🚀 TOM DISPATCH — Send commands to CC CLI panes
# Usage: ./tom-dispatch.sh P0 "/cook build feature X"
# ═══════════════════════════════════════════════════════

SESSION="${TOM_SESSION:-tom_hum}"
TARGET="$1"   # P0, P1, P2, P3
CMD="$2"      # /cook "task description"

if [ -z "$TARGET" ] || [ -z "$CMD" ]; then
    echo "Usage: $0 <P0|P1|P2|P3> <command>"
    exit 1
fi

# Map P0-P3 to tmux pane index
case "$TARGET" in
    P0) PANE=0 ;; P1) PANE=1 ;; P2) PANE=2 ;; P3) PANE=3 ;;
    P4) PANE=4 ;; P5) PANE=5 ;;
    *) echo "❌ Invalid target: $TARGET (use P0-P5)"; exit 1 ;;
esac

TMUX_BIN="/opt/homebrew/bin/tmux"

# Check pane exists
if ! $TMUX_BIN has-session -t "$SESSION" 2>/dev/null; then
    echo "❌ Session '$SESSION' not found"
    exit 1
fi

# Check if worker is idle (? for shortcuts = ready for input)
POUT=$($TMUX_BIN capture-pane -t "$SESSION:0.$PANE" -p -S -5 2>/dev/null)
if echo "$POUT" | grep -q "esc to interrupt"; then
    echo "⏳ $TARGET busy (esc to interrupt visible) — skipping"
    exit 0
fi

# Send the command
echo "🚀 $TARGET ← $CMD"
$TMUX_BIN send-keys -t "$SESSION:0.$PANE" "$CMD" Enter

# Log
echo "[$(date '+%H:%M:%S')] $TARGET ← $CMD" >> /tmp/tom-dispatch.log
