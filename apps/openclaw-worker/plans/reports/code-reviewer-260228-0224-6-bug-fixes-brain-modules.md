# Code Review: 6 Bug Fixes — Brain Modules

**Date:** 2026-02-28
**Files:** brain-spawn-manager.js, brain-boot-sequence.js, brain-output-hash-stagnation-watchdog.js, brain-mission-runner.js, brain-respawn-controller.js, config.js
**LOC reviewed:** ~550 across 6 files
**Scout findings:** 3 edge cases discovered (see below)

---

## Overall Assessment

The 6 fixes are directionally correct and address real, verified bugs. The most impactful improvement is the stagnation watchdog rewrite — the old unreachable-branch bug would have silently never triggered respawn. The CHAIRMAN OVERRIDE removal simplifies routing. The circular-dep solution via lazy-require is correct.

Two issues warrant attention before this ships to production: one medium bug (respawnBrain call on line 163 drops its return value), and one low/clarification issue in `isBrainAlive` semantics.

---

## Critical Issues

None.

---

## High Priority

### H1 — respawnBrain return value silently dropped on line 163 (brain-mission-runner.js)

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-mission-runner.js:163`

```js
// Line 163 — inside the state-machine BRAIN DIED branch:
await respawnBrain(isPlanning ? 'PLAN' : 'EXECUTION', true);
return { success: false, result: 'brain_died', elapsed };
```

Contrast with the pre-dispatch guard on line 105:

```js
const ok = await respawnBrain(isPlanning ? 'PLAN' : 'EXECUTION', true);
if (!ok) return { success: false, result: 'brain_died_fatal', elapsed: 0 };
```

The pre-dispatch call correctly checks `ok`. The in-loop call on line 163 does not. Since `respawnBrain` now always returns `false`, the behavior is the same either way (both paths return a failure result immediately after). However:

- The inconsistency is confusing — someone reading line 163 will expect respawn succeeded before `brain_died` is returned.
- If `respawnBrain` is ever re-enabled, line 163 will silently ignore a successful respawn and still abort the mission.

**Fix:**

```js
const recovered = await respawnBrain(isPlanning ? 'PLAN' : 'EXECUTION', true);
if (!recovered) {
  return { success: false, result: 'brain_died', elapsed };
}
// (if respawn re-enabled, continue polling here)
return { success: false, result: 'brain_died', elapsed };
```

Or at minimum add a comment acknowledging the intentional discard.

---

## Medium Priority

### M1 — isBrainAlive receives a full pane address but isSessionAlive checks base session only (correct, but confusing contract)

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-spawn-manager.js:105-113`

```js
function isBrainAlive(sessionName = TMUX_SESSION_PRO) {
  if (!isSessionAlive(config.TMUX_SESSION)) return false;  // checks "tom_hum", not "tom_hum:brain.0"
  try {
    const output = execSync(
      `tmux capture-pane -t ${sessionName} -p 2>/dev/null`, ...
    );
```

`sessionName` default is `TMUX_SESSION_PRO` = `tom_hum:brain.0`. `isSessionAlive` is then called with `config.TMUX_SESSION` = `tom_hum` (base session name, no window/pane suffix). This is actually the correct behavior — `tmux has-session` requires only the session name, not a pane address. But the parameter name `sessionName` is misleading because it really carries a *pane address* (`session:window.pane`).

The old bug (appending `.0` to an already-indexed pane) is fixed. The current code is correct.

**Recommendation:** Rename the parameter to `paneTarget` to make the dual usage clear:

```js
function isBrainAlive(paneTarget = TMUX_SESSION_PRO) {
  if (!isSessionAlive(config.TMUX_SESSION)) return false;
  const output = execSync(`tmux capture-pane -t ${paneTarget} -p 2>/dev/null`, ...);
```

This is low friction — callers pass `TMUX_SESSION` (a pane address), and the internal `isSessionAlive` call correctly strips back to base session.

---

### M2 — hashHistory initialized as `[]` at module scope but treated as sparse array

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-output-hash-stagnation-watchdog.js:18,32,66`

Module-scope initialization:
```js
let hashHistory = [];
```

`startOutputHashWatchdog()` correctly resets to `[[], []]`. But if `checkOutputHash()` ran before `startOutputHashWatchdog()` (e.g., during a re-require edge case), line 32 would catch it:

```js
if (!hashHistory[paneIdx]) hashHistory[paneIdx] = [];
```

This guard is correct and defensive. Good.

However, `stopOutputHashWatchdog` does not reset `hashHistory = [[], []]`. After a stop-start cycle, old hash state from the previous run survives until the next `startOutputHashWatchdog()` call (which does reset). Since `startOutputHashWatchdog` always calls `stopOutputHashWatchdog` first and then resets, this is not a real bug — just worth noting.

---

### M3 — sendEnter in watchdog uses wrong default sessionName (functional issue)

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-output-hash-stagnation-watchdog.js:55-56`

```js
const { sendEnter } = require('./brain-tmux-controller');
sendEnter(paneIdx);
```

