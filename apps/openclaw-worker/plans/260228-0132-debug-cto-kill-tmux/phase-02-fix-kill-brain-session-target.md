# Phase 2: Fix killBrain Session Target

## Context Links
- Plan overview: `plans/260228-0132-debug-cto-kill-tmux/plan.md`
- Files: `lib/brain-spawn-manager.js`, `lib/brain-respawn-controller.js`
- Root cause log: `BRAIN: tmux session tom_hum:brain.1 killed` → entire `tom_hum` session destroyed

## Parallelization Info
- **Blocked by Phase 1** (needs `TMUX_SESSION_BASE` export)
- Can run in parallel with Phase 3 after Phase 1 completes
- No file overlap with Phase 3

## Overview
- Priority: P1 (critical)
- Status: pending
- `respawnBrain()` in `brain-respawn-controller.js` L44 computes `sessionName = TMUX_SESSION_API = 'tom_hum:brain.1'`, then calls `killBrain(sessionName)`. Inside `killBrain()`, that string is passed to `tmux kill-session -t tom_hum:brain.1`. tmux interprets `tom_hum:brain.1` as "pane 1 of window brain in session tom_hum" — so it kills the **entire session** `tom_hum`, not just pane 1. Both PRO and API panes die.
- Secondary: `isBrainAlive()` at L103 defaults to `TMUX_SESSION_PRO` but internally hardcodes `.0` for pane capture (L107) — functionally correct but semantically confusing. After Phase 1, the default should be `TMUX_SESSION_BASE` for consistency.

## Key Insights
- `tmux kill-session -t <target>` where target is a pane qualifier (`session:window.pane`) still kills the whole session — tmux resolves the session part and kills it entirely.
- `killBrain()` should ALWAYS use the base session name `config.TMUX_SESSION = 'tom_hum'` — never a window or pane target.
- `respawnBrain()` must NOT pass `TMUX_SESSION_PRO/API` to `killBrain()` — pass nothing (use default `config.TMUX_SESSION`).
- `isBrainAlive()` L107: already uses hardcoded `.0` pane — change default param to `TMUX_SESSION_BASE` for consistency, but internal logic unchanged.

## Requirements
- `killBrain()` default param stays `config.TMUX_SESSION` (already correct at L94) — no change
- `respawnBrain()` L53: stop passing `sessionName` to `killBrain()` — call `killBrain()` with no args
- `respawnBrain()` L44: remove the `sessionName` variable derivation (no longer needed)
- `respawnBrain()` L61: `waitForPrompt()` call — change sessionName arg from `sessionName` to `TMUX_SESSION_BASE` (imported from Phase 1)
- `isBrainAlive()` L103: update default param from `TMUX_SESSION_PRO` to `TMUX_SESSION_BASE`
- Import `TMUX_SESSION_BASE` in `brain-spawn-manager.js` (replace `TMUX_SESSION_PRO` in the import if no longer needed there)
- Import `TMUX_SESSION_BASE` in `brain-respawn-controller.js` (add alongside existing imports)

## Architecture
```
BEFORE:
  respawnBrain('EXECUTION')
  → sessionName = TMUX_SESSION_API = 'tom_hum:brain.1'
  → killBrain('tom_hum:brain.1')
  → tmux kill-session -t tom_hum:brain.1
  → tmux resolves session=tom_hum → KILLS ENTIRE SESSION

AFTER:
  respawnBrain('EXECUTION')
  → killBrain()                    ← no args
  → tmux kill-session -t tom_hum  ← intentional full kill (correct: we want fresh boot)
  → spawnBrain()                   ← boots both panes fresh
```

## Related Code Files
- Modify: `lib/brain-spawn-manager.js` (L23-25, L103)
- Modify: `lib/brain-respawn-controller.js` (L22, L44-45, L53, L61)

## Implementation Steps

### Step 1 — Update import in brain-spawn-manager.js (L23-25)

`TMUX_SESSION_PRO` is used only in `isBrainAlive()` default param after this fix. Replace with `TMUX_SESSION_BASE`.

**Old code (lines 22-25):**
```js
const {
  TMUX_SESSION_PRO, TMUX_SESSION_API,
  tmuxExec, isSessionAlive, capturePane,
} = require('./brain-tmux-controller');
```

**New code (lines 22-25):**
```js
const {
  TMUX_SESSION_BASE,
  tmuxExec, isSessionAlive, capturePane,
} = require('./brain-tmux-controller');
```

### Step 2 — Fix `isBrainAlive()` default param (brain-spawn-manager.js L103)

**Old code (line 103):**
```js
function isBrainAlive(sessionName = TMUX_SESSION_PRO) {
```

