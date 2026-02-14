# Report: CLAUDE.md Updated to v29.0 Multi-Pane Architecture

**Agent:** project-manager
**Date:** 2026-02-11
**File:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/CLAUDE.md`

## Changes Made

### Version
- v2026.2.9 -> v29.0

### Tech Stack Table
- Brain Control: "Dual-mode: direct/tmux" -> "Multi-pane tmux (v29, primary) or external (legacy fallback)"

### Architecture Tree
- Added `brain-tmux.js` as PRIMARY brain module
- Added `brain-headless-per-mission.js` (alternative)
- Added `mission-complexity-classifier.js`
- Marked `brain-process-manager.js` as legacy fallback
- Updated `task-queue.js` description: "concurrent processing"
- Updated `m1-cooling-daemon.js` description: "+ pane throttling"

### config.js Section
- Added `PANE_COUNT` (env: `TOM_HUM_PANE_COUNT`, default 4)
- Added `TMUX_SESSION` = `tom_hum_brain`
- Removed `BRAIN_MODE` (no longer dual-mode; tmux is primary)

### Brain Architecture (fully rewritten)
- **Primary: Multi-Pane Tmux** — spawnBrain creates N panes, acquirePane/releasePane, per-pane state, named paste buffers, per-pane context management, crash recovery, backward compat (PANE_COUNT=1)
- **Fallback: External Mode** — legacy brain-process-manager.js
- **New section: Concurrent Processing** — task-queue.js with getMaxActivePanes() gating
- **New section: Load-Based Pane Throttling** — load >7 = 0 panes, 5-7 = 2 panes, <5 = all panes

### Development Rules
- Test instructions updated for brain-tmux.js (was brain-process-manager.js)
- Added single-pane and multi-pane test commands

### Quality Gates
- "Sequential processing only" -> "Concurrent processing up to PANE_COUNT (default 4), throttled by M1 load"
- "Auto-CTO generates quality tasks when queue empty for 5min" -> "30s" (matches config.AUTO_CTO_EMPTY_THRESHOLD = 6 * 5s)
- Added "+ dynamic pane throttling" to M1 cooling daemon line

## Verified Against Source
- `brain-tmux.js` (477 lines) — multi-pane architecture confirmed
- `config.js` — PANE_COUNT=4, TMUX_SESSION='tom_hum_brain' confirmed
- `task-queue.js` — concurrent processQueue + getMaxActivePanes confirmed
- `m1-cooling-daemon.js` — getMaxActivePanes() load thresholds confirmed
- `task-watcher.js` — imports brain-tmux (not brain-process-manager) confirmed
- `mission-dispatcher.js` — imports runMission from brain-tmux confirmed
