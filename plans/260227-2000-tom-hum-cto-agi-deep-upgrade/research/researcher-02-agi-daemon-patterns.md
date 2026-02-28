# Research: AGI-Level Self-Healing Daemon Patterns
**Date:** 2026-02-27 | **Role:** Researcher-02 | **Focus:** Industry patterns for 100/100 resilience

---

## 1. Current State (Tôm Hùm as-is)

**Score: ~70/100.** Three healing layers exist but have critical gaps:

| Layer | Implemented | Gap |
|-------|-------------|-----|
| Process health | tmux has-session, pgrep | No heartbeat file; death detected reactively not proactively |
| Mission health | Stale lock check (30min) | Lock stale threshold too high; no output-hash watchdog active |
| Recovery | clearStaleLocks + respawn | `restartProxy()` is a NO-OP (logs "skip" and returns false) |
| Perception | `perception-engine.js` sweeps CPU/disk/mem/proxy | Not wired into mission dispatch gating |
| Self-healer monitor | `setInterval` every 5min | Only checks stale lock + proxy; does NOT kick stuck brain |

**Root cause of "gets stuck":** Brain (tmux pane) may be alive but frozen (TUI Purgatory, context hang, infinite spinner). The 5-minute monitor only checks the lock file age, never injects a wakeup or confirms output progression.

---

## 2. Proven Industry Patterns

### 2.1 Erlang OTP Supervisor Trees (Gold Standard)
- **OneForOne:** restart only the crashed child; other workers continue
- **OneForAll:** restart all children when one fails (for tightly coupled state)
- **RestForOne:** restart failed child + all siblings started after it
- **Key insight:** Each process has a `max_restarts` within `max_seconds` window; exceeding = supervisor itself crashes upward to parent → "let it crash" philosophy

**Apply to Tôm Hùm:**
- `task-watcher.js` = root supervisor
- `brain-process-manager` = child worker (OneForOne restart)
- `mission-dispatcher` = sibling that must NOT restart when brain crashes
- Implement restart budget: max 3 respawns per 10 minutes, then escalate

### 2.2 Heartbeat + Watchdog Timer (Embedded/Industrial)
- Worker writes timestamp to shared file every N seconds ("I'm alive")
- Watchdog reads file; if timestamp older than 2×N → declare dead → kill & restart
- **Anti-livelock:** worker that hangs indefinitely still fails heartbeat even if process is running
- Used by: systemd (sd_notify + WatchdogUSec), Kubernetes liveness probes, PostgreSQL postmaster

