# Phase 1: Fix capturePane Double-Indexing (CORE FIX)

## Context Links
- Plan overview: `plans/260228-0132-debug-cto-kill-tmux/plan.md`
- File: `lib/brain-tmux-controller.js`
- Root cause log: `TMUX ERROR [session=tom_hum:brain.1]: can't find pane: 1.1`

## Parallelization Info
- **Must run FIRST** — phases 2 and 3 depend on `TMUX_SESSION_BASE` export added here
- Blocks: Phase 2, Phase 3
- No conflict with any other file

## Overview
- Priority: P1 (critical)
- Status: pending
- The `capturePane(workerIdx, sessionName)` function appends `.${idx}` to `sessionName`. When callers pass `TMUX_SESSION_API = 'tom_hum:brain.1'` (which already encodes pane index `.1`), the result is `tom_hum:brain.1.1` — an invalid double-indexed target. tmux rejects this → failure triggers false "brain dead" detection → session killed.

## Key Insights
- `TMUX_SESSION_PRO = 'tom_hum:brain.0'` and `TMUX_SESSION_API = 'tom_hum:brain.1'` are **full pane targets** (`session:window.pane`), NOT bare session names.
- `capturePane()` at line 69 does `${sessionName}.${idx}` — when sessionName already ends in `.0` or `.1`, this double-appends the pane index.
- Fix: introduce `TMUX_SESSION_BASE = 'tom_hum:brain'` (window target, no pane suffix). All callers using `capturePane(idx, ...)` should pass `TMUX_SESSION_BASE`.
- Keep `TMUX_SESSION_PRO` / `TMUX_SESSION_API` as read-only convenience aliases for non-capturePane uses (e.g. `isSessionAlive`, `sendEnter` where the full pane target is appropriate).

## Requirements
- Add `TMUX_SESSION_BASE` constant = `'tom_hum:brain'` (window-level target, no pane index)
- Export `TMUX_SESSION_BASE` from `brain-tmux-controller.js`
- `capturePane()` must only use `TMUX_SESSION_BASE` as its default sessionName (not `TMUX_SESSION_PRO`)
- `pasteText()`, `sendEnter()`, `sendCtrlC()` construct their own `target = ${sessionName}.${idx}` — they must also default to `TMUX_SESSION_BASE`, not `TMUX_SESSION_PRO`
- `waitForPrompt()` passes sessionName to `capturePane()` — must default to `TMUX_SESSION_BASE`
- `isBrainAlive()` in `brain-spawn-manager.js` L107 already hardcodes `.0` correctly — no change needed there
- Do NOT change `isSessionAlive()` default — it checks session existence, not pane capture

## Architecture
```
BEFORE:
  capturePane(1, TMUX_SESSION_API)
  → tmux capture-pane -t tom_hum:brain.1.1   ← INVALID

AFTER:
  capturePane(1, TMUX_SESSION_BASE)
  → tmux capture-pane -t tom_hum:brain.1     ← CORRECT
```

## Related Code Files
- Modify: `lib/brain-tmux-controller.js`
- Consumers (no change needed to them — they already pass workerIdx + sessionName correctly):
  - `lib/brain-mission-runner.js` — passes `(workerIdx, TMUX_SESSION)` where TMUX_SESSION is already `TMUX_SESSION_PRO` or `TMUX_SESSION_API`; these will need to switch to `TMUX_SESSION_BASE` — see Note below
  - `lib/brain-output-hash-stagnation-watchdog.js` — Phase 3 fixes this
  - `lib/brain-respawn-controller.js` — Phase 2 fixes this

**Note on brain-mission-runner.js:** Lines 59, 67, 103, 112, 116, 117, 127-128, 137-146, 161, 168, 196, 202 all use `TMUX_SESSION` (local var set to either `TMUX_SESSION_PRO` or `TMUX_SESSION_API`). After Phase 1, these callers must use `TMUX_SESSION_BASE` when calling `capturePane()` but may keep using the full pane target for `sendEnter/sendCtrlC/tmuxExec`. However, `capturePane(workerIdx, TMUX_SESSION)` will now double-index again if TMUX_SESSION is still set to `TMUX_SESSION_PRO/API`.

Cleanest fix: update `brain-mission-runner.js` L59 to always assign `TMUX_SESSION_BASE` to the local `TMUX_SESSION` var (since it is only used as the session identifier passed to capturePane + tmuxExec, not as a pane target). The actual pane target in `tmuxExec` calls is already constructed as `${TMUX_SESSION}.${workerIdx}` which becomes `tom_hum:brain.0` or `tom_hum:brain.1` — correct.

Include `brain-mission-runner.js` L59 fix in this phase.

## Implementation Steps

### Step 1 — Add `TMUX_SESSION_BASE` constant (brain-tmux-controller.js L15-16)

**Old code (lines 15-16):**
```js
const TMUX_SESSION_PRO = `${config.TMUX_SESSION}:brain.0`; // Pane 0: Claude Pro (Planner)
const TMUX_SESSION_API = `${config.TMUX_SESSION}:brain.1`; // Pane 1: Gemini Proxy (Executor)
```

**New code (lines 15-17):**
```js
const TMUX_SESSION_BASE = `${config.TMUX_SESSION}:brain`; // Window target (no pane index) — use with capturePane(idx)
const TMUX_SESSION_PRO = `${config.TMUX_SESSION}:brain.0`; // Full pane target: Pane 0 — do NOT pass to capturePane()
const TMUX_SESSION_API = `${config.TMUX_SESSION}:brain.1`; // Full pane target: Pane 1 — do NOT pass to capturePane()
```

### Step 2 — Fix `capturePane()` default sessionName (brain-tmux-controller.js L54)

