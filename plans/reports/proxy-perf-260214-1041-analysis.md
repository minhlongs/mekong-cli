# Phân Tích Proxy Adapter Performance

**File:** `scripts/anthropic-adapter.js`
**Ngày phân tích:** 2026-02-14

## 3 Đề Xuất Cải Tiến

### 1. **Loại bỏ console.log trong production code** (Priority: Cao)

**Vấn đề:** Có nhiều `console.log()` trong các hàm:
- `markOllama429()` - dòng 109
- `markGoogle429()` - dòng 116
- Trong proxy handlers - dòng 377, 382, 412, 422, 458, 465, 564, 573, 593, 601

**Giải pháp:** Sử dụng environment variable để control logging:
```javascript
const DEBUG = process.env.PROXY_DEBUG === '1';
const log = DEBUG ? console.log : () => {};
```

### 2. **Queue processing瓶颈 - single-threaded** (Priority: Trung bình)

**Vấn đề:** `processQueue()` sử dụng `setTimeout` sequential - không tận dụng Node.js async:

```javascript
// Hiện tại: Sequential
setTimeout(() => {
    const handler = queue.shift();
    if (handler) handler();
    processing = false;
    lastRequestTime = Date.now();
}, delay);
```

**Giải pháp:** Parallel processing với limit:
```javascript
const MAX_PARALLEL = 4;
let active = 0;

function processQueue() {
    while (active < MAX_PARALLEL && queue.length > 0) {
        active++;
        const handler = queue.shift();
        handler();
        active--;
        if (queue.length > 0) processQueue();
    }
}
```

### 3. **Missing gzip compression cho response** (Priority: Thấp)

**Vấn đề:** Không có compression - payload lớn (đặc biệt với stream) sẽ chậm.

**Giải pháp:** Thêm compression:
```javascript
const compression = require('compression');

server.use(compression({ level: 6, filter: (req, res) => {
    return /json|event-stream/i.test(res.getHeader('Content-Type'));
}}));
```

---

## Tóm tắt

| # | Cải Tiến | Impact | Complexity |
|---|-----------|--------|------------|
| 1 | Remove console.log | Medium | Low |
| 2 | Parallel queue | High | Medium |
| 3 | Gzip compression | Low | Low |
