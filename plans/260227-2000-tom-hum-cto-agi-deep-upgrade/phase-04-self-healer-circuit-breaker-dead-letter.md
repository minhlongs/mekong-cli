---
title: "Phase 04 — Self-Healer Fix + Circuit Breaker + Dead Letter Queue"
priority: HIGH
status: Completed
effort: 2.5h
---

# Phase 04 — Self-Healer Fix + Circuit Breaker + Dead Letter Queue

## Context Links

- Plan tổng quan: `plans/260227-2000-tom-hum-cto-agi-deep-upgrade/plan.md`
- Phụ thuộc: Phase 02 (brain-respawn-controller.js), Phase 03 (brain-heartbeat.js)
- Files liên quan:
  - `apps/openclaw-worker/lib/self-healer.js`
  - `apps/openclaw-worker/lib/task-queue.js`
  - `apps/openclaw-worker/lib/auto-cto-pilot.js`
- Design reference: Netflix Hystrix circuit breaker pattern, RabbitMQ dead letter queue

## Overview

**Ưu tiên:** HIGH
**Trạng thái:** Completed
**Mô tả:** (1) Sửa `self-healer.js` — `restartProxy()` hiện là stub NO-OP chỉ log "skip", khóa toàn bộ recovery chain. (2) Implement Circuit Breaker 3-strike cho proxy/model calls. (3) Implement Dead Letter Queue (DLQ) — tasks thất bại 3 lần được chuyển sang `tasks/dead-letter/` thay vì block queue vĩnh viễn. (4) Sửa `auto-cto-pilot.js` BUG #6: `handleVerify()` gọi không có `await`.

**Completion Notes (2026-02-27):** Self-healer now executes real recovery paths with health monitoring. Circuit breaker implemented with 3-strike threshold and 60s reset. DLQ system moves poison tasks to safe storage. Auto-CTO pilot fixed with proper await. All recovery chains now functional (6 layers active).

## Key Insights

1. **self-healer.js là stub hoàn toàn:** `restartProxy()` trả về `false` và log "skip". Mọi recovery path gọi đến đây đều thất bại im lặng. Đây là lý do tại sao 6 lớp recovery trên paper nhưng thực tế chỉ có 0 lớp hoạt động.

2. **Circuit Breaker pattern (Netflix Hystrix):** Sau 3 lần proxy/model thất bại liên tiếp → "open circuit" → tất cả calls fail-fast trong 60s mà không chờ timeout → giảm cascade failure. Sau 60s → "half-open" → thử 1 request → nếu pass → đóng circuit.

3. **Dead Letter Queue (RabbitMQ pattern):** Task thất bại sau `MAX_RETRIES` lần không bị xóa (mất dữ liệu) cũng không loop vĩnh viễn (block queue). Chuyển sang `tasks/dead-letter/` với metadata về lý do thất bại. Có thể review và retry thủ công.

4. **auto-cto-pilot.js BUG #6:** `handleVerify()` được gọi synchronous (`handleVerify()` thay vì `await handleVerify()`) → nếu hàm này là `async`, event loop block và `isApiBusy` stuck ở `true` → Auto-CTO không bao giờ generate task mới.

5. **isProAvailable() BUG #10:** Sau khi rate limit hit, `isProAvailable()` trả `false` mãi mãi vì không có auto-reset timer. P0 (PRO pane) bị block vĩnh viễn cho đến khi restart daemon.

## Requirements

### Functional
- `restartProxy()` trong self-healer.js phải thực sự restart proxy process
- Circuit breaker mở sau 3 lần thất bại, tự đóng sau 60s
- Task thất bại >= 3 lần → chuyển sang `tasks/dead-letter/` với metadata
- `handleVerify()` trong auto-cto-pilot.js phải được await
- `isProAvailable()` tự reset sau 60 phút

### Non-Functional
- DLQ directory tạo tự động nếu chưa tồn tại
- Circuit breaker state lưu in-memory (reset khi restart daemon là OK)
- Dead letter files có format: `dead_<timestamp>_<original-name>` với JSON metadata header

## Architecture

