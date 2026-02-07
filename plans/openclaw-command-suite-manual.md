# OpenClaw Command Suite v1.0: User Manual

> **Date:** 2026-02-07
> **Status:** Operational 🟢

## 1. Overview

The OpenClaw Command Suite transforms your Telegram chat into a CLI terminal for your fleet (T1, T2, etc.).
It supports two modes: **Shell Mode** (Raw Execution) and **Agent Mode** (Intelligent Execution).

## 2. Command Reference

### 🧠 Agent Mode (The "Brain")

_Routes to Mekong CLI Agent (Claude)._

| Command        | Description                                  | Example                                             |
| :------------- | :------------------------------------------- | :-------------------------------------------------- |
| `/plan [goal]` | Create an implementation plan.               | `/plan Fix the login page CSS`                      |
| `/cook [task]` | Execute code changes based on plan.          | `/cook Implement the new login design`              |
| `/ask [query]` | Query codebase or documentation.             | `/ask How does the authentication middleware work?` |
| `/deploy`      | Smart deployment (Agent decides strategy).   | `/deploy AgencyOS to production`                    |
| **(Default)**  | Any other text is sent to Agent as a prompt. | `Analyze the recent error logs`                     |

### 🔧 Shell Mode (The "Hands")

_Routes to System Shell (Bash/Zsh)._

| Command   | Description                     | Example                    |
| :-------- | :------------------------------ | :------------------------- |
| `!ping`   | Check connectivity.             | `!ping google.com`         |
| `!status` | Check system load.              | `!uptime`                  |
| `!ls`     | List files in Mekong directory. | `!ls -la apps/`            |
| `!update` | Git pull and restart.           | `!git pull && npm install` |

## 3. How It Works

1. **You** send `/plan ...` in Telegram.
2. **OpenClaw** (Cloud) forwards it to **T1** (Local).
3. **Task Watcher** detects the `/` prefix.
4. **Agent** (`claude`) receives the command and executes it using its skills (e.g. `planner`, `fs`, `git`).

## 4. Troubleshooting

- If no response in 1 min, check `apps/openclaw-worker/watcher.log` on T1.
- Restart Bridge: `!pkill -f task-watcher && nohup node apps/openclaw-worker/task-watcher.js &` (Use Shell Mode!)
