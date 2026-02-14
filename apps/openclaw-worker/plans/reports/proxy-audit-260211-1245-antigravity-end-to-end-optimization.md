# Antigravity Proxy End-to-End Audit — Nhanh, Mạnh, Tiết Kiệm Quota

**Date:** 2026-02-11 12:45
**Scope:** proxy-interceptor.cjs, openclaw-worker/*, proxy config
**Branch:** master

---

## 1. HIỆN TRẠNG PROXY

### Infrastructure
| Component | Detail |
|-----------|--------|
| Proxy binary | `antigravity-claude-proxy v2.5.0` |
| Port | 8080 (localhost) |
| Accounts | 2x Google AI Studio Ultra |
| Account selection | Health-score strategy (initial=100, rate-limit penalty=-20) |
| Retry | 5 retries, 500ms-15s exponential backoff |
| Fallback | --fallback flag active |
| Token bucket | 1500 max, 100/min refill |

### Usage Statistics (23 ngày)
| Metric | Value |
|--------|-------|
| Total requests | **152,422** |
| Last 24h | **16,236** |
| Top model | gemini/3-pro-high: 70,575 (46%) |
| Second | claude/opus-4-6-thinking: 29,805 (20%) |
| Third | claude/sonnet-4-5-thinking: 14,861 (10%) |
| usage-history.json size | 75KB (403 hourly buckets) |

### Account Health
- `billwill.mentor@gmail.com` (ultra) — ✅ healthy, no rate limits
- `longtho638@gmail.com` (ultra) — ✅ healthy, no rate limits

---

## 2. AUDIT FINDINGS

### 2.1 Proxy Interceptor (`~/.claude/proxy-interceptor.cjs`)

**Trước:** 71 dòng, mở TCP connection mới mỗi request, code trùng lặp.

**Vấn đề:**
- ❌ Không dùng connection pooling → mỗi request = TCP handshake mới
- ❌ Logic detect anthropic host bị duplicate giữa request/get
- ❌ Không có keep-alive → latency cao hơn cần thiết

**Đã sửa:**
- ✅ `http.Agent({ keepAlive: true, maxSockets: 6 })` — connection pooling
- ✅ Extracted `isAnthropicHost()` và `buildProxyOptions()` — DRY
- ✅ Từ 71 → 52 dòng, ngắn gọn hơn

**Token savings estimate:** ~5-10ms latency reduction per request (TCP reuse)

### 2.2 Mission Prompt Bloat

**Trước:** `VI_PREFIX` + `FILE_LIMIT` duplicate ở 2 files (mission-dispatcher.js + mission-complexity-classifier.js)

| Constant | Trước | Sau |
|----------|-------|-----|
| `FILE_LIMIT` | 82 chars ("Chỉ sửa TỐI ĐA 5 file mỗi mission. Nếu cần sửa nhiều hơn, báo cáo danh sách còn lại.") | 22 chars ("Tối đa 5 file/mission.") |
| `VI_PREFIX` | 29 chars | 29 chars (giữ nguyên) |
| Location | Hardcoded x2 | config.js (SSoT) |

**Token savings:** ~60 chars × ~0.25 tokens/char = ~15 tokens/mission × ~670 missions/ngày ≈ **10,000 tokens/ngày saved**

### 2.3 Quota Tracking Gap

**Trước:** Proxy tracks request counts per hour (usage-history.json), nhưng Tôm Hùm không biết:
- Mission nào tốn bao nhiêu tokens
- Project nào tốn quota nhiều nhất
- Không có interface để tách quota dev-brain vs marketing

**Đã tạo:** `lib/quota-tracker.js`
- Track estimated tokens per mission (prompt length / 4)
- Daily totals by project, by channel
- `readProxyUsage()` — đọc trực tiếp usage-history.json
- `CHANNELS` enum: `dev-brain` | `marketing` | `interactive`
- Auto-cleanup: chỉ giữ 7 ngày data
- Integrated vào `mission-dispatcher.js` — auto-record mỗi mission

### 2.4 Anti-Die Protection Gap

**Trước:** `mission-recovery.js` chỉ handle model errors + context overflow. Không handle:
- ❌ Quota exhaustion (429/RESOURCE_EXHAUSTED)
- ❌ Cascade failures (3+ liên tiếp) → brain stuck
- ❌ Auto-trigger proxy-recovery.sh

**Đã thêm:**
- ✅ `QUOTA_EXHAUSTION_PATTERNS` — detect 429, rate_limit, quota_exceeded
- ✅ Circuit breaker: 3 failures liên tiếp → pause 60s → auto `triggerProxyRecovery()`
- ✅ `recordSuccess()`/`recordFailure()` — state tracking
- ✅ `checkCircuitBreaker()` — gate check in task-queue.js trước mỗi dispatch
- ✅ `triggerProxyRecovery()` — dùng `execFileSync` (an toàn, no shell injection)

---

## 3. CODE CHANGES SUMMARY

| File | Action | Lines Changed |
|------|--------|---------------|
| `~/.claude/proxy-interceptor.cjs` | Refactor: keep-alive pool + DRY | 71→52 |
| `config.js` | Add: `VI_PREFIX`, `FILE_LIMIT` constants | +3 |
| `lib/mission-dispatcher.js` | Refactor: use config constants, add quota tracking | ~10 |
| `lib/mission-complexity-classifier.js` | Refactor: use config constants | ~2 |
| `lib/mission-recovery.js` | Major: quota detection, circuit breaker | 83→153 |
| `lib/task-queue.js` | Add: circuit breaker gate + success/failure recording | ~15 |
| `lib/quota-tracker.js` | **NEW**: Token consumption tracking module | 140 |

---

## 4. RECOMMENDATIONS (Priority Order)

### P0 — Đã Implement (Session này)
1. ✅ Connection pooling proxy interceptor (keep-alive)
2. ✅ DRY mission prompt constants (10K tokens/ngày saved)
3. ✅ Quota tracker per mission/project/channel
4. ✅ Circuit breaker: 3 failures → 60s pause → auto-recovery
5. ✅ Quota exhaustion detection (429/RESOURCE_EXHAUSTED)

### P1 — Recommend Next Sprint
6. **Quota daily limits per channel** — Đặt hard cap: dev-brain max 80% daily quota, marketing max 20%. Config trong quota-tracker.js (interface đã sẵn, chỉ cần set limits).
7. **Usage dashboard CLI** — `node lib/quota-tracker.js --summary` để xem quota realtime từ terminal.
8. **Proxy config: giảm maxRetries từ 5 → 3** — Mỗi retry tốn thêm ~2-15s latency. 3 retries đủ cho hầu hết cases.

### P2 — Nice to Have
9. **Request body compression** — Proxy chạy localhost → compression overhead > savings (NOT recommended).
10. **DNS optimization** — Proxy tự handle upstream DNS, ta không control được.
11. **jq/pv/zstd CLI tools** — Marginal value cho M1 16GB setup. Proxy đã track usage natively.

### KHÔNG khuyến nghị
- ❌ JSON body minification: CC CLI gửi body đã minified sẵn
- ❌ zstd/lz4 compression: localhost traffic, overhead > savings
- ❌ pv pipe viewer: thêm process = thêm RAM, M1 đã tight

---

## 5. ĐƯỜNG TRUYỀN ANALYSIS

| Metric | Value | Assessment |
|--------|-------|-----------|
| Proxy → Google API | ~200-400ms RTT | Normal (US servers) |
| CC CLI → Proxy | <1ms (localhost) | ✅ Optimal |
| Connection reuse | **NEW** (keep-alive pool) | ✅ Eliminates TCP handshake |
| DNS resolution | Handled by proxy binary | N/A |
| Max sockets | 6 concurrent | Matches 2-pane brain config |

---

## 6. QUOTA ROTATION STRATEGY

Hiện tại proxy dùng `health-score` strategy:
- Success = +10 score, Rate limit = -20, Failure = -30
- Recovery = +25/hour, Min usable = 20

**Recommendation:** Giữ nguyên strategy. Proxy tự rotate khi 1 account bị rate-limited. Với 2 Ultra accounts và 16K requests/ngày, quota đủ cho cả dev-brain + marketing.

**Khi thêm Marketing Agent:**
1. Set `CHANNELS.MARKETING` trong quota-tracker.js
2. Pass `channel: 'marketing'` khi `recordMission()`
3. Monitor via `getChannelQuota('marketing')`
4. Set daily limit khi cần (P1 recommendation #6)

---

## Unresolved Questions
- Proxy binary (`antigravity-claude-proxy`) là closed-source npm package — không audit được internal code
- usage-history.json sẽ grow indefinitely (75KB/23 days ≈ 1.2MB/year) — proxy nên auto-prune
