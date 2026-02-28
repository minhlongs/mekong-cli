---
title: "Fix CTO Tmux Freeze with 3-Layer Parallel Architecture"
description: "Resolves event loop freezing caused by execSync tmux capture-pane under parallel subagent load"
status: pending
priority: P1
effort: 2h
branch: master
tags: [core, bugfix, performance, tmux]
created: 2026-02-23
---

# Fix CTO Tmux Freeze (Parallel Mode)

## Overview
This plan implements the 3-layer solution requested by the CTO to eliminate event-loop blocking caused by frequent `execSync('tmux capture-pane')` polling when CC CLI spawns multiple parallel subagents.

## Implementation Phases

### Phase 1: Output Capture & File Reading (Layer 1)
- **Status**: Pending
- **File**: [phase-01-log-capture.md](./phase-01-log-capture.md)
- **Objective**: Replace tmux socket polling with local file reading using macOS `script` utility.

### Phase 2: Hang Detection (Layer 2)
- **Status**: Pending
- **File**: [phase-02-hang-detection.md](./phase-02-hang-detection.md)
- **Objective**: Implement 3-minute mtime-based inactivity detection and Ctrl+C intervention.

### Phase 3: Tmux Rate Limiting (Layer 3)
- **Status**: Pending
- **File**: [phase-03-tmux-rate-limit.md](./phase-03-tmux-rate-limit.md)
- **Objective**: Apply tmux optimizations (`c0-change-interval` and alternatives) to throttle TUI redraws.
