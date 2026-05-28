#!/bin/bash
# Check CTO daemon health — PID, uptime, restart count
# Usage: ./check-daemon-health.sh

echo "[daemon] CTO Daemon Health Check"
echo "================================"

# Check if tmux session exists
if tmux has-session -t cto 2>/dev/null; then
    echo "[daemon] tmux session 'cto': ACTIVE"
else
    echo "[daemon] tmux session 'cto': NOT FOUND" >&2
    echo "[daemon] Try: tmux ls" >&2
fi

# Check s6 service if in Docker
if [ -d /etc/s6-overlay ]; then
    echo "[daemon] s6-overlay detected (Docker mode)"
    for svc in cloudcli xvfb mekong-gateway; do
        if [ -d "/etc/s6-overlay/s6-rc.d/$svc" ]; then
            echo "[daemon] Service $svc: present"
        fi
    done
fi

# Check LLM servers
for port in 11435 11436; do
    if curl -sf "http://127.0.0.1:$port/v1/models" > /dev/null 2>&1; then
        echo "[daemon] LLM :$port — healthy"
    else
        echo "[daemon] LLM :$port — unreachable" >&2
    fi
done