`sendEnter` signature (from `brain-tmux-controller.js:112`):

```js
function sendEnter(workerIdx, sessionName = TMUX_SESSION_PRO) {
```

The default `sessionName` is `TMUX_SESSION_PRO` = `tom_hum:brain.0`. When the watchdog fires for `paneIdx = 0`, this is correct — the kick goes to the right pane. When it fires for `paneIdx = 1`, `sendEnter(1)` expands to `tmux send-keys -t tom_hum:brain.0.1 Enter`. The `.0.1` suffix is a tmux pane addressing scheme — `session:window.pane`. `TMUX_SESSION_PRO` = `tom_hum:brain.0` means session `tom_hum`, window `brain`, pane `0`. Appending `.1` would produce `tom_hum:brain.0.1` which tmux parses as session `tom_hum`, window `brain`, pane `1` — which IS `TMUX_SESSION_API`.

Wait — let me re-examine. `TMUX_SESSION_PRO` = `tom_hum:brain.0`. In `sendEnter`:
```js
const target = `${sessionName}.${workerIdx}`;
// → "tom_hum:brain.0.1"  for paneIdx=1
```

Tmux documentation: `session:window.pane`. `tom_hum:brain.0` is session=`tom_hum`, window=`brain`, pane=`0`. Adding `.1` makes `tom_hum:brain.0.1` — tmux will reject this as an invalid target (extra `.pane` segment after already specifying pane `0`).

**This is a genuine bug.** The watchdog must pass the correct session string per pane:

```js
const { sendEnter, TMUX_SESSION_PRO, TMUX_SESSION_API } = require('./brain-tmux-controller');
const SESSION = paneIdx === 0 ? TMUX_SESSION_PRO : TMUX_SESSION_API;
sendEnter(paneIdx, SESSION);
```

OR (simpler) since `TMUX_SESSION_PRO/API` already encode the pane index, just pass the full target directly:

```js
const targets = [TMUX_SESSION_PRO, TMUX_SESSION_API];
// then use tmuxExec(`tmux send-keys -t ${targets[paneIdx]} Enter`)
```

The P0 case (paneIdx=0) works accidentally because the default `TMUX_SESSION_PRO` + `.0` = `tom_hum:brain.0.0`. That too is malformed — tmux may interpret it as `pane 0` on `window brain.0`, but in practice tmux is lenient with `.0` suffix on an already-qualified pane, so it happens to work. The P1 kickstart is broken.

---

### M4 — findIdleWorker receives sessionName but isWorkerBusy ignores it (signature mismatch)

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-spawn-manager.js:138-146,167`

```js
function findIdleWorker(sessionName = config.TMUX_SESSION, intent = 'EXECUTION') {
  const targetPane = isProIntent ? 0 : 1;
  if (!isWorkerBusy(targetPane, sessionName)) {  // passes sessionName
    ...
  }
}

function isWorkerBusy(idx) {  // sessionName silently dropped
  try {
    autoCleanStaleLock(idx);
    return fs.existsSync(workerLockFile(idx));
  } catch { return false; }
}
```

`isWorkerBusy` only accepts `idx`. The `sessionName` argument from `findIdleWorker` is silently dropped. Worker lock state is file-based (`.mission-active-P${idx}.lock`) so it is session-agnostic by design — this is not a bug in behavior. But passing `sessionName` to a function that ignores it suggests either: (a) a future intent to make lock checking session-aware, or (b) leftover from a refactor. Clean up the call to avoid confusion:

```js
if (!isWorkerBusy(targetPane)) {
```

---

## Low Priority

### L1 — Duplicate JSDoc block on generateClaudeCommand (brain-spawn-manager.js:58-66)

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-spawn-manager.js:58-66`

Two consecutive JSDoc comments describe the same function — the first (lines 57-61) is a stale description from before the model upgrade; the second (lines 62-66) is correct. The stale comment says "claude-3-7-sonnet" and "Antigravity API profile", while the live code uses `claude-opus-4-6` with direct Anthropic API. Remove the first block.

---

### L2 — respawnBrain on line 163 leaves the workerLock held through `brain_died` return path

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-mission-runner.js:160-164,229-231`

```js
// Line 160-164 (inside while loop)
if (!isSessionAlive(TMUX_SESSION)) {
  ...
  await respawnBrain(isPlanning ? 'PLAN' : 'EXECUTION', true);
  return { success: false, result: 'brain_died', elapsed };
}

// Line 229-231 (finally block)
} finally {
  clearWorkerLock(workerIdx);
}
```

The `finally` block correctly clears the lock on all exit paths — including `return` inside the loop. So the lock IS cleared. This is correct behavior; just worth confirming for reviewers.

---

### L3 — config.js OPUS_MODEL is claude-opus-4-5 while generateClaudeCommand uses claude-opus-4-6

**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/config.js:45` vs `brain-spawn-manager.js:72`

```js
// config.js
OPUS_MODEL: 'claude-opus-4-5-20250514',

// brain-spawn-manager.js (PRO pane)
`claude --model claude-opus-4-6 --dangerously-skip-permissions`
```

