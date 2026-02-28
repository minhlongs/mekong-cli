# TMUX & Node.js Automation Research

## TOPIC 1: `tmux capture-pane` Socket Contention
- **Mechanism**: `tmux` uses a single server process. All client commands (including `capture-pane`) communicate via a single UNIX socket (`/tmp/tmux-UID/default`).
- **Concurrent Calls**: Tmux queues concurrent socket requests. Under light load, parallel `capture-pane` calls resolve quickly. However, under heavy load (frequent fast polling across multiple panes + active UI rendering), the single-threaded event loop of the tmux server can become a bottleneck.
- **Freeze Risk**: High-frequency polling (e.g., `< 1s` interval across many workers) causes socket contention. If the server is busy handling massive I/O from pane processes, the `capture-pane` client commands can block or timeout, causing the caller (Node.js `execSync`) to freeze the Node.js event loop.
- **Best Practice**: Reduce polling frequency (e.g., 2s-3s instead of 500ms) or use `pipe-pane` to stream output asynchronously rather than synchronous `capture-pane` polling.

## TOPIC 2: `script` Command for CLI Capture
- **Mechanism**: macOS ships with the BSD version of `script`. It spawns a pseudo-terminal (PTY), tricks the child process into thinking it has a real TTY, and logs all bytes (including ANSI escape codes).
- **Syntax**: `script -q /tmp/output.log bash -c "command"` (`-q` = quiet mode).
- **Interactive Apps**: It **does** capture colored/ANSI output from interactive CLIs like Claude Code.
- **Drawbacks**:
  - Generates massive files full of ANSI control sequences, backspaces, and redraws (`^D`, `\033[K`, `\r`).
  - Parsing the raw file for specific text (e.g., "Cooked for") requires complex regex to strip ANSI.
  - Less interactive control compared to a live tmux pane.
- **Alternatives on macOS**: `unbuffer`, `socat`, and `stdbuf` are not installed by default on macOS and require Homebrew (`expect` package for `unbuffer`, `coreutils` for `stdbuf`).

## TOPIC 3: `fs.watch` vs `fs.stat` on macOS
- **fs.watch()**: Uses `kqueue` on macOS. It is highly efficient for detecting file modifications without polling. However, macOS `fs.watch` has known quirks (firing twice, or failing to fire for certain atomic writes or files in `/tmp`). In my test, watching a file in `/tmp` failed to emit an event on append.
- **fs.stat()**: Synchronous `fs.statSync()` is extremely fast. 100 calls take ~0ms.
- **Best Practice**: Given `fs.watch` unreliability on macOS, a low-frequency polling mechanism using `fs.stat()` or `fs.readFileSync()` every 1-3 seconds is actually safer and performant enough for log checking.

## TOPIC 4: tmux Rate Limiting Options
- **Legacy Options**: `c0-change-interval` and `c0-change-trigger` were removed in tmux 2.1+. They **do not exist** in modern tmux (v3.6a).
- **Modern Handling**: Tmux v2.1+ automatically implements rate limiting by dropping intermediate screen redraws when the pane is producing output faster than the terminal can render it.
- **Options left**: `status-interval` controls the status bar refresh rate, but doesn't affect the pane rendering rate.
- **Implication**: We cannot tweak tmux config to fix rate-limiting freezes. We must throttle our own polling in Node.js instead.

## Unresolved Questions
1. If `capture-pane` is slow due to socket contention, would using `pipe-pane -o` to stream the output to a file and having Node.js tail that file be significantly faster/safer?
2. How exactly does `execSync` timeout behave when the `tmux` command gets stuck? (Does Node throw immediately, or does the OS leave zombie processes?)