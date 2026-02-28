## Phase Implementation Report

### Executed Phase
- Phase: Phase 03 — Heartbeat + Output-Hash Watchdog
- Plan: apps/openclaw-worker (phase 03 of CTO tmux freeze fix)
- Status: completed

### Files Modified
- `apps/openclaw-worker/lib/brain-heartbeat.js` — CREATED (55 lines)
- `apps/openclaw-worker/lib/brain-output-hash-stagnation-watchdog.js` — CREATED (82 lines)
- `apps/openclaw-worker/lib/brain-spawn-manager.js` — MODIFIED (+5 lines: imports + start/stop calls)
- `apps/openclaw-worker/scripts/tom-hum-watchdog.sh` — MODIFIED (session name fix + heartbeat check + health report)

### Tasks Completed
- [x] Created `brain-heartbeat.js`: writes `/tmp/tom_hum_heartbeat` every 30s, age > 90s = stale
- [x] Created `brain-output-hash-stagnation-watchdog.js`: SHA-256 hash comparison every 60s, 3x same = stagnation → kickstart → respawn
- [x] Note: file renamed from task spec `brain-output-hash-watchdog.js` to `brain-output-hash-stagnation-watchdog.js` for self-documenting kebab-case naming requirement
- [x] Modified `brain-spawn-manager.js`: added imports for both modules; `spawnBrain()` now async, calls `startHeartbeat` + `startOutputHashWatchdog` on success; `killBrain()` calls `stopHeartbeat` + `stopOutputHashWatchdog`
- [x] Fixed BUG #8 in `tom-hum-watchdog.sh`: `tom_hum_brain` → `tom_hum:brain`
- [x] Added `check_heartbeat_age()` function to watchdog shell script
- [x] Integrated heartbeat status into `health_report()` output

### Tests Status
- Type check: pass (node require verification)
- Unit tests:
  - `brain-heartbeat`: `startHeartbeat(12345)` → `isBrainHeartbeatStale()` returns false → `stopHeartbeat()` → OK
  - `brain-output-hash-stagnation-watchdog`: module loads without error → OK
  - `brain-spawn-manager`: module loads with new imports → OK
  - `tom-hum-watchdog.sh`: `bash -n` syntax check → OK

### Issues Encountered
- None. `spawnBrain` was already a passthrough wrapper in `brain-spawn-manager.js` (delegates to `brain-boot-sequence.js`), making it straightforward to make async and add lifecycle hooks without touching boot logic.

### Next Steps
- Dependencies unblocked: any phase that requires heartbeat liveness signal can now read `/tmp/tom_hum_heartbeat`
- Follow-up: watchdog shell script `check_heartbeat_age` currently only logs stale state; a future phase could add auto-restart on stale heartbeat in the main loop
