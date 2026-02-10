# Phase 3: launchd Auto-Restart + Install Script

## Context Links
- [Parent Plan](plan.md)
- [Phase 2: Task Watcher](phase-02-rewrite-task-watcher.md)
- [Research: launchd](research/researcher-02-launchd-process-mgmt.md)

## Overview
- **Priority:** P2
- **Status:** pending
- **Description:** Create launchd plist for task-watcher auto-restart on crash/login, plus install/uninstall script

## Key Insights
- launchd is native macOS — zero dependencies, auto-start on login
- KeepAlive restarts process if it exits for any reason
- ThrottleInterval prevents restart loops
- Environment variables set in plist for Antigravity Proxy config

## Requirements

### Functional
- Auto-start task-watcher on user login
- Auto-restart if task-watcher crashes
- Log stdout/stderr to dedicated files
- Set required env vars (ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY)
- Install/uninstall script for easy setup
- Status check command

### Non-Functional
- ThrottleInterval ≥ 10s (prevent restart storms)
- Log rotation (launchd doesn't do this — note in docs)
- Clean uninstall removes plist and stops service

## Architecture

```
scripts/
├── tom-hum-launchd-install.sh      # Install plist + load
├── com.mekong.tom-hum-watcher.plist # launchd plist template

~/Library/LaunchAgents/
└── com.mekong.tom-hum-watcher.plist # Installed copy
```

## Related Code Files
- **Create:** `scripts/tom-hum-launchd-install.sh`
- **Create:** `scripts/com.mekong.tom-hum-watcher.plist`

## Implementation Steps

### Step 1: Create plist file
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mekong.tom-hum-watcher</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>/Users/macbookprom1/mekong-cli/apps/openclaw-worker/task-watcher.js</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/macbookprom1/mekong-cli</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_BASE_URL</key>
        <string>http://127.0.0.1:8080</string>
        <key>ANTHROPIC_API_KEY</key>
        <string>${ANTHROPIC_API_KEY}</string>
        <key>MEKONG_DIR</key>
        <string>/Users/macbookprom1/mekong-cli</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>

    <key>KeepAlive</key>
    <true/>

    <key>ThrottleInterval</key>
    <integer>10</integer>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/macbookprom1/tom_hum_stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/macbookprom1/tom_hum_stderr.log</string>
</dict>
</plist>
```

### Step 2: Create install/uninstall script
```bash
#!/bin/bash
# tom-hum-launchd-install.sh
# Usage:
#   ./tom-hum-launchd-install.sh install   # Install and start
#   ./tom-hum-launchd-install.sh uninstall # Stop and remove
#   ./tom-hum-launchd-install.sh status    # Check status
#   ./tom-hum-launchd-install.sh restart   # Restart service

PLIST_NAME="com.mekong.tom-hum-watcher"
PLIST_SRC="$(dirname "$0")/com.mekong.tom-hum-watcher.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

case "$1" in
    install)
        # Substitute env vars in plist template
        # Copy to LaunchAgents
        # launchctl load
        ;;
    uninstall)
        # launchctl unload
        # Remove plist
        ;;
    status)
        # launchctl list | grep tom-hum
        ;;
    restart)
        # unload + load
        ;;
esac
```

### Step 3: Handle API key securely
- Plist template uses `${ANTHROPIC_API_KEY}` placeholder
- Install script reads from env and substitutes
- Alternative: plist references a file `~/.mekong/api-key` that task-watcher reads at startup
- **Preferred approach:** task-watcher reads `~/.mekong/api-key` at startup, plist doesn't contain key

## Todo List
- [ ] Create plist template file
- [ ] Create install/uninstall script with install/uninstall/status/restart
- [ ] Test install → auto-start on login
- [ ] Test KeepAlive → crash recovery
- [ ] Test uninstall → clean removal
- [ ] Verify API key not stored in plist

## Success Criteria
- `tom-hum-launchd-install.sh install` installs and starts service
- Process auto-restarts within 10s of crash
- Process starts automatically on login
- `tom-hum-launchd-install.sh status` shows running state
- Clean uninstall removes all artifacts

## Risk Assessment
- **Risk:** Node.js path may differ (`/opt/homebrew/bin/node` vs `/usr/local/bin/node`)
  - **Mitigation:** Install script detects `which node` and writes correct path
- **Risk:** API key in plist is readable by other processes
  - **Mitigation:** Read key from file at runtime, not in plist

## Security Considerations
- API key NOT stored in plist — read from `~/.mekong/api-key` or env at runtime
- Plist file permissions: 644 (standard for LaunchAgents)
- Log files may contain sensitive output — set 600 permissions

## Next Steps
- Test full end-to-end flow: login → task-watcher starts → mission dropped → dispatched → completed → archived
