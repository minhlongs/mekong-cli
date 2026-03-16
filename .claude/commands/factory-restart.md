---
description: "Safely restart factory loop without killing active CC CLI tasks"
argument-hint: [--force | --status]
allowed-tools: Bash
---

# /factory-restart — Safe Factory Loop Restart

Gracefully restarts `factory-loop.sh` without interrupting active CC CLI panes.

## Implementation

```bash
PID_FILE="/tmp/factory.pid"
FACTORY_SCRIPT="$HOME/mekong-cli/factory-loop.sh"

echo "=== Factory Loop Manager ==="

# Check current status
if [ -f "$PID_FILE" ]; then
  CURRENT_PID=$(cat "$PID_FILE" 2>/dev/null || echo "0")
  if kill -0 "$CURRENT_PID" 2>/dev/null; then
    echo "Factory running — PID: $CURRENT_PID"
  else
    echo "Factory dead — stale PID: $CURRENT_PID"
    CURRENT_PID=0
  fi
else
  echo "Factory not running (no PID file)"
  CURRENT_PID=0
fi

# Status only
if echo "$ARGUMENTS" | grep -q "status"; then
  if [ "$CURRENT_PID" -gt 0 ]; then
    echo "Uptime: $(ps -o etime= -p $CURRENT_PID 2>/dev/null || echo 'unknown')"
    echo "Metrics: $(wc -l < /tmp/factory-metrics.log 2>/dev/null || echo '0') events"
  fi
  exit 0
fi

# Graceful restart: SIGTERM (triggers trap cleanup)
if [ "$CURRENT_PID" -gt 0 ]; then
  echo "Sending SIGTERM to factory PID $CURRENT_PID..."
  kill -TERM "$CURRENT_PID" 2>/dev/null || true
  sleep 3
  # Verify it stopped
  if kill -0 "$CURRENT_PID" 2>/dev/null; then
    echo "Factory didn't stop — sending SIGKILL..."
    kill -9 "$CURRENT_PID" 2>/dev/null || true
  fi
  echo "Factory stopped."
fi

# Start fresh
echo "Starting factory-loop.sh..."
nohup bash "$FACTORY_SCRIPT" >> "$HOME/tom_hum_cto.log" 2>&1 &
NEW_PID=$!
echo "Factory restarted — PID: $NEW_PID"
echo "Log: tail -f ~/tom_hum_cto.log"
```

## Goal context

<goal>$ARGUMENTS</goal>