**Apply to Tôm Hùm:**
- brain-process-manager writes `HEARTBEAT_FILE=/tmp/tom_hum_heartbeat` every 30s during mission
- self-healer checks heartbeat age; if >90s → force respawn (currently doesn't exist)
- This catches: frozen tmux panes, infinite CC CLI spinner, proxy deadlock

### 2.3 Output Progress Hashing (Stale Detection)
- Hash last N bytes of stdout every 60s
- Two identical hashes in a row → output stagnant → trigger kickstart
- Three identical hashes → escalate to hard restart
- **Already designed** in SELF_HEALING_EVOLUTION.md §2.3 but NOT wired into self-healer.js monitor loop

**Critical gap:** `self-healer.js::healthCheck()` does NOT call any output hash check. The heartbeat + hash check must be added to the 5-min interval.

### 2.4 Circuit Breaker (Netflix Hystrix pattern)
States: `CLOSED` → `OPEN` → `HALF_OPEN`
- CLOSED: normal operation
- OPEN: after N failures, stop calling failing service, return fallback immediately
- HALF_OPEN: after cooldown, allow one probe call; success → CLOSED, fail → OPEN
- **Prevents:** retry storms, cascading failures, wasted quota on dead endpoints

**Apply to Tôm Hùm:**
- Proxy circuit breaker: after 3 consecutive HTTP 5xx → OPEN (skip missions, alert Telegram)
- Model circuit breaker: after 3 `model_not_found` → OPEN on that model, force fallback
- Missing entirely from current codebase

### 2.5 Dead Letter Queue (DLQ)
- Poison pill missions (those that crash CC CLI repeatedly) get moved to DLQ
- DLQ reviewed after cooldown or manually by operator
- Prevents: single bad task file from looping and burning quota
- Redis, AWS SQS, RabbitMQ all implement this natively

**Apply to Tôm Hùm:**
- `task-queue.js` needs a `tasks/dead-letter/` directory
- After 3 failed attempts on same mission file → move to dead-letter, send Telegram alert
- Currently: failed missions go back to active queue or stay as zombie lock

### 2.6 Health Check Endpoint (HTTP Probe)
- Expose `GET /health` returning JSON: `{status, uptime, missionCount, lastHeartbeat, brainAlive}`
- External monitor (cron, launchd, Telegram bot) can poll it
- Enables: external watchdog (if even the Node process dies, nothing restarts it)

**Apply to Tôm Hùm:**
- Add tiny HTTP server (8 lines with Node `http` module) on port 9090
- launchd plist already exists (`com.mekong.9router.plist`) — extend for Tôm Hùm
- `curl localhost:9090/health` from cron every 2min; if fail → `launchctl kickstart` the daemon

### 2.7 Supervisor-Monitored Timers (Go/Kubernetes pattern)
- Each long-running operation registers a deadline
- Supervisor goroutine / controller loop cancels operation after deadline
- Prevents: infinite waits on external API, hung `execSync` calls

**Apply to Tôm Hùm:**
- `brain-process-manager::runMission()` has `MISSION_TIMEOUT_MS` (45min) — good
- BUT timeout only applies to `claude -p` subprocess; if direct mode hangs before spawning → no timeout
- Add per-phase timeouts: spawn timeout (30s), first-output timeout (60s), idle timeout (90s)

---

## 3. Gap Analysis: Current vs AGI 100/100

| Pattern | Status | Priority |
|---------|--------|----------|
| Heartbeat file (worker→watchdog) | MISSING | P0 — prevents ghost brain |
| Output progress hash watchdog | DESIGNED, NOT WIRED | P0 — prevents frozen spinner |
| Proxy NO-OP restart | BUG (restartProxy returns false) | P0 — recovery broken |
| Dead Letter Queue | MISSING | P1 — prevents poison pill loops |
| Circuit Breaker for proxy/model | MISSING | P1 — prevents quota burn |
| Health HTTP endpoint | MISSING | P1 — enables external watchdog |
| Per-phase timeouts | PARTIAL (mission-level only) | P2 |
| Erlang-style restart budgets | PARTIAL (MAX_RESPAWNS_PER_HOUR) | P2 |
| Perception engine wired to gating | DESIGNED, NOT WIRED | P2 |

---

## 4. Recommended Implementation Order

1. **Fix `restartProxy()` NO-OP** — single line fix, unblocks all recovery paths
2. **Add heartbeat file** in `runMission()` + heartbeat-age check in `healthCheck()` (replace 5min with 90s interval)
3. **Wire output-hash stagnation check** into `healthCheck()` → sends `\n` kickstart on stale
4. **Implement DLQ** in `task-queue.js` — move missions failing >2x to `tasks/dead-letter/`
5. **Add circuit breaker** in `mission-recovery.js` — 3-strike rule per model/proxy
6. **Add health HTTP endpoint** (port 9090) — 8 lines in `task-watcher.js`

---

## 5. Node.js-Specific Considerations

- `setInterval` drifts under load; use `setTimeout` recursion or `node-cron` for precise intervals
- `execSync` in health checks can block event loop; always set `timeout:5000` (already done)
- Uncaught promise rejections in health loop kill daemon silently — wrap all async health checks in try/catch
- `fs.watch` misses events on macOS for `tasks/` dir — current codebase uses polling fallback (good)

---

## Unresolved Questions

- Should DLQ missions auto-retry after 24h, or require manual review?
- Heartbeat file approach vs. in-memory timestamp: file survives process restart, but adds I/O; for M1 SSD this is negligible.
- Should the health HTTP endpoint authenticate (bearer token) to prevent accidental exposure?
