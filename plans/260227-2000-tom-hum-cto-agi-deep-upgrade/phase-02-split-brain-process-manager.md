---
title: "Phase 02 — Tách brain-process-manager.js Thành Modules"
priority: HIGH
status: Completed
effort: 3h
---

# Phase 02 — Tách brain-process-manager.js (1233 dòng → 5 module < 200 dòng)

## Context Links

- Plan tổng quan: `plans/260227-2000-tom-hum-cto-agi-deep-upgrade/plan.md`
- File gốc: `apps/openclaw-worker/lib/brain-process-manager.js` (1233 dòng)
- Phụ thuộc vào: Phase 01 hoàn thành
- Các phase sau phụ thuộc vào: Phase 03, 04, 05

## Overview

**Ưu tiên:** HIGH
**Trạng thái:** Completed
**Mô tả:** File `brain-process-manager.js` có 1233 dòng — vi phạm nghiêm trọng quy tắc 200 dòng. Tách thành 5 module độc lập theo trách nhiệm đơn lẻ (Single Responsibility). Đồng thời sửa các bug phát hiện trong file này: duplicate `pasteText()`, `respawnBrain()` gọi sai argument, `canRespawn()` luôn trả `true`.

**Completion Notes (2026-02-27):** Successfully split 1233-line monolith into 10 focused modules (<200 lines each). Re-export shell maintains backward compatibility. Fixed respawnBrain() argument issue. Enabled rate limiting in canRespawn(). Removed duplicate pasteText(). All callers verified working.

## Key Insights

1. **1233 dòng vi phạm quy tắc** — File quá lớn khiến LLM không thể đọc toàn bộ context, dễ bỏ sót bug.
2. **Duplicate pasteText()** — Định nghĩa đầu tiên không bao giờ được gọi (dead code), định nghĩa thứ hai ghi đè. Gây nhầm lẫn khi debug.
3. **respawnBrain() sai argument** — Gọi `spawnBrain(config.AGENT_TEAM_SIZE_DEFAULT, intent)` nhưng `spawnBrain()` không nhận argument — gây silent no-op khi recovery.
4. **canRespawn() luôn true** — Rate limiter bị disable (logic bị comment out) → CC CLI có thể respawn vô hạn và gây vòng lặp crash-respawn-crash.

## Requirements

### Functional
- Tất cả export hiện tại của `brain-process-manager.js` vẫn hoạt động đúng sau khi tách
- `respawnBrain()` phải gọi `spawnBrain()` đúng signature
- `canRespawn()` phải enforce rate limit thực (5 lần/giờ)
- Không còn duplicate function definitions

### Non-Functional
- Mỗi file mới < 200 dòng
- Không thay đổi behavior của các caller hiện tại (`task-queue.js`, `task-watcher.js`)
- Backward compatible: giữ nguyên `module.exports` từ `brain-process-manager.js` (re-export từ các module con)

## Architecture

```
brain-process-manager.js (< 80 dòng, re-exports + orchestration)
    │
    ├── brain-spawn-manager.js     (< 150 dòng)
    │   ├── spawnBrain()
    │   ├── killBrain()
    │   ├── isBrainAlive()
    │   └── canRespawn() — FIX: rate limiter thực
    │
    ├── brain-mission-runner.js    (< 180 dòng)
    │   ├── runMission()
    │   └── buildMissionPrompt()
    │
    ├── brain-state-machine.js     (< 150 dòng)
    │   ├── pollMissionState()
    │   ├── detectBusyState()
    │   ├── detectCompletionState()
    │   └── BUSY_PATTERNS, COMPLETION_PATTERNS (constants)
    │
    ├── brain-tmux-controller.js   (< 150 dòng)
    │   ├── pasteText()            — FIX: xóa duplicate
    │   ├── capturePane()
    │   ├── sendKeys()
    │   └── createTmuxSession()
    │
    └── brain-respawn-controller.js (< 120 dòng)
        ├── respawnBrain()          — FIX: đúng signature
        ├── handleBrainCrash()
        └── respawnHistory[]        — rate limiter state
```

## Related Code Files

