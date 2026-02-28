---
title: "Phase 2: Fix Tmux Inputs"
description: "Address the dropped inputs issue (e.g., re-enable kick-start safely, or ensure send-keys is reliable)."
status: completed
priority: P1
effort: 1h
branch: main
tags: [optimization, tmux, inputs, kick-start]
created: 2026-02-23
---

# Phase 2: Fix Tmux Inputs

## Context Links
- [Execution Analysis Report](./reports/researcher-01-execution-analysis.md)
- [Plan Overview](./plan.md)

## Overview
**Priority:** P1
**Current Status:** pending
**Brief Description:** Modify `brain-process-manager.js` to address the dropped inputs issue in Tmux. The previous kick-start mechanism was disabled because it resent the entire prompt, causing duplicate tasks. A smarter, dynamic kick-start must be implemented to only send an empty `\n` if the state remains `idle` with text sitting on the prompt line.

## Key Insights
- The orchestration relies on pasting text into Tmux and sending an `Enter` keystroke.
- If Tmux drops the initial `Enter` or the CLI is sluggish, the prompt sits on the line forever.
- The system eventually times out or misclassifies the state, causing silent mission failures.
- Sending the full prompt again causes duplicate tasks.

## Requirements
### Functional
- Detect if a prompt has been sent but the CLI remains in the `idle` state for an extended period.
- If stuck, send *only* an empty `\n` to kick-start the process without duplicating the prompt.
- Ensure the state detection logic accurately identifies a stuck prompt versus genuine idle waiting.

### Non-functional
- The kick-start mechanism must be reliable and not trigger prematurely.

## Architecture
### Component Interactions
- `brain-process-manager.js` manages the Tmux session and state polling.
- It will monitor the state and invoke the new kick-start logic if a timeout threshold is reached after sending a command.

### Data Flow
1. Send command via Tmux.
2. Start monitoring state (`idle`, `busy`).
3. If state remains `idle` after a specific duration (e.g., 5-10 seconds), send a single `\n` via Tmux.
4. Continue monitoring for state change.

## Related Code Files
- **Modify:** `lib/brain-process-manager.js`

## Implementation Steps
1. **Analyze `brain-process-manager.js`:** Review the existing state polling and command submission logic.
2. **Implement Smart Kick-Start:**
   - Add a timer or state tracker to monitor how long the system has been `idle` since the last command was sent.
   - Create a `sendEnter()` function (or modify the existing one) to send *only* `\n` (using `tmux send-keys Enter`).
   - Trigger `sendEnter()` if the idle timeout is exceeded.
3. **Verify:** Test the new kick-start mechanism by intentionally delaying or dropping the initial Enter key during a manual test to see if the system recovers.

## Todo List
- [ ] Review Tmux command submission logic in `lib/brain-process-manager.js`.
- [ ] Implement smart `\n`-only kick-start.
- [ ] Add timeout/state tracking to trigger kick-start.
- [ ] Verify fix prevents duplicate tasks and stalled missions.

## Success Criteria
- Missions do not stall indefinitely when the initial `Enter` is dropped or delayed.
- The kick-start mechanism successfully triggers execution without duplicating the task.

## Risk Assessment
- **Potential Issue:** Kick-start might trigger prematurely if the CLI is genuinely slow to respond to the initial Enter, potentially causing issues if it was already processing.
- **Mitigation:** Set a conservative timeout (e.g., 10 seconds) before triggering the kick-start.

## Security Considerations
- No new security risks introduced.

## Next Steps
- Proceed to [Phase 3: Improve State Detection](./phase-03-improve-state-detection.md) to address regex fragility.
