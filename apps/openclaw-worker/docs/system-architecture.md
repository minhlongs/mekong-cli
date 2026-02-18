# System Architecture

## Overview
OpenClaw Worker (Code Name: **Tom Hum**) is an autonomous task dispatch daemon responsible for orchestrating missions within the Mekong ecosystem.

## Core Components

### 1. Task Dispatcher (`task-watcher.js`)
- Monitors `tasks/` directory for new mission files.
- Routes missions to appropriate sub-projects or executes them locally.
- Manages the lifecycle of the "Brain" (Claude Code CLI process).

### 2. The Brain (`lib/brain-process-manager.js`)
- Wraps the Claude Code CLI (`claude`).
- Controls input/output via standard streams (or `tmux` in fallback mode).
- Ensures persistent context and recovery from crashes.

### 3. AI DevKit Integration (New)
- **Role**: Tactical Execution Engine.
- **Components**:
  - **CLI**: `ai-devkit` for interactive workflow guidance.
  - **Memory**: `@ai-devkit/memory` MCP server for session context.
- **Workflow ("Hybrid V")**:
  - **Strategy**: ClaudeKit agents (`/plan`, `/scout`) define *what* to do.
  - **Tactics**: AI DevKit commands (`/execute-plan`, `/code-review`) guide *how* to do it step-by-step.

## Data Flow
1. **Mission Ingestion**: `mission_*.txt` placed in `tasks/`.
2. **Dispatch**: `task-watcher.js` parses mission and spawns Brain.
3. **Execution**: Brain uses ClaudeKit/AI DevKit tools to modify code/files.
4. **Verification**: `post-mission-gate.js` runs builds/tests.
5. **Completion**: Result logged to `mission-journal.js` and task moved to `tasks/processed/`.
