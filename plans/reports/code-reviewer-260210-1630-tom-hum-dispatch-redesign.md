# Code Review: Tom Hum Dispatch Redesign

## Code Review Summary

### Scope
- Files reviewed: 10
- Lines of code analyzed: 893
- Review focus: Full implementation of Tom Hum Dispatch Redesign (Phase 1-3)
- Plan: `plans/260210-1614-tom-hum-dispatch-redesign/`

### Overall Assessment

**Verdict: SOLID implementation** -- clean modular split, correct IPC protocol, no secrets in reviewed files. One high-priority gap (API key not available via launchd) and one medium concern (`pkill -x claude` kills ALL claude processes). The expect script exceeds 200-line rule at 314 lines but is justified by Tcl's lack of module system.

---

### Critical Issues

**[C-1] Hardcoded API keys in OTHER scripts (out of scope but flagged)**

Files NOT under review but detected by grep:
- `/Users/macbookprom1/mekong-cli/scripts/qwen_bridge.py` lines 22-23: hardcoded `sk-*` keys
- `/Users/macbookprom1/mekong-cli/scripts/start-telegram-bot.sh` line 16: hardcoded `GOOGLE_API_KEY`
- `/Users/macbookprom1/mekong-cli/scripts/tom-hum-cc.sh` line 18: hardcoded `API_KEY`

**Impact:** If these files are committed to git, API keys are exposed. Recommend rotating these keys and moving them to env vars or `~/.mekong/` key files.

---

### High Priority Findings

**[H-1] API key not available when running via launchd**

- `com.mekong.tom-hum-watcher.plist` does NOT set `ANTHROPIC_API_KEY` in `EnvironmentVariables`
- `brain-process-manager.js` line 30 reads `process.env.ANTHROPIC_API_KEY || ''`
- `tom-hum-launchd-install.sh` saves key to `~/.mekong/api-key` (line 42-43) but nothing reads it at runtime
- Plan Phase 3 stated preferred approach: "task-watcher reads `~/.mekong/api-key` at startup" -- **not implemented**
- **Result:** When launched via launchd, API key = empty string passed to expect/claude

**Mitigation options:**
1. Add API key read from `~/.mekong/api-key` in `brain-process-manager.js` `spawnBrain()`
2. Or inject the key into the installed plist via `sed` during `install_service()`

If Antigravity Proxy at 127.0.0.1:8080 handles auth internally, this may be non-blocking. Still fragile.

**[H-2] `pkill -x claude` kills ALL claude processes**

- `brain-process-manager.js` line 20: `execSync('pkill -x claude 2>/dev/null')`
- Kills every `claude` process on the system, not just the one managed by this script
- If user has other CC CLI sessions open, they will be terminated

**Recommendation:** Track the expect process PID and only kill its children, or remove this line entirely since the expect script already handles its own process.

---

### Medium Priority Improvements

**[M-1] Expect script at 314 lines exceeds 200-line rule**

The expect script is the longest file. Tcl lacks a native module system, so splitting is impractical. The duplicated debounce logic (wait_for_prompt vs mission completion detection) could theoretically be consolidated into a shared proc, but given Tcl scoping constraints, current approach is acceptable.

**[M-2] Fallback prompt pattern `> \s*$` may false-positive**

- `tom-hum-persistent-dispatch.exp` lines 93, 258: pattern `-re {> \s*$}`
- Could match HTML output lines ending with `>`, CLI output like `git log >`, etc.
- Debounce mitigates this, but a tighter pattern (e.g., anchored to beginning of line) would be safer

**[M-3] `generateNextTask()` in auto-cto-pilot.js has no try-catch**

- `auto-cto-pilot.js` line 53: `fs.writeFileSync(...)` -- if this throws, the exception propagates into `setInterval` callback
- Node.js won't crash on uncaught setInterval errors, but the auto-CTO cycle stops
- Wrapping in try-catch with log would make it more resilient

**[M-4] Hardcoded user path fallbacks in config.js**

- Line 3: `'/Users/macbookprom1/mekong-cli'` as fallback for `MEKONG_DIR`
- Line 9: `'/Users/macbookprom1/tom_hum_cto.log'` as fallback for `TOM_HUM_LOG`
- Acceptable for personal tool; would need parameterization for team use

**[M-5] `mission-dispatcher.js` timeout comparison is indirect**

- Line 63: `elapsed * 1000 > timeoutMs` where elapsed is in seconds
- Works correctly but `Date.now() - startTime > timeoutMs` is clearer
- Not a bug, just readability

---

### Low Priority Suggestions

**[L-1] `mission-dispatcher.js` re-requires child_process inside setInterval**

- Line 75: `const { execSync } = require('child_process')` inside the interval callback
- Node.js caches `require()` calls so no perf impact, but moving to top-level is cleaner

**[L-2] Emoji in log messages**

- Multiple files use emoji in log strings. Fine for human reading but may cause issues with log parsers expecting ASCII

**[L-3] `m1-cooling-daemon.js` cache deletion is aggressive**

- Line 39: `rm -rf ~/Library/Caches/com.apple.dt.* ~/Library/Caches/node* ~/Library/Caches/typescript`
- Intentional for thermal management, but could interfere with concurrent builds
- The `node*` glob is broad -- could match non-Node caches

