---
title: "Fix CTO ngáo ngủ tắt tmux"
description: "3 targeted fixes for tmux session kill bugs: double pane-indexing in capturePane, killBrain targeting wrong session, watchdog targeting wrong pane."
status: pending
priority: P1
effort: 1.5h
branch: master
tags: [bugfix, tmux, openclaw-worker, daemon]
created: 2026-02-28
---

# Fix: CTO ngáo ngủ tắt tmux

## Problem Summary

Tmux sessions killed erroneously 2x in 20 minutes due to 3 compounding bugs in session-name/pane-index handling.

## Dependency Graph

```
Phase 1 (brain-tmux-controller.js)
  └─ Phase 2 (brain-spawn-manager.js, brain-respawn-controller.js)  ← after Phase 1
  └─ Phase 3 (brain-output-hash-stagnation-watchdog.js)             ← after Phase 1
```

Phase 2 and Phase 3 can run in parallel after Phase 1 completes.

## File Ownership Matrix

| Phase | File | Lines Changed | Can Parallel? |
|-------|------|---------------|---------------|
| 1 | `lib/brain-tmux-controller.js` | L15-16, L54-69 | No (blocks 2+3) |
| 2 | `lib/brain-spawn-manager.js` | L94, L103-111 | Yes (with Phase 3) |
| 2 | `lib/brain-respawn-controller.js` | L44, L53 | Yes (with Phase 3) |
| 3 | `lib/brain-output-hash-stagnation-watchdog.js` | L18, L32, L55, L62 | Yes (with Phase 2) |

## Phases

| # | Phase | Status | Effort |
|---|-------|--------|--------|
| 1 | [Fix capturePane double-indexing](phase-01-fix-capture-pane-double-indexing.md) | pending | 30m |
| 2 | [Fix killBrain session target](phase-02-fix-kill-brain-session-target.md) | pending | 30m |
| 3 | [Fix watchdog pane targeting](phase-03-fix-watchdog-pane-targeting.md) | pending | 30m |

## Key Dependencies

- `config.TMUX_SESSION = 'tom_hum'` (base session name)
- `TMUX_SESSION_PRO = 'tom_hum:brain.0'` — includes window AND pane index
- `TMUX_SESSION_API = 'tom_hum:brain.1'` — includes window AND pane index
- Phase 1 exports `TMUX_SESSION_BASE` which phases 2 and 3 consume
