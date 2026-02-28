# Phase 1: Output Capture & File Reading (Layer 1)

## Objective
Replace tmux socket polling with local file reading.

## Implementation Steps
1. In `lib/brain-process-manager.js`, ensure `runMission` wraps its logic in `try-finally` and calls `clearMissionLock()` in the `finally` block to prevent mission lock leaks.
2. In `lib/brain-process-manager.js`, ensure `tmux capture-pane` is completely replaced by local file reading (e.g., using `tail -n 50`) in the `capturePane` function where possible.
3. Validate file paths when reading local log files.
4. Remove any rogue `console.log` statements in production paths for these functions.
