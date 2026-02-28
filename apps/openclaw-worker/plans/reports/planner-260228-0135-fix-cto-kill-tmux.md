# Planner Report: Fix CTO ngáo ngủ tắt tmux

**Date:** 2026-02-28 | **Plan:** `plans/260228-0132-debug-cto-kill-tmux/`

## Summary

3 bugs compound to cause tmux session `tom_hum` to be killed erroneously (observed twice in 20 min). All bugs trace to the same root: `TMUX_SESSION_PRO/API` constants encode a full pane target (`session:window.pane`) but are passed where only a window-level target (`session:window`) is expected.

## Root Causes Found

| # | Bug | File | Line | Effect |
|---|-----|------|------|--------|
| 1 | `capturePane(idx, TMUX_SESSION_API)` appends `.idx` to a string already ending in `.1` | `brain-tmux-controller.js` | L69 | `tom_hum:brain.1.1` invalid → false brain-dead detection |
| 2 | `respawnBrain()` passes `TMUX_SESSION_API` to `killBrain()` → `tmux kill-session -t tom_hum:brain.1` kills entire session | `brain-respawn-controller.js` | L53 | Both PRO+API panes destroyed on every respawn |
| 3 | Watchdog calls `capturePane(1)` with no sessionName → defaults to `TMUX_SESSION_PRO='tom_hum:brain.0'` → constructs `tom_hum:brain.0.1` (invalid) → always returns `''` → hash always same → false stagnation → respawn | `brain-output-hash-stagnation-watchdog.js` | L32, L62 | False stagnation every 3 min |

## Fix Strategy

**Core change:** Add `TMUX_SESSION_BASE = 'tom_hum:brain'` (window-level target) to `brain-tmux-controller.js`. All functions that append pane index internally (`capturePane`, `sendEnter`, `sendCtrlC`, `pasteText`, `waitForPrompt`) default to `TMUX_SESSION_BASE` instead of `TMUX_SESSION_PRO`. Callers pass `TMUX_SESSION_BASE` explicitly.

## Files Changed

| File | Changes |
|------|---------|
| `lib/brain-tmux-controller.js` | Add `TMUX_SESSION_BASE` const + export; fix 5 function defaults |
| `lib/brain-mission-runner.js` | Import `TMUX_SESSION_BASE`; L59 assign to local `TMUX_SESSION` var |
| `lib/brain-spawn-manager.js` | Import `TMUX_SESSION_BASE`; fix `isBrainAlive()` default |
| `lib/brain-respawn-controller.js` | Import `TMUX_SESSION_BASE`; remove `sessionName` derivation; `killBrain()` with no args |
| `lib/brain-output-hash-stagnation-watchdog.js` | Pass `TMUX_SESSION_BASE` in 3 call sites |

## Execution Order

```
Phase 1 (brain-tmux-controller.js + brain-mission-runner.js)   ~30m
  ↓
Phase 2 (brain-spawn-manager.js, brain-respawn-controller.js)  ~30m  ┐ parallel
Phase 3 (brain-output-hash-stagnation-watchdog.js)             ~30m  ┘
```

Total estimated effort: ~1h 30m

## Unresolved Questions

- `brain-mission-runner.js` L59: after setting `TMUX_SESSION = TMUX_SESSION_BASE`, the `isPlanning` check is no longer used for routing session names — confirm with Chairman that PRO/API pane routing is handled solely via `workerIdx` (0=PRO, 1=API) and not session-name switching. Current code at L67 already uses `findIdleWorker()` with `intent` to select `workerIdx` — so routing is already workerIdx-based. `TMUX_SESSION_BASE` unification should be safe.
- `isBrainAlive()` at `brain-spawn-manager.js` L107 hardcodes `${sessionName}.0` — after the default param change to `TMUX_SESSION_BASE`, callers that pass `TMUX_SESSION_PRO` explicitly (if any) would construct `tom_hum:brain.0.0`. Grep confirms no explicit caller passes anything to `isBrainAlive()` — default-only usage — so this is safe.
