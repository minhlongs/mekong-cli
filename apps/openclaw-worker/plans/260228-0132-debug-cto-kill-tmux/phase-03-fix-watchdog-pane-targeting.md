# Phase 3: Fix Watchdog Pane Targeting

## Context Links
- Plan overview: `plans/260228-0132-debug-cto-kill-tmux/plan.md`
- File: `lib/brain-output-hash-stagnation-watchdog.js`
- Root cause log: `[HASH_WATCHDOG] Step 2: Kickstart ineffective, triggering respawn` → kill event 2

## Parallelization Info
- **Blocked by Phase 1** (needs `TMUX_SESSION_BASE` export)
- Can run in parallel with Phase 2 after Phase 1 completes
- No file overlap with Phase 2

## Overview
- Priority: P1 (critical)
- Status: pending
- `capturePane(WATCHDOG_PANE)` at lines 32 and 62 calls `capturePane` with no explicit `sessionName`, so it falls back to the old default `TMUX_SESSION_PRO = 'tom_hum:brain.0'`. With `WATCHDOG_PANE = 1`, this constructs target `tom_hum:brain.0.1` — pane index 1 appended to a string that already encodes pane 0. tmux rejects it → output is always empty string → hash is always identical → stagnation triggers → respawn → session killed.
- After Phase 1, the default changes to `TMUX_SESSION_BASE`, so `capturePane(1)` → `tom_hum:brain.1` which is correct. But the watchdog must also explicitly pass `TMUX_SESSION_BASE` in all call sites for clarity and safety.
- `sendEnter(WATCHDOG_PANE)` at line 55 has the same default issue — must also pass `TMUX_SESSION_BASE` explicitly.

## Key Insights
- `WATCHDOG_PANE = 1` is correct — P1 is the Executor (API) pane that runs missions and is most likely to stagnate.
- The fix is purely about passing the correct `sessionName` to `capturePane()` and `sendEnter()`.
- After Phase 1 fixes the defaults, the watchdog calls with no sessionName would accidentally work correctly — but explicit passing is required for clarity and to survive future default changes.
- The watchdog must NOT import `TMUX_SESSION_PRO` or `TMUX_SESSION_API` — import `TMUX_SESSION_BASE` only.

## Requirements
- Import `TMUX_SESSION_BASE` from `brain-tmux-controller` in the lazy-require blocks (lines 31, 54, 61)
- Pass `TMUX_SESSION_BASE` explicitly in all `capturePane(WATCHDOG_PANE, ...)` calls (lines 32, 62)
- Pass `TMUX_SESSION_BASE` explicitly in the `sendEnter(WATCHDOG_PANE, ...)` call (line 55)
- No change to `WATCHDOG_PANE`, `HASH_INTERVAL_MS`, `STAGNATION_THRESHOLD`, or `KICKSTART_WAIT_MS`
- No change to the `respawnBrain()` call at line 67 (Phase 2 fixes that side)

## Architecture
```
BEFORE (capturePane at line 32):
  capturePane(1)
  → default sessionName = TMUX_SESSION_PRO = 'tom_hum:brain.0'
  → tmux capture-pane -t tom_hum:brain.0.1   ← INVALID
  → returns ''  → hash always same → false stagnation

AFTER:
  capturePane(1, TMUX_SESSION_BASE)
  → tmux capture-pane -t tom_hum:brain.1     ← CORRECT
  → returns real pane output → hash varies → no false stagnation
```

## Related Code Files
- Modify: `lib/brain-output-hash-stagnation-watchdog.js`
  - Lines 31-32 (`checkOutputHash` → lazy capturePane require + call)
  - Lines 54-55 (`handleStagnation` → lazy sendEnter require + call)
  - Lines 61-62 (`handleStagnation` → lazy capturePane require + call)

## Implementation Steps

### Step 1 — Fix capturePane call in checkOutputHash() (lines 31-32)