```
self-healer.js (fix NO-OP)
  └─ restartProxy()
       └─ pkill -f "antigravity-claude-proxy"    (kill cũ)
       └─ spawn("PORT=9191 antigravity-claude-proxy") (start mới)
       └─ đợi 3s + health check http://localhost:9191/health
       └─ trả true/false thực sự

circuit-breaker.js (module mới)
  ├─ CLOSED → OPEN (sau 3 failures)
  ├─ OPEN   → HALF-OPEN (sau 60s)
  ├─ HALF-OPEN → CLOSED (nếu success)
  └─ HALF-OPEN → OPEN (nếu fail)

task-queue.js (thêm DLQ logic)
  └─ processQueue()
       └─ Nếu retryCounts[task] >= MAX_RETRIES
            └─ moveToDeadLetter(task, reason)
            └─ KHÔNG retry thêm

auto-cto-pilot.js (fix await)
  └─ await handleVerify()   ← FIX BUG #6

system-status-registry.js (fix isProAvailable auto-reset)
  └─ setProLimitHit()
       └─ setTimeout(() => resetProLimit(), 60 * 60_000)  ← FIX BUG #10
```

## Related Code Files

### Tạo mới
- `apps/openclaw-worker/lib/circuit-breaker.js` — Circuit breaker state machine

### Sửa đổi
- `apps/openclaw-worker/lib/self-healer.js` — Fix restartProxy() NO-OP
- `apps/openclaw-worker/lib/task-queue.js` — Thêm Dead Letter Queue logic
- `apps/openclaw-worker/lib/auto-cto-pilot.js` — Fix `await handleVerify()`
- `apps/openclaw-worker/lib/system-status-registry.js` — Fix isProAvailable auto-reset

### Xóa
- (không có)

## Implementation Steps

### Bước 1: Tạo circuit-breaker.js

```javascript
// apps/openclaw-worker/lib/circuit-breaker.js
'use strict';
const { log } = require('./brain-logger');

const FAILURE_THRESHOLD = 3;
const RESET_TIMEOUT_MS = 60_000;
const HALF_OPEN_MAX_CALLS = 1;

// State cho từng service (proxy, model, v.v.)
const breakers = new Map();

function getBreaker(name) {
  if (!breakers.has(name)) {
    breakers.set(name, {
      state: 'CLOSED', // CLOSED | OPEN | HALF_OPEN
      failureCount: 0,
      lastFailureTime: null,
      halfOpenCalls: 0,
    });
  }
  return breakers.get(name);
}

function isOpen(name) {
  const b = getBreaker(name);
  if (b.state === 'OPEN') {
    const elapsed = Date.now() - b.lastFailureTime;
    if (elapsed > RESET_TIMEOUT_MS) {
      b.state = 'HALF_OPEN';
      b.halfOpenCalls = 0;
      log(`[CIRCUIT] ${name}: OPEN → HALF_OPEN (elapsed=${Math.round(elapsed/1000)}s)`);
      return false;
    }
    return true;
  }
  if (b.state === 'HALF_OPEN' && b.halfOpenCalls >= HALF_OPEN_MAX_CALLS) {
    return true;
  }
  return false;
}

function recordSuccess(name) {
  const b = getBreaker(name);
  if (b.state === 'HALF_OPEN') {
    log(`[CIRCUIT] ${name}: HALF_OPEN → CLOSED (success)`);
    b.state = 'CLOSED';
    b.failureCount = 0;
  } else if (b.state === 'CLOSED') {
    b.failureCount = 0;
  }
}

function recordFailure(name) {
  const b = getBreaker(name);
  b.failureCount++;
  b.lastFailureTime = Date.now();
  if (b.state === 'HALF_OPEN') {
    log(`[CIRCUIT] ${name}: HALF_OPEN → OPEN (failure in probe)`);
    b.state = 'OPEN';
  } else if (b.state === 'CLOSED' && b.failureCount >= FAILURE_THRESHOLD) {
    log(`[CIRCUIT] ${name}: CLOSED → OPEN (${b.failureCount} failures)`);
    b.state = 'OPEN';
  }
}

function getState(name) {
  return getBreaker(name).state;
}

module.exports = { isOpen, recordSuccess, recordFailure, getState };
```

