# Research Report: File mtime & tmux automation patterns

## 1. File mtime-based hang detection patterns
- **macOS mtime Resolution**: APFS (modern macOS) supports nanosecond resolution, but Node.js `fs.stat().mtimeMs` returns sub-second precision. Checking mtime is reliable down to milliseconds.
- **Hang Detection Pattern**: Track the last modification time of a log/output file (e.g. `fs.statSync(file).mtimeMs`). If `Date.now() - mtimeMs > THRESHOLD` (e.g., 3 mins), the process is hung.
- **Race Conditions**: During heavy I/O, mtime might delay updating, or a process might be computing without logging. To mitigate, combine mtime checks with CPU/process status checks (`ps -p`).

## 2. Sending Ctrl+C to tmux pane safely
- **Reliability**: `tmux send-keys -t SESSION:PANE C-c` reliably sends `SIGINT`.
- **Propagation in CC CLI**: If Claude Code is in a deep subagent loop (e.g. running bash commands), `C-c` will interrupt the current child process (like a hanging test or script) and return control to the CC CLI prompt. It rarely kills CC CLI itself unless pressed multiple times rapidly.
- **Wait Time**: After sending `C-c`, wait at least 2-3 seconds before checking if the process recovered (by looking for the `❯` prompt).
- **Kickstart vs Abort**: Use `Enter` (`C-m`) to "kickstart" a stuck prompt (e.g., waiting for input). Use `C-c` to "abort" a runaway computation or hung command.

## 3. Parallel CC CLI subagents and tmux socket load
- **CC CLI Architecture**: CC CLI spawns subagents as local processes, communicating via stdio or internal IPC, *not* via tmux panes.
- **Tmux Contention Risk**: In the current architecture, `openclaw-worker` uses `execSync('tmux capture-pane ...')` to read state. With multiple workers (e.g., 4) polling every 500ms, this generates 8 calls/sec. Each `execSync` forks a process and opens the tmux socket.
- **The Freezing Issue**: Heavy tmux socket polling (8+ times/sec) blocks the Node.js event loop due to `execSync` synchronicity and causes tmux server socket contention, leading to CLI freezes. Currently, a `TMUX_MIN_GAP_MS = 5000` (5s throttle) is implemented in `capturePane()` as a guard.

## 4. Node.js `execSync` vs `exec` for tmux commands
- **Safety of `execSync`**: `execSync` blocks the entire Node.js event loop while waiting for the shell to return. With a 10s timeout, a slow tmux socket can freeze the orchestrator completely for up to 10s per call.
- **Better Pattern**: Use `exec` (or `spawn`) wrapped in a Promise. This allows the event loop to continue processing other workers, API requests, and timers while waiting for the tmux output.

### Recommended Fix Pattern for Tmux Contention
Instead of `execSync` polling:
```javascript
const util = require('util');
const exec = util.promisify(require('child_process').exec);

async function capturePaneAsync(target) {
  try {
    const { stdout } = await exec(`tmux capture-pane -t ${target} -p -S -50`, { timeout: 5000 });
    return stdout;
  } catch (err) {
    console.error('Tmux capture failed', err);
    return null;
  }
}
```

## Unresolved Questions
1. Should we replace the 5s `TMUX_MIN_GAP_MS` throttle entirely if we migrate `capturePane` from `execSync` to async `exec`?
2. If `C-c` fails to interrupt a hung CC CLI subagent loop, what is the escalation path? (Kill pane and respawn?)