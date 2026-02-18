## Phase Implementation Report

### Executed Phase
- Phase: Remove ALL tmux from Tom Hum daemon
- Plan: Direct task (no plan directory)
- Status: completed

### Files Deleted
- `scripts/tom-hum-autonomous-daemon-launcher.sh` — tmux daemon launcher
- `scripts/tom-hum-dispatch.exp` — expect dispatch script
- `.claude/commands/tom-hum.md` — /tom-hum ClaudeKit command

### Files Modified
- `apps/openclaw-worker/lib/brain-process-manager.js` (635 -> 139 lines) — gutted to external-only mode
- `apps/openclaw-worker/config.js` (59 -> 52 lines) — removed 7 tmux/brain-mode configs
- `apps/openclaw-worker/task-watcher.js` (76 lines, 1 comment updated)

### What Was Removed from brain-process-manager.js
- **Interactive mode**: spawnBrainInteractive, killBrainInteractive, isBrainAliveInteractive, runMissionInteractive (tmux + expect PTY)
- **Direct mode**: spawnBrainDirect, killBrainDirect, isBrainAliveDirect, runMissionDirect, spawnDirectProc (claude -p subprocess)
- **Tmux mode**: spawnBrainTmux, killBrainTmux, isBrainAliveTmux, runMissionTmux, waitForPrompt, capturePane, isPromptVisible
- **Infrastructure**: modeMap dispatch, tmux() helper, spawn import, recovery import, all tmux state variables (expectProc, shuttingDown, lastSpawnTime, rapidFailCount, activeMissionReject, activeMissionStart)
- **Engine helpers**: isQwen, getProxyPort, getModelName, getEngineLabel (unused by external mode)

### What Was Kept
- `log()`, `sleep()`, `getApiKey()` helpers
- `isBrainAlive()` — pgrep for claude process
- `runMission()` — file IPC (MISSION_FILE + DONE_FILE polling)
- `spawnBrain()` / `killBrain()` — simple log-only stubs

### Config Keys Removed
- BRAIN_MODE, EXPECT_SCRIPT, TMUX_SESSION, TMUX_WIDTH, TMUX_HEIGHT, PROMPT_DEBOUNCE_MS

### Tests Status
- Type check: N/A (JavaScript, no TypeScript)
- Node require verification: PASS (all 7 modules load clean)
- Full daemon boot: PASS (task-watcher.js boots, logs "external" mode, exits cleanly)

### Verified Imports (all PASS)
- config.js -> 23 keys exported
- brain-process-manager.js -> 5 exports (spawnBrain, killBrain, isBrainAlive, runMission, log)
- mission-dispatcher.js -> 3 exports (executeTask, buildPrompt, detectProjectDir)
- task-queue.js -> 4 exports (startWatching, stopWatching, isQueueEmpty, enqueue)
- auto-cto-pilot.js -> 2 exports (startAutoCTO, stopAutoCTO)
- m1-cooling-daemon.js -> 2 exports (startCooling, stopCooling)

### Issues Encountered
None. All imports resolved cleanly.

### Notes
- `isBrainAlive()` pgrep pattern updated from `expect.*tom-hum-dispatch` to `claude` (since expect scripts deleted)
- `mission-recovery.js` still exists but is no longer imported by brain-process-manager (was only used by direct mode). Can be deleted separately if desired.
- `scripts/tom-hum-persistent-dispatch.exp` and `scripts/tom-hum-cc.sh` still exist — not in scope for this task.
