# Research Report: File mtime-based Hang Detection & Node.js tmux Patterns

## 1. File mtime-based Hang Detection in Node.js
**Pattern Analysis:**
- Using `fs.statSync(path).mtimeMs` is the standard synchronous approach in Node.js to check file modification times.
- `Date.now() - stat.mtimeMs` calculates the file's age in milliseconds.
- This pattern already exists in `lib/brain-process-manager.js` (lines 591-611) for cleaning stale worker lock files (`STALE_LOCK_THRESHOLD_MS = 2 * 60 * 1000`).

**Implementation Recommendation:**
For general hang detection (e.g., detecting if CC CLI or tmux is frozen), create a "heartbeat" file or use the existing log file. Compare its `mtimeMs` against a threshold (e.g., 5 minutes):
```javascript
const stat = fs.statSync(logPath);
if (Date.now() - stat.mtimeMs > 5 * 60 * 1000) {
    // 5 minutes no activity -> assume hang
    handleHang();
}
```

## 2. Sending Ctrl+C to tmux Pane in Node.js
**Command Syntax:**
- `tmux send-keys -t SESSION:PANE C-c` is the correct syntax for sending SIGINT to a process inside a tmux pane.
- Already used in `brain-process-manager.js` line 762: `tmuxExec(\`tmux send-keys -t ${TMUX_SESSION}:0.${workerIdx} C-c\`);`

**When to use vs `SIGINT` vs kill:**
- **tmux send-keys C-c**: Best for gently interrupting CC CLI operations (like canceling a long generation or escaping a prompt) without killing the entire CLI process. It allows the CLI to handle the interrupt gracefully.
- **process.kill(pid, 'SIGINT')**: Requires knowing the specific child PID. Harder to track when CC CLI is nested inside tmux.
- **kill subprocess / tmux kill-session**: A heavy-handed approach. Only use if `C-c` fails multiple times or if the entire tmux session is unrecoverable.

## 3. Reading Tail of Log File (Alternative to capture-pane)
**Performance & Approach:**
- `tmux capture-pane` is slow, creates socket contention, and has freezing issues (as noted in `brain-process-manager.js` line 168: "Prevents tmux socket contention that causes freezing").
- Reading log files directly via Node.js is significantly faster and avoids tmux IPC entirely.

**Implementation (Reading last N bytes efficiently):**
Don't use `fs.readFileSync` for large logs as it loads the whole file into memory. Use this pattern:
```javascript
function tailFile(filePath, bytes = 1024) {
    const stat = fs.statSync(filePath);
    const startPos = Math.max(0, stat.size - bytes);

    // For small tails, readSync with buffer is fast and sync
    const buffer = Buffer.alloc(Math.min(bytes, stat.size));
    const fd = fs.openSync(filePath, 'r');
    fs.readSync(fd, buffer, 0, buffer.length, startPos);
    fs.closeSync(fd);

    return buffer.toString('utf-8');
}
```

## 4. Impact of `script -q` on CC CLI Interactive TUI
**Compatibility:**
- `script -q /path/to/log.txt command` records an interactive terminal session faithfully.
- **Yes, it works with TUI applications** (ncurses, React Ink which CC CLI uses) because it allocates a pseudo-terminal (PTY) for the child process.
- **ANSI capture:** It captures *all* ANSI escape codes faithfully (colors, cursor movements, spinners).

**Considerations for our use case:**
- Because `script` captures all cursor movements and spinners (like the braille spinners CC CLI uses), the resulting file will contain a lot of control characters (`\b`, `\r`, `\x1b[K`).
- Any parsing logic reading this file must aggressively strip ANSI codes (which `brain-process-manager.js` already does via its `stripAnsi` function).
- **Alternative:** Redirecting stdout/stderr directly (`> log.txt`) breaks React Ink/TUI apps because they detect they aren't attached to a TTY and either fail or drop to a simplified, non-interactive print mode. `script` preserves the interactive PTY environment while logging.

## Unresolved Questions
1. If we switch to reading a file created by `script` instead of `tmux capture-pane`, will the file writing buffer delay cause synchronization issues with our polling logic? (e.g., file isn't flushed immediately when CC CLI outputs "Cooked").
2. Does `script` handle nested PTY resizing correctly if the parent tmux pane resizes?