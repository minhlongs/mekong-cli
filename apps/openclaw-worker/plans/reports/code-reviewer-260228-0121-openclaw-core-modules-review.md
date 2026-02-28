# Code Review — openclaw-worker Core Modules

**Date:** 2026-02-28
**Scope:** 12 core modules (2527 LOC tổng)
**Reviewer:** code-reviewer agent

---

## Tóm tắt

6 files vượt 200 LOC. Nhiều silent catch, dead code, hardcoded path, và 2 logic bug nghiêm trọng (circuit-breaker HALF_OPEN không hoạt động, `archiveProcessedMissions` undefined khi import).

---

## CRITICAL ISSUES

### 1. `circuit-breaker.js` — `halfOpenCalls` không bao giờ tăng (Logic Bug)

**File:** `lib/circuit-breaker.js:27`

`isOpen()` kiểm tra `halfOpenCalls >= 1` để block request, nhưng `halfOpenCalls` không bao giờ được tăng ở bất cứ đâu trong file. Kết quả: HALF_OPEN state luôn cho qua mọi request thay vì chỉ 1 test request — toàn bộ circuit-breaker HALF_OPEN logic bị vô hiệu.

```js
// HIỆN TẠI: halfOpenCalls tăng ở đâu? → KHÔNG CÓ
if (b.state === 'HALF_OPEN' && b.halfOpenCalls >= 1) return true; // never true

// FIX: Trong isOpen() khi state là HALF_OPEN, phải tăng counter
if (b.state === 'HALF_OPEN') {
  b.halfOpenCalls++;           // <-- thêm dòng này
  if (b.halfOpenCalls >= 1) return true;
}
```

### 2. `task-watcher.js:193` — `archiveProcessedMissions` không tồn tại trong `task-queue.js`

**File:** `task-watcher.js:193`

```js
const { archiveProcessedMissions } = require('./lib/task-queue');
```

`task-queue.js` exports: `startWatching, stopWatching, isQueueEmpty, enqueue, initDLQ, moveToDeadLetter, getQueueStats` — **không có** `archiveProcessedMissions`. Variable này là `undefined`, và bất kỳ call nào sẽ throw `TypeError: archiveProcessedMissions is not a function`. Hiện tại không thấy call trong code, nhưng import undefined là dead weight và nguy hiểm.

**Fix:** Xóa dòng import đó.

---

## HIGH PRIORITY

### 3. `brain-boot-sequence.js` — Hardcoded path `/Users/macbookprom1/` rải khắp file

**File:** `lib/brain-boot-sequence.js:23,27,32,95,96,108,109,127,131,132`

13+ hardcoded path tuyệt đối với username `macbookprom1`. Code này sẽ break ngay khi chạy trên bất kỳ máy nào khác, hoặc khi username đổi.

```js
// HIỆN TẠI (line 95-96):
'/Users/macbookprom1/.npm/_npx/a3241bba59c344f5/node_modules/...',
'/Users/macbookprom1/mekong-cli',

// HIỆN TẠI (line 108-109):
const profilePro = '/Users/macbookprom1/.claude_antigravity_pro';
const profileApi = '/Users/macbookprom1/.claude_antigravity_api';
```

Tương tự ở `brain-spawn-manager.js:68,72,77`.

**Fix:** Dùng `process.env.HOME` hoặc `os.homedir()`:
```js
const HOME = process.env.HOME || require('os').homedir();
const profilePro = path.join(HOME, '.claude_antigravity_pro');
const profileApi = path.join(HOME, '.claude_antigravity_api');
```

MCP server path hardcode `a3241bba59c344f5` (npm cache hash) đặc biệt nguy hiểm — sẽ break khi npm cache được clean. Nên dùng `which` hoặc `npx` resolve.

### 4. `brain-boot-sequence.js` — Hàm `generateClaudeCommand` bị duplicate 100%

**Files:** `lib/brain-spawn-manager.js:62` và `lib/brain-boot-sequence.js:18`

Hai file define cùng một hàm `generateClaudeCommand` với logic giống hệt nhau. Comment ở boot-sequence nói "Inlined here to avoid circular dependency" nhưng đây là DRY violation. Nếu sửa logic ở một chỗ, chỗ kia không được cập nhật.

