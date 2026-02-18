## 🧬 BRAIN SURGERY REPORT: CRITIQUE PHASE (知彼)

**Date:** 2026-02-18
**Surgeon:** Antigravity (Claude Code)
**Subject:** OpenClaw Worker Core Logic

### 1. Stale Lock Race Condition (CRITICAL)
- **Problem:** `STALE_LOCK_THRESHOLD_MS` (30m) is less than `MISSION_TIMEOUT_MS` (45m).
- **Impact:** If a valid mission runs for 35 minutes, the lock is deleted by the cleaner. The queue sees the worker as idle and dispatches a *new* mission to the *same* active tmux pane/process.
- **Result:** Interleaved inputs, double-execution, catastrophic context corruption.
- **Score:** 100/100 (Severity: 10, Fixability: 10)

### 2. Token Inefficiency (HIGH)
- **Problem:** `mission-dispatcher.js` injects a massive "CLAUDEKIT v2.9.1 MANDATORY" block into *every* mission prompt.
- **Impact:** Wastes ~1k-2k tokens per mission. Multiplied by 50 missions/day = 100k wasted tokens.
- **Result:** Slower processing, higher cost, context window pollution.
- **Score:** 63/100 (Severity: 7, Fixability: 9)

### 3. Artificial Latency (MEDIUM)
- **Problem:** `brain-process-manager.js` enforces `MIN_MISSION_SECONDS` of 60 seconds.
- **Impact:** Fast tasks (e.g., "fix typo") that finish in 5 seconds are forced to wait 55 seconds.
- **Result:** Reduced throughput for small, atomic tasks.
- **Score:** 60/100 (Severity: 6, Fixability: 10)

### 4. Regex Fragility (MEDIUM)
- **Problem:** State detection relies on fragile regex (`Thinking`, `Compacting...`) in `brain-process-manager.js`.
- **Impact:** UI changes in Claude CLI or different spinner animations cause the brain to hang or fail to detect completion.
- **Score:** 55/100 (Severity: 5, Fixability: 11)

### 5. Reactive Context Cleanup (LOW)
- **Problem:** Context clearing only happens *after* a regex warning is detected.
- **Impact:** Reactive instead of proactive. Risk of hitting hard limits before cleanup.
- **Score:** 48/100 (Severity: 8, Fixability: 6)

---

### EVOLUTION PLAN (Step 3)

We will fix the **TOP 3** weaknesses:

1.  **Fix Stale Lock Race Condition**: Increase `STALE_LOCK_THRESHOLD_MS` to 60 minutes.
2.  **Optimize Token Efficiency**: Refactor `mission-dispatcher.js` to use a lightweight prompt or one-time initialization.
3.  **Remove Artificial Latency**: Reduce `MIN_MISSION_SECONDS` to 10s or 0s (relying on robust state detection).
