# P1 Proxy Hang Investigation

**Date:** 2026-02-27 21:08
**Agent:** debugger
**Report:** debugger-260227-2108-p1-proxy-hang-investigation.md

---

## Executive Summary

P1 (Gemini Proxy Executor) hangs frequently due to **3 compounding root causes**:

1. **CRITICAL — Model quota exhausted:** `gemini-3.1-pro-high` is at **0% remaining on ALL accounts** (reset: 14:38 UTC). P1 has no explicit `--model` flag, so the proxy silently blocks/stalls on rate-limited requests instead of fast-failing.
2. **HIGH — Watchdog only monitors P0, not P1:** `brain-output-hash-stagnation-watchdog.js` calls `capturePane()` with no `workerIdx` (defaults to `1`, but `sendEnter` hardcodes pane `0`). Stagnation detection fires only on P0; P1 hangs silently.
3. **MEDIUM — `TMUX_SESSION_PRO` and `TMUX_SESSION_API` are identical strings** (`tom_hum:brain`). This means any module defaulting to `TMUX_SESSION_API` still targets P0's session namespace — no isolation at the tmux level.

---

## Evidence

### 1. Proxy health — P1 model 0% quota on all accounts

```json
billwill.mentor@gmail.com:
  gemini-3.1-pro-high remaining: 0%  | rateLimited: true | reset: 14:38 UTC
  gemini-3.1-pro-low remaining: 0%   | rateLimited: true
  claude-opus-4-6-thinking: 0%       | rateLimited: true
  claude-sonnet-4-6: 0%              | rateLimited: true

cashback.mentoring@gmail.com:
  gemini-3.1-pro-high remaining: 0%  | rateLimited: true | reset: 14:38 UTC
  gemini-3.1-pro-low remaining: 0%   | rateLimited: true
  claude-opus-4-6-thinking: 0%       | rateLimited: true
  claude-sonnet-4-6: 0%              | rateLimited: true
```

P1 pane shows: `🤖 gemini-3.1-pro-high[1m]  🔋 5%  ⏰ 3`
The model `gemini-3.1-pro-high` is **exhausted on ALL 2 accounts simultaneously**.

P0 (Pro) uses `claude-3-7-sonnet-20250219` via `CLAUDE_CONFIG_DIR=~/.claude_antigravity_pro` with `unset ANTHROPIC_BASE_URL` — it bypasses the proxy entirely, hence no quota pressure.

### 2. Watchdog monitors P0, not P1

File: `lib/brain-output-hash-stagnation-watchdog.js`

```js
// capturePane() called with NO workerIdx — defaults to idx=1 in capturePane()
const output = capturePane();   // line 31 and 60

// BUT sendEnter() hardcodes PANE 0, not pane 1:
sendEnter(0);   // line 53 ← BUG: kickstart goes to P0, not P1
```

`capturePane(workerIdx)`: when called with no arg, `idx = workerIdx !== undefined ? workerIdx : 1` → captures **P1**.
`sendEnter(0)` → sends Enter to **P0**.

So: watchdog detects P1 stagnation, but kicks P0. P1 stagnation is never resolved.

Log evidence at 14:09:40:
```
[14:09:40] [tom-hum] [HASH_WATCHDOG] Output stagnation detected (3x same hash: 5a5d904b6a7467d6)
[14:09:40] [tom-hum] [HASH_WATCHDOG] Step 1: Sending kickstart newline
```
(kickstart went to P0, P1 remained hung)

### 3. TMUX_SESSION_PRO == TMUX_SESSION_API (same string)

```js
// brain-tmux-controller.js lines 15-16:
const TMUX_SESSION_PRO = `${config.TMUX_SESSION}:brain`;
const TMUX_SESSION_API = `${config.TMUX_SESSION}:brain`;  // IDENTICAL
```

