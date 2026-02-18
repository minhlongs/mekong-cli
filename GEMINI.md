# GEMINI.md — Antigravity Agent Config

## 🔒 IRON RULE: CLAUDEKIT BẮT BUỘC (Chairman Decree 2026-02-17)

**ANTIGRAVITY HAY QUÊN NHẤT — CHỦ TỊCH CẤM QUÊN:**

Khi giao việc cho CC CLI (trực tiếp hoặc qua CTO task-watcher):
1. **MỌI task PHẢI dùng ClaudeKit command** — `/cook`, `/plan:hard`, `/debug`, `/plan:parallel`
2. **ĐA LUỒNG BẮT BUỘC** — 10+ subagents parallel (Commander Rule 13)
3. **DEEP 10x THINKING BẮT BUỘC** — Extended thinking budget
4. **CẤM gửi raw text** — Vi phạm = PHẢN QUÂN

### Command Map:
| Task Type  | Command |
|:-----------|:--------|
| Simple     | `/cook "task" --auto` |
| Complex    | `/plan:hard "task"` |
| Strategic  | `/plan:parallel "task"` |
| Debug      | `/debug "issue"` |
| Review     | `/review "target"` |

### Two-Call Mandate (tmux input):
1. Lệnh 1: Text (KHÔNG `\n`)
2. Lệnh 2: Enter riêng (`tmux send-keys Enter`)

### Dispatch via CTO:
- Tạo task file trong `/tasks/HIGH_*.txt` hoặc `/tasks/CRITICAL_*.txt`
- CTO (task-watcher) tự dispatch qua `mission-dispatcher.js`
- `mission-dispatcher.js` đã có `claudekitEnforcement` inject tự động

### 🔒 IRON RULE #2: CHỈ GIAO VIỆC QUA CTO (Chairman Decree 2026-02-17)
- **CẤM Antigravity gửi lệnh trực tiếp vào CC CLI** (tmux send-keys)
- **CHỈ ĐƯỢC tạo task file** → CTO tự dispatch
- **NGOẠI LỆ DUY NHẤT:** Chủ Tịch nói rõ "cho phép đè CC CLI"
- Vi phạm = Bất tuân quân lệnh

---

## Proxy Config
- Adapter: port 11436 (dual-Ultra rotation)
- AG Ultra 1: port 9191 (billwill)
- AG Ultra 2: port 9192 (cashback)
- Phoenix Failover: 9191↔9192 auto-retry
