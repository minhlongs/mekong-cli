#!/bin/bash
# tom-hum-launchd-install.sh — Install/manage Tôm Hùm task-watcher as launchd service
#
# Usage:
#   ./tom-hum-launchd-install.sh install   # Install and start service
#   ./tom-hum-launchd-install.sh uninstall # Stop and remove service
#   ./tom-hum-launchd-install.sh status    # Check service status
#   ./tom-hum-launchd-install.sh restart   # Restart service
#   ./tom-hum-launchd-install.sh logs      # Tail log files

set -euo pipefail

PLIST_NAME="com.mekong.tom-hum-watcher"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEKONG_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_TEMPLATE="$SCRIPT_DIR/com.mekong.tom-hum-watcher.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
NODE_PATH="$(which node 2>/dev/null || echo '/opt/homebrew/bin/node')"
API_KEY_FILE="$HOME/.mekong/api-key"

info()  { echo "  [INFO]  $*"; }
ok()    { echo "  [OK]    $*"; }
err()   { echo "  [ERROR] $*" >&2; }

install_service() {
    echo "=== Installing $PLIST_NAME ==="

    # Validate dependencies
    if [ ! -f "$PLIST_TEMPLATE" ]; then
        err "Plist template not found: $PLIST_TEMPLATE"
        exit 1
    fi
    if [ ! -x "$NODE_PATH" ]; then
        err "Node.js not found at $NODE_PATH"
        exit 1
    fi

    # Ensure API key available at runtime
    if [ ! -f "$API_KEY_FILE" ]; then
        if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
            mkdir -p "$(dirname "$API_KEY_FILE")"
            echo "$ANTHROPIC_API_KEY" > "$API_KEY_FILE"
            chmod 600 "$API_KEY_FILE"
            ok "API key saved to $API_KEY_FILE"
        else
            err "No API key found. Set ANTHROPIC_API_KEY env var or create $API_KEY_FILE"
            exit 1
        fi
    fi

    # Unload existing service
    launchctl unload "$PLIST_DST" 2>/dev/null || true

    # Substitute placeholders in template
    mkdir -p "$HOME/Library/LaunchAgents"
    sed -e "s|__NODE_PATH__|$NODE_PATH|g" \
        -e "s|__MEKONG_DIR__|$MEKONG_DIR|g" \
        -e "s|__HOME__|$HOME|g" \
        "$PLIST_TEMPLATE" > "$PLIST_DST"

    ok "Plist installed: $PLIST_DST"
    info "Node: $NODE_PATH"
    info "Working dir: $MEKONG_DIR"

    # Load service
    launchctl load "$PLIST_DST"
    ok "Service loaded and started"

    # Set log permissions
    touch "$HOME/tom_hum_stdout.log" "$HOME/tom_hum_stderr.log"
    chmod 600 "$HOME/tom_hum_stdout.log" "$HOME/tom_hum_stderr.log"

    echo ""
    ok "Installation complete! Service will auto-start on login."
    info "Check status: $0 status"
    info "View logs: $0 logs"
}

uninstall_service() {
    echo "=== Uninstalling $PLIST_NAME ==="

    launchctl unload "$PLIST_DST" 2>/dev/null && ok "Service stopped" || info "Service was not running"

    if [ -f "$PLIST_DST" ]; then
        rm "$PLIST_DST"
        ok "Plist removed: $PLIST_DST"
    else
        info "Plist not found (already removed)"
    fi

    ok "Uninstall complete"
}

show_status() {
    echo "=== $PLIST_NAME Status ==="
    if launchctl list "$PLIST_NAME" 2>/dev/null; then
        ok "Service is loaded"
        # Show PID
        PID=$(launchctl list "$PLIST_NAME" 2>/dev/null | awk 'NR==2{print $1}')
        [ "$PID" != "-" ] && info "PID: $PID" || info "Not currently running"
    else
        info "Service is not loaded"
    fi
}

restart_service() {
    echo "=== Restarting $PLIST_NAME ==="
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    sleep 1
    launchctl load "$PLIST_DST"
    ok "Service restarted"
}

show_logs() {
    echo "=== Tailing Tôm Hùm logs (Ctrl+C to stop) ==="
    tail -f "$HOME/tom_hum_stdout.log" "$HOME/tom_hum_stderr.log" "$HOME/tom_hum_cto.log" 2>/dev/null
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
