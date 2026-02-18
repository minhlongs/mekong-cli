# Autonomous Task Engine Analysis

**Date:** 2026-02-15
**System:** OpenClaw Worker ("Tom Hum")
**Version:** v2026.2.14

## 1. System Overview

The OpenClaw Worker is a sophisticated, autonomous agent runner designed to execute "Binh Phap" (Art of War) strategic software development tasks. It operates as a daemon (`task-watcher.js`) that orchestrates a "Brain" (Claude Code CLI) running inside a `tmux` session.

## 2. Core Components

### 2.1. The Nervous System (Task Queue)
- **File Watcher:** `lib/task-queue.js` monitors `tasks/` for `mission_*.txt`.
- **Parallel Dispatch:** Supports concurrent execution (default 3 missions) by maintaining a pool of worker panes.
- **Safety Gates:**
  - **Pre-flight:** Checks proxy health.
  - **Thermal:** Checks system load (M1 Cooling).
  - **Content:** Validates prompt safety via `safety-guard.js`.

### 2.2. The Strategist (Auto-CTO)
- **Logic:** `lib/auto-cto-pilot.js` activates when the task queue is empty.
- **Cycle:** Rotates through a configured list of projects (`84tea`, `anima119`, etc.).
- **Tasks:** Assigns specific "Binh Phap" maintenance tasks:
  - `console_cleanup` (Simple)
  - `type_safety` (Medium)
  - `security_scan` (Complex)
  - `i18n_sync` (Medium)
- **Infinite Game:** Explicitly tracks cycles. When a project is "clean", it resets the task list to begin the next cycle of improvement.

### 2.3. The Muscle (Brain Tmux)
- **Execution:** `lib/brain-tmux.js` manages a `tmux` session with multiple panes.
  - **P0:** Supervisor/Monitor (or God Mode Worker).
  - **P1-Pn:** Worker panes.
- **State Machine:** Scrapes terminal output to detect:
  - `BUSY`: "Photosynthesizing", "Crunching", "Vibing".
  - `DONE`: "Cooked for Xm Ys", "Sautéed for...".
  - `STUCK`: TUI menus, "Interrupted", "Rewind".
  - `QUESTION`: Approval prompts (auto-approves with Enter).
- **Resilience:**
  - **Auto-Respawn:** If the CLI crashes or drops to a shell prompt.
  - **Unsticking:** Sends Escape or Ctrl+C to exit TUI menus.
  - **Context Management:** periodically runs `/clear` or `/compact`.

### 2.4. The Immune System (Self-Healer)
- **Healer:** `lib/self-healer.js` monitors health.
- **Proxy Recovery:** Restarts `anthropic-adapter.js` if the proxy is down.
- **Model Fallback:** Switches models (Sonnet → Gemini → Qwen) if `RESOURCE_EXHAUSTED` or model rejection occurs.

## 3. Workflow

1.  **Input:** A text file `mission_project_task.txt` is dropped into `tasks/`.
2.  **Routing:** `mission-dispatcher.js` detects the project directory.
3.  **Prompt Engineering:** The prompt is wrapped with context (e.g., "Answer in Vietnamese", "Monorepo Rules").
4.  **Dispatch:**
    - The task is assigned to an idle `tmux` pane.
    - Text is pasted via a named buffer.
5.  **Execution Loop:** The system polls the pane for completion or failure.
6.  **Gatekeeper:**
    - Upon success, `post-mission-gate.js` verifies the build/tests (if applicable).
7.  **Output:**
    - File moved to `tasks/processed/`.
    - Telegram notification sent.

## 4. Key Strengths
- **True Autonomy:** Can run indefinitely without human input via Auto-CTO.
- **Resilience:** "Let it crash" philosophy with aggressive recovery.
- **Parallelism:** Maximizes hardware utilization (M1 Max) via tmux panes.

## 5. Recommendations
- **Dynamic Config:** Move regex patterns to a JSON config to handle CLI output changes easier.
- **Telepresence:** The `live-mission-viewer.js` is excellent; consider exposing a web-based read-only dashboard.
