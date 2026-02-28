# Code Review: Tom Hum CTO AGI Deep Upgrade

**Date:** 2026-02-27
**Scope:** 14 new modules + 8 modified modules + task-watcher.js wiring
**LOC changed:** ~3,200 lines across 23 files
**Focus:** Module decomposition of brain-process-manager.js monolith

---

## Overall Assessment

The decomposition of the 56KB `brain-process-manager.js.bak` monolith into 14 focused sub-modules is architecturally sound. The backward-compatible facade pattern (`brain-process-manager.js` re-exports) preserves the public API. Circular dependencies are avoided (all modules load cleanly via `node -e require()`). The new modules add real observability (health server, heartbeat, circuit breaker, AGI score calculator).

**Verdict:** Solid refactor with 5 critical/high issues to address.

---

## Critical Issues

### C1. Duplicate `isShellPrompt` function (DRY violation)

**Files:**
- `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-spawn-manager.js` (lines 107-117)
- `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-state-machine.js` (lines 172-182)

Both contain identical implementations. `brain-mission-runner.js` imports from `brain-spawn-manager`, but the canonical location should be `brain-state-machine.js` (state detection module). If either diverges during future edits, silent bugs result.

**Fix:** Delete from `brain-spawn-manager.js`, re-export from `brain-state-machine.js`:
```js
// brain-spawn-manager.js — remove lines 107-117, add:
const { isShellPrompt } = require('./brain-state-machine');
```

### C2. Duplicate `generateClaudeCommand` function

**Files:**
- `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-boot-sequence.js` (lines 18-30)
- `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-spawn-manager.js` (lines 62-74)

Identical function inlined in both files. Comment on line 17 of `brain-boot-sequence.js` says "Inlined here to avoid circular dependency with brain-spawn-manager.js" but `brain-boot-sequence.js` does NOT require `brain-spawn-manager.js`, so no circular exists. Both files already require `brain-logger` and `brain-tmux-controller`.

**Fix:** Remove from `brain-boot-sequence.js`, import from `brain-spawn-manager.js`:
```js
const { generateClaudeCommand } = require('./brain-spawn-manager');
```

### C3. Hardcoded user path throughout codebase

**Files:** `brain-boot-sequence.js` (lines 20, 25, 88-89, 101-102, 120, 124-125), `brain-spawn-manager.js` (lines 64, 70), `learning-engine.js` (line 26)

Paths like `/Users/macbookprom1/.claude_antigravity_pro` and `/Users/macbookprom1/tom_hum_cto.log` are hardcoded instead of using `config.js` or `process.env.HOME`. This makes the code non-portable and exposes the username in source.

**Fix:** Use `config.js` constants or `path.join(os.homedir(), ...)`:
```js
const CLAUDE_PRO_DIR = path.join(os.homedir(), '.claude_antigravity_pro');
```

---

## High Priority

### H1. `TMUX_SESSION_PRO` and `TMUX_SESSION_API` are identical

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-tmux-controller.js` (lines 15-16)

```js
const TMUX_SESSION_PRO = `${config.TMUX_SESSION}:brain`;
const TMUX_SESSION_API = `${config.TMUX_SESSION}:brain`;
```

Both point to the same session string. `brain-mission-runner.js` routes planning tasks to `TMUX_SESSION_PRO` and execution to `TMUX_SESSION_API` (line 59), but since they are identical, the intent-based routing has no effect. If the intent is dual-pane (pane 0 vs pane 1 within same session), the session name being identical is correct, but then the variable naming is misleading. If the intent is separate sessions, this is a bug.

**Fix:** Either:
- Remove `TMUX_SESSION_API` and use only `TMUX_SESSION_PRO` (since they are the same)
- Or if separate sessions were intended, fix the value

### H2. `evolution-engine.js` `loadHistory` not exported for `brain-supervisor.js`

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/evolution-engine.js` (line 413)

`brain-supervisor.js` (line 286) calls `require('./evolution-engine').loadHistory()`. However, checking the exports on line 413:

```js
module.exports = { checkEvolutionTriggers, generateSkill, optimizeTokenRouting, triggerBrainSurgery, getEvolutionScore, loadState };
```

`loadHistory` IS NOT in the export list. `loadState` is exported, but `loadHistory` is not. This will cause `loadHistory` to be `undefined` at runtime.

**Fix:** Add `loadHistory` to exports:
```js
module.exports = { checkEvolutionTriggers, generateSkill, optimizeTokenRouting,
  triggerBrainSurgery, getEvolutionScore, loadState, loadHistory };
```

### H3. `circuit-breaker.js` imports `log` from wrong module

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/circuit-breaker.js` (line 2)

```js
const { log } = require('./brain-process-manager');
```

All new modules were refactored to use `brain-logger.js` as the canonical logging source. `circuit-breaker.js` still imports from the facade. While it works (facade re-exports `log`), it creates an unnecessary dependency on the facade instead of the leaf logger module.

**Fix:**
```js
const { log } = require('./brain-logger');
```

### H4. Files exceeding 200-line limit

| File | Lines | Over by |
|------|-------|---------|
| `auto-cto-pilot.js` | 610 | 410 |
| `evolution-engine.js` | 420 | 220 |
| `task-watcher.js` | 371 | 171 |
| `brain-supervisor.js` | 334 | 134 |
| `task-queue.js` | 292 | 92 |
| `brain-mission-runner.js` | 289 | 89 |

The `auto-cto-pilot.js` is 3x the limit. `evolution-engine.js` is 2x. Both are candidates for further decomposition:
- `auto-cto-pilot.js`: Extract error parsers (`parseBuildErrors`, `parseLintErrors`, `parseTestErrors`) into `cto-error-parsers.js`
- `evolution-engine.js`: Extract `generateSkill` and `optimizeTokenRouting` into `evolution-skill-factory.js`
- `task-watcher.js`: Extract WAL recovery and boot self-heal into `boot-recovery.js`

---

## Medium Priority

### M1. 25+ modules define their own `log()` function

25 modules in `lib/` define local `function log(msg)` with varying formats instead of using `brain-logger.js`. Examples: `brain-supervisor.js`, `evolution-engine.js`, `learning-engine.js`, `self-healer.js`.

This means log output from different modules has inconsistent timestamps and prefixes, making debugging harder.

**Fix:** Gradually migrate all modules to `const { log } = require('./brain-logger')`.

### M2. `brain-output-hash-stagnation-watchdog.js` uses inline require in hot path

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-output-hash-stagnation-watchdog.js` (lines 31, 52, 59, 64)

