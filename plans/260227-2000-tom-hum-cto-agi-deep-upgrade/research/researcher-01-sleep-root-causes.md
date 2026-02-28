# Tôm Hùm Sleeping/Stuck Root Causes

**Date:** 2026-02-27 | **Scope:** `apps/openclaw-worker/lib/`

---

## Files Analyzed

- `brain-process-manager.js` — brain spawn, tmux state machine, runMission
- `task-queue.js` — fs.watch, poll, queue processing
- `mission-dispatcher.js` — prompt build, executeTask, retry loop
- `self-healer.js` — monitor loop, lock detection
- `brain-supervisor.js` — 60s escalation loop
- `auto-cto-pilot.js` — scheduling, LLM-vision gate, phase routing

---

## Root Causes (Priority Order)

### 1. State Machine Completion False Negatives (HIGH)

**File:** `brain-process-manager.js` ~line 985

The `runMission()` state machine REQUIRES:
- (a) cooked-pattern match, OR
- (b) `wasBusy = true` then 3 consecutive IDLE polls, OR
- (c) Never BUSY, elapsed > 45s, then 6 consecutive IDLE polls

**Problem:** `BUSY_PATTERNS` are Claude's animated spinner text (`Thinking`, `Sautéing`, `Frolicking`, etc.). If CC CLI via Antigravity Proxy responds immediately **without ever showing a spinner** (fast API), `wasBusy` stays `false`. The daemon then requires 6× idle confirms before failing, adding 3–4min of wait before aborting with `failed_to_start`. Queue is **blocked for the full duration**.

**Impact:** Each missed BUSY state = 3+ min daemon freeze before recovery path triggers.

---

### 2. Anti-Stack Pre-Dispatch Loop (18 × 10s = 3 min blocking) (HIGH)

**File:** `brain-process-manager.js` ~line 800

Before dispatching any mission, the code runs a **synchronous blocking loop** (up to 18 attempts × 10s sleep each = **180s max**) waiting for CC CLI to become non-busy. If compaction runs > 3min, it sends `/clear` and waits 10s more.

During this time:
- `activeCount` in `task-queue.js` is already incremented (line 39)
- No other task can start (dual-stream cap = 2, but 1 slot is stuck in pre-dispatch)
- The queue appears "full" even though no real work is happening

**Impact:** A compaction stall → daemon appears dead for up to 5+ min.

---

### 3. Silent Catch in task-queue.js Poll (LOW-MEDIUM)

**File:** `task-queue.js` line 219

```js
} catch (e) { }  // ← silent, no log
```

If `fs.readdirSync(config.WATCH_DIR)` throws (permissions issue, dir deleted, disk error), the poll silently swallows the error. `fs.watch` watcher may also silently stop on macOS under heavy I/O. If both fail simultaneously → **no task detection, daemon appears sleeping indefinitely**.

---

### 4. `isBrainAlive()` Weak Detection (MEDIUM)

**File:** `brain-process-manager.js` line 577

Uses `tmux has-session` only. Does NOT check if CC CLI is actually running inside the session (tmux session can exist with a dead/crashed CC CLI inside). `isShellPrompt()` check is a fallback — but only runs at mission dispatch time, not proactively.

**Gap:** CC CLI crashes between missions → tmux session alive → `isBrainAlive()` returns `true` → next mission dispatched into a dead shell → stuck forever until `failed_to_start` timeout (6 × idle confirms ≈ unknown duration).

---

### 5. Brain Supervisor Blind Spot for Direct-Mode Brain (MEDIUM)

**File:** `brain-supervisor.js` line 252

Supervisor's stuck detection (`isBusy() || isAtPrompt()`) reads **tmux pane**. But per CLAUDE.md, the default brain mode is `direct` (claude -p as child process). The supervisor was written for `tmux` mode.

**Gap:** In `direct` mode, pane capture returns empty or stale → supervisor always sees "neither busy nor at prompt" → `stuckSince` timer starts → triggers premature respawn (after 20min) even when a claude -p process is running normally.

---

### 6. `auto-cto-pilot.js` LLM Vision Gate Failure Cascades to Full Stop (MEDIUM)

**File:** `auto-cto-pilot.js` line 367

```js
} catch (innerE) {
  log(`[LLM-VISION][P${pIdx}] Capture failed: ${innerE.message}`);
  if (pIdx === 1) isApiBusy = true;  // ← assume busy on error
}
```

If the LLM interpreter (`interpretState`) fails (proxy down, timeout, rate limit), `isApiBusy` is set `true`. Auto-CTO then skips the current cycle and reschedules with no task generation. If this persists, Auto-CTO **never generates tasks** → queue stays empty → daemon idles indefinitely.

---

### 7. `self-healer.js` Not Actually Restarting Anything (LOW)

**File:** `self-healer.js` lines 58-61, 179-181

`restartProxy()` logs "skip auto-restart" and returns `false`. `healthCheck()` detects proxy down but the restart line is **commented out**. The healer can detect stuck locks but cannot recover the most critical failure modes (brain death, proxy down).

---

### 8. `activeCount` Leak if Exception in `processQueue()` (MEDIUM)

**File:** `task-queue.js` lines 50-177

The `finally` block at line 171 decrements `activeCount`. However, if `executeTask()` itself hangs indefinitely (e.g., `runMission()` awaiting a dead tmux session), the `finally` never runs. With `MAX_ACTIVE = 2`, both slots become permanently occupied → queue stuck permanently.

`runMission()` has a `timeoutMs`-based deadline loop, so in theory this resolves. But timeouts for complex missions are 45min → the queue appears dead for up to 45min per slot.

---

## Dead State Summary Table

| Scenario | Where It Happens | Dead Duration |
|---|---|---|
| Proxy spinner never fires (no BUSY) | runMission state machine | 3–5min per mission |
| Compaction stall (>3min) | anti-stack pre-dispatch loop | 3–5min per mission |
| fs.watch silent death | task-queue poll catch | Infinite (until restart) |
| CC CLI in dead shell | isBrainAlive() false positive | 45min (mission timeout) |
| LLM Vision error → isApiBusy=true | auto-cto-pilot | Indefinite (no tasks generated) |
| activeCount leak / 45min timeout | processQueue finally | 45min × 2 slots = 90min |

---

## Key Missing Health Checks

1. **No heartbeat mechanism** — daemon never writes a "last-alive" timestamp; external monitor cannot distinguish healthy/sleeping.
2. **No queue watchdog** — nothing detects "queue non-empty but activeCount=0 for >N minutes."
3. **No CC CLI process-level check** — `isBrainAlive()` checks tmux, not the CC CLI PID inside.
4. **Self-healer not integrated** — `preFlightCheck()` and `startMonitor()` are imported but the monitor's recovery actions are stubs.

---

## Unresolved Questions

1. In `direct` mode (default), does brain-supervisor cause premature respawns due to empty pane capture?
2. What is the actual `POLL_INTERVAL_MS` value from config? If > 5s, file detection lag may compound queue stalls.
3. Is `llm-interpreter.js` (`interpretState`) hitting rate limits on the proxy? If so, Auto-CTO is always throttled.
4. Are there any concurrent file writes to `tasks/` directory causing `fs.watch` to misbehave on macOS APFS?
