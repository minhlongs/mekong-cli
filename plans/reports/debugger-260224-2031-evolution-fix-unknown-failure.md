# Brain Surgery v32 — Fix Evolution Engine Failure Classification

**Date:** 2026-02-24
**Commit:** ba78d7bf
**File changed:** `apps/openclaw-worker/lib/evolution-engine.js` (1 file, +21/-8)

---

## Root Cause Analysis

### Trigger 1: `repeated_failure: "unknown"` (14/20 missions)

**Root cause:** Schema mismatch. 748 cũ entries trong `mission-history.json` không có `failureType` field — chỉ có `buildResult.output`. Evolution engine (v31) chỉ đọc `m.failureType || m.resultCode` — cả hai đều undefined → fallback `'unknown'`.

Thực tế các missions đó có failure reason trong `buildResult.output`:
- `"duplicate_rejected"` — 10+ entries
- `"brain_died"` — 2 entries
- `"max_retries_exhausted"` — 3 entries

**Fix:** Thêm `|| m.buildResult?.output` vào key extraction chain.

---

### Trigger 2: `repeated_failure: "duplicate_rejected"` (3/20 missions — thực tế 13+)

**Root cause:** `duplicate_rejected` là **behavior mong muốn** (DEDUP_TTL = 10min đang hoạt động đúng), nhưng evolution đếm nó như actionable failure. Nhiều evolution surgery missions gửi trong < 10 phút → bị reject đúng → evolution tự trigger brain surgery vô hạn.

**Fix:** Thêm `BENIGN_FAILURES` set = `{duplicate_rejected, all_workers_busy, mission_locked, busy_blocked}`. Exclude khỏi pattern counting và success rate denominator.

---

### Trigger 3: `low_success_rate: 10%`

**Root cause:** 18/20 missions "failed" nhưng 13 là `duplicate_rejected` (benign). Denominator sai → tỉ lệ thấp giả.

**Fix:** `recentActual` filter loại benign failures trước khi tính rate. Require `recentActual.length >= 5` để có đủ data.

---

## Kết quả sau fix

| Metric | Trước | Sau |
|--------|-------|-----|
| `unknown` trigger | 14 lần | 0 lần |
| `duplicate_rejected` trigger | 13 lần | 0 lần (benign) |
| Success rate actual | 10% (sai) | 29% (7 actual missions: 2 OK / 7) |
| Actionable failures | `unknown` x14 | `max_retries_exhausted` x3 |

---

## Files sửa đổi

- `/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib/evolution-engine.js`
  - Line 106-126: Define `BENIGN_FAILURES`, fix success rate calculation
  - Line 128-141: Reuse `BENIGN_FAILURES`, add `buildResult.output` fallback

---

## Verify

```
node --check evolution-engine.js → SYNTAX OK
node --check task-queue.js → SYNTAX OK
node --check brain-process-manager.js → SYNTAX OK
Simulation: "unknown" = 0, "duplicate_rejected" = 0 (excluded)
```

---

## Unresolved Questions

1. `max_retries_exhausted` x3 + `brain_died` x2 trong 7 actual missions → success rate 29% vẫn dưới 70%. Cần điều tra tại sao missions dài (120-132s) exhaust retries — có thể model/proxy timeout issues.

2. `buildResult.output` có thể chứa full build log (nhiều dòng), không phải chỉ failure code. Trong trường hợp build thành công rồi thất bại ở stage khác, key sẽ là full log → sẽ không match BENIGN_FAILURES. Cần normalize buildResult.output thành short code trước khi dùng làm key — nhưng đây là enhancement cho v33, không urgent.
