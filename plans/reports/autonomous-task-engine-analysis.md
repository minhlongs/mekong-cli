# Autonomous Task Engine Analysis

**Date:** 2026-02-15
**System:** OpenClaw Worker (Tom Hum) v2026.2.13
**Scope:** Architecture analysis of the autonomous execution system.

## 1. Executive Summary

The OpenClaw Worker ("Tom Hum") is a robust, autonomous daemon designed to manage and execute coding tasks using the Claude Code CLI. It features a sophisticated architecture that supports:
- **Parallel Execution:** Running multiple missions simultaneously across different tmux panes.
- **Self-Healing:** Automatic recovery from proxy failures, model errors, and CLI crashes.
- **Auto-Pilot (Auto-CTO):** Self-generation of maintenance and quality assurance tasks when the queue is idle.
- **Resource Management:** Thermal protection for M1 chips and context window management.
- **Constitutional Safety:** Pre-flight LLM-based validation of mission intent.

## 2. Architecture Overview

The system operates as a Node.js daemon (`task-watcher.js`) that orchestrates several subsystems:

| Component | Responsibility |
|-----------|----------------|
| **Task Watcher** (`task-watcher.js`) | Lifecycle management, boot sequence, and signal handling. |
| **Task Queue** (`lib/task-queue.js`) | File watching, queue management, and concurrency control. |
| **Mission Dispatcher** (`lib/mission-dispatcher.js`) | Project routing, prompt engineering, and execution triggers. |
| **Brain Manager** | Dual-mode execution engine: **Tmux** (persistent) or **Headless** (per-mission). |
| **Auto-CTO** (`lib/auto-cto-pilot.js`) | Generates work during idle periods. |
| **Self Healer** (`lib/self-healer.js`) | System health monitoring and recovery. |
| **Safety Guard** (`lib/safety-guard.js`) | LLM-based constitutional check before dispatch. |
| **Team Mutex** (`lib/team-mutex.js`) | Locking mechanism to prevent resource contention between Swarm and Agent Teams. |

### Data Flow
1. **Input:** Task files (`mission_*.txt`) are dropped into `tasks/`.
2. **Detection:** `task-queue.js` detects new files via `fs.watch` or polling.
3. **Safety Check:** `safety-guard.js` validates the prompt using `gemini-1.5-flash` against the Binh Phap Constitution.
4. **Dispatch:** If concurrency slots are available, `mission-dispatcher.js` routes the task to the correct project and builds the prompt.
5. **Execution:**
    - **Tmux Mode:** `brain-tmux.js` selects an idle worker pane.
    - **Headless Mode:** `brain-headless-per-mission.js` spawns a dedicated `claude -p` process.
6. **Completion:** Upon success/failure, the task file is moved to `tasks/processed/`, and the result is logged/notified (Telegram).
7. **Idle:** If the queue is empty, `auto-cto-pilot.js` generates new maintenance tasks.

## 3. Key Subsystems Analysis

### 3.1. Parallel Coordination & Brain Modes
The system supports two execution modes for the "Brain" (Claude Code CLI):

- **Tmux Mode (`lib/brain-tmux.js`):**
    - **Persistent Session:** Runs inside a `tmux` session named `tom_hum_brain`.
    - **Worker Rotation:** Implements `rotateWorker()` to select idle panes (P1-P3).
    - **State Detection:** Regex-based scraping of pane output to detect `BUSY`, `DONE`, or `STUCK`.
    - **Isolation:** Named buffers used for pasting text to prevent race conditions.

- **Headless Mode (`lib/brain-headless-per-mission.js`):**
    - **Per-Mission Process:** Spawns a fresh `claude -p` process for each mission.
    - **Isolation:** Complete process isolation; a crash in one mission does not affect others.
    - **Configuration:** `stdin` must be set to `ignore` to prevent hanging.
    - **Logging:** Output streamed directly to `tom_hum_cto.log`.

### 3.2. Self-Assigning Task Logic (Auto-CTO)
Implemented in `lib/auto-cto-pilot.js`, this subsystem ensures the agent is never idle.

- **Trigger:** Activates when the task queue is empty for a defined threshold.
- **Strategy:** Round-robin iteration through configured projects (`config.PROJECTS`).
- **Task Selection:** Picks from a predefined list of "Binh Phap" tasks (e.g., `type_safety`, `console_cleanup`, `security_scan`).
- **Applicability:** Checks if the task is relevant to the project (e.g., checks for `tsconfig.json` for TypeScript tasks).
- **Persistence:** Maintains state in `.tom_hum_state.json` to track completed tasks per project.
- **Infinite Loop:** Resets completion state when all tasks are done to ensure continuous improvement.

