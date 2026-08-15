#!/bin/bash
# Setup merge daemon as launchd service — tự động merge PR mỗi 5 phút
# Chạy 1 lần: bash scripts/setup-merge-daemon.sh

PLIST="$HOME/Library/LaunchAgents/com.mekong.merge-daemon.plist"
SCRIPT="$HOME/mekong-cli/scripts/merge-daemon.cjs"
LOG_DIR="$HOME/mekong-cli/logs"

mkdir -p "$LOG_DIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mekong.merge-daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which node)</string>
        <string>$SCRIPT</string>
        <string>--once</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/merge-daemon.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/merge-daemon.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin</string>
        <key>HOME</key>
        <string>$HOME</string>
    </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST"
echo "✅ Merge daemon installed. Polling sophia-ai-factory every 5 minutes."
echo "   Logs: $LOG_DIR/merge-daemon.log"
