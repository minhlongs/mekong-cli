# Brain Surgery Critique Report

**Date:** 2026-02-18
**Subject:** Introspection Findings & Critical Weaknesses
**Status:** CRITICAL
**Files Analyzed:**
- `apps/openclaw-worker/config.js`
- `apps/openclaw-worker/lib/brain-process-manager.js`
- `apps/openclaw-worker/lib/mission-dispatcher.js`

## Executive Summary
A deep introspection of the OpenClaw Worker brain architecture has revealed critical flaws that threaten stability and efficiency. Code analysis confirms 4 major weaknesses.

## Weaknesses Detected

### 1. Stale Lock Race Condition (CRITICAL)
**Location:**
- `apps/openclaw-worker/config.js`: `MISSION_TIMEOUT_MS: 45 * 60 * 1000` (Line 25)
- `apps/openclaw-worker/lib/brain-process-manager.js`: `STALE_LOCK_THRESHOLD_MS = 30 * 60 * 1000` (Line 527)

**Analysis:**
`STALE_LOCK_THRESHOLD_MS` (30m) < `MISSION_TIMEOUT_MS` (45m).
This allows a new mission to "steal" the lock of a running mission if it runs longer than 30 minutes but less than 45 minutes. This results in two brain processes fighting for control of the same tmux pane, leading to catastrophic command injection collisions.

- **Severity:** 10 (Catastrophic collision)
- **Fixability:** 10 (Config change)
- **Score:** 100
- **Action:** Increase `STALE_LOCK_THRESHOLD_MS` to 60m or reduce `MISSION_TIMEOUT_MS`.

### 2. Token Inefficiency
**Location:**
- `apps/openclaw-worker/lib/mission-dispatcher.js`: `buildPrompt` function (Lines 130-271)

**Analysis:**
The `buildPrompt` function injects a massive static prompt for every single mission, including:
- "COMMANDER RULE 13" / "HÀN BĂNG MODE" (Lines 164-169)
- "CLAUDEKIT v2.9.1 MANDATORY" block (Lines 200-207)
- Routing logic descriptions (Lines 187-197)

This consumes the context window unnecessarily, increasing costs and latency, and reducing the model's "thinking" capacity for the actual task.

- **Severity:** 7 (Cost/Speed)
- **Fixability:** 9 (Prompt engineering)
- **Score:** 63
- **Action:** Refactor prompt construction to be dynamic and lean. Use a condensed system prompt or specialized prompts based on task type.

### 3. Artificial Latency
**Location:**
- `apps/openclaw-worker/lib/brain-process-manager.js`: `MIN_MISSION_SECONDS = 60` (Line 41)

**Analysis:**
The `detectState` function enforces `elapsedSec > MIN_MISSION_SECONDS` (Line 846) before accepting an "idle-no-busy" completion state. This forces the worker to sleep/poll for at least 60 seconds even if a trivial task (e.g., "read file") completed in 5 seconds.

- **Severity:** 6 (Throughput)
- **Fixability:** 10 (Config change)
- **Score:** 60
- **Action:** Reduce `MIN_MISSION_SECONDS` to 10s or implement smarter busy detection.

### 4. Reactive Context Cleanup
**Location:**
- `apps/openclaw-worker/lib/brain-process-manager.js`: `hasContextLimit` (Lines 98-103) & `compactIfNeeded` (Lines 495-503)

**Analysis:**
The brain primarily relies on reactive cleanup (`/Context limit reached/i` regex) or a very loose periodic check (`COMPACT_EVERY_N = 50`). This is risky for long-running sessions where context degradation happens before the hard limit is hit.

- **Severity:** 8 (Risky memory management)
- **Fixability:** 6 (Requires logic overhaul)
- **Score:** 48
- **Action:** Implement proactive context window management based on token usage tracking.

## Conclusion
The **Stale Lock Race Condition** is a critical stability risk (Score 100) and must be patched immediately (P0). Other issues affect performance and efficiency and should be addressed in the `v2026.2.19` patch.
