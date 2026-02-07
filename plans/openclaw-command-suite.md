# OpenClaw Command Suite: The "Giao Việc" Standard

> **Date:** 2026-02-07
> **Objective:** Standardization of Telegram Slash Commands for OpenClaw.

## 1. Problem

Currently, OpenClaw requires natural language (`/cmd mekong Do X`). This is flexible but slow and error-prone. The user wants a structured, "clickable" experience like `claudekit-engineer` or `mekong-cli`.

## 2. Command Architecture

We will implement a **Central Command Registry** in `raas-gateway` (Cloud) that maps `/slash` commands to:

1.  **Immediate execution** (e.g. `/status`).
2.  **Routed execution** (e.g. `/deploy` -> CD to app -> run command).
3.  **Agentic execution** (e.g. `/plan` -> invoke `ck plan`).

## 3. The "Standard" Command Set (v1.0)

Based on `claudekit-engineer` inspiration:

### 3.1. Core Operations

| Command   | Alias     | Action                                       |
| :-------- | :-------- | :------------------------------------------- |
| `/status` | `/watzup` | Check Bridge, T1, and Active Workers.        |
| `/ping`   | -         | Check Latency between Cloud <-> Local.       |
| `/update` | -         | Update OpenClaw Bridge (git pull + restart). |

### 3.2. Agentic Work (The "Brain")

These map directly to `claudekit` commands on T1.
| Command | Action (on T1) |
| :--- | :--- |
| `/plan [goal]` | Runs `ck plan "[goal]"` (Creates implementation plan). |
| `/cook [task]` | Runs `ck cook "[task]"` (Executes code). |
| `/ask [query]` | Runs `ck ask "[query]"` (Q&A about codebase). |

### 3.3. DevOps & Deployment (The "Hands")

| Command         | Action (on T1)                                          |
| :-------------- | :------------------------------------------------------ |
| `/deploy [app]` | `cd apps/[app] && vercel deploy --prod`                 |
| `/logs [app]`   | Retrieve recent logs (via `vercel logs` or local file). |
| `/fix [issue]`  | Smart debug: Analyze error -> Fix.                      |

### 3.4. Fleet Management

| Command      | Action                                                    |
| :----------- | :-------------------------------------------------------- |
| `/fleet`     | List all active agent sessions (using `jps` or `screen`). |
| `/stop [id]` | Kill a specific agent session.                            |

## 4. Implementation Strategy

### Phase 1: Gateway Parser (Cloud)

Modify `raas-gateway/index.js` to parse these commands _before_ sending to Bridge.

- **Why?** To provide instant feedback ("Command received: Planning...") and format the payload strictly.

### Phase 2: Bridge Executor (Local)

Modify `task-watcher.js` to understand "Structured Tasks".

- Instead of just raw text, it receives JSON: `{ type: "plan", payload: "Fix login" }`.
- It then spawns the correct tool (`ck`, `vercel`, `git`).

### Phase 3: Telegram Menu

Use `setMyCommands` to register these in the Telegram UI so they auto-complete.
