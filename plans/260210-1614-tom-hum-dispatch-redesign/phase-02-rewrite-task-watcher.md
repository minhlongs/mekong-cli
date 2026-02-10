# Phase 2: Rewrite Task Watcher

## Context Links
- [Parent Plan](plan.md)
- [Phase 1: Expect Script](phase-01-rewrite-expect-dispatch.md)
- [Research: Process Mgmt](research/researcher-02-launchd-process-mgmt.md)
- Current file: `apps/openclaw-worker/task-watcher.js` (331 lines → rewrite)

## Overview
- **Priority:** P1
- **Status:** pending
- **Description:** Rewrite task-watcher.js with clean architecture: atomic file IPC, graceful lifecycle, modular structure

## Key Insights
- Current file is 331 lines, monolithic — split into focused modules
- File IPC must use atomic writes (tmp+rename) to prevent corruption
- Brain process management needs proper lifecycle (spawn, monitor, kill)
- Cooling daemon and auto-CTO features retained but cleaned up
- API key should NOT be hardcoded — read from env or config

## Requirements

### Functional
- Watch `tasks/` directory for `mission_*.txt` files
- Queue missions sequentially (one at a time)
- Deliver missions via atomic file write to `/tmp/tom_hum_next_mission.txt`
- Poll `/tmp/tom_hum_mission_done` for completion signal
- Archive completed missions to `tasks/processed/`
- Spawn and manage expect brain process
- Auto-CTO: generate Binh Phap maintenance tasks when queue empty
- M1 cooling daemon: monitor load, kill resource hogs

### Non-Functional
- Graceful shutdown (SIGTERM/SIGINT → kill brain → exit)
- No hardcoded API keys in source code
- Modular file structure (under 200 lines per file)
- Atomic file writes for IPC

## Architecture

```
apps/openclaw-worker/
├── task-watcher.js                    # Main entry — orchestrates everything
├── lib/
│   ├── brain-process-manager.js       # Spawn/monitor/kill expect brain
│   ├── mission-dispatcher.js          # Atomic IPC: write mission, poll done
│   ├── task-queue.js                  # File watching, queuing, archiving
│   ├── auto-cto-pilot.js             # Binh Phap auto-task generation
│   └── m1-cooling-daemon.js          # System resource monitoring
└── config.js                          # Constants, paths, env vars
```

**Data flow:**
```
fs.watch(tasks/) → queue → dispatcher → atomic write mission file
                                      → poll done file
                                      → archive mission
```

## Related Code Files
- **Rewrite:** `apps/openclaw-worker/task-watcher.js`
- **Create:** `apps/openclaw-worker/lib/brain-process-manager.js`
- **Create:** `apps/openclaw-worker/lib/mission-dispatcher.js`
- **Create:** `apps/openclaw-worker/lib/task-queue.js`
- **Create:** `apps/openclaw-worker/lib/auto-cto-pilot.js`
- **Create:** `apps/openclaw-worker/lib/m1-cooling-daemon.js`
- **Create:** `apps/openclaw-worker/config.js`

## Implementation Steps

### Step 1: Create `config.js`
```javascript
// All constants, paths, env vars in one place
module.exports = {
  MEKONG_DIR: process.env.MEKONG_DIR || '/Users/macbookprom1/mekong-cli',
  WATCH_DIR: ...,
  PROCESSED_DIR: ...,
  LOG_FILE: process.env.TOM_HUM_LOG || '/Users/macbookprom1/tom_hum_cto.log',
  MISSION_FILE: '/tmp/tom_hum_next_mission.txt',
  DONE_FILE: '/tmp/tom_hum_mission_done',
  EXPECT_SCRIPT: ...,
  TASK_PATTERN: /^mission_.*\.txt$/,
  MISSION_TIMEOUT_MS: 45 * 60 * 1000,
  POLL_INTERVAL_MS: 3000,
  COOLING_INTERVAL_MS: 90000,
  AUTO_CTO_EMPTY_THRESHOLD: 60,
};
```

### Step 2: Create `lib/brain-process-manager.js`
- `spawnBrain()` — spawn expect script as child process
- `killBrain()` — graceful kill with SIGTERM, then SIGKILL after 5s
- `isBrainAlive()` — check process state
- `onBrainExit(callback)` — register exit handler
- Pass env vars (ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY) via process.env
- **API key from env only**: `process.env.ANTHROPIC_API_KEY`

### Step 3: Create `lib/mission-dispatcher.js`
- `dispatchMission(prompt)` — atomic write to mission file (tmp+rename)
- `waitForCompletion(timeoutMs)` — poll done file, return result
- `buildPrompt(taskContent)` — route to project dir, build /cook command
- Atomic write pattern:
  ```javascript
  const tmpFile = MISSION_FILE + '.tmp';
  fs.writeFileSync(tmpFile, content);
  fs.renameSync(tmpFile, MISSION_FILE);
  ```

### Step 4: Create `lib/task-queue.js`
- `startWatching()` — fs.watch + periodic poll
- `enqueue(filename)` — add to queue, deduplicate
- `processNext()` — dequeue, read content, dispatch, archive
- `archiveTask(filename)` — move to processed/

### Step 5: Create `lib/auto-cto-pilot.js`
- Track empty queue cycles
- After threshold: generate next Binh Phap task for next project
- State persistence in `tasks/.tom_hum_state.json`
- Project rotation: 84tea → apex-os → sophia → anima119 → well

### Step 6: Create `lib/m1-cooling-daemon.js`
- Periodic load/RAM check (every 90s)
- Kill known resource hogs (pyrefly, pyright)
- Hard cooling on high load (>8) or low RAM (<200MB)

### Step 7: Rewrite `task-watcher.js` as orchestrator
- Import all modules
- Initialize: spawnBrain, startWatching, start cooling, start auto-CTO
- Graceful shutdown handler:
  ```javascript
  ['SIGTERM', 'SIGINT'].forEach(sig => {
      process.on(sig, () => {
          log(`Received ${sig} — shutting down`);
          killBrain();
          process.exit(0);
      });
  });
  ```
- Main file under 80 lines (just wiring)

## Todo List
- [ ] Create config.js with all constants
- [ ] Create brain-process-manager.js
- [ ] Create mission-dispatcher.js with atomic writes
- [ ] Create task-queue.js with file watching
- [ ] Create auto-cto-pilot.js
- [ ] Create m1-cooling-daemon.js
- [ ] Rewrite task-watcher.js as thin orchestrator
- [ ] Remove hardcoded API key (use env var)
- [ ] Test full flow: drop mission file → dispatch → completion → archive

## Success Criteria
- task-watcher.js under 80 lines (orchestrator only)
- All modules under 200 lines each
- No hardcoded API keys
- Atomic file writes prevent IPC corruption
- Graceful shutdown kills brain process cleanly
- Auto-CTO and cooling daemon work as before

## Risk Assessment
- **Risk:** Module splitting could break require() paths
  - **Mitigation:** Use relative paths, test imports
- **Risk:** fs.renameSync not atomic across filesystems
  - **Mitigation:** /tmp is same filesystem on macOS, safe

## Security Considerations
- API key read from `process.env.ANTHROPIC_API_KEY` only
- No secrets committed to git
- Log file should not contain API keys

## Next Steps
- Phase 3: launchd plist for auto-restart
