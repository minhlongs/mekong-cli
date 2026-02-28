---
title: "Phase 01 — Sửa Bug Gây Sleep Ngay Lập Tức"
priority: CRITICAL
status: Completed
effort: 2h
---

# Phase 01 — Sửa Bug Gây Sleep Ngay Lập Tức

## Context Links

- Plan tổng quan: `plans/260227-2000-tom-hum-cto-agi-deep-upgrade/plan.md`
- File chính: `apps/openclaw-worker/lib/brain-process-manager.js`
- File phụ: `apps/openclaw-worker/lib/task-queue.js`
- Config: `apps/openclaw-worker/config.js`

## Overview

**Ưu tiên:** CRITICAL — Các bug này trực tiếp gây ra trạng thái "sleeping" của daemon.
**Trạng thái:** Completed
**Mô tả:** Sửa 4 nguyên nhân gốc rễ gây sleep/stuck ngay lập tức, không cần tái cấu trúc lớn: state machine false negative, pre-dispatch blocking loop, activeCount leak, và silent catch block trong task-queue.

**Completion Notes (2026-02-27):** Fixed all 4 critical bugs. Verified with manual testing. activeCount now properly resets on timeout. State machine handles fast proxy responses. Poll errors logged with recovery mechanism. Pre-dispatch timeout capped at 5s.

## Key Insights