The `capturePane` import is lazy (inside the function body). Add `TMUX_SESSION_BASE` to the destructure and pass it explicitly.

**Old code (lines 31-33):**
```js
    const { capturePane } = require('./brain-tmux-controller');
    const output = capturePane(WATCHDOG_PANE);
    const hash = hashOutput(output);
```

**New code (lines 31-33):**
```js
    const { capturePane, TMUX_SESSION_BASE } = require('./brain-tmux-controller');
    const output = capturePane(WATCHDOG_PANE, TMUX_SESSION_BASE);
    const hash = hashOutput(output);
```

### Step 2 — Fix sendEnter call in handleStagnation() (lines 54-55)

**Old code (lines 54-56):**
```js
    const { sendEnter } = require('./brain-tmux-controller');
    sendEnter(WATCHDOG_PANE);
  } catch (e) {
```

**New code (lines 54-56):**
```js
    const { sendEnter, TMUX_SESSION_BASE } = require('./brain-tmux-controller');
    sendEnter(WATCHDOG_PANE, TMUX_SESSION_BASE);
  } catch (e) {
```

### Step 3 — Fix capturePane call in handleStagnation() post-kickstart check (lines 61-62)

**Old code (lines 61-63):**
```js
    const { capturePane } = require('./brain-tmux-controller');
    const output = capturePane(WATCHDOG_PANE);
    const newHash = hashOutput(output);
```

**New code (lines 61-63):**
```js
    const { capturePane, TMUX_SESSION_BASE } = require('./brain-tmux-controller');
    const output = capturePane(WATCHDOG_PANE, TMUX_SESSION_BASE);
    const newHash = hashOutput(output);
```

## Todo List
- [ ] Fix `capturePane` lazy-require + call in `checkOutputHash()` at lines 31-32
- [ ] Fix `sendEnter` lazy-require + call in `handleStagnation()` at lines 54-55
- [ ] Fix `capturePane` lazy-require + call in post-kickstart check at lines 61-62
- [ ] Verify: `node --check lib/brain-output-hash-stagnation-watchdog.js` — no syntax errors
- [ ] Smoke-test: confirm `WATCHDOG_PANE = 1` + `TMUX_SESSION_BASE` → target `tom_hum:brain.1`

## Success Criteria
- All three `capturePane` and `sendEnter` calls in the watchdog pass `TMUX_SESSION_BASE` explicitly
- No call to `capturePane(WATCHDOG_PANE)` without a sessionName argument remains in this file
- `node --check lib/brain-output-hash-stagnation-watchdog.js` passes
- Hash stagnation watchdog no longer produces empty-string hashes on a live pane
- No reference to `TMUX_SESSION_PRO` or `TMUX_SESSION_API` in this file

## Conflict Prevention
- Phase 2 touches `brain-spawn-manager.js` and `brain-respawn-controller.js` only — zero overlap
- The `respawnBrain()` call at line 67 is left unchanged here — Phase 2 fixes the respawn side
- Lazy-require pattern preserved (circular dep safety) — only destructuring updated

## Risk Assessment
- Minimal risk: three one-line changes, each adding one argument to an existing function call
- Lazy-require pattern means `TMUX_SESSION_BASE` is evaluated at call time — after Phase 1 exports it, this is safe
- If Phase 1 is not applied first, this fix alone does nothing (default still wrong) — phase dependency enforced

## Security Considerations
- No auth changes, no secrets, no external calls

## Next Steps
- After Phase 2 and Phase 3 both complete: integration test
  1. Ensure `tom_hum` tmux session exists with window `brain`, panes 0 and 1
  2. Write `tasks/mission_test_watchdog.txt` with content `echo WATCHDOG_TEST`
  3. Tail `~/tom_hum_cto.log` — confirm no `can't find pane` errors
  4. Let watchdog run 3 cycles (3 min) — confirm no false stagnation trigger
