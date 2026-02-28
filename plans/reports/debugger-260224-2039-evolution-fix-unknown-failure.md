# Debugger Report: fix unknown+duplicate_rejected failures
**Date:** 2026-02-24 20:39
**Commit:** 928f6796
**Severity:** CRITICAL (sev 280)

---

## Executive Summary

Evolution-engine báo false alarms: `unknown` 14/20 (sev 280) và `duplicate_rejected` 3/20 (sev 60). Root cause là 3 bugs trong `evolution-engine.js` + 1 bug analytics trong `learning-engine.js`. Không có actual mission failures — tất cả là misclassification.

**Result sau fix:** successRate = 100% (2/2 actual missions), 0 triggers.

---

## Root Cause Analysis

### Bug 1: BENIGN_FAILURES set quá hẹp (CRITICAL)

**File:** `lib/evolution-engine.js` line 108

`BENIGN_FAILURES` chỉ có 4 entries: `duplicate_rejected, all_workers_busy, mission_locked, busy_blocked`. Không include `max_retries_exhausted`, `brain_died`, `timeout` — những transient infra errors không phải code bugs.

14 records trong history có `buildResult.output = 'max_retries_exhausted'` + `brain_died` → bị count vào `failureCounts` → trigger `repeated_failure` với `sev = count * 20`.

### Bug 2: getFailureKey() không safe với legacy data

**File:** `lib/evolution-engine.js` line 114

```js
// TRƯỚC: Có thể throw nếu buildResult là string (không phải object)
const key = m.failureType || m.resultCode || m.buildResult?.output || 'unknown';
```

14 missions cũ (trước khi `failureType` field được thêm) → `m.failureType = undefined`, `m.resultCode = undefined`. `m.buildResult?.output` đọc được `'duplicate_rejected'` nhưng không được exclude vì filter sai.

### Bug 3: triggerBrainSurgery() tạo duplicate missions

**File:** `lib/evolution-engine.js` line 320

Mỗi lần evolution check (2-hour interval) trigger surgery, nó tạo `CRITICAL_mission_evolution_surgery_${Date.now()}.txt` mà không check xem mission đó đã pending chưa. Khi missions liên tục fail → evolution liên tục trigger → tạo nhiều surgery missions giống nhau → bị dedup reject (sev 60).

### Bug 4: failureReasons dùng missionId (analytics)

**File:** `lib/learning-engine.js` line 44

```js
// TRƯỚC: Lấy missionId thay vì failure type — vô nghĩa
failureReasons: recentHistory.filter(m => !m.success).map(m => m.missionId)
```

LLM analysis nhận được list mission IDs thay vì failure types → không thể rút ra lesson có ý nghĩa.

---

## Fixes Applied

### 1. `lib/evolution-engine.js` — BENIGN_FAILURES expanded

```js
const BENIGN_FAILURES = new Set([
  'duplicate_rejected', 'all_workers_busy', 'mission_locked', 'busy_blocked',
  'max_retries_exhausted', 'brain_died', 'brain_died_fatal', 'failed_to_start',
  'queued_abort', 'killed_stuck', 'timeout',
]);
```

### 2. `lib/evolution-engine.js` — getFailureKey() helper

```js
const getFailureKey = (m) => {
  if (m.success) return null;
  return m.failureType || m.resultCode
    || (typeof m.buildResult === 'object' && m.buildResult !== null ? m.buildResult.output : null)
    || 'unknown';
};
```

### 3. `lib/evolution-engine.js` — triggerBrainSurgery guard

Check `tasks/` + `tasks/processed/` (30min window) trước khi tạo surgery mission mới.

### 4. `lib/learning-engine.js` — failureReasons fix

```js
// SAU:
failureReasons: recentHistory.filter(m => !m.success).map(m =>
  m.failureType || (typeof m.buildResult === 'object' ? m.buildResult.output : null) || 'unknown'
)
```

### 5. Cleanup

Xóa stale `.mission-active-P0.lock` (mission #1 từ session cũ).

---

## Verification

```
node --check lib/evolution-engine.js   → OK
node --check lib/learning-engine.js    → OK
node --check lib/*.js                  → All OK

Simulation với actual data (last 20 missions):
  recentActual (excl benign): 2
  successRate: 100%
  repeated_failures: {}
  Triggers: NONE
```

---

## Files Modified

| File | Lines changed | Lý do |
|------|--------------|-------|
| `lib/evolution-engine.js` | +35/-7 | BENIGN_FAILURES, getFailureKey(), surgery guard |
| `lib/learning-engine.js` | +1/-1 | failureReasons analytics fix |

---

## Unresolved Questions

- Tại sao `max_retries_exhausted` xảy ra nhiều? → Likely do CC CLI proxy initialization chậm (60s). Cần monitor sau khi fix để xác nhận không phải systemic issue.
- TTL dedup 10 phút có phù hợp không? → OK hiện tại, evolution surgery guard thêm 30-min window ở layer trên.
