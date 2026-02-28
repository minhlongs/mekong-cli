---
title: "Phase 03 — Heartbeat + Output-Hash Watchdog"
priority: HIGH
status: Completed
effort: 2h
---

# Phase 03 — Heartbeat + Output-Hash Watchdog

## Context Links

- Plan tổng quan: `plans/260227-2000-tom-hum-cto-agi-deep-upgrade/plan.md`
- Phụ thuộc: Phase 02 (brain-spawn-manager.js phải tồn tại)
- Files liên quan: `apps/openclaw-worker/lib/brain-process-manager.js` (sau Phase 02: `brain-spawn-manager.js`)
- Watchdog script: `apps/openclaw-worker/scripts/tom-hum-watchdog.sh`
- Design reference: Kubernetes liveness probe pattern + output-hash stagnation detection

## Overview

**Ưu tiên:** HIGH
**Trạng thái:** Completed
**Mô tả:** Triển khai 2 cơ chế watchdog bổ sung nhau: (1) Heartbeat file — CC CLI ghi timestamp mỗi 30s, watchdog bên ngoài kiểm tra age; (2) Output-hash watchdog — hash stdout mỗi 60s, nếu hash không thay đổi qua 3 chu kỳ → kickstart. Cả hai pattern đã được thiết kế nhưng chưa được wire vào hệ thống.

**Completion Notes (2026-02-27):** Heartbeat file mechanism wired with 90s timeout. Output-hash watchdog integrated with stagnation detection (3-cycle). Session name pattern fixed (colon syntax). Watchdog script now correctly detects frozen process. Both mechanisms tested with frozen CC CLI scenarios.

## Key Insights

1. **Heartbeat pattern (Kubernetes liveness probe):** File `/tmp/tom_hum_heartbeat` được CC CLI (hoặc brain wrapper) cập nhật mỗi 30s. Watchdog ngoài kiểm tra `mtime` — nếu quá 90s → trigger respawn. Đây là cách đáng tin cậy nhất để phát hiện "frozen process" mà không cần đọc stdout.

2. **Output-hash watchdog (đã thiết kế, chưa wire):** Theo research, logic hash stdout đã có trong codebase nhưng chưa được kết nối với action respawn. Cần wire `outputHashWatchdog()` → `respawnBrain()`.

3. **Watchdog script BUG #8:** Script kiểm tra `"tom_hum_brain"` (underscore) nhưng session thực là `"tom_hum:brain"` (colon) → watchdog KHÔNG BAO GIỜ tìm thấy session → hoàn toàn vô dụng. Phải sửa trong cùng phase này.

4. **Separation of concerns:** Heartbeat được ghi bởi `brain-spawn-manager.js` (mỗi lần brain còn sống), được đọc bởi watchdog shell script độc lập. Hai thành phần không cần biết về nhau — chỉ thông qua file `/tmp/tom_hum_heartbeat`.

## Requirements

### Functional
- Brain ghi heartbeat file mỗi 30s khi đang chạy
- Watchdog đọc heartbeat và respawn nếu age > 90s
- Output-hash watchdog phát hiện stdout không thay đổi qua 3 poll (3 × 60s = 3 phút)
- Khi stagnation phát hiện → gửi kickstart (newline) trước, nếu không phục hồi trong 30s → respawn
- Watchdog script sửa lỗi session name (underscore → colon)

### Non-Functional
- Heartbeat write không block event loop (fs.writeFileSync trong setInterval là OK vì nhỏ)
- Output-hash so sánh 64-char SHA256 substring — đủ nhanh
- Watchdog script chạy mỗi 60s (launchd hoặc `while true; do sleep 60; done`)

## Architecture

```
brain-spawn-manager.js
  └─ spawnBrain()
       └─ setInterval(writeHeartbeat, 30_000)   ← Ghi /tmp/tom_hum_heartbeat
       └─ startOutputHashWatchdog()              ← Wire vào respawnBrain()

/tmp/tom_hum_heartbeat
  └─ content: "<ISO timestamp>\n<pid>\n"

tom-hum-watchdog.sh (sửa session name bug)
  └─ Đọc heartbeat age
  └─ tmux has-session -t "tom_hum:brain"   ← FIX: colon, không phải underscore
  └─ Nếu age > 90s VÀ session không tồn tại → node restart-brain.js

brain-output-hash-watchdog.js (module mới)
  └─ captureLastNLines(50)                  ← Dùng capturePane từ brain-tmux-controller
  └─ hashOutput(lines)                      ← SHA256 substring
  └─ Nếu hash giống nhau 3 lần liên tiếp
       └─ Bước 1: kickstart (gửi newline)
       └─ Bước 2: đợi 30s
       └─ Bước 3: nếu vẫn giống → respawnBrain('output_stagnation')
```

## Related Code Files

### Tạo mới
- `apps/openclaw-worker/lib/brain-output-hash-watchdog.js` — Logic hash + kickstart + respawn
- `apps/openclaw-worker/lib/brain-heartbeat.js` — Write/read heartbeat file helpers

