# Research: launchd Plist & Process Management

## 1. macOS launchd Plist for Node.js Auto-Restart

**Location:** `~/Library/LaunchAgents/com.mekong.tom-hum-watcher.plist`

Key properties:
- `KeepAlive: true` — restarts if process exits
- `ThrottleInterval: 10` — min 10s between restarts (prevents loops)
- `StandardOutPath / StandardErrorPath` — log files
- `WorkingDirectory` — set CWD
- `EnvironmentVariables` — set env vars
- `RunAtLoad: true` — start on login

**Install/control:**
```bash
launchctl load ~/Library/LaunchAgents/com.mekong.tom-hum-watcher.plist
launchctl unload ~/Library/LaunchAgents/com.mekong.tom-hum-watcher.plist
launchctl start com.mekong.tom-hum-watcher
launchctl stop com.mekong.tom-hum-watcher
```

## 2. Claude CLI --resume Behavior

- `claude --resume` resumes the most recent conversation
- `claude --continue` is the preferred flag (alias for resume)
- Can combine: `claude --continue --dangerously-skip-permissions`
- If no previous session: starts fresh (no error)
- Session state stored in `~/.claude/` directory

## 3. Process Supervision Comparison

| Approach | Pros | Cons |
|----------|------|------|
| **launchd** | Native macOS, auto-start login, KeepAlive | XML config, macOS-only |
| **pm2** | Feature-rich, log rotation | Extra dependency, Node-centric |
| **tmux** | Visual, manual inspection | No auto-restart, manual |
| **supervisord** | Cross-platform | Python dependency, overkill |

**Recommendation: launchd** for task-watcher (native, zero deps, auto-restart). tmux optional for visual debugging.

## 4. Graceful Shutdown in Node.js

```javascript
process.on('SIGTERM', () => {
    if (brainProcess) brainProcess.kill('SIGTERM');
    // Give child 5s to cleanup
    setTimeout(() => {
        if (brainProcess) brainProcess.kill('SIGKILL');
        process.exit(0);
    }, 5000);
});
```

Important: handle both SIGTERM (launchd stop) and SIGINT (Ctrl+C).

## 5. M1 Resource Considerations

- Node.js watcher: ~30MB RSS baseline
- Expect + CC CLI: ~200MB RSS
- Total: ~230MB — fine for 16GB M1
- Cooling daemon should monitor both processes
- Use `nice -n 10` for lower priority if needed
