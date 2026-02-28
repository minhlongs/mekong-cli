#!/bin/bash
# 9router-launchd-install.sh — Install/manage 9Router as a persistent launchd service
#
# Usage:
#   ./9router-launchd-install.sh install   # Install and start
#   ./9router-launchd-install.sh uninstall # Stop and remove
#   ./9router-launchd-install.sh status    # Check status
#   ./9router-launchd-install.sh restart   # Restart
#   ./9router-launchd-install.sh logs      # Tail logs

set -euo pipefail

PLIST_NAME="com.mekong.9router"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_TEMPLATE="$SCRIPT_DIR/com.mekong.9router.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
ROUTER_PATH="$(which 9router 2>/dev/null || echo '/opt/homebrew/bin/9router')"

info()  { echo "  [INFO]  $*"; }
ok()    { echo "  [OK]    $*"; }
err()   { echo "  [ERROR] $*" >&2; }

install_service() {
    echo "=== Installing $PLIST_NAME ==="

    if [ ! -f "$PLIST_TEMPLATE" ]; then
        err "Plist template not found: $PLIST_TEMPLATE"; exit 1
    fi
    if [ ! -x "$ROUTER_PATH" ]; then
        err "9router not found at $ROUTER_PATH"; exit 1
    fi

    # Kill any stray background instance first
    pkill -f "9router.*20128" 2>/dev/null || true

    # Unload existing
    launchctl unload "$PLIST_DST" 2>/dev/null || true

    mkdir -p "$HOME/Library/LaunchAgents"
    sed -e "s|__9ROUTER_PATH__|$ROUTER_PATH|g" \
        -e "s|__HOME__|$HOME|g" \
        "$PLIST_TEMPLATE" > "$PLIST_DST"

    ok "Plist installed: $PLIST_DST"
    info "9router: $ROUTER_PATH"

    launchctl load "$PLIST_DST"
    ok "Service loaded and started"

    touch "$HOME/9router_stdout.log" "$HOME/9router_stderr.log"
    chmod 600 "$HOME/9router_stdout.log" "$HOME/9router_stderr.log"

    echo ""
    ok "9Router running on port 20128. Will auto-start on login."
    info "Check: curl -sf http://localhost:20128/api/models | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d[\"models\"]), \"models\")'"
}

uninstall_service() {
    echo "=== Uninstalling $PLIST_NAME ==="
    launchctl unload "$PLIST_DST" 2>/dev/null && ok "Service stopped" || info "Not running"
    [ -f "$PLIST_DST" ] && rm "$PLIST_DST" && ok "Plist removed" || info "Plist already gone"
    ok "Uninstall complete"
}

show_status() {
    echo "=== $PLIST_NAME Status ==="
    if launchctl list "$PLIST_NAME" 2>/dev/null; then
        ok "Service is loaded"
        PID=$(launchctl list "$PLIST_NAME" 2>/dev/null | awk 'NR==2{print $1}')
        [ "$PID" != "-" ] && info "PID: $PID" || info "Not currently running"
        # Quick health check
        MODELS=$(curl -sf http://localhost:20128/api/models 2>/dev/null | \
            python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['models']))" 2>/dev/null || echo "?")
        info "Models available: $MODELS"
    else
        info "Service is not loaded"
    fi
}

restart_service() {
    echo "=== Restarting $PLIST_NAME ==="
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    pkill -f "9router.*20128" 2>/dev/null || true
    sleep 1
    launchctl load "$PLIST_DST"
    ok "Service restarted"
}

show_logs() {
    echo "=== Tailing 9Router logs (Ctrl+C to stop) ==="
    tail -f "$HOME/9router_stdout.log" "$HOME/9router_stderr.log" 2>/dev/null
}

case "${1:-help}" in
    install)   install_service ;;
    uninstall) uninstall_service ;;
    status)    show_status ;;
    restart)   restart_service ;;
    logs)      show_logs ;;
    *)
        echo "Usage: $0 {install|uninstall|status|restart|logs}"
        exit 1
        ;;
esac
