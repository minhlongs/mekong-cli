---
title: "Phase 3: Improve State Detection"
description: "Address the state detection fragility (make regex more robust for CC CLI)."
status: completed
priority: P2
effort: 2h
branch: main
tags: [optimization, state-detection, regex, tmux]
created: 2026-02-23
---

# Phase 3: Improve State Detection

## Context Links
- [Execution Analysis Report](./reports/researcher-01-execution-analysis.md)
- [Plan Overview](./plan.md)

## Overview
**Priority:** P2
**Current Status:** pending
**Brief Description:** Modify `brain-process-manager.js` (and any related polling logic) to address the fragility of state detection. The orchestrator tracks execution by polling Tmux output and matching regex patterns (`BUSY_PATTERNS`, `COMPLETION_PATTERNS`). If ClaudeKit updates its UI, these regexes might fail. Reduce reliance on exact text matching and explore process-level checks or more robust regex patterns.

## Key Insights
- Relying solely on exact text matching for `BUSY_PATTERNS` can lead to false negatives (system incorrectly assumes it's idle).
- The system might incorrectly assume the process finished instantly or failed, missing the execution window entirely.
- Automated prompts (like answering "2" for API keys) can stall if the prompt text changes slightly.

## Requirements
### Functional
- Enhance the regex patterns in `BUSY_PATTERNS` and `COMPLETION_PATTERNS` to be more resilient to UI changes.
- Consider adding alternative state checks (e.g., CPU usage, presence of the `claude` child process).
- Ensure the state detection accurately differentiates between "idle waiting for input", "busy processing", and "completed".

### Non-functional
- State detection must be fast and reliable.

## Architecture
### Component Interactions
- `brain-process-manager.js` polls Tmux output.
- It evaluates the output against `BUSY_PATTERNS` and `COMPLETION_PATTERNS` to determine the state (`idle`, `busy`).
- If alternative state checks are added, they will interact with system utilities (e.g., `ps`, `top`) to provide additional context.

### Data Flow
1. Fetch Tmux pane output.
2. Evaluate output against robust regex patterns.
3. If necessary, query system process information.
4. Update internal state (`isBusy`, `idleTime`, etc.).

## Related Code Files
- **Modify:** `lib/brain-process-manager.js`

## Implementation Steps
1. **Analyze Current Regex Patterns:** Review `BUSY_PATTERNS` and `COMPLETION_PATTERNS` in `lib/brain-process-manager.js`.
2. **Improve Regex Robustness:**
   - Expand `BUSY_PATTERNS` to include common keywords (e.g., "Thinking", "Reading", "Writing", "Executing") rather than strict exact matches.
   - Refine `COMPLETION_PATTERNS` (e.g., `❯`) to account for varying terminal environments or slight UI changes.
3. **Explore Process-Level Checks (Optional but Recommended):**
   - Investigate if it's feasible to check if the `claude` process (or its children) is actively using CPU as a supplementary indicator of `busy` state.
4. **Test State Detection:** Simulate various ClaudeKit outputs (busy, idle, completed) and verify that the orchestrator accurately tracks the state.

## Todo List
- [ ] Review `lib/brain-process-manager.js` regex patterns.
- [ ] Expand and refine `BUSY_PATTERNS` and `COMPLETION_PATTERNS`.
- [ ] Investigate process-level checks (CPU/process presence).
- [ ] Verify state tracking accuracy under different scenarios.

## Success Criteria
- The orchestrator reliably detects `busy` and `completed` states even if ClaudeKit introduces minor UI changes.
- False negatives (assuming idle when busy) and silent failures are significantly reduced.

## Risk Assessment
- **Potential Issue:** Overly broad regex patterns might lead to false positives (assuming busy when idle).
- **Mitigation:** Carefully balance the regex patterns and consider process-level checks as a secondary verification mechanism.

## Security Considerations
- No new security risks introduced.

## Next Steps
- Begin implementation of [Phase 1: Optimize Mission Dispatcher](./phase-01-optimize-mission-dispatcher.md).