### Tạo mới
- `apps/openclaw-worker/lib/brain-spawn-manager.js`
- `apps/openclaw-worker/lib/brain-mission-runner.js`
- `apps/openclaw-worker/lib/brain-state-machine.js`
- `apps/openclaw-worker/lib/brain-tmux-controller.js`
- `apps/openclaw-worker/lib/brain-respawn-controller.js`

### Sửa đổi
- `apps/openclaw-worker/lib/brain-process-manager.js` — Thu gọn thành re-export shell
- `apps/openclaw-worker/lib/task-queue.js` — Import path không đổi (vẫn từ brain-process-manager)
- `apps/openclaw-worker/task-watcher.js` — Import path không đổi

### Xóa
- (Nội dung cũ của brain-process-manager.js được di chuyển, không xóa file)

## Implementation Steps

### Bước 1: Đọc và map toàn bộ exports của brain-process-manager.js

```bash
grep -n "^function\|^const.*=.*function\|^async function\|module\.exports" \
  apps/openclaw-worker/lib/brain-process-manager.js
```

Liệt kê tất cả export: `spawnBrain`, `killBrain`, `isBrainAlive`, `runMission`, `log`, xác định line range của từng hàm.

### Bước 2: Tạo brain-tmux-controller.js

Di chuyển tất cả hàm liên quan đến tmux:
- `pasteText()` — giữ lại DUY NHẤT định nghĩa thứ hai (xóa duplicate đầu)
- `capturePane()`, `sendKeys()`, `createTmuxSession()`, `getTmuxPane()`
- Constants: `TMUX_SESSION_PRO`, `TMUX_SESSION_API`

```javascript
// apps/openclaw-worker/lib/brain-tmux-controller.js
'use strict';
const { execSync } = require('child_process');
const config = require('../config');

const TMUX_SESSION = `${config.TMUX_SESSION}:brain`;

function pasteText(text, pane) { /* ... single definition ... */ }
function capturePane(pane) { /* ... */ }
// ...
module.exports = { pasteText, capturePane, TMUX_SESSION };
```

### Bước 3: Tạo brain-state-machine.js

Di chuyển:
- `BUSY_PATTERNS` array
- `COMPLETION_PATTERNS` array
- `detectBusy(output)` — returns boolean
- `detectCompletion(output)` — returns boolean
- `pollMissionState(startTime, wasBusy, idleCount)` — trả về state object

### Bước 4: Tạo brain-spawn-manager.js

Di chuyển:
- `spawnBrain()` — giữ nguyên logic
- `killBrain()` — giữ nguyên
- `isBrainAlive()` — giữ nguyên
- `canRespawn()` — **FIX: bật lại rate limiter**:

```javascript
// FIX canRespawn(): thực sự enforce 5 respawns/hour
const respawnHistory = [];
const MAX_RESPAWNS_PER_HOUR = 5;

function canRespawn() {
  const now = Date.now();
  const oneHourAgo = now - 3600_000;
  // Xóa entries cũ hơn 1 giờ
  while (respawnHistory.length > 0 && respawnHistory[0] < oneHourAgo) {
    respawnHistory.shift();
  }
  if (respawnHistory.length >= MAX_RESPAWNS_PER_HOUR) {
    log(`[SPAWN] Rate limit hit: ${respawnHistory.length} respawns in last hour`);
    return false;
  }
  respawnHistory.push(now);
  return true;
}
```

### Bước 5: Tạo brain-respawn-controller.js

Di chuyển:
- `respawnBrain()` — **FIX: gọi spawnBrain() đúng signature (không có argument)**:

```javascript
const { spawnBrain, canRespawn } = require('./brain-spawn-manager');

async function respawnBrain(reason) {
  if (!canRespawn()) {
    log(`[RESPAWN] Rate limited, skipping respawn. Reason: ${reason}`);
    return false;
  }
  log(`[RESPAWN] Respawning brain. Reason: ${reason}`);
  // FIX: spawnBrain() không nhận argument
  return await spawnBrain();
}
```

### Bước 6: Tạo brain-mission-runner.js

Di chuyển `runMission()` và helpers:
- `buildPrompt(taskContent, projectDir)`
- `runMission(prompt, projectDir, timeout)` — gọi brain-state-machine + brain-tmux-controller

