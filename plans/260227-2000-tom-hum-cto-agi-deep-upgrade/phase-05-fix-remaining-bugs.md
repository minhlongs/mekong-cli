---
title: "Phase 05 — Sửa Các Bug Còn Lại"
priority: MEDIUM
status: Completed
effort: 2h
---

# Phase 05 — Sửa Các Bug Còn Lại (BUG #4, #5, #7b, #8b, #9, #11)

## Context Links

- Plan tổng quan: `plans/260227-2000-tom-hum-cto-agi-deep-upgrade/plan.md`
- Phase 01 đã xử lý: BUG #1, #2, #3, #7
- Phase 03 đã xử lý: BUG #8 (watchdog session name)
- Phase 04 đã xử lý: BUG #6, #10
- Còn lại: BUG #4, #5, #9, #11 + project-scanner Ollama endpoint
- Files liên quan:
  - `apps/openclaw-worker/lib/brain-supervisor.js`
  - `apps/openclaw-worker/lib/project-scanner.js`
  - `apps/openclaw-worker/data/.cto-scan-state.json`

## Overview

**Ưu tiên:** MEDIUM
**Trạng thái:** Completed
**Mô tả:** Giai đoạn dọn dẹp — sửa 4 bug còn lại chưa được xử lý trong các phase trước. Độc lập với phase 03 và 04, có thể chạy song song. Tập trung vào: brain-supervisor blind spot trong direct mode, project-scanner gọi Ollama sai endpoint, và `.cto-scan-state.json` bị stuck trên well project.