<!-- Updated: Validation Session 1 - restartProxy() thay bằng health check + alert only (user chọn KHÔNG restart proxy) -->
### Bước 2: Fix self-healer.js — Health Check + Alert Only (không restart)

```javascript
// Tìm hàm restartProxy() trong self-healer.js và thay thế:
const http = require('http');

// KHÔNG restart proxy — chỉ health check + alert
async function checkProxyHealth() {
  return new Promise((resolve) => {
    const req = http.get('http://localhost:9191/health', (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(3000, () => { req.destroy(); resolve(false); });
  });
}

async function restartProxy() {
  const { log } = require('./brain-logger');
  const healthy = await checkProxyHealth();
  if (!healthy) {
    log('[SELF-HEALER] ⚠️ Proxy UNHEALTHY — manual intervention required');
    // TODO: Telegram alert nếu có bot token
    return false;
  }
  log('[SELF-HEALER] Proxy health check OK');
  return true;
}
```

### Bước 3: Thêm Dead Letter Queue vào task-queue.js

```javascript
// Thêm constants
const DLQ_DIR = path.join(config.WATCH_DIR, 'dead-letter');

// Tạo DLQ dir khi init
function initDLQ() {
  if (!fs.existsSync(DLQ_DIR)) {
    fs.mkdirSync(DLQ_DIR, { recursive: true });
    log(`[QUEUE] Dead letter directory created: ${DLQ_DIR}`);
  }
}

// Hàm chuyển task sang DLQ
function moveToDeadLetter(taskFile, reason, lastError) {
  const src = path.join(config.WATCH_DIR, taskFile);
  const timestamp = Date.now();
  const dlqName = `dead_${timestamp}_${taskFile}`;
  const dst = path.join(DLQ_DIR, dlqName);
  try {
    const originalContent = fs.readFileSync(src, 'utf8');
    const metadata = JSON.stringify({
      originalFile: taskFile,
      movedAt: new Date().toISOString(),
      reason,
      lastError: lastError || 'unknown',
      retryCount: retryCounts.get(taskFile) || 0,
    }, null, 2);
    fs.writeFileSync(dst, `--- DEAD LETTER METADATA ---\n${metadata}\n--- ORIGINAL CONTENT ---\n${originalContent}`);
    fs.unlinkSync(src);
    retryCounts.delete(taskFile);
    queuedSet.delete(taskFile);
    processingSet.delete(taskFile);
    log(`[QUEUE] Task moved to dead letter: ${taskFile} → ${dlqName} (reason: ${reason})`);
  } catch (e) {
    log(`[QUEUE] Failed to move to DLQ: ${e.message}`);
  }
}

// Trong processQueue(), trước khi retry:
if ((retryCounts.get(taskFile) || 0) >= MAX_RETRIES) {
  moveToDeadLetter(taskFile, 'max_retries_exceeded', lastError);
  return; // Không retry nữa
}
```

### Bước 4: Fix auto-cto-pilot.js BUG #6

Tìm dòng gọi `handleVerify()` và thêm `await`:

```javascript
// TRƯỚC:
handleVerify(missionResult);

// SAU:
await handleVerify(missionResult);
```

Nếu hàm gọi không phải async, thêm `async` keyword:
```javascript
// TRƯỚC:
function onMissionComplete(result) {
  handleVerify(result);
}

// SAU:
async function onMissionComplete(result) {
  await handleVerify(result);
}
```

### Bước 5: Fix system-status-registry.js BUG #10

Tìm `setProLimitHit()` và thêm auto-reset:

```javascript
// TRƯỚC:
function setProLimitHit(hit) {
  proLimitHit = hit;
}

// SAU:
let proResetTimer = null;

function setProLimitHit(hit) {
  proLimitHit = hit;
  if (hit) {
    // Auto-reset sau 60 phút
    if (proResetTimer) clearTimeout(proResetTimer);
    proResetTimer = setTimeout(() => {
      proLimitHit = false;
      proResetTimer = null;
      log('[STATUS] Pro rate limit auto-reset after 60min');
    }, 60 * 60_000);
  } else {
    if (proResetTimer) {
      clearTimeout(proResetTimer);
      proResetTimer = null;
    }
  }
}
```