No separate session for API — both names resolve to `tom_hum:brain`. Differentiation happens only via pane index (0 vs 1), but modules that default to `sessionName = TMUX_SESSION_PRO` may address wrong panes.

### 4. Supervisor reports 60% success rate, triggers surgery at every cycle

```
[14:06:15] [supervisor] Level 4: Triggering brain surgery — Success rate 60% < 70%
[14:07:27] [supervisor] Level 4: Triggering brain surgery — Success rate 60% < 70%
[14:08:27] [supervisor] Brain surgery on cooldown, skipping
[14:09:27] [supervisor] Brain surgery on cooldown, skipping
```

Evolution check returns `triggered=false, score=undefined` — surgery not actually executing, but the continuous respawn cycle causes repeated Tom Hum restarts. Each restart re-boots dual-pane tmux, loses P1 mid-task state.

### 5. P1 has no explicit model fallback in boot command

```js
// brain-spawn-manager.js / brain-boot-sequence.js API command:
`export ANTHROPIC_BASE_URL="http://127.0.0.1:9191"` +
`&& claude --dangerously-skip-permissions`   // NO --model flag
```

The proxy picks the model. When `gemini-3.1-pro-high` is exhausted, the proxy's fallback behavior determines what happens — if no available fallback model is configured or all are exhausted, the request hangs waiting for retry or timeout.

---

## Root Cause Chain

```
gemini-3.1-pro-high EXHAUSTED (0% both accounts)
  → P1 sends requests → proxy blocks/stalls → P1 hangs waiting
  → Watchdog detects P1 stagnation (captures pane 1)
  → BUT: watchdog sends kickstart to pane 0 (P0) ← wrong target
  → P1 still hung, nothing resolved
  → After 3 stagnation cycles: triggers respawn
  → Supervisor also sees 60% success rate → triggers surgery
  → Tom Hum restarts → new dual-pane boot → P1 gets same exhausted model
  → Cycle repeats every ~3-5 min
```

---

## Fix Recommendations

### Fix 1 (CRITICAL): Correct watchdog kickstart target — send to pane 1, not 0

File: `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/brain-output-hash-stagnation-watchdog.js`

```js
// Line 53 — BEFORE:
sendEnter(0);

// AFTER:
const workerIdx = 1; // P1 is the executor pane being monitored
sendEnter(workerIdx);
```

Also: make `capturePane()` and `sendEnter()` use a consistent `WATCHDOG_PANE` constant:

```js
const WATCHDOG_PANE = 1; // P1 = Executor (API) pane

// In checkOutputHash:
const output = capturePane(WATCHDOG_PANE);

// In handleStagnation:
sendEnter(WATCHDOG_PANE);
// ... post-check:
const output = capturePane(WATCHDOG_PANE);
```

### Fix 2 (CRITICAL): Add explicit model fallback for P1 when primary exhausted

File: `lib/brain-boot-sequence.js` / `lib/brain-spawn-manager.js`

```js
// API command — add a fallback-friendly model that has quota
function generateClaudeCommand(intent = 'API') {
  // ...
  return `export CLAUDE_CONFIG_DIR="${dir}" && unset ANTHROPIC_API_KEY` +
    ` && export ANTHROPIC_BASE_URL="http://127.0.0.1:9191" && export ANTHROPIC_AUTH_TOKEN="test"` +
    ` && export NPM_CONFIG_WORKSPACES=false && export npm_config_workspaces=false` +
    ` && claude --model gemini-2.5-pro --dangerously-skip-permissions`;
    //                  ^^^^^^^^^^^^^^^^^^ explicitly pick model with available quota
}
```

`gemini-2.5-pro` currently has **100% remaining** on both accounts. Or use the proxy's fallback chain by picking a model with available quota instead of relying on proxy auto-selection when primary is exhausted.

### Fix 3 (HIGH): Add P1-specific stagnation recovery — model rotation on repeated hangs