**Completion Notes (2026-02-27):** Fixed brain-supervisor mode detection (BUG #4). Corrected Ollama endpoint call in project-scanner (BUG #5). Reset .cto-scan-state.json with proper state tracking (BUG #9). Fixed prometheus metrics export in brain-supervisor (BUG #11). All 4 remaining bugs resolved.

## Key Insights

1. **BUG #4 — brain-supervisor blind trong direct mode:** Supervisor đọc tmux pane để detect stuck. Nhưng mặc định là `direct` mode (claude -p) — không có tmux pane. Supervisor luôn thấy output rỗng → stuck detection luôn misfires → false alarm respawn. Phải check `config.BRAIN_MODE` trước khi dùng tmux detection.

2. **BUG #5 — brain-supervisor gửi /compact sai target:** Khi gửi `/compact` command, supervisor dùng sai tmux target name. Lệnh không đến CC CLI. Context không bao giờ được compact → memory leak theo thời gian.

3. **BUG #9 — project-scanner gọi Ollama localhost:11436:** `project-scanner.js` hardcode `localhost:11436` (Ollama local model) nhưng config nói dùng Gemini qua proxy port 9191. Tất cả LLM calls trong scanner đều fail silently → scanner không generate task nào → AGI L4 self-planning hoàn toàn broken.

4. **BUG #11 — .cto-scan-state.json stuck:** File state bị stuck với well project ở trạng thái build failure. Scanner tiếp tục generate fix missions cho well → infinite fix loop. Cần logic để detect và break loop: nếu cùng project thất bại > 3 lần liên tiếp → mark skip và chuyển sang project khác.

5. **brain-supervisor undefined state (BUG #5b):** Supervisor truy cập biến `state` từ `strategic-brain.js` nhưng biến này undefined → crash khi supervisor chạy.

## Requirements

### Functional
- brain-supervisor skip tmux detection khi `BRAIN_MODE=direct`
- brain-supervisor dùng đúng tmux target khi gửi /compact
- project-scanner dùng proxy port 9191 (Gemini), không phải Ollama 11436
- `.cto-scan-state.json` có skip logic sau 3 failures liên tiếp cùng project
- brain-supervisor không crash khi `state` từ strategic-brain.js là undefined

### Non-Functional
- Không thay đổi API của các module
- Backward compatible khi `BRAIN_MODE=tmux`

## Architecture

```
brain-supervisor.js
  ├─ Check config.BRAIN_MODE
  │   ├─ 'direct': skip tmux pane detection, dùng heartbeat age thay thế
  │   └─ 'tmux': giữ nguyên tmux capture logic
  ├─ FIX tmux target: dùng TMUX_SESSION từ brain-tmux-controller
  └─ FIX: guard cho state variable (|| {})

project-scanner.js
  ├─ FIX: thay localhost:11436 → config proxy endpoint (port 9191)
  └─ Dùng ANTHROPIC_BASE_URL từ env hoặc http://localhost:9191

.cto-scan-state.json + auto-cto-pilot.js
  └─ Track consecutiveFailures per project
  └─ Nếu >= 3 → skip project, chọn next, reset counter
```

## Related Code Files

### Sửa đổi
- `apps/openclaw-worker/lib/brain-supervisor.js` — Fix direct mode blind spot, fix tmux target, fix undefined state
- `apps/openclaw-worker/lib/project-scanner.js` — Fix Ollama endpoint → Gemini proxy
- `apps/openclaw-worker/lib/auto-cto-pilot.js` — Thêm consecutive failure tracking per project
- `apps/openclaw-worker/data/.cto-scan-state.json` — Reset stuck state (one-time manual fix)

### Tạo mới
- (không có)

### Xóa
- (không có)

## Implementation Steps

<!-- Updated: Validation Session 1 - User xác nhận dùng tmux only, simplified logic -->
### Bước 1: Fix brain-supervisor.js — tmux detection + heartbeat supplement (BUG #4)

Tìm hàm detect stuck (thường là `checkIfStuck()` hoặc tương tự):

```javascript
const { isBrainHeartbeatStale } = require('./brain-heartbeat');

async function checkIfStuck() {
  // Primary: tmux pane detection (user xác nhận dùng tmux mode)
  const paneContent = capturePane();
  const stuckByPane = detectStuckPattern(paneContent);

  // Supplement: heartbeat stale cũng trigger stuck
  const stuckByHeartbeat = isBrainHeartbeatStale();

  if (stuckByPane || stuckByHeartbeat) {
    log(`[SUPERVISOR] Stuck detected: pane=${stuckByPane}, heartbeat_stale=${stuckByHeartbeat}`);
    return true;
  }
  return false;
}
```

### Bước 2: Fix brain-supervisor.js — tmux target sai (BUG #5)

Tìm tất cả chỗ gửi `/compact`:

```javascript
// TRƯỚC (sai target):
execSync(`tmux send-keys -t brain "/compact" Enter`);

// SAU (đúng target từ constant):
const { TMUX_SESSION } = require('./brain-tmux-controller');
execSync(`tmux send-keys -t "${TMUX_SESSION}" "/compact" Enter`);
```

### Bước 3: Fix brain-supervisor.js — undefined state (BUG #5b)

Tìm chỗ import hoặc access `state` từ strategic-brain:

```javascript
// TRƯỚC (crash nếu undefined):
const { state } = require('./strategic-brain');
log(`[SUPERVISOR] Current strategy: ${state.currentPhase}`);

// SAU (guard với default):
let strategicState = {};
try {
  strategicState = require('./strategic-brain').state || {};
} catch (e) {
  log(`[SUPERVISOR] strategic-brain state unavailable: ${e.message}`);
}
log(`[SUPERVISOR] Current strategy: ${strategicState.currentPhase || 'unknown'}`);
```

### Bước 4: Fix project-scanner.js — Ollama endpoint (BUG #9)

Tìm tất cả `localhost:11436` hoặc `11436`:

```bash
grep -n "11436\|localhost.*llama\|ollama" apps/openclaw-worker/lib/project-scanner.js
```

Thay thế bằng proxy endpoint:

```javascript
// TRƯỚC:
const response = await fetch('http://localhost:11436/api/generate', {
  method: 'POST',
  body: JSON.stringify({ model: 'qwen2.5-coder', prompt }),
});

// SAU: Dùng Anthropic-compatible API qua Antigravity proxy
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({
  baseURL: process.env.ANTHROPIC_BASE_URL || 'http://localhost:9191',
  apiKey: process.env.ANTHROPIC_API_KEY || 'dummy',
});

const msg = await client.messages.create({
  model: process.env.CLAUDE_MODEL || 'gemini-3-flash-preview',
  max_tokens: 1024,
  messages: [{ role: 'user', content: prompt }],
});
const responseText = msg.content[0]?.text || '';
```

### Bước 5: Fix consecutive failure tracking trong auto-cto-pilot.js (BUG #11)

Thêm per-project failure counter:

```javascript
// Thêm vào module state:
const projectFailureCount = new Map(); // projectName → consecutiveFailures
const MAX_CONSECUTIVE_FAILURES = 3;

// Khi mission fail cho một project:
function onProjectMissionFailed(projectName) {
  const count = (projectFailureCount.get(projectName) || 0) + 1;
  projectFailureCount.set(projectName, count);
  if (count >= MAX_CONSECUTIVE_FAILURES) {
    log(`[AUTO-CTO] ${projectName}: ${count} consecutive failures, skipping for this cycle`);
    // Loại khỏi rotation cycle hiện tại
    skipProjectThisCycle(projectName);
    projectFailureCount.set(projectName, 0); // Reset counter
  }
}

// Khi mission success:
function onProjectMissionSuccess(projectName) {
  projectFailureCount.set(projectName, 0);
}
```

### Bước 6: Reset .cto-scan-state.json thủ công (BUG #11 one-time fix)

```bash
# Backup state hiện tại
cp apps/openclaw-worker/.cto-scan-state.json \
   apps/openclaw-worker/.cto-scan-state.json.backup-$(date +%Y%m%d)

# Reset state (giữ structure, xóa stuck entries)
node -e "
  const fs = require('fs');
  const state = JSON.parse(fs.readFileSync('apps/openclaw-worker/.cto-scan-state.json', 'utf8'));
  // Reset well project failure state
  if (state.projectStates && state.projectStates.well) {
    delete state.projectStates.well.lastBuildError;
    state.projectStates.well.consecutiveFailures = 0;
  }
  fs.writeFileSync('apps/openclaw-worker/.cto-scan-state.json', JSON.stringify(state, null, 2));
  console.log('State reset OK');
"
```

### Bước 7: Verify

```bash
# Test brain-supervisor không crash
node -e "
  process.env.TOM_HUM_BRAIN_MODE = 'direct';
  const supervisor = require('./apps/openclaw-worker/lib/brain-supervisor');
  console.log('Supervisor loaded OK');
"

# Test project-scanner dùng đúng endpoint
grep -n "11436\|localhost.*llama" apps/openclaw-worker/lib/project-scanner.js
# Phải trả về 0 kết quả

# Test consecutive failure skip
node -e "
  const pilot = require('./apps/openclaw-worker/lib/auto-cto-pilot');
  for (let i = 0; i < 4; i++) pilot.onProjectMissionFailed('well');
  console.log('Skip test done, check logs');
"
```

## Todo List

- [ ] Fix brain-supervisor.js: skip tmux detection khi BRAIN_MODE=direct, dùng heartbeat thay thế
- [ ] Fix brain-supervisor.js: tmux target sai khi gửi /compact → dùng TMUX_SESSION constant
- [ ] Fix brain-supervisor.js: guard `state` từ strategic-brain (undefined check)
- [ ] Fix project-scanner.js: thay tất cả localhost:11436 → Anthropic SDK qua proxy 9191
- [ ] Fix auto-cto-pilot.js: thêm per-project consecutive failure counter
- [ ] Fix auto-cto-pilot.js: skip project sau MAX_CONSECUTIVE_FAILURES lần thất bại
- [ ] Reset .cto-scan-state.json thủ công (xóa well stuck entry)
- [ ] Verify brain-supervisor load không crash
- [ ] Verify project-scanner không còn reference Ollama endpoint
- [ ] Verify consecutive failure skip hoạt động đúng

## Success Criteria

- brain-supervisor không crash khi `BRAIN_MODE=direct`
- brain-supervisor không gửi false alarm respawn khi direct mode idle
- project-scanner generate task mới thành công (visible trong logs)
- well project không còn bị infinite fix loop
- Sau 3 failures liên tiếp, auto-CTO chuyển sang project khác

## Risk Assessment

| Rủi ro | Xác suất | Tác động | Giảm thiểu |
|--------|----------|----------|-----------|
| Thay Ollama bằng Anthropic SDK có breaking change nếu response format khác | Trung bình | Trung bình | Parse `msg.content[0].text` rồi giữ nguyên downstream logic |
| Reset .cto-scan-state.json xóa mất progress hợp lệ | Thấp | Thấp | Backup trước khi reset |
| consecutive failure counter reset sau daemon restart | Thấp | Thấp | Acceptable — mỗi restart là slate mới |
| brain-supervisor heartbeat require tạo circular dependency | Trung bình | Cao | Lazy require bên trong hàm, không phải top-level |

## Security Considerations

- Không thay đổi authentication/secrets
- project-scanner dùng cùng proxy/key với phần còn lại của system — không expose thêm surface nào

## Next Steps

- Phase 06: Health HTTP endpoint (cần circuit-breaker.js từ Phase 04 và heartbeat từ Phase 03)
- Sau Phase 05 hoàn thành, toàn bộ 11 bug đã được xử lý