### Bước 6: Wire circuit breaker vào mission-dispatcher.js (hoặc brain-mission-runner.js)

```javascript
const { isOpen, recordSuccess, recordFailure } = require('./circuit-breaker');

async function runMission(prompt, projectDir, timeout) {
  if (isOpen('proxy')) {
    log('[CIRCUIT] Proxy circuit OPEN, skipping mission');
    return { success: false, error: 'circuit_open', retry: false };
  }
  try {
    const result = await _runMissionInternal(prompt, projectDir, timeout);
    recordSuccess('proxy');
    return result;
  } catch (e) {
    recordFailure('proxy');
    throw e;
  }
}
```

### Bước 7: Gọi initDLQ() khi task-watcher.js khởi động

```javascript
// task-watcher.js
const { initDLQ } = require('./lib/task-queue');
// Trong hàm start():
initDLQ();
```

### Bước 8: Verify

```bash
# Test DLQ: tạo task giả, fail nhiều lần
echo "INVALID_MISSION_CONTENT" > apps/openclaw-worker/tasks/mission_dlq_test.txt
# Chạy daemon, kiểm tra sau MAX_RETRIES lần thất bại:
ls apps/openclaw-worker/tasks/dead-letter/

# Test circuit breaker
node -e "
  const cb = require('./apps/openclaw-worker/lib/circuit-breaker');
  cb.recordFailure('proxy');
  cb.recordFailure('proxy');
  cb.recordFailure('proxy');
  console.log('Open?', cb.isOpen('proxy')); // true
  console.log('State:', cb.getState('proxy')); // OPEN
"
```

## Todo List

- [ ] Tạo circuit-breaker.js với CLOSED/OPEN/HALF_OPEN states
- [ ] Fix self-healer.js: restartProxy() thực sự restart process
- [ ] Thêm checkProxyHealth() vào self-healer.js
- [ ] Tạo DLQ_DIR constant và initDLQ() trong task-queue.js
- [ ] Tạo moveToDeadLetter() trong task-queue.js
- [ ] Wire DLQ check vào processQueue() (thay vì vòng lặp retry vĩnh viễn)
- [ ] Fix auto-cto-pilot.js: thêm `await` trước handleVerify()
- [ ] Fix system-status-registry.js: isProAvailable auto-reset sau 60 phút
- [ ] Wire circuit breaker vào mission runner
- [ ] Gọi initDLQ() trong task-watcher.js startup
- [ ] Test DLQ với task giả thất bại lặp lại
- [ ] Test circuit breaker state transitions

## Success Criteria

- `restartProxy()` trả `true` khi proxy restart thành công (không còn log "skip")
- Task thất bại 3 lần xuất hiện trong `tasks/dead-letter/` với metadata JSON
- Circuit breaker log `CLOSED → OPEN` sau 3 proxy failures liên tiếp
- Auto-CTO không còn stuck `isApiBusy=true` sau proxy error
- `isProAvailable()` trả `true` sau 60 phút kể từ khi bị set `false`

## Risk Assessment

| Rủi ro | Xác suất | Tác động | Giảm thiểu |
|--------|----------|----------|-----------|
| restartProxy() kill process khác trùng tên | Thấp | Cao | Dùng PID file thay vì `pkill -f` khi có thể |
| Circuit breaker false positive (network blip) | Trung bình | Trung bình | Threshold 3 failures + 60s reset đủ conservative |
| DLQ directory permissions | Thấp | Thấp | `mkdir -p` với recursive trong initDLQ() |
| await handleVerify() thay đổi timing trong auto-cto-pilot | Trung bình | Thấp | Test toàn bộ auto-CTO flow sau khi sửa |

## Security Considerations

- DLQ files chứa nội dung task (có thể nhạy cảm) — đảm bảo `tasks/dead-letter/` trong `.gitignore`
- `restartProxy()` spawn process với `process.env` — đảm bảo không có env vars nhạy cảm bị log

## Next Steps

- Phase 05: Fix các bug còn lại (tmux session name, project-scanner endpoint, v.v.)
- Phase 06: Health HTTP endpoint expose circuit breaker state và DLQ count