**Fix:** Tạo `lib/claude-command-builder.js` export hàm này, cả hai file import từ đó.

### 5. `brain-mission-runner.js:87,91,172,253,276` — Inline `require()` trong hot path

**File:** `lib/brain-mission-runner.js`

Có 8+ `require()` calls được gọi bên trong polling loop (chạy mỗi 500ms):
```js
// Dòng 87 (trong try block trong runMission):
const { countTokensBetween, recordMission, getDailyUsage } = require('./token-tracker');

// Dòng 172 (trong while loop):
const { checkStuckIntervention } = require('./brain-system-monitor');

// Dòng 253 (trong _handleIdleState):
const { getMissionSummary, clearCache } = require('./llm-interpreter');
```

Node.js cache `require()` sau lần đầu nên không gây overhead lớn, nhưng pattern này làm code khó đọc và có thể tạo issues sau hot-reload (SIGUSR1 xóa cache). Di chuyển tất cả lên top-level imports.

### 6. `brain-respawn-controller.js:50` — Race condition trong rate limiter

**File:** `lib/brain-respawn-controller.js:46-52`

```js
if (!canRespawn()) {
  // ...
  respawnTimestamps.length = 0;  // Xóa TẤT CẢ timestamps sau cooldown
}
respawnTimestamps.push(Date.now());
```

Sau khi cooldown xong, code xóa sạch `respawnTimestamps` rồi push timestamp mới. Nghĩa là sau mỗi lần hit rate limit + cooldown, bộ đếm reset về 1 — cho phép 5 respawn tiếp theo ngay lập tức. Đây là reset không có giới hạn tổng.

**Fix:** Không xóa sạch; chỉ để `canRespawn()` filter timestamps cũ (đã làm trong `brain-spawn-manager.js:49-52`). Xóa block `respawnTimestamps.length = 0` trong `brain-respawn-controller.js`.

---

## MEDIUM PRIORITY

### 7. `brain-spawn-manager.js:156` — Silent catch block (mất thông tin lỗi)

**File:** `lib/brain-spawn-manager.js:156`

```js
function autoCleanStaleLock(idx) {
  try {
    // ...
  } catch (e) { }  // SILENT — không log gì
}
```

Khi lock file cleanup fail (permission error, fs error), không có log. Khó debug khi stale lock không được clear.

**Fix:**
```js
} catch (e) { log(`[HEALER] Lock cleanup P${idx} error: ${e.message}`); }
```

### 8. `brain-spawn-manager.js:175,179` — Silent catch trên file operations quan trọng

**File:** `lib/brain-spawn-manager.js:175,179`

```js
function setWorkerLock(idx, missionNum) {
  try { fs.writeFileSync(...); } catch { }  // SILENT
}

function clearWorkerLock(idx) {
  try { fs.unlinkSync(...); } catch { }  // SILENT
}
```

Nếu lock file không tạo được, mission sẽ không có lock → nhiều mission chạy song song. Nếu lock không xóa được, worker bị block vĩnh viễn.

**Fix:** Thêm `log()` trong catch.

### 9. `mission-dispatcher.js:19` — `console.log` fallback leak vào production logs

**File:** `lib/mission-dispatcher.js:19-25`

```js
let log = console.log;  // fallback
try {
  const bpm = require('./brain-process-manager');
  if (bpm.log) log = bpm.log;
} catch (e) {
  console.error(`WARN: brain-process-manager not found (${e.message}). Using console.log.`);
}
```

Nếu `brain-process-manager` load fail, tất cả logs từ `mission-dispatcher` đi thẳng vào `process.stdout` thay vì log file. Import trực tiếp từ `brain-logger` sẽ sạch hơn:

```js
const { log } = require('./brain-logger');
```

### 10. `mission-dispatcher.js:61-62` — Dead code: `VI_PREFIX` và `FILE_LIMIT` module-level bị shadow

**File:** `lib/mission-dispatcher.js:61-62,226-227`

