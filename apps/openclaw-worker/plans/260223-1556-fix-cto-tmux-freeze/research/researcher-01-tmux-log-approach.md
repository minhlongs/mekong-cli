# TMUX Socket Contention & Terminal Logging Research

## 1. TMUX Socket Contention & Freeze Root Cause

### The Problem
Polling `tmux capture-pane` at high frequencies (like every 500ms) causes severe performance issues and freezing in `tmux`.
- **Why:** `tmux` uses a single Unix domain socket (`/tmp/tmux-UID/default`) per server process for all IPC (Inter-Process Communication).
- **Socket Contention:** Every `tmux capture-pane` command spawns a new client process that connects to this socket, asks the server for pane content, waits for the response, and disconnects.
- **The Freeze:** When multiple processes rapidly poll the socket while the server is simultaneously trying to process heavy terminal I/O (e.g., streaming LLM output), the single-threaded event loop becomes completely saturated handling IPC requests. This blocks terminal drawing and command execution, causing the UI to freeze entirely.

### Safe Polling Interval
- **Documented Safe Limit:** There is no hardcoded "safe" limit, but general consensus and script authors suggest polling no faster than every **2000ms (2 seconds)** for basic status line updates, and **3000ms-5000ms** for full pane captures during heavy output.
- **Current Mitigation:** The codebase currently uses `TMUX_MIN_GAP_MS = 5000` (5s), which is a safe throttle but causes severe UI lag (status dashboard only updates every 5s).

## 2. The `script` Command Alternative

Using the `script` command bypasses `tmux` IPC entirely by teeing the pseudo-terminal (PTY) output directly to a file at the OS level.

### macOS vs Linux Differences
The syntax differs significantly between macOS (BSD) and Linux (util-linux):

- **macOS (BSD `script`):**
  - Syntax: `script -q /path/to/log.txt command_to_run`
  - `-q`: Quiet mode (suppresses "Script started on..." header)
  - No need for `-c` flag (it takes the command directly as trailing arguments).
  - Timing: Flushes buffer on newline or after a short delay.

- **Linux (util-linux `script`):**
  - Syntax: `script -q -c "command_to_run" /path/to/log.txt`
  - Requires `-c` flag to specify the command.
  - Requires `--flush` or `stdbuf` to prevent heavy buffering (otherwise output won't appear in the file until the process exits).

### Non-blocking Tail Reading in Node.js
To read the log file efficiently without polling the filesystem:
```javascript
const fs = require('fs');
// Read last N bytes instead of reading the whole file into memory
function getTail(filepath, bytes = 4096) {
  try {
    const stats = fs.statSync(filepath);
    const size = stats.size;
    if (size === 0) return '';
    const readLen = Math.min(bytes, size);
    const buf = Buffer.alloc(readLen);
    const fd = fs.openSync(filepath, 'r');
    fs.readSync(fd, buf, 0, readLen, size - readLen);
    fs.closeSync(fd);
    return buf.toString('utf-8');
  } catch (e) { return ''; }
}
```

## 3. TMUX Rate Limit Options (c0-change)

### The Options
- `c0-change-trigger`: The number of C0 control characters (like newlines `\n` or backspaces `\b`) the pane receives before rate-limiting kicks in.
- `c0-change-interval`: The time window (in milliseconds) in which the trigger count must be reached to activate rate-limiting.

### How They Prevent Freezes
When a terminal program spams heavy output (like npm installs or LLM text streams), `tmux` tries to render every single frame. This consumes massive CPU and blocks the socket.
By setting these options, `tmux` detects rapid output bursts and temporarily stops redrawing the terminal pane. Instead, it processes the text in the background and only updates the screen periodically (usually every 100ms-250ms), drastically reducing CPU load and keeping the IPC socket responsive.

### Correct Syntax
```bash
# Triggers rate limiting if 50 control characters are received within 300ms
tmux set-option -g c0-change-interval 300
tmux set-option -g c0-change-trigger 50
```
*Note: These options were introduced in tmux 1.7, but their behavior changed in tmux 2.1 (which introduced a new backoff algorithm), making manual c0-change options obsolete or ignored in newer versions (>2.1). Instead, modern tmux uses an automatic backoff algorithm for pane output.*

## Unresolved Questions
1. Does the macOS version of `script -q` buffer output for interactive CLI tools like `claude`, preventing real-time parsing? (May require `stdbuf -o0 script...` or `PTY` wrapper).
2. Since `c0-change-*` options are obsolete in modern `tmux` (macOS usually ships tmux 3.x via brew), is there a modern equivalent, or is the `script` log file approach strictly superior?

Sources:
- [Tmux IPC and Socket Contention (StackOverflow)](https://stackoverflow.com/questions/59109043/tmux-performance-issues-when-running-capture-pane-frequently)
- [macOS BSD script man page](https://keith.github.io/xcode-man-pages/script.1.html)
- [Tmux Changelog (c0-change removal in 2.1)](https://raw.githubusercontent.com/tmux/tmux/master/CHANGES)