**[L-4] Missing `isProcessing` reset on early return in task-queue.js**

- Lines 17-20: If `filePath` doesn't exist, function returns via `finally` block which does reset `isProcessing`
- Actually correct due to `finally` block -- no bug here

---

### Positive Observations

1. **Clean module separation**: task-watcher.js is 41 lines (target was <80). Each lib module has a single responsibility.
2. **Atomic file IPC**: `dispatchMission()` uses tmp+rename pattern -- correct POSIX atomic write for same-filesystem operations.
3. **No circular dependencies**: Dependency graph is acyclic (config <- brain <- mission <- task-queue, auto-cto; config <- m1-cooling).
4. **Graceful shutdown**: SIGTERM/SIGINT handlers in task-watcher.js properly kill the brain process before exit.
5. **Respawn rate limiting**: Expect script limits to 5 respawns/hour with 300s cooldown -- prevents restart storms.
6. **Debounce on prompt detection**: 500ms debounce + drain of post-debounce output prevents false completions during Opus 4.6 thinking pauses.
7. **launchd template uses placeholders**: `__NODE_PATH__`, `__MEKONG_DIR__`, `__HOME__` substituted at install time via `sed` -- good portability approach.
8. **Install script validates dependencies**: Checks for node binary, plist template, API key before installing.
9. **No secrets in any reviewed file**: API key sourced from env vars only in the reviewed scope.
10. **IPC protocol is consistent**: Mission file path `/tmp/tom_hum_next_mission.txt` and done file `/tmp/tom_hum_mission_done` match exactly between expect script constants and Node.js `config.js`.

---

### Race Condition Analysis (File IPC)

| Scenario | Risk | Assessment |
|----------|------|------------|
| Mission write/read | LOW | Atomic write (tmp+rename), single writer (Node), single reader (expect) |
| Done file write/read | LOW | Single writer (expect), single reader (Node), poll-based |
| Mission file deleted before read | NONE | Expect reads then deletes atomically in sequence |
| Done file cleared prematurely | LOW | `dispatchMission()` clears done file before writing mission; no active mission at that point |
| Concurrent task processing | NONE | `isProcessing` mutex in Node.js single-thread event loop |
| State file (auto-CTO) | LOW | Single reader/writer, no external access |

**Verdict:** No race conditions identified. Single-writer/single-reader design with atomic writes is correct for this use case.

---

### Task Completeness Verification

| Phase | Task | Status |
|-------|------|--------|
| 1 | Write expect script with prompt detection | DONE |
| 1 | ANSI-aware prompt regex (UTF-8 + fallback) | DONE |
| 1 | Debounce logic (500ms) | DONE |
| 1 | Crash recovery (respawn with --continue) | DONE |
| 1 | Respawn rate limiting (5/hour) | DONE |
| 1 | Mission timeout (2700s in expect, 45min in Node) | DONE |
| 2 | config.js | DONE |
| 2 | brain-process-manager.js | DONE |
| 2 | mission-dispatcher.js with atomic writes | DONE |
| 2 | task-queue.js | DONE |
| 2 | auto-cto-pilot.js | DONE |
| 2 | m1-cooling-daemon.js | DONE |
| 2 | task-watcher.js as thin orchestrator (<80 lines) | DONE (41 lines) |
| 2 | No hardcoded API keys in reviewed files | DONE |
| 3 | Plist template with placeholders | DONE |
| 3 | Install script (install/uninstall/status/restart/logs) | DONE |
| 3 | API key NOT stored in plist | DONE (but runtime path incomplete -- see H-1) |

**All code deliverables present.** One gap: API key runtime access from launchd context (H-1).

---

### Recommended Actions

1. **[HIGH]** Fix API key availability for launchd: read `~/.mekong/api-key` in `brain-process-manager.js` or inject into plist during install
2. **[HIGH]** Replace `pkill -x claude` with targeted PID kill or remove entirely
3. **[MEDIUM]** Wrap `generateNextTask()` body in try-catch in `auto-cto-pilot.js`
4. **[MEDIUM]** Tighten fallback prompt regex `> \s*$` to reduce false-positive risk
5. **[LOW]** Move `require('child_process')` to top-level in `mission-dispatcher.js`
6. **[CRITICAL/OUT-OF-SCOPE]** Rotate and remove hardcoded keys in `qwen_bridge.py`, `start-telegram-bot.sh`, `tom-hum-cc.sh`

### Metrics

| Metric | Value |
|--------|-------|
| Files under 200 lines | 9/10 (expect script 314 -- justified) |
| Hardcoded secrets (in scope) | 0 |
| Hardcoded secrets (out of scope) | 3 files with keys |
| Race conditions identified | 0 |
| Circular dependencies | 0 |
| IPC protocol consistency | 100% match |

---

### Unresolved Questions

1. Does Antigravity Proxy at `127.0.0.1:8080` handle API key injection? If yes, H-1 is non-blocking.
2. Is `pkill -x claude` intentional to ensure clean state, or should it only kill the managed process?
3. Should the expect script's fallback prompt pattern `> \s*$` be tightened, or is the debounce sufficient protection?