```js
// Module level (line 61-62) — NEVER USED
const VI_PREFIX = 'Trả lời bằng TIẾNG VIỆT. ';
const FILE_LIMIT = 'Chỉ sửa TỐI ĐA 5 file mỗi mission...';

// Inside buildPrompt() (line 226-227) — shadow + override module vars
const FILE_LIMIT = 'Sửa < 5 file mỗi mission.';
const VI_PREFIX = '';
```

Module-level constants bị shadow hoàn toàn bởi local variables trong `buildPrompt()`. Module-level vars không được dùng ở bất cứ đâu khác. Xóa module-level vars.

### 11. `brain-mission-runner.js:39` — `tokensSinceCompact` tăng nhưng không bao giờ dùng để quyết định gì

**File:** `lib/brain-mission-runner.js:39,182`

```js
let tokensSinceCompact = 0;
// ...
tokensSinceCompact += tk.tokens;  // dòng 182
```

Biến này được cộng dồn nhưng không trigger bất kỳ action nào (compact đã bị disable). Là dead counter.

**Fix:** Xóa `tokensSinceCompact` hoặc thêm logic sử dụng nó.

### 12. `task-watcher.js:38-75` — `console.log` trước khi `log()` được import

**File:** `task-watcher.js:38-75` vs line 90

`log = require('./lib/brain-process-manager').log` được import ở line 90, nhưng `console.log` được dùng ở lines 38-75 (PID lock + proxy startup). Đây không phải bug critical nhưng làm logs bị split: một phần vào stdout, một phần vào log file.

**Fix:** Có thể chấp nhận ở early-boot phase vì `brain-logger` chưa available. Nhưng nên thêm comment giải thích.

---

## LOW PRIORITY

### 13. Files vượt 200 LOC (theo development rules)

| File | LOC | Nên split |
|------|-----|-----------|
| `lib/mission-dispatcher.js` | 487 | `prompt-builder.js` + `project-router.js` + `task-executor.js` |
| `lib/brain-mission-runner.js` | 289 | `idle-handler.js` tách `_handleIdleState` |
| `task-watcher.js` | 371 | `boot-sequence.js` tách boot logic |
| `lib/task-queue.js` | 292 | `queue-processor.js` tách `processQueue` |
| `lib/brain-state-machine.js` | 213 | Có thể chấp nhận (pattern arrays lớn) |
| `lib/brain-spawn-manager.js` | 205 | Borderline OK |

`mission-dispatcher.js` (487 LOC) là nghiêm trọng nhất — hàm `buildPrompt` một mình dài ~180 dòng.

### 14. `brain-respawn-controller.js:42` — Param `useContinue` không bao giờ được dùng

**File:** `lib/brain-respawn-controller.js:42`

```js
async function respawnBrain(intent = 'EXECUTION', useContinue = true) {
  // useContinue không được dùng trong function body
```

Param dead từ refactor. Xóa để tránh confuse.

### 15. `config.js:31` — `POLL_INTERVAL_MS: 100` nhưng comment sai

**File:** `config.js:31`, `task-queue.js:276`

```js
// config.js
POLL_INTERVAL_MS: 100, // "100ms Polling"

// task-queue.js line 276
}, config.POLL_INTERVAL_MS); // PROJECT FLASH: 1s Backup Poll  ← SAI (100ms, không phải 1s)
```

Comment trong `task-queue.js` nói "1s Backup Poll" nhưng thực tế là 100ms. Misleading.

### 16. `brain-mission-runner.js` — `_handleIdleState` có signature 13 params

**File:** `lib/brain-mission-runner.js:237-240`

Hàm `_handleIdleState` nhận 13 parameters. Nên extract thành object hoặc closure.

---

## Unresolved Questions

1. `circuit-breaker.js` — `isOpen()` trong HALF_OPEN có nên tăng `halfOpenCalls` trước hay sau khi check? Nếu tăng trước, call đầu tiên luôn bị block (halfOpenCalls = 1 >= 1). Có thể intention là cho qua 1 test call, sau đó block → tăng TRƯỚC check là đúng.

2. `brain-boot-sequence.js:95` — MCP server path hardcode npm cache hash `a3241bba59c344f5` — đây có phải intentional không? Hay nên dùng `npx @modelcontextprotocol/server-filesystem` resolve?

3. `task-watcher.js:193` — `archiveProcessedMissions` import undefined — có plan implement function này không?
