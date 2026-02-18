---
description: Giao việc cho Claude Code CLI qua Antigravity Proxy
---

# /giao-viec-cc — Giao Việc Cho CC CLI

> 🔒 **IRON RULE — CLAUDEKIT BẮT BUỘC** (Chairman Decree 2026-02-17)

## ĐỌC TRƯỚC KHI LÀM:
1. **MỌI task PHẢI dùng ClaudeKit command** — CẤM gửi raw text
2. **ĐA LUỒNG BẮT BUỘC** — 10+ subagents (Commander Rule 13)
3. **DEEP 10x THINKING BẮT BUỘC** — Extended thinking budget

## ClaudeKit Command Map (KHÔNG ĐƯỢC QUÊN!)

| Task Type  | ClaudeKit Command |
|:-----------|:------------------|
| Simple     | `/cook "task" --auto` |
| Medium     | `/cook "task" --auto` |
| Complex    | `/plan:hard "task"` |
| Strategic  | `/plan:parallel "task"` |
| Debug      | `/debug "issue"` |
| Review     | `/review "target"` |
| Brain Surgery | `/cook "task"` with `/insights` |

## Workflow Steps

### Step 1: Tạo task file

// turbo
```bash
cat > /Users/macbookprom1/mekong-cli/tasks/HIGH_<task_name>.txt << 'TASK'
[MISSION: <TASK_NAME>]
Working Dir: <project_dir>

<task description>

CLAUDEKIT MANDATORY: Dùng /cook hoặc /plan:hard. BẮT BUỘC đa luồng 10+ subagents.
TASK
```

### Step 2: Clear lock và restart CTO

// turbo
```bash
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.mission-active.lock
pkill -9 -f 'task-watcher' 2>/dev/null
sleep 2
cd /Users/macbookprom1/mekong-cli/apps/openclaw-worker && nohup /opt/homebrew/bin/node task-watcher.js >> /Users/macbookprom1/tom_hum_cto.log 2>&1 &
echo "CTO started: PID $!"
```

### Step 3: Monitor

// turbo
```bash
sleep 30 && tail -n 15 /Users/macbookprom1/tom_hum_cto.log && echo "=== CC CLI ===" && tmux capture-pane -t tom_hum_brain -p 2>/dev/null | tail -8
```

## ⚠️ CẢNH BÁO ANTIGRAVITY

**Mầy (Antigravity) HAY QUÊN NHẤT** — Chủ Tịch cấm quên:
- CẤM gửi raw text vào CC CLI — PHẢI có `/cook`, `/plan:hard`, `/debug`
- CẤM chạy single-thread — PHẢI 10+ subagents parallel
- CẤM shallow thinking — PHẢI deep 10x reasoning
- Vi phạm = PHẢN QUÂN

## Two-Call Mandate (CC CLI Input)

Khi gửi trực tiếp vào tmux:
1. **Lệnh 1**: Text task (KHÔNG có `\n` cuối)
2. **Lệnh 2**: Enter riêng (`tmux send-keys Enter`)
