# Proxy Architecture Review - anthropic-adapter.js

**Date:** 2026-02-14 09:47
**File:** `/Users/macbookprom1/mekong-cli/scripts/anthropic-adapter.js`
**Lines:** 617
**Review Type:** Architecture & Security Analysis

---

## Executive Summary

| Category | Score | Status |
|----------|-------|--------|
| Architecture | 8/10 | Good |
| Error Handling | 7/10 | Acceptable |
| Security | 6/10 | Needs Improvement |
| Performance | 9/10 | Excellent |
| Maintainability | 7/10 | Good |

**Overall: 7.4/10 - Production Ready with Minor Concerns**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    anthropic-adapter v4                      │
│                     Triple-Provider Proxy                    │
├─────────────────────────────────────────────────────────────┤
│  Client (CC CLI) ──→ localhost:11436/v1/messages           │
│                              │                               │
│                              ▼                               │
│                    Request Queue                             │
│                    (FIFO + Throttle)                         │
│                              │                               │
│        ┌─────────────────────┼─────────────────────┐        │
│        ▼                     ▼                     ▼        │
│  Ollama Cloud        Google AI Studio      OpenRouter       │
│   (8 keys)            (6 keys)            ($10 credit)      │
│   Primary Fallback     Secondary Fallback   Last Resort     │
└─────────────────────────────────────────────────────────────┘
```

### Provider Priority
1. **Ollama Cloud** - Primary (8 Anthropic-native keys)
2. **Google AI Studio** - Secondary (6 keys: 2 Ultra billing + 4 free)
3. **OpenRouter** - Last resort (OpenAI-compatible)

---

## Strengths

### ✅ Excellent Rate Limiting
```javascript
// Key state tracking per provider
const keyState = OLLAMA_KEYS.map(() => ({
    calls: [], blockedUntil: 0, total: 0, hits429: 0,
}));
```
- Per-key cooldown (65s) on 429 errors
- Smart key selection by load (least used first)
- Queue-based request throttling (800ms min gap)

### ✅ Clean Conversion Layer
- `anthropicToOpenAI()` - Format conversion
- `anthropicToGemini()` - Gemini API format
- `geminiToAnthropic()` - Response back-conversion
- `openAIToAnthropic()` - OpenAI response handling

### ✅ Streaming Support
- Full SSE stream conversion (Anthropic ↔ OpenAI format)
- Chunk-by-chunk processing with delta tracking

### ✅ Health Endpoint
```javascript
GET /health
{
  status: 'ok',
  requests: requestCount,
  total429: total429,
  queue: queue.length,
  ollama: [...],
  openrouter: {...},
  google: [...]
}
```

---

## Concerns & Recommendations

### 🔴 Security Issues

#### Issue 1: Hardcoded API Keys
**Severity: HIGH**

All API keys are hardcoded in the source file:
- Ollama keys (8)
- OpenRouter key (1)
- Google keys (6)

**Risk:** Credential exposure if code is committed to Git or shared.

**Fix:**
```javascript
// Move to environment variables
const OLLAMA_KEYS = process.env.OLLAMA_KEYS?.split(',') || [];
const OPENROUTER_KEY = process.env.OPENROUTER_KEY || '';
const GOOGLE_KEYS = process.env.GOOGLE_KEYS?.split(',') || [];
```

#### Issue 2: No Input Validation
**Severity: MEDIUM**

No validation of incoming request body before processing:
```javascript
req.on('end', () => {
    let parsed;
    try { parsed = JSON.parse(body); } catch (e) { ... }
    // No schema validation on parsed.body
```

**Risk:** Malformed requests could cause unexpected behavior or injection.

**Fix:**
```javascript
const z = require('zod');
const RequestSchema = z.object({
    model: z.string(),
    messages: z.array(z.object({ role: z.string(), content: z.any() })),
    max_tokens: z.number().optional(),
    temperature: z.number().optional(),
    tools: z.array(z.object({}).passthrough()).optional()
});
```

### 🟡 Architecture Improvements

#### Issue 3: Memory Leak Risk - Call History
**Severity: LOW**

Call history accumulates in memory without cleanup:
```javascript
keyState.forEach(k => {
    k.calls = k.calls.filter(t => now - t < 60000);
});
```
While this filters old calls, the array can still grow large during high traffic spikes.

**Fix:** Use circular buffer or decay function instead of array.

#### Issue 4: No Circuit Breaker Pattern
**Severity: MEDIUM**

When a provider fails repeatedly, it continues being attempted:
```javascript
function isOpenRouterAvailable() {
    if (openrouterState.blocked && Date.now() < openrouterState.blockedUntil) return false;
    openrouterState.blocked = false;  // Always resets!
    return true;
}
```

**Fix:** Implement progressive backoff (1min → 5min → 15min → 1hr).

#### Issue 5: Missing Timeout Handling
**Severity: MEDIUM**

HTTPS requests have no timeout:
```javascript
const proxyReq = https.request({...}, (proxyRes) => { ... });
// No proxyReq.setTimeout() call
```

**Risk:** Stuck requests can cause memory leaks and hung sessions.

**Fix:**
```javascript
proxyReq.setTimeout(30000, () => {
    proxyReq.destroy(new Error('Request timeout'));
});
```

### 🟢 Minor Issues

#### Issue 6: Inconsistent Error Logging
Some errors log messages, others don't:
```javascript
proxyReq.on('error', (err) => {
    console.error(`[${ts()}] ❌ Ollama: ${err.message}`);
    // ...
});
```
But `catch (e) { }` blocks are silent in some places.

#### Issue 7: No Graceful Shutdown
Server has no SIGTERM handler. Long-running requests will be killed abruptly.

**Fix:**
```javascript
process.on('SIGTERM', () => {
    server.close(() => {
        console.log('Proxy shutdown complete');
        process.exit(0);
    });
    // Cancel queued requests
});
```

---

## Performance Analysis

### ✅ Excellent Design
- Queue-based serialization prevents rate limit hits
- Key selection by lowest load ensures even distribution
- Minimal object creation in hot path
- Cache-friendly filtering (calls array)

### ⚠️ Optimization Opportunities

#### 1. Stream Conversion Efficiency
```javascript
// Current: Split entire chunk into lines
const lines = chunk.toString().split('\n');
// Could use line reader stream for large chunks
```

#### 2. Schema Validation
Current JSON.parse is generic. Could use faster parser (e.g., `quicktype`) for high-volume scenarios.

---

## Code Quality

| Metric | Score | Notes |
|--------|-------|-------|
| Cyclomatic Complexity | 6/10 | Many nested if/else blocks |
| Documentation | 5/10 | No JSDoc comments, minimal inline docs |
| Testing | 0/10 | No test suite present |
| Type Safety | 5/10 | Plain JS, no TypeScript |
| Error Handling | 7/10 | Some silent failures |

---

## Recommendations Priority

### Critical (Do Immediately)
1. **Move API keys to environment variables**
2. **Add request body validation**
3. **Implement timeout on all HTTP requests**

### High Priority (This Week)
4. **Add circuit breaker pattern**
5. **Implement SIGTERM graceful shutdown**
6. **Add comprehensive error logging**

### Medium Priority (This Month)
7. **Add unit tests (Jest/Mocha)**
8. **Convert to TypeScript for type safety**
9. **Add health monitoring webhook alerts**
10. **Implement metrics export (Prometheus format)**

---

## Security Checklist

- [x] Rate limiting implemented
- [x] Input validation (basic JSON parsing)
- [ ] API keys in environment variables ❌
- [ ] HTTPS verification enabled
- [ ] Request body schema validation ❌
- [ ] CORS headers configured ❌
- [ ] Graceful shutdown handler ❌
- [ ] Timeout handling ❌
- [ ] Circuit breaker pattern ❌

**Current Status: 4/10 - Needs Security Hardening**

---

## Conclusion

The `anthropic-adapter.js` is a **well-architected proxy** with excellent rate limiting and request distribution. However, it requires **immediate security hardening** before production deployment:

1. **Move keys to environment variables** - Critical
2. **Add timeout handling** - Critical
3. **Implement request validation** - Critical
4. **Add circuit breaker** - High priority
5. **Add tests** - Medium priority

**Current Recommendation:** Use for development/testing only. Fix security issues before production use.

---

*Report generated: 2026-02-14 09:47*
*Reviewer: CC CLI Architecture Audit*
