---
description: 🦞 Manage Tôm Hùm autonomous daemon (start/stop/status/logs)
argument-hint: [start|stop|status|logs]
---

## Tôm Hùm Daemon Manager

<action>$ARGUMENTS</action>

Based on the action above, execute ONE of these:

### `start`
```bash
bash scripts/tom-hum-autonomous-daemon-launcher.sh
```
Then verify with `tmux has-session -t tom-hum` after 5s.

### `stop`
```bash
tmux kill-session -t tom-hum-brain 2>/dev/null; tmux kill-session -t tom-hum 2>/dev/null
```
Confirm both sessions killed.

### `status`
Run these checks and report:
```bash
tmux has-session -t tom-hum 2>/dev/null && echo "tom-hum: ALIVE" || echo "tom-hum: DEAD"
tmux has-session -t tom-hum-brain 2>/dev/null && echo "tom-hum-brain: ALIVE" || echo "tom-hum-brain: DEAD"
pgrep -f task-watcher.js >/dev/null && echo "node: ALIVE (PID $(pgrep -f task-watcher.js))" || echo "node: DEAD"
tail -5 ~/tom_hum_cto.log
```

### `logs`
```bash
tail -50 ~/tom_hum_cto.log
```

If no action provided, show status.