Two different Opus versions in two different places. `generateClaudeCommand` hardcodes `claude-opus-4-6` (correct, upgraded in this PR). `config.OPUS_MODEL` still reads `claude-opus-4-5-20250514`. If any module routes through `config.OPUS_MODEL` instead of calling `generateClaudeCommand`, it will use the old model. Confirm `config.OPUS_MODEL` is unused or update it.

Quick check: `config.OPUS_MODEL` appears in config but is not referenced in the 6 reviewed files. Verify via broader grep.

---

## Edge Cases Found by Scout

### E1 — Watchdog fires on legitimately idle pane (false positive stagnation)

The watchdog triggers after 3 consecutive identical hashes (~3 minutes). A P0 pane waiting for a slow `/plan:hard` call (LLM thinking, no output) will look identical across 3 polls. This sends a spurious Enter, which may break mid-generation by submitting incomplete input. The hash reset after kickstart (`hashHistory[paneIdx] = []`) prevents repeated spam, but one spurious Enter per 3-min stagnation window remains.

Mitigation (not blocking): consider checking for active mission lock before kickstarting. If `isWorkerBusy(paneIdx)` returns true, skip the kickstart (the pane is intentionally busy, not frozen).

### E2 — Circular dependency risk: boot-sequence lazy-require on module init

The lazy-require pattern (`require('./brain-spawn-manager').generateClaudeCommand(intent)`) inside `brain-boot-sequence.js` is called at function invocation time, not module load time — so the circular reference is broken correctly. However, if `spawnBrain()` in `brain-spawn-manager.js` ever calls `require('./brain-boot-sequence').spawnBrain` synchronously (not in an async path), and boot-sequence's top-level execution hits the lazy-require before spawn-manager finishes exporting, a partial-export cycle could surface. Current async path (`await require('./brain-boot-sequence').spawnBrain(...)`) means this executes after the event loop tick — all modules are fully initialized by then. Safe as implemented.

### E3 — respawnBrain callers in brain-mission-runner.js: both call sites return/exit immediately after

Line 105-106: `if (!ok) return brain_died_fatal` — handled.
Line 163: returns `brain_died` unconditionally — handled (effectively same behavior since ok=false always).
No caller relies on a successful respawn to continue mission dispatch. When respawnBrain is eventually re-enabled, both call sites will need logic to continue the poll loop on `ok === true`.

---

## Positive Observations

- The lazy-require approach for breaking circular dependency is idiomatic Node.js and correct.
- `startOutputHashWatchdog` resetting `hashHistory = [[], []]` on each start is clean — no stale P0/P1 history cross-contamination.
- Disabling respawnBrain with a clear explanatory comment and warning log is the right engineering tradeoff — explicitly documented, not silently removed.
- The `finally { clearWorkerLock(workerIdx) }` pattern in `runMission` is robust — all exit paths (normal, timeout, exception, brain_died) correctly release the lock.
- Duplicate function detection and single-source-of-truth enforcement (generateClaudeCommand) is good hygiene.
- All 6 files pass `node --check` with zero syntax errors.

---

## Recommended Actions

1. **[High]** Fix `sendEnter(paneIdx)` in watchdog for P1 pane — pass correct `TMUX_SESSION_API` for `paneIdx=1`. This is the only functional bug in the current code.
2. **[High]** Acknowledge or fix the dropped return value of `respawnBrain` on line 163 of `brain-mission-runner.js` — at minimum add a comment.
3. **[Medium]** Align `config.OPUS_MODEL` with the upgraded `claude-opus-4-6` model to avoid split-brain model routing if any future code uses the config constant.
4. **[Low]** Remove the stale JSDoc block (lines 57-61) from `generateClaudeCommand` in `brain-spawn-manager.js`.
5. **[Low]** Fix `findIdleWorker` call to `isWorkerBusy(targetPane)` — drop the unused `sessionName` argument.
6. **[Future]** When re-enabling `respawnBrain`, update both call sites in `brain-mission-runner.js` to continue polling on successful respawn rather than returning `brain_died`.

---

## Metrics

- Syntax errors: 0
- Circular dependency: 0 (lazy-require correctly breaks the cycle)
- Orphaned imports of removed functions: 0 (WINDOW_PRO/WINDOW_API fully removed)
- respawnBrain callers handling `false`: 1/2 (line 105 checks, line 163 does not)
- Test coverage: N/A (daemon, manual testing only per CLAUDE.md)

---

## Unresolved Questions

1. Is `config.OPUS_MODEL` (`claude-opus-4-5-20250514`) referenced anywhere outside the reviewed files? If yes, it needs updating to `claude-opus-4-6`.
2. For the watchdog false-positive risk (E1): is the intent to kickstart all frozen panes regardless of active mission, or only truly idle panes? If the former, current code is intentional. If the latter, add an `isWorkerBusy` guard.
3. When is `respawnBrain` planned to be re-enabled with per-pane granularity (kill only the dead pane, not both)? The current `false` stub is a safe placeholder but leaves brain-death unrecovered permanently until manual intervention.
