#!/bin/bash
set -e

CLAUDE_USER="claude"
CLAUDE_HOME="/home/claude"
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

# UID/GID remapping
CURRENT_UID=$(id -u "$CLAUDE_USER")
CURRENT_GID=$(id -g "$CLAUDE_USER")

if [ "$PGID" != "$CURRENT_GID" ]; then
    groupmod -o -g "$PGID" claude
fi
if [ "$PUID" != "$CURRENT_UID" ]; then
    usermod -o -u "$PUID" claude
fi

chown "$PUID:$PGID" "$CLAUDE_HOME"
chown "$PUID:$PGID" "$CLAUDE_HOME/.claude" 2>/dev/null || true

# Pre-create ~/.claude.json
if [ ! -f "$CLAUDE_HOME/.claude.json" ]; then
    echo '{"hasCompletedOnboarding":true,"installMethod":"native"}' > "$CLAUDE_HOME/.claude.json"
    chown "$PUID:$PGID" "$CLAUDE_HOME/.claude.json"
fi

export DISPLAY=:99

# Bootstrap
SENTINEL="$CLAUDE_HOME/.claude/.mekong-bootstrapped"
if [ ! -f "$SENTINEL" ]; then
    echo "[mekong] First boot — running bootstrap"
    if ! /usr/local/bin/bootstrap.sh; then
        echo "[mekong] ERROR: bootstrap failed — container may be misconfigured" >&2
    fi
fi

echo "[mekong] Starting s6-overlay..."
exec /init "$@"