**New code (line 103):**
```js
function isBrainAlive(sessionName = TMUX_SESSION_BASE) {
```

Note: internal body unchanged — L107 still uses `${sessionName}.0` which becomes `tom_hum:brain.0` — correct.

### Step 3 — Update import in brain-respawn-controller.js (L22)

**Old code (line 22):**
```js
const { TMUX_SESSION_PRO, TMUX_SESSION_API, waitForPrompt } = require('./brain-tmux-controller');
```

**New code (line 22):**
```js
const { TMUX_SESSION_BASE, waitForPrompt } = require('./brain-tmux-controller');
```

### Step 4 — Remove erroneous sessionName derivation in respawnBrain() (L43-44)

**Old code (lines 42-53):**
```js
async function respawnBrain(intent = 'EXECUTION', useContinue = true) {
  const isPlanning = intent === 'PLAN' || intent === 'RESEARCH';
  const sessionName = isPlanning ? TMUX_SESSION_PRO : TMUX_SESSION_API;

  if (!canRespawn()) {
    log(`RESPAWN: Rate limit (${MAX_RESPAWNS_PER_HOUR}/hr) — cooldown ${RESPAWN_COOLDOWN_MS / 1000}s`);
    await new Promise(r => setTimeout(r, RESPAWN_COOLDOWN_MS));
    // After cooldown, old timestamps are naturally filtered by canRespawn()
  }
  respawnTimestamps.push(Date.now());

  killBrain(sessionName);
```

**New code (lines 42-53):**
```js
async function respawnBrain(intent = 'EXECUTION', useContinue = true) {
  if (!canRespawn()) {
    log(`RESPAWN: Rate limit (${MAX_RESPAWNS_PER_HOUR}/hr) — cooldown ${RESPAWN_COOLDOWN_MS / 1000}s`);
    await new Promise(r => setTimeout(r, RESPAWN_COOLDOWN_MS));
    // After cooldown, old timestamps are naturally filtered by canRespawn()
  }
  respawnTimestamps.push(Date.now());

  killBrain(); // always kill by base session name (config.TMUX_SESSION)
```

### Step 5 — Fix waitForPrompt call in respawnBrain() (L61)

`sessionName` variable no longer exists. Use `TMUX_SESSION_BASE`.

**Old code (line 60-61):**
```js
  log(`RESPAWN: Session ${sessionName} rebuilt via spawnBrain()`);
  return waitForPrompt(120000, 0, sessionName);
```

**New code (line 60-61):**
```js
  log(`RESPAWN: Session rebuilt via spawnBrain()`);
  return waitForPrompt(120000, 0, TMUX_SESSION_BASE);
```

## Todo List
- [ ] Replace `TMUX_SESSION_PRO, TMUX_SESSION_API` import with `TMUX_SESSION_BASE` in `brain-spawn-manager.js` L22-25
- [ ] Fix `isBrainAlive()` default param to `TMUX_SESSION_BASE` at L103
- [ ] Replace `TMUX_SESSION_PRO, TMUX_SESSION_API` import with `TMUX_SESSION_BASE` in `brain-respawn-controller.js` L22
- [ ] Remove `isPlanning` + `sessionName` derivation in `respawnBrain()` L43-44
- [ ] Change `killBrain(sessionName)` → `killBrain()` at L53
- [ ] Fix log message and `waitForPrompt` call at L60-61
- [ ] Verify: `node --check lib/brain-spawn-manager.js` — no syntax errors
- [ ] Verify: `node --check lib/brain-respawn-controller.js` — no syntax errors

## Success Criteria
- `respawnBrain()` calls `killBrain()` with no args in all code paths
- `killBrain()` executes `tmux kill-session -t tom_hum` (base session only)
- `isBrainAlive()` default param is `TMUX_SESSION_BASE`
- No reference to `TMUX_SESSION_PRO` or `TMUX_SESSION_API` remains in either file
- Both files pass `node --check`

## Conflict Prevention
- Phase 3 touches `brain-output-hash-stagnation-watchdog.js` only — zero overlap
- `killBrain()` body in `brain-spawn-manager.js` L94-101 is unchanged (default already `config.TMUX_SESSION`)
- `spawnBrain()` call at L57 unchanged

## Risk Assessment
- Low risk: removing unused `sessionName` variable; `killBrain()` default was already `config.TMUX_SESSION`
- Intentional behavior: `respawnBrain()` kills the entire `tom_hum` session then reboots — this is correct since `spawnBrain()` recreates both panes

## Security Considerations
- No auth changes, no secrets

## Next Steps
- After both Phase 2 and Phase 3 complete: run manual test cycle (write a test mission file, observe logs confirm no spurious kills)