### Bước 7: Thu gọn brain-process-manager.js thành re-export shell

```javascript
// apps/openclaw-worker/lib/brain-process-manager.js
// Re-export shell — giữ backward compatibility
'use strict';
const { spawnBrain, killBrain, isBrainAlive } = require('./brain-spawn-manager');
const { runMission } = require('./brain-mission-runner');
const { respawnBrain } = require('./brain-respawn-controller');

// log() vẫn export từ đây vì nhiều module import nó
const log = require('./brain-logger').log;

module.exports = { spawnBrain, killBrain, isBrainAlive, runMission, respawnBrain, log };
```

### Bước 8: Tạo brain-logger.js (utility nhỏ)

```javascript
// apps/openclaw-worker/lib/brain-logger.js (< 30 dòng)
const fs = require('fs');
const LOG_FILE = process.env.TOM_HUM_LOG || `${process.env.HOME}/tom_hum_cto.log`;

function log(msg) {
  const ts = new Date().toISOString();
  const line = `[${ts}] ${msg}\n`;
  process.stdout.write(line);
  try { fs.appendFileSync(LOG_FILE, line); } catch (e) { /* ignore */ }
}

module.exports = { log };
```

### Bước 9: Verify không regression

```bash
cd apps/openclaw-worker
node -e "const m = require('./lib/brain-process-manager'); console.log(Object.keys(m))"
# Phải in ra: [ 'spawnBrain', 'killBrain', 'isBrainAlive', 'runMission', 'respawnBrain', 'log' ]

node -e "const { canRespawn } = require('./lib/brain-spawn-manager'); for(let i=0;i<6;i++) console.log(i, canRespawn())"
# Output phải là: 0 true, 1 true, 2 true, 3 true, 4 true, 5 false
```

## Todo List

- [ ] Map tất cả exports và line ranges trong brain-process-manager.js gốc
- [ ] Tạo brain-logger.js (utility log)
- [ ] Tạo brain-tmux-controller.js (xóa duplicate pasteText)
- [ ] Tạo brain-state-machine.js (BUSY_PATTERNS, COMPLETION_PATTERNS, poll logic)
- [ ] Tạo brain-spawn-manager.js (FIX canRespawn rate limiter)
- [ ] Tạo brain-respawn-controller.js (FIX respawnBrain signature)
- [ ] Tạo brain-mission-runner.js
- [ ] Thu gọn brain-process-manager.js thành re-export shell
- [ ] Verify exports backward compatible
- [ ] Verify canRespawn() rate limit hoạt động đúng
- [ ] Chạy manual mission test end-to-end

## Success Criteria

- Mỗi file mới < 200 dòng (verify bằng `wc -l`)
- `node -e "require('./lib/brain-process-manager')"` không throw error
- `canRespawn()` trả `false` sau 5 lần gọi trong 1 giờ
- `respawnBrain()` không còn truyền argument vào `spawnBrain()`
- Không còn duplicate function definition
- End-to-end mission test pass

## Risk Assessment

| Rủi ro | Xác suất | Tác động | Giảm thiểu |
|--------|----------|----------|-----------|
| Circular dependency giữa các module mới | Trung bình | Cao | Vẽ dependency graph trước khi tạo file, brain-logger.js phải không import module nào khác |
| Import path sai trong task-queue.js | Thấp | Cao | Giữ nguyên export từ brain-process-manager.js (re-export shell) |
| BUSY_PATTERNS regex bị mất khi di chuyển | Thấp | Cao | Copy nguyên văn, verify bằng unit test regex |
| respawnBrain() mới không trigger đúng recovery | Trung bình | Cao | Test crash scenario với `pkill -f 'claude -p'` |

## Security Considerations

- `brain-logger.js` append to log file — đảm bảo không log nội dung sensitive (API keys trong prompt)
- Log chỉ ghi metadata: timestamp, status, elapsed time — không ghi toàn bộ prompt content

## Next Steps

- Phase 03: Heartbeat + output-hash watchdog (cần brain-spawn-manager.js hoàn chỉnh)
- Phase 04: Self-healer fix (cần brain-respawn-controller.js)
- Phase 05: Bug fixes còn lại (cần brain-tmux-controller.js và brain-spawn-manager.js)