### 3.3. Failure Recovery Mechanisms
The system is designed to be resilient ("Antifragile").

- **Self-Healer (`lib/self-healer.js`):**
    - **Proxy Check:** Verifies proxy health before every dispatch. Restarts `anthropic-adapter.js` if down.
    - **CLI Monitor:** Checks for stuck sessions, shell prompts (crash), or stale output.
    - **Nuclear Option:** Fully kills and respawns the tmux pane if recovery fails multiple times.

- **Mission Recovery (`lib/mission-recovery.js`):**
    - **Model Fallback:** Switches models (e.g., Sonnet -> Gemini -> Qwen) on HTTP 400/429 errors.
    - **Context Overflow:** Truncates prompts that exceed token limits to 8000 characters.

### 3.4. Constitutional Safety Guard
Implemented in `lib/safety-guard.js`, this module acts as a pre-flight risk assessment.

- **Mechanism:** Calls `gemini-1.5-flash` via the proxy to analyze the raw mission prompt.
- **Constitution:** Checks against 5 rules:
    1. No destructive actions (mass deletion).
    2. No exfiltration of secrets.
    3. No unauthorized modification of core rules.
    4. No malicious code execution.
    5. No recursive harm (fork bombs).
- **Fail-Open:** If the safety check fails (network error), it allows the mission to proceed to prevent blocking work, logging the error.

### 3.5. Team Mutex (Swarm vs. Agent Teams)
Implemented in `lib/team-mutex.js`, this prevents resource contention.

- **Problem:** "Swarm" mode runs many lightweight daemons. "Agent Teams" spawn 4-9 heavy sub-agents. Running both kills the machine.
- **Solution:** File-based lock (`/tmp/tom_hum_team_active.lock`).
- **Logic:**
    - When an Agent Team starts, it acquires the lock.
    - The Swarm Dispatcher checks `isTeamActive()` before every dispatch.
    - If a team is active, the Swarm pauses execution until the lock is released or expires (2-hour stale timeout).

### 3.6. Governance & Logic Gates (Binh Phap Enforcement)
The system enforces strict operational rules via dedicated logic modules.

- **Mission Complexity (`lib/mission-complexity-classifier.js`):**
    - **🌪️ Wind (Gió - Simple):** `/cook "task" --fast --no-test --auto` (30% budget).
    - **🌲 Forest (Rừng - Medium):** `/cook "task" --auto` (60% budget).
    - **🔥 Fire (Lửa - Complex):** `/cook "task" --auto` + **Agent Team Block** (100% budget, spawns sub-agents).

- **Martial Law (`lib/quan-luat-enforcer.js`):**
    - **Chain of Command:** Antigravity > Brain > CC CLI.
    - **Territory Integrity:** Daemons cannot modify files outside their assigned domain.

- **Safety Gates (`lib/post-mission-gate.js`):**
    - **Blast Radius:** Blocks commits changing >15 files or deleting >500 lines.
    - **Build Verification:** Runs `npm run build` and `typecheck`. Push rejected if fails.

### 3.7. Resource Governor
Implemented in `lib/resource-governor.js`, this module protects the host hardware (M1 Mac).

- **Metrics:** Monitors `vm.loadavg` and `vm_stat` (Free RAM).
- **Kill Tiers:**
    - **Tier 3 (Expendable - Kill First):** Artist, Scribe, Diplomat. (Kill if RAM > 80%)
    - **Tier 2 (Important):** Merchant, Sage. (Kill if RAM > 90%)
    - **Tier 1 (Critical - Protected):** Hunter, Builder, Dispatcher, Reviewer, Operator, Architect.
- **Action:** If thresholds are exceeded, it proactively kills low-tier daemons to free up resources for the Brain.

## 4. Strengths & Weaknesses

### Strengths
- **Robustness:** Highly resilient to external failures (proxy, API, process crashes).
- **Scalability:** Parallel execution maximizing M1 chip usage.
- **Safety:** Multi-layered protection (Constitutional LLM check + Logic Gates).
- **Autonomy:** Can run indefinitely without human intervention via Auto-CTO.
- **Observability:** Detailed logging and real-time visualization.

### Weaknesses
- **Complexity:** State detection in Tmux mode relies on fragile regex scraping.
- **Resource Intensity:** Running multiple LLM agents requires strict governance to prevent OOM.
- **Latency:** Safety checks and proxy handshakes add overhead to start times.

## 5. Conclusion
The Autonomous Task Engine is a mature, production-grade system that effectively turns the Claude Code CLI into a reliable, autonomous worker. Its layered architecture (Dispatcher -> Queue -> Brain) and defensive subsystems (Safety Guard, Resource Governor) make it suitable for continuous, unattended operation.
