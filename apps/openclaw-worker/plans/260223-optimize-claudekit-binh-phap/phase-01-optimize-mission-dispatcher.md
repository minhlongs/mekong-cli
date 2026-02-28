---
title: "Phase 1: Optimize Mission Dispatcher"
description: "Address the Hàn Băng mode issue to ensure Binh Phap is still passed or handle downgrade smarter without completely breaking the flow."
status: completed
priority: P1
effort: 1h
branch: main
tags: [optimization, mission-dispatcher, thermal, binh-phap]
created: 2026-02-23
---

# Phase 1: Optimize Mission Dispatcher

## Context Links
- [Execution Analysis Report](./reports/researcher-01-execution-analysis.md)
- [Plan Overview](./plan.md)

## Overview
**Priority:** P1
**Current Status:** completed
**Brief Description:** Modify `mission-dispatcher.js` to handle thermal downgrades (Hàn Băng Mode) more intelligently. Instead of completely replacing advanced commands (like `/plan:parallel`) with a basic `/cook`, ensure the intent and Binh Phap rules are preserved, or gracefully downgrade while keeping the core task intact. Also, expose thermal visibility in logs.

## Key Insights
- High system load (>30) currently strips advanced commands entirely, defaulting to `/cook`.
- This causes complex multi-agent Binh Phap strategies to fail silently or execute poorly.
- We need to balance CPU/RAM preservation with task fidelity.
- Thermal visibility is currently missing in the mission logs, making it hard to diagnose why a task was downgraded.

## Requirements
### Functional
- When load > 30, downgrade commands gracefully rather than dropping them entirely.
- If a command is downgraded, the original intent and core task parameters must be preserved.
- Log the thermal state and downgrade action clearly in the mission logs.

### Non-functional
- Ensure the changes do not cause the system to crash or overload when under heavy load.
- Maintain fast execution of the dispatcher logic.

## Architecture
### Component Interactions
- `mission-dispatcher.js` will interact with the system load metrics to determine the execution path.
- It will modify the prompt string sent to `brain-process-manager.js` based on the thermal state.

### Data Flow
1. Receive task and system load.
2. Check if load > 30.
3. If true, apply intelligent downgrade logic to the prompt.
4. Append thermal warning to the mission log.
5. Return formatted prompt.

## Related Code Files
- **Modify:** `lib/mission-dispatcher.js`
- **Modify:** `lib/m1-cooling-daemon.js` (if necessary for exposing load state)

## Implementation Steps
1. **Analyze Current Downgrade Logic:** Review the exact implementation of the `load > 30` check in `lib/mission-dispatcher.js`.
2. **Implement Intelligent Downgrade:**
   - Instead of replacing the command with `/cook`, try to keep the original command but remove highly parallel or memory-intensive flags if applicable.
   - If `/cook` must be used, ensure the *entire* original task description is appended to it, not just a generic message.
   - Ensure Binh Phap context is still included in the prompt.
3. **Enhance Logging:**
   - Add a visible warning to the output mission log indicating that the system is operating in Hàn Băng Mode and the command was modified.
4. **Test Logic:** Write or run existing tests to verify that high-load scenarios produce the expected degraded prompts without losing the core task.

## Todo List
- [ ] Review `lib/mission-dispatcher.js` downgrade logic.
- [ ] Implement smarter command preservation during thermal throttling.
- [ ] Add thermal state visibility to mission logs.
- [ ] Verify changes with manual or automated testing.

## Success Criteria
- Under high load (>30), advanced commands are modified to use fewer resources but retain the full task description and Binh Phap context.
- Mission logs clearly state when a downgrade occurs due to thermal throttling.

## Risk Assessment
- **Potential Issue:** Downgraded commands might still fail if the system is completely overwhelmed.
- **Mitigation:** Rely on the `m1-cooling-daemon.js` to handle extreme cases (killing processes), while this phase focuses on prompt optimization.

## Security Considerations
- No new security risks introduced. Changes are confined to prompt string manipulation.

## Next Steps
- Proceed to [Phase 2: Fix Tmux Inputs](./phase-02-fix-tmux-inputs.md) to address the dropped inputs issue.