Uses `require('./brain-tmux-controller')` and `require('./brain-respawn-controller')` inside async functions that run every 60s. While Node.js caches requires, this pattern is fragile and can mask circular dependency issues.

**Fix:** Move requires to top-level with lazy-init pattern or document why inline.

### M3. `brain-health-server.js` binds to `127.0.0.1` only

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-health-server.js` (line 102)

Binds to `127.0.0.1` which is correct for security (localhost only). However, the optional Bearer token auth (line 18-21) accepts empty token as "auth disabled". This is documented but worth noting: if someone port-forwards 9090, no auth is required by default.

No action needed unless deploying remotely.

### M4. `brain-respawn-controller.js` clears ALL timestamps after cooldown

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-respawn-controller.js` (line 50)

```js
respawnTimestamps.length = 0;
```

After rate-limit cooldown, ALL timestamps are wiped. This means immediately after cooldown, 5 rapid respawns could happen before the rate limiter kicks in again. Should only remove timestamps older than 1 hour.

**Fix:**
```js
const cutoff = Date.now() - 3600000;
while (respawnTimestamps.length > 0 && respawnTimestamps[0] < cutoff) respawnTimestamps.shift();
```

### M5. `brain-system-monitor.js` uses blocking `execSync('sleep ...')` for cooling

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-system-monitor.js` (line 38)

```js
execSync(`sleep ${coolingTime / 1000}`);
```

This blocks the entire Node.js event loop for 10 seconds when `isOverheating()` is called. While the comment says "Intentionally block to force system slowdown," this freezes ALL event listeners, timers, and the health server during the block.

**Fix:** Use `await new Promise(r => setTimeout(r, coolingTime))` in an async wrapper.

---

## Positive Observations

1. **Clean module decomposition**: The monolith split follows single-responsibility well. `brain-logger.js` (leaf node, no deps on other brain-* modules) is correctly at the bottom of the dependency tree.
2. **Backward-compatible facade**: `brain-process-manager.js` is now a 37-line re-export shell. All existing consumers continue working without changes.
3. **No circular dependencies**: Verified by requiring all 14 new modules in sequence -- all load without errors.
4. **Circuit breaker pattern**: Proper state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED) with configurable thresholds.
5. **Heartbeat mechanism**: Simple and effective file-based liveness check with age-based staleness detection.
6. **AGI score calculator**: Pure function, no side effects, easy to test. 5 dimensions x 20 pts scoring is well-structured.
7. **Health server**: Proper HTTP status codes (503 for critical, 200 for ok), Prometheus-compatible `/metrics` endpoint, optional Bearer auth.
8. **DLQ (Dead Letter Queue)**: Good fault-tolerance pattern for missions that exhaust retries.
9. **Write-ahead log (WAL)**: Crash recovery for in-flight missions in `task-watcher.js`.

---

## Recommended Actions (Priority Order)

1. **[CRITICAL]** Fix `loadHistory` missing from `evolution-engine.js` exports (H2) -- runtime error when brain-supervisor checks success rate
2. **[CRITICAL]** Deduplicate `isShellPrompt` -- choose `brain-state-machine.js` as canonical (C1)
3. **[CRITICAL]** Deduplicate `generateClaudeCommand` -- keep in `brain-spawn-manager.js` only (C2)
4. **[HIGH]** Fix `circuit-breaker.js` log import to use `brain-logger` (H3)
5. **[HIGH]** Clarify or fix `TMUX_SESSION_PRO` = `TMUX_SESSION_API` identity (H1)
6. **[HIGH]** Split `auto-cto-pilot.js` (610 lines) -- extract error parsers to stay under 200 lines (H4)
7. **[MEDIUM]** Fix respawn timestamp clearing to be time-based, not full wipe (M4)
8. **[MEDIUM]** Replace `execSync('sleep ...')` blocking call with async (M5)
9. **[LOW]** Migrate remaining modules to centralized `brain-logger.js` (M1)
10. **[LOW]** Move hardcoded paths to `config.js` (C3) -- lower priority since this is a local daemon

---

## Unresolved Questions

1. Are `TMUX_SESSION_PRO` and `TMUX_SESSION_API` intentionally identical? The dual-pane architecture uses pane indices (0, 1) within the same session, so same session name may be correct, but the naming suggests separate sessions.
2. Should the health server port (9090) be registered in `config.js` alongside the proxy port (9191)?
3. The `brain-boot-sequence.js` copies OAuth credentials from `~/.claude/` to sandbox profiles on every boot (lines 118-131). Is this secure if the daemon runs unattended? Credentials are copied to disk in plaintext.