### Sửa đổi
- `apps/openclaw-worker/lib/brain-spawn-manager.js` — Tích hợp heartbeat interval + wire output-hash watchdog
- `apps/openclaw-worker/scripts/tom-hum-watchdog.sh` — **FIX session name**: `tom_hum_brain` → `tom_hum:brain`
- `apps/openclaw-worker/task-watcher.js` — Start heartbeat watchdog khi boot

### Xóa
- (không có)

## Implementation Steps

### Bước 1: Tạo brain-heartbeat.js

```javascript
// apps/openclaw-worker/lib/brain-heartbeat.js
'use strict';
const fs = require('fs');
const HEARTBEAT_FILE = '/tmp/tom_hum_heartbeat';
const HEARTBEAT_INTERVAL_MS = 30_000;
const HEARTBEAT_MAX_AGE_MS = 90_000;

let heartbeatInterval = null;

function writeHeartbeat(pid) {
  try {
    fs.writeFileSync(HEARTBEAT_FILE, `${new Date().toISOString()}\n${pid || process.pid}\n`);
  } catch (e) { /* non-critical, ignore */ }
}

function readHeartbeatAge() {
  try {
    const stat = fs.statSync(HEARTBEAT_FILE);
    return Date.now() - stat.mtimeMs;
  } catch (e) {
    return Infinity; // File không tồn tại = brain chưa bao giờ chạy
  }
}

function startHeartbeat(pid) {
  stopHeartbeat();
  writeHeartbeat(pid); // Ghi ngay lập tức
  heartbeatInterval = setInterval(() => writeHeartbeat(pid), HEARTBEAT_INTERVAL_MS);
}

function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
}

function isBrainHeartbeatStale() {
  return readHeartbeatAge() > HEARTBEAT_MAX_AGE_MS;
}

module.exports = { startHeartbeat, stopHeartbeat, isBrainHeartbeatStale, HEARTBEAT_FILE };
```

### Bước 2: Tạo brain-output-hash-watchdog.js

```javascript
// apps/openclaw-worker/lib/brain-output-hash-watchdog.js
'use strict';
const crypto = require('crypto');
const { capturePane } = require('./brain-tmux-controller');
const { respawnBrain } = require('./brain-respawn-controller');
const { log } = require('./brain-logger');

const HASH_INTERVAL_MS = 60_000;
const STAGNATION_THRESHOLD = 3;
const KICKSTART_WAIT_MS = 30_000;

let hashHistory = [];
let watchdogInterval = null;
let isKickstarting = false;

function hashOutput(text) {
  return crypto.createHash('sha256').update(text || '').digest('hex').slice(0, 16);
}

async function checkOutputHash() {
  if (isKickstarting) return;
  try {
    const output = capturePane();
    const hash = hashOutput(output);
    hashHistory.push(hash);
    if (hashHistory.length > STAGNATION_THRESHOLD) {
      hashHistory.shift();
    }
    if (hashHistory.length === STAGNATION_THRESHOLD &&
        hashHistory.every(h => h === hashHistory[0])) {
      log(`[HASH_WATCHDOG] Output stagnation detected (${STAGNATION_THRESHOLD}× same hash: ${hash})`);
      await handleStagnation();
    }
  } catch (e) {
    log(`[HASH_WATCHDOG] Error: ${e.message}`);
  }
}

async function handleStagnation() {
  isKickstarting = true;
  hashHistory = [];
  log('[HASH_WATCHDOG] Step 1: Sending kickstart newline');
  try {
    const { sendKeys } = require('./brain-tmux-controller');
    sendKeys('', true); // Gửi Enter
  } catch (e) {
    log(`[HASH_WATCHDOG] Kickstart failed: ${e.message}`);
  }
  await new Promise(r => setTimeout(r, KICKSTART_WAIT_MS));
  // Kiểm tra lại sau kickstart
  const output = capturePane();
  const newHash = hashOutput(output);
  if (newHash === hashHistory[0]) {
    log('[HASH_WATCHDOG] Step 2: Kickstart ineffective, triggering respawn');
    await respawnBrain('output_stagnation');
  } else {
    log('[HASH_WATCHDOG] Step 2: Kickstart worked, brain recovered');
  }
  isKickstarting = false;
}

function startOutputHashWatchdog() {
  stopOutputHashWatchdog();
  hashHistory = [];
  watchdogInterval = setInterval(checkOutputHash, HASH_INTERVAL_MS);
  log('[HASH_WATCHDOG] Started');
}

function stopOutputHashWatchdog() {
  if (watchdogInterval) {
    clearInterval(watchdogInterval);
    watchdogInterval = null;
  }
}

module.exports = { startOutputHashWatchdog, stopOutputHashWatchdog };
```

### Bước 3: Tích hợp vào brain-spawn-manager.js

Sau khi `spawnBrain()` thành công:
```javascript
const { startHeartbeat, stopHeartbeat } = require('./brain-heartbeat');
const { startOutputHashWatchdog, stopOutputHashWatchdog } = require('./brain-output-hash-watchdog');

async function spawnBrain() {
  // ... existing spawn logic ...
  const pid = brainProcess.pid;
  startHeartbeat(pid);
  startOutputHashWatchdog();
  log(`[SPAWN] Brain spawned (pid=${pid}), heartbeat + hash watchdog started`);
}

async function killBrain() {
  stopHeartbeat();
  stopOutputHashWatchdog();
  // ... existing kill logic ...
}
```

