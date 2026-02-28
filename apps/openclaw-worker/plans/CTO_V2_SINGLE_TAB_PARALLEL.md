# CTO v2: Giám Sát Đa Luồng — Single CC CLI Tab

## 🎯 Mục tiêu
- **1 CC CLI tab duy nhất** — không multi-pane tmux
- CC CLI tự quản lý đa luồng bên trong (subagents, parallel tool calls)
- CTO giám sát + dispatch qua 1 tab duy nhất
- Anh NHÌN THẤY được 2 tasks chạy đồng thời

## 📊 Hiện Trạng (v1)

```
PROBLEM: Architecture hiện tại = multi-pane tmux (P0-P3)
  → spawnBrain() tạo 4 panes, mỗi pane 1 CC CLI
  → Overhead lớn: 4 CC CLI instances × RAM × context
  → Thực tế: chỉ 1-2 pane hoạt động, phí tài nguyên
  → Anh phải xài tmux attach để xem → không trực quan

SOLUTION: 1 CC CLI + internal parallelism
  → CC CLI đã support:
    • Parallel tool calls (tự động — tool use song song)
    • /cook → CC CLI tự decompose + parallel subtasks
    • Background processing (internal subagents)
  → CTO dispatch prompt ĐỌC: "Làm A và B SONG SONG"
  → CC CLI bên trong tự tạo parallel execution
```

## 🔧 Changes Required

### Phase 1: Simplify Brain to Single-Tab (brain-process-manager.js)
- `spawnBrain()` → 1 pane only (no split-window)
- Remove `AGENT_TEAM_SIZE_DEFAULT` multi-pane logic
- Keep P0 as single worker pane
- Remove `findIdleWorker()` / `rotateWorker()` (always P0)
- Simplify `runMission()` — always target pane 0

### Phase 2: Parallel Dispatch via Prompt Engineering (mission-dispatcher.js)
- `buildPrompt()` → inject parallel instruction
- When CTO generates 2+ tasks, COMBINE into 1 mega-prompt:
  ```
  /cook "Task A AND Task B — execute both in PARALLEL using subagents"
  ```
- CC CLI's internal engine handles parallelism (tool calls in parallel)
- Visual: anh thấy CC CLI output interleave giữa 2 tasks

### Phase 3: CTO Supervisor v2 (brain-supervisor.js)
- Monitor single pane output
- Detect parallel execution markers in output
- Track: mission start → parallel indicators → completion
- Dashboard: live status in tmux status-bar (single pane)

### Phase 4: Visual Dashboard (cto-visual-dashboard.js)
- Simplify to single-pane monitoring
- tmux status-bar: `🦞 CTO v2 | 🔴 2 tasks parallel | 45s`
- Parse CC CLI output for parallel execution indicators

## ⚠️ Tradeoffs

| Aspect | Multi-Pane (v1) | Single-Tab (v2) |
|:-------|:---------------|:----------------|
| **RAM** | 4× CC CLI | 1× CC CLI ✅ |
| **Context** | 4 separate contexts | 1 shared context ✅ |
| **Parallelism** | True parallel | CC CLI internal ✅ |
| **Visual** | 4 panes = messy | 1 tab = clean ✅ |
| **Control** | Complex dispatch | Simple dispatch ✅ |
| **Overhead** | High | Low ✅ |

## 📋 Implementation Order

```
1. [Phase 1] Simplify spawnBrain() → 1 pane
2. [Phase 2] Update buildPrompt() → parallel combo prompt  
3. [Phase 3] Update supervisor → single-pane monitoring
4. [Phase 4] Update dashboard → single-pane status
5. Test: dispatch 2 tasks → see CC CLI handle both
```

## 🔒 Config Changes

```javascript
// config.js
AGENT_TEAM_SIZE_DEFAULT: 1,  // ← was 4
MAX_CONCURRENT_MISSIONS: 1,  // ← was 4 (1 CC CLI, parallel inside)
FULL_CLI_MODE: true,         // P0 = worker (no monitor pane)
PARALLEL_PROMPT_MODE: true,  // NEW: combine tasks into parallel prompt
```