**Old code (line 54):**
```js
function capturePane(workerIdx, sessionName = TMUX_SESSION_PRO) {
```

**New code (line 54):**
```js
function capturePane(workerIdx, sessionName = TMUX_SESSION_BASE) {
```

### Step 3 — Fix `pasteText()` default sessionName (brain-tmux-controller.js L100)

**Old code (line 100):**
```js
function pasteText(text, workerIdx, sessionName = TMUX_SESSION_PRO) {
```

**New code (line 100):**
```js
function pasteText(text, workerIdx, sessionName = TMUX_SESSION_BASE) {
```

### Step 4 — Fix `sendEnter()` default sessionName (brain-tmux-controller.js L112)

**Old code (line 112):**
```js
function sendEnter(workerIdx, sessionName = TMUX_SESSION_PRO) {
```

**New code (line 112):**
```js
function sendEnter(workerIdx, sessionName = TMUX_SESSION_BASE) {
```

### Step 5 — Fix `sendCtrlC()` default sessionName (brain-tmux-controller.js L117)

**Old code (line 117):**
```js
function sendCtrlC(workerIdx, sessionName = TMUX_SESSION_PRO) {
```

**New code (line 117):**
```js
function sendCtrlC(workerIdx, sessionName = TMUX_SESSION_BASE) {
```

### Step 6 — Fix `waitForPrompt()` default sessionName (brain-tmux-controller.js L123)

**Old code (line 123):**
```js
async function waitForPrompt(timeoutMs = 120000, workerIdx = 0, sessionName = TMUX_SESSION_PRO) {
```

**New code (line 123):**
```js
async function waitForPrompt(timeoutMs = 120000, workerIdx = 0, sessionName = TMUX_SESSION_BASE) {
```

### Step 7 — Export `TMUX_SESSION_BASE` (brain-tmux-controller.js L133-146)

**Old code (line 133-135):**
```js
module.exports = {
  TMUX_SESSION_PRO,
  TMUX_SESSION_API,
```

**New code (line 133-136):**
```js
module.exports = {
  TMUX_SESSION_BASE,
  TMUX_SESSION_PRO,
  TMUX_SESSION_API,
```

### Step 8 — Fix brain-mission-runner.js local TMUX_SESSION assignment (L59)

**Old code (line 59):**
```js
  const TMUX_SESSION = isPlanning ? TMUX_SESSION_PRO : TMUX_SESSION_API;
```

**New code (line 59):**
```js
  const TMUX_SESSION = TMUX_SESSION_BASE; // always use window-level target; workerIdx selects pane
```

**Also update the import at brain-mission-runner.js L21-24 to include TMUX_SESSION_BASE:**

**Old code (lines 21-24):**
```js
const {
  TMUX_SESSION_PRO, TMUX_SESSION_API,
  tmuxExec, isSessionAlive, capturePane,
  sendEnter, sendCtrlC,
} = require('./brain-tmux-controller');
```

**New code (lines 21-24):**
```js
const {
  TMUX_SESSION_BASE,
  tmuxExec, isSessionAlive, capturePane,
  sendEnter, sendCtrlC,
} = require('./brain-tmux-controller');
```

## Todo List
- [ ] Add `TMUX_SESSION_BASE` constant at L15 of `brain-tmux-controller.js`
- [ ] Fix `capturePane()` default at L54
- [ ] Fix `pasteText()` default at L100
- [ ] Fix `sendEnter()` default at L112
- [ ] Fix `sendCtrlC()` default at L117
- [ ] Fix `waitForPrompt()` default at L123
- [ ] Export `TMUX_SESSION_BASE` in `module.exports`
- [ ] Update `brain-mission-runner.js` import to use `TMUX_SESSION_BASE`
- [ ] Update `brain-mission-runner.js` L59 to always assign `TMUX_SESSION_BASE`
- [ ] Verify: `node -e "const c = require('./lib/brain-tmux-controller'); console.log(c.TMUX_SESSION_BASE)"` outputs `tom_hum:brain`

## Success Criteria
- `TMUX_SESSION_BASE` exported and equals `'tom_hum:brain'`
- `capturePane(1)` with no sessionName → executes `tmux capture-pane -t tom_hum:brain.1` (not `tom_hum:brain.0.1`)
- `capturePane(1, TMUX_SESSION_BASE)` → `tmux capture-pane -t tom_hum:brain.1` — correct
- No caller passes `TMUX_SESSION_PRO/API` to `capturePane()` directly
- `node --check lib/brain-tmux-controller.js` — no syntax errors
- `node --check lib/brain-mission-runner.js` — no syntax errors

## Conflict Prevention
- `TMUX_SESSION_PRO` and `TMUX_SESSION_API` remain exported — Phase 2 still imports them for `isSessionAlive()` and `waitForPrompt()` in `brain-respawn-controller.js`
- Only `capturePane`, `pasteText`, `sendEnter`, `sendCtrlC`, `waitForPrompt` defaults change
- `tmuxExec` default stays `TMUX_SESSION_PRO` — it's used for logging only (`sessionName` param used only in error log string, not as tmux target)

## Risk Assessment
- Low risk: isolated to default parameter values and one constant addition
- `brain-mission-runner.js` L59 change: `TMUX_SESSION_BASE` is used as base for pane-target construction (`${TMUX_SESSION}.${workerIdx}`) — correct since `'tom_hum:brain.1'` is the desired output
- Existing explicit callers that pass `TMUX_SESSION_PRO/API` to capturePane (if any) will now double-index — search confirms none remain after this phase

## Security Considerations
- No auth changes, no secrets, no external calls

## Next Steps
- After this phase: Phase 2 (`brain-spawn-manager.js`, `brain-respawn-controller.js`) and Phase 3 (`brain-output-hash-stagnation-watchdog.js`) can run in parallel