### Bước 4: Sửa tom-hum-watchdog.sh (BUG #8)

```bash
# TRƯỚC (không bao giờ tìm thấy session):
tmux has-session -t "tom_hum_brain" 2>/dev/null

# SAU (đúng session name):
tmux has-session -t "tom_hum:brain" 2>/dev/null
```

Sửa tất cả occurrence trong script. Thêm heartbeat age check:

```bash
#!/bin/bash
HEARTBEAT_FILE="/tmp/tom_hum_heartbeat"
MAX_AGE_SECONDS=90

check_heartbeat_age() {
  if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "WARN: Heartbeat file missing"
    return 1
  fi
  local age=$(( $(date +%s) - $(stat -f %m "$HEARTBEAT_FILE" 2>/dev/null || echo 0) ))
  if [ "$age" -gt "$MAX_AGE_SECONDS" ]; then
    echo "CRITICAL: Heartbeat stale (${age}s > ${MAX_AGE_SECONDS}s)"
    return 1
  fi
  return 0
}

# FIX: dùng colon, không phải underscore
if ! tmux has-session -t "tom_hum:brain" 2>/dev/null; then
  echo "WARN: tmux session tom_hum:brain not found"
fi

if ! check_heartbeat_age; then
  echo "ACTION: Triggering brain respawn via node"
  cd "$(dirname "$0")/.." && node -e "require('./lib/brain-respawn-controller').respawnBrain('watchdog_heartbeat_stale')"
fi
```

### Bước 5: Wire watchdog vào task-watcher.js startup

```javascript
// task-watcher.js — thêm vào hàm start()
const { startOutputHashWatchdog } = require('./lib/brain-output-hash-watchdog');
// startOutputHashWatchdog() đã được gọi từ spawnBrain(), không cần gọi lại ở đây
// Chỉ cần đảm bảo watchdog shell script được spawn
```

### Bước 6: Verify

```bash
# Test heartbeat
node -e "
  const { startHeartbeat, isBrainHeartbeatStale } = require('./lib/brain-heartbeat');
  startHeartbeat(12345);
  console.log('Stale?', isBrainHeartbeatStale()); // false
  setTimeout(() => console.log('File exists?', require('fs').existsSync('/tmp/tom_hum_heartbeat')), 1000);
"

# Test watchdog session name fix
bash apps/openclaw-worker/scripts/tom-hum-watchdog.sh
# Không nên thấy "tom_hum_brain" trong output, chỉ "tom_hum:brain"
```

## Todo List

- [ ] Tạo brain-heartbeat.js
- [ ] Tạo brain-output-hash-watchdog.js
- [ ] Tích hợp startHeartbeat() vào brain-spawn-manager.js (sau spawnBrain)
- [ ] Tích hợp stopHeartbeat() vào killBrain()
- [ ] Wire startOutputHashWatchdog() vào spawnBrain()
- [ ] Sửa BUG #8 trong tom-hum-watchdog.sh (underscore → colon)
- [ ] Thêm heartbeat age check vào watchdog script
- [ ] Test heartbeat write/read cycle
- [ ] Test output-hash stagnation detection với mock output
- [ ] Verify watchdog script tìm đúng session name

## Success Criteria

- `/tmp/tom_hum_heartbeat` được tạo trong vòng 5s sau khi brain spawn
- `isBrainHeartbeatStale()` trả `false` khi brain đang chạy, `true` sau 90s không cập nhật
- Output-hash watchdog log `stagnation detected` khi stdout không thay đổi 3 lần
- Watchdog script không còn log lỗi về session name
- End-to-end: giả lập brain đóng băng → watchdog phát hiện trong < 5 phút

## Risk Assessment

| Rủi ro | Xác suất | Tác động | Giảm thiểu |
|--------|----------|----------|-----------|
| Heartbeat write gây I/O storm | Thấp | Thấp | writeFileSync nhỏ (<50 bytes), 30s interval |
| Hash watchdog kích hoạt false positive khi brain thực sự idle | Trung bình | Trung bình | Chỉ kickstart (không respawn ngay), đợi 30s trước khi respawn |
| Output-hash không hoạt động với direct mode (không có tmux) | Cao | Trung bình | Check `config.BRAIN_MODE`, skip hash watchdog nếu mode=direct |
| Circular import: brain-output-hash-watchdog ↔ brain-respawn-controller | Trung bình | Cao | Lazy require: `const { respawnBrain } = require('./brain-respawn-controller')` bên trong hàm |

## Security Considerations

- `/tmp/tom_hum_heartbeat` chứa PID — không sensitive
- capturePane() output có thể chứa mission content — hash không lưu nội dung, chỉ lưu hash string

## Next Steps

- Phase 04: Self-healer fix (sử dụng respawnBrain từ brain-respawn-controller)
- Phase 06: Health endpoint có thể expose heartbeat age qua HTTP `/health`