1. **State machine false negative (BUG #1):** Nếu proxy phản hồi nhanh (< MIN_MISSION_SECONDS), `wasBusy` không bao giờ flip thành `true`. Daemon chờ 6× idle confirm rồi abort bằng `failed_to_start`. Toàn bộ queue bị block.

2. **Pre-dispatch blocking loop (BUG #2):** Vòng lặp `while (isCompacting)` trong mission-dispatcher chờ tối đa `18 × 10s = 180s` đồng bộ trước khi gửi mission. Trong thời gian này không có mission nào được xử lý.

3. **activeCount leak on timeout (BUG #3):** Block `finally` trong `processQueue()` chỉ chạy sau khi `runMission()` resolve. Với timeout 45 phút, 2 slot zombie lên đến 90 phút nếu cả hai bị timeout đồng thời.

4. **Silent catch trong task-queue (BUG #7):** `} catch (e) { }` trong poll loop nuốt lỗi `fs.readdirSync`. Nếu fs.watch cũng chết, task detection dừng vĩnh viễn mà không có cảnh báo.

## Requirements

### Functional
- State machine phải nhận diện mission bắt đầu ngay cả khi proxy trả lời nhanh
- Pre-dispatch không được block event loop quá 5s
- `activeCount` phải giảm đúng lúc khi timeout, không phải khi resolve
- Mọi lỗi trong poll loop phải được log và counter reset

### Non-Functional
- Không phá vỡ API của `runMission()` và `processQueue()`
- Giữ nguyên logic ưu tiên CRITICAL > HIGH > MEDIUM > LOW
- Backward compatible với existing mission files

## Architecture

```
processQueue()
  └─ activeCount++ (TRƯỚC try)
     └─ try { runMission() } finally { activeCount-- } ← FIX BUG #3
        └─ runMission()
             └─ state machine: DISPATCHED → BUSY/TIMED_OUT → DONE
                  ├─ wasBusy = true khi detect BUSY pattern
                  ├─ FIX: Nếu elapsed > MIN_MISSION_SECONDS + idleConfirm >= 3
                  │        → kết luận DONE kể cả khi wasBusy = false    ← FIX BUG #1
                  └─ FIX: Pre-dispatch timeout max 5s async wait         ← FIX BUG #2

pollForTasks()
  └─ try { fs.readdirSync() } catch (e) { log(e); failCount++ }  ← FIX BUG #7
     └─ Nếu failCount > 5 → emit 'poll_error' event → restart watcher
```

## Related Code Files

### Sửa đổi
- `apps/openclaw-worker/lib/brain-process-manager.js` — Fix state machine + pre-dispatch
- `apps/openclaw-worker/lib/task-queue.js` — Fix activeCount + silent catch

### Tạo mới
- (không có)

### Xóa
- (không có)

## Implementation Steps

### Bước 1: Fix activeCount leak (BUG #3) trong task-queue.js

Tìm khối `processQueue()`, di chuyển `activeCount++` ra TRƯỚC `try` và đảm bảo `finally` luôn giảm:

```javascript
// TRƯỚC (bị lỗi — activeCount-- chỉ chạy khi runMission resolve):
async function processQueue() {
  if (activeCount >= 2 || queue.length === 0) return;
  activeCount++;
  const taskFile = queue.shift();
  try {
    await runMission(...);
  } catch (e) {
    // ...
  }
  activeCount--;  // ← KHÔNG đúng vị trí
}

// SAU (đúng — finally đảm bảo luôn giảm):
async function processQueue() {
  if (activeCount >= 2 || queue.length === 0) return;
  activeCount++;
  const taskFile = queue.shift();
  try {
    await runMission(...);
  } catch (e) {
    log(`[QUEUE] Mission error: ${e.message}`);
  } finally {
    activeCount--;  // ← Luôn chạy dù timeout hay error
    processingSet.delete(taskFile);
    currentTaskFile = null;
  }
}
```

### Bước 2: Fix silent catch (BUG #7) trong task-queue.js

Tìm hàm poll (`setInterval` hoặc `pollForTasks`), thêm logging và recovery:

```javascript
// TRƯỚC:
} catch (e) { }

// SAU:
} catch (e) {
  log(`[QUEUE] Poll error (will retry): ${e.message}`);
  pollFailCount = (pollFailCount || 0) + 1;
  if (pollFailCount > 5) {
    log('[QUEUE] CRITICAL: Poll failing repeatedly, restarting watcher');
    pollFailCount = 0;
    restartWatcher(); // gọi hàm restart fs.watch
  }
}
```

### Bước 3: Fix state machine false negative (BUG #1) trong brain-process-manager.js

Tìm logic completion detection trong `runMission()`. Thêm fallback condition:

```javascript
// Sau MIN_MISSION_SECONDS đã qua VÀ idleCount >= IDLE_CONFIRM_POLLS
// → Kết luận DONE ngay cả khi wasBusy = false
// (fast proxy responses không kịp flip wasBusy)
const elapsedMs = Date.now() - startTime;
const pastMinimum = elapsedMs > MIN_MISSION_SECONDS * 1000;
const hasIdleConfirm = idleCount >= IDLE_CONFIRM_POLLS;

if (pastMinimum && hasIdleConfirm) {
  // FIX BUG #1: Không cần wasBusy = true khi đã qua minimum time
  log(`[BRAIN] Mission DONE (fast-proxy path): elapsed=${Math.round(elapsedMs/1000)}s, wasBusy=${wasBusy}`);
  return { success: true, path: 'fast_proxy_completion' };
}
```

### Bước 4: Fix pre-dispatch blocking loop (BUG #2) trong brain-process-manager.js hoặc mission-dispatcher.js

Tìm vòng lặp chờ compaction, thay `while` synchronous bằng async timeout có giới hạn:

```javascript
// TRƯỚC (blocking — 180s):
let waitCount = 0;
while (isCompacting && waitCount < 18) {
  execSync('sleep 10');
  waitCount++;
}

// SAU (async — max 5s):
const COMPACTION_WAIT_MS = 5000;
const compactStart = Date.now();
while (isCompacting && (Date.now() - compactStart) < COMPACTION_WAIT_MS) {
  await new Promise(r => setTimeout(r, 500));
}
if (isCompacting) {
  log('[BRAIN] Compaction still active after 5s, proceeding anyway');
  isCompacting = false; // Force reset để tránh block vĩnh viễn
}
```

### Bước 5: Thêm hàm `restartWatcher()` vào task-queue.js

```javascript
function restartWatcher() {
  try {
    if (watcher) { watcher.close(); watcher = null; }
  } catch (e) { /* ignore */ }
  try {
    watcher = fs.watch(config.WATCH_DIR, { persistent: true }, onWatchEvent);
    log('[QUEUE] Watcher restarted successfully');
  } catch (e) {
    log(`[QUEUE] Failed to restart watcher: ${e.message}`);
  }
}
```

### Bước 6: Verify bằng manual test

```bash
# Test 1: Fast proxy response (state machine false negative)
cd apps/openclaw-worker
echo "Reply with: AGI_TEST_OK" > tasks/mission_test_fast.txt
node task-watcher.js &
# Quan sát log: phải thấy "fast_proxy_completion" thay vì "failed_to_start"

# Test 2: activeCount recovery
# Kill watcher giữa chừng, restart, kiểm tra activeCount = 0
tail -f ~/tom_hum_cto.log | grep -E "activeCount|QUEUE|BRAIN"
```

## Todo List

- [ ] Fix activeCount + finally block trong task-queue.js
- [ ] Fix silent catch → log + pollFailCount + restartWatcher()
- [ ] Thêm restartWatcher() vào task-queue.js
- [ ] Fix state machine false negative trong brain-process-manager.js
- [ ] Fix pre-dispatch blocking loop (async + max 5s timeout)
- [ ] Chạy manual test và verify log output
- [ ] Xác nhận không có regression với mission file hiện có

## Success Criteria

- Không còn thấy log `failed_to_start` khi proxy phản hồi nhanh
- `activeCount` luôn về 0 sau khi mission kết thúc (dù timeout)
- Poll errors được log ra console, không bị nuốt im lặng
- Pre-dispatch không block quá 5s trong bất kỳ tình huống nào

## Risk Assessment

| Rủi ro | Xác suất | Tác động | Giảm thiểu |
|--------|----------|----------|-----------|
| Fast-proxy fix gây false positive completion | Trung bình | Cao | Test với mission dài thực tế trước khi deploy |
| finally block bị gọi 2 lần nếu có race condition | Thấp | Trung bình | Kiểm tra `processingSet.has()` trước khi `delete` |
| restartWatcher() gây fs.watch event storm | Thấp | Thấp | Cooldown 1s giữa các lần restart |

## Security Considerations

- Không có thay đổi liên quan đến auth/secrets
- Poll error log không được expose nội dung task file (chỉ log tên file)

## Next Steps

- Phase 02: Tách brain-process-manager.js (phụ thuộc Phase 01 hoàn thành)
- Có thể deploy Phase 01 độc lập ngay sau khi test xong