When P1 stagnates > 2 cycles without recovery after kickstart, inject a model-switch hint:

```js
// In handleStagnation — after kickstart fails:
if (stallCount >= 2) {
  log('[HASH_WATCHDOG] P1 persistent stagnation — injecting model switch');
  const { pasteText, sendEnter } = require('./brain-tmux-controller');
  pasteText('/model', 1); // trigger CC CLI model picker or use proxy fallback
  sendEnter(1);
}
```

### Fix 4 (MEDIUM): Disambiguate TMUX_SESSION_API constant

File: `lib/brain-tmux-controller.js`

```js
// Current (confusing — same value):
const TMUX_SESSION_PRO = `${config.TMUX_SESSION}:brain`;
const TMUX_SESSION_API = `${config.TMUX_SESSION}:brain`;

// Better: make the pane index explicit in naming, keep same session:
const TMUX_SESSION = `${config.TMUX_SESSION}:brain`;
const TMUX_PANE_PRO = 0;  // P0 — Planner
const TMUX_PANE_API = 1;  // P1 — Executor
```

### Fix 5 (LOW): Supervisor surgery loop — fix evolution-engine return value

`checkEvolutionTriggers()` returns `triggered=false, score=undefined`. The surgery fires but does nothing, causing constant supervisor noise. Either fix the evolution engine return shape or add a guard:

```js
// brain-supervisor.js triggerSurgery():
const result = checkEvolutionTriggers();
if (!result || result.score === undefined) {
  log('Evolution engine returned invalid result — skipping surgery');
  return false;
}
```

---

## Immediate Action

P1 is currently hung right now. `gemini-3.1-pro-high` resets at **14:38 UTC** (~28 min from report time 14:10).

To recover P1 immediately without waiting for reset:

```bash
# Option A: Send kickstart to P1 directly
tmux send-keys -t tom_hum:brain.1 Enter

# Option B: Switch P1 to gemini-2.5-pro (100% quota available)
tmux send-keys -t tom_hum:brain.1 '/model gemini-2.5-pro' Enter

# Option C: Wait for 14:38 UTC reset — gemini-3.1-pro-high restores
```

---

## Summary Table

| # | Issue | Severity | File | Fix |
|---|-------|----------|------|-----|
| 1 | `gemini-3.1-pro-high` 0% quota — P1 blocks on every LLM call | CRITICAL | proxy / boot-sequence | Use `gemini-2.5-pro` (100% available) explicitly in P1 command |
| 2 | Watchdog `sendEnter(0)` fixes P0, not hung P1 | HIGH | brain-output-hash-stagnation-watchdog.js | Change to `sendEnter(1)` + consistent `WATCHDOG_PANE=1` |
| 3 | `TMUX_SESSION_PRO == TMUX_SESSION_API` — no isolation | MEDIUM | brain-tmux-controller.js | Export `TMUX_PANE_PRO=0`, `TMUX_PANE_API=1` constants |
| 4 | Supervisor triggers surgery every 60s but `evolution-engine` returns undefined | MEDIUM | brain-supervisor.js | Guard on `result.score === undefined` |
| 5 | No per-pane stagnation counter — can't distinguish P0 vs P1 freeze | LOW | brain-output-hash-stagnation-watchdog.js | Track stagnation per pane index |

---

## Unresolved Questions

- Does the proxy have a configured fallback model for `gemini-3.1-pro-high` exhaustion? (Not visible from `/health` endpoint — need to check proxy `accounts.json`.)
- Is there a second proxy on port 9192 (Cashback)? `lobster-proxy-pilot.js` references it but `ANTHROPIC_BASE_URL` in P1 only points to 9191. If 9192 is healthy, routing P1 there would double available quota.
- Why does P1 show `🔋 5%` context? If context is near full, `/compact` would help — but supervisor's compact only fires on < 15% and sends to the whole session (`${TMUX_SESSION}` without pane index), not specifically P1.
