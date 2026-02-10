---
name: tmux
description: Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output.
---

# tmux Skill

Use tmux only when you need an interactive TTY. Prefer bash background mode for long-running, non-interactive tasks.

## Quickstart

```bash
SOCKET_DIR="${TMPDIR:-/tmp}/clawdbot-tmux-sockets"
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/clawdbot.sock"
SESSION=clawdbot-python

tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'PYTHON_BASIC_REPL=1 python3 -q' Enter
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200
```

## Orchestrating Multiple Agents

```bash
SOCKET="${TMPDIR:-/tmp}/codex-army.sock"

# Create multiple sessions
for i in 1 2 3 4 5; do
  tmux -S "$SOCKET" new-session -d -s "agent-$i"
done

# Launch agents in different workdirs
tmux -S "$SOCKET" send-keys -t agent-1 "cd /tmp/project1 && codex --yolo 'Fix bug X'" Enter

# Poll for completion
for sess in agent-1 agent-2; do
  if tmux -S "$SOCKET" capture-pane -p -t "$sess" -S -3 | grep -q "❯"; then
    echo "$sess: DONE"
  fi
done
```

## Key Commands

- List: `tmux -S "$SOCKET" list-sessions`
- Send: `tmux -S "$SOCKET" send-keys -t target -l -- "$cmd"`
- Capture: `tmux -S "$SOCKET" capture-pane -p -J -t target -S -200`
- Kill: `tmux -S "$SOCKET" kill-session -t "$SESSION"`
- Kill all: `tmux -S "$SOCKET" kill-server`
