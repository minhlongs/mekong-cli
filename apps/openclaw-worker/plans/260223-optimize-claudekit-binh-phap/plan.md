---
title: "Optimize Binh Phap and ClaudeKit Execution"
description: "Implementation plan to address execution failures of Binh Phap rules and ClaudeKit commands in OpenClaw worker"
status: pending
priority: P1
effort: 3h
branch: main
tags: [optimization, execution, binh-phap, claudekit, openclaw]
created: 2026-02-23
---

# Optimize Binh Phap and ClaudeKit Execution

## Overview
This plan addresses the execution failures of Binh Phap rules and ClaudeKit slash commands in the OpenClaw worker. The primary issues are related to thermal downgrades bypassing advanced commands, dropped inputs in Tmux causing tasks to hang, and fragile state detection based on regex matching.

## Phases

### [Phase 1: Optimize Mission Dispatcher](./phase-01-optimize-mission-dispatcher.md)
**Status:** pending
**Priority:** P1
**Focus:** Address the Hàn Băng (thermal management) mode issue. Ensure Binh Phap commands are properly preserved or downgraded intelligently without breaking the execution flow, and expose thermal state in logs.

### [Phase 2: Fix Tmux Inputs](./phase-02-fix-tmux-inputs.md)
**Status:** pending
**Priority:** P1
**Focus:** Address dropped inputs in Tmux by re-enabling and improving the kick-start mechanism safely to prevent duplicate task dispatches while ensuring commands are successfully submitted.

### [Phase 3: Improve State Detection](./phase-03-improve-state-detection.md)
**Status:** pending
**Priority:** P2
**Focus:** Address the fragility of state detection by expanding regex patterns, reducing reliance on exact text matching, and potentially incorporating process-level checks to accurately determine when ClaudeKit is busy or idle.

## Dependencies
- Access to OpenClaw worker source code (`lib/mission-dispatcher.js`, `lib/brain-process-manager.js`).
- Understanding of ClaudeKit CLI prompt behavior.

## Key Considerations
- Ensure that modifying the kick-start mechanism strictly avoids duplicating tasks (the reason it was previously disabled).
- Thermal downgrades must balance system stability with the need to execute complex Binh Phap plans.