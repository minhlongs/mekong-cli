#!/bin/bash
echo "=== $(date +%T) ==="
echo "[1] OPUS:"
OPUS=$(tmux capture-pane -t opus_algo:0.0 -p -S -15 2>/dev/null | tail -10 || echo "")
if echo "$OPUS" | grep -qE "Bash\(|Read [0-9]|Write\(|Edit\(|Running|Manifesting|Stewing|Bloviating|Tempering|Actioning|Cogitated|Infusing|Composting|Warping|Sautéed|Churned|Baked|Crunched"; then
  echo "  ⚙️ WORKING"
elif echo "$OPUS" | grep -qE "❯|bypass"; then
  echo "  💤 IDLE"
  if echo "$OPUS" | grep -qE "\?|muốn|chọn|Options|confirm|queued|Lỗi|Error"; then
    echo "  ⚠️ HAS QUESTIONS/ISSUES:"
    echo "$OPUS" | grep -iE "\?|muốn|chọn|Options|confirm|queued|Lỗi|Error" | head -2 | sed 's/^/    /'
  else
    echo "  ✅ No questions"
  fi
else
  echo "  ❓ UNKNOWN"
fi

echo "[2] CTO (P1-P3):"
for p in 1 2 3; do
  ST=$(tmux capture-pane -t tom_hum:0.$p -p 2>/dev/null | tail -n 8 || echo "")
  if echo "$ST" | grep -qE "Bash\(|Read [0-9]|Write\(|Edit\(|Hashing|Blanching|Creating|Hatching|Puttering|Generating|Tempering|Crunching|Running|Bloviating|Actioning|Manifesting|Stewing|Billowing|Cogitated|Dilly-dallying|Infusing|Churned|Sautéed|Composting|Baked|Warping"; then
    echo "  P$p: ⚙️ WORKING"
  else
    echo "  P$p: 💤 IDLE"
    # Show last relevant status if idle
    echo "$ST" | grep -E "cook|test|queued|error|Failed|Success" | tail -1 | sed 's/^/    /' || echo "    (No recent tasks)"
  fi
done

echo "[3] M1 HEALTH:"
vm_stat | awk '/free/ {print "  RAM: "$3}'
sysctl -n vm.loadavg | awk '{print "  Load: "$0}'
df -h / | tail -1 | awk '{print "  SSD: "$4}'
