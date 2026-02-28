## Phase Implementation Report

### Executed Phase
- Phase: phase-05-fix-remaining-bugs (BUG #4, #5, #9, #11)
- Plan: /Users/macbookprom1/mekong-cli/plans/260227-2000-tom-hum-cto-agi-deep-upgrade/
- Status: completed

### Files Modified

| File | Lines Changed | Description |
|------|--------------|-------------|
| `apps/openclaw-worker/lib/brain-supervisor.js` | +8 | BUG #4: heartbeat stale supplement in stuck detection |
| `apps/openclaw-worker/lib/project-scanner.js` | +22 / -14 | BUG #9: replaced Ollama (11436) fetch with Antigravity Proxy callLLM |
| `apps/openclaw-worker/lib/auto-cto-pilot.js` | +24 | BUG #11: per-project consecutive failure tracking + wired into handleVerify |

### Tasks Completed

- [x] BUG #4 (brain-supervisor): Added lazy `require('./brain-heartbeat').isBrainHeartbeatStale()` check inside stuck detection block — logs heartbeat stale signal when brain may be frozen in direct mode
- [x] BUG #5 (brain-supervisor tmux target): Verified `TMUX_SESSION` is already correctly set to `${config.TMUX_SESSION}:brain` = `tom_hum:brain`. No `tom_hum_brain` (underscore) references found. No fix needed.
- [x] BUG #5b (undefined state from strategic-brain): `state?.currentProject` bug is in `strategic-brain.js` line 79 (not in brain-supervisor). `brain-supervisor.js` has no strategic-brain import so no guard needed there. Root cause: `state` should be `projectState` in `selectStrategicTask` — see Unresolved Questions.
- [x] BUG #9 (project-scanner Ollama): Added `callLLM(prompt)` helper using `PROXY_URL` = `process.env.ANTHROPIC_BASE_URL || 'http://localhost:9191'`. Replaced `fetch('http://127.0.0.1:11436/v1/chat/completions', ...)` with `callLLM(prompt)`. Refactored from OpenAI-format to Anthropic Messages API format.
- [x] BUG #11 (auto-cto-pilot): Added `projectFailureCount` Map + `MAX_CONSECUTIVE_FAILURES=3`. Added `onProjectMissionFailed(projectName)` and `onProjectMissionSuccess(projectName)` functions. Wired into `handleVerify`: success path calls `onProjectMissionSuccess`, MAX_FIX_CYCLES exhausted path calls `onProjectMissionFailed`. Exported both functions.

### Tests Status
- Type check: N/A (CommonJS, no TS)
- Unit tests: N/A (daemon modules)
- Load verification:
  - `brain-supervisor OK` — pass
  - `project-scanner OK` — pass
  - `auto-cto-pilot OK` — pass
- Ollama reference audit: only comment line remains, no functional 11436 calls

### Issues Encountered

**BUG #5b root cause is in strategic-brain.js, not brain-supervisor.js:**
- `strategic-brain.js` line 79: `state?.currentProject || 'well'` — `state` is undefined (not declared in `selectStrategicTask` scope)
- Should be `projectState?.currentProject || project` using the function parameter
- `brain-supervisor.js` has no strategic-brain import so cannot guard it from supervisor side
- Fix requires modifying `strategic-brain.js` which is outside Phase 05 file ownership

**BUG #5 (tmux target):** Already correct. `TMUX_SESSION = \`${config.TMUX_SESSION}:brain\`` resolves to `tom_hum:brain`. All `send-keys` and `capture-pane` calls use this variable — no hardcoded underscore variant found.

### Next Steps
- BUG #5b: Modify `strategic-brain.js` line 79 to use `projectState?.currentProject || project` — requires separate phase or ownership grant
- Confirm `ANTHROPIC_BASE_URL` env var is set in openclaw-worker runtime environment (defaults to port 9191)
- Monitor `[SCANNER]` logs after deploy to verify proxy calls succeed vs previous Ollama connection refused errors

### Unresolved Questions
1. BUG #5b actual fix location: `strategic-brain.js:79` — `state` → `projectState`. Is this file owned by another phase agent?
2. Should `callLLM` in `project-scanner.js` use `config.MODEL_NAME` instead of `config.FALLBACK_MODEL_NAME` for primary analysis? Current code uses `FALLBACK_MODEL_NAME` to match original intent.
