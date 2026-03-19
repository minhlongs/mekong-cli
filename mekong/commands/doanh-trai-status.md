# Doanh Trại Status — All Department Overview

Show status of all 6 Doanh Trại departments (tmux sessions).

## Usage
```
mekong doanh-trai-status
```

## Script
```bash
#!/bin/bash
echo "═══════════════════════════════════════════════════════"
echo "  DOANH TRẠI TÔM HÙM — Department Status"
echo "═══════════════════════════════════════════════════════"

SESSIONS=("tom_hum:Engineering" "tom_hum_sales:Sales" "tom_hum_mktg:Marketing" "tom_hum_docs:Documentation" "tom_hum_ops:Operations" "tom_hum_design:Design")

for entry in "${SESSIONS[@]}"; do
  IFS=':' read -r session dept <<< "$entry"
  if tmux has-session -t "$session" 2>/dev/null; then
    pane_count=$(tmux list-panes -t "$session" 2>/dev/null | wc -l | tr -d ' ')
    echo "  ✅ ${dept} (${session}) — ${pane_count} panes"
  else
    echo "  ❌ ${dept} (${session}) — not running"
  fi
done

echo ""
echo "Daemons:"
pgrep -f "cto-daemon" >/dev/null && echo "  ✅ CTO daemon (engineering)" || echo "  ❌ CTO daemon"
pgrep -f "doanh-trai-daemon" >/dev/null && echo "  ✅ Doanh Trại daemon (all depts)" || echo "  ❌ Doanh Trại daemon"

echo ""
echo "Logs:"
echo "  Engineering: .mekong/cto-daemon.log"
echo "  All depts:   .mekong/doanh-trai.log"
echo "═══════════════════════════════════════════════════════"
```
