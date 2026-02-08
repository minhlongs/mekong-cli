# Research: Gemini API Key Conflict + LLM Resilience Patterns

**Date:** 2026-02-08
**Researcher:** researcher-01
**Sources:** google-genai SDK v1.x source (installed at `/Users/macbookprom1/Library/Python/3.9/lib/python/site-packages/google/genai/`)

---

## Topic 1: Gemini API Key Resolution

### How `google-genai` SDK Resolves API Keys

Source: `_api_client.py` lines 93-109, 537-588

**Resolution order in `BaseApiClient.__init__`:**
```python
env_api_key = get_env_api_key()        # reads env vars
self.api_key = api_key or env_api_key  # explicit param wins if truthy
```

**`get_env_api_key()` priority:**
1. `GOOGLE_API_KEY` (highest priority)
2. `GEMINI_API_KEY` (fallback)
3. If BOTH set: SDK logs warning, uses `GOOGLE_API_KEY`

**Key finding:** Explicit `api_key=` param to `genai.Client()` DOES override env vars. The `or` means env var is only used when param is `None`/empty.

### Why Mekong's `os.environ.pop("GOOGLE_API_KEY")` Fix Works

Current code (llm_client.py:64-67) pops `GOOGLE_API_KEY` before creating the client. This is **correct but belt-and-suspenders** -- the explicit `api_key=self.gemini_key` already wins. The pop prevents:
- Other Google SDK components (auth, cloud libraries) from picking up wrong key
- Warning log spam from the SDK about "both keys set"
- Edge cases where `self.gemini_key` could be empty string (falsy), causing env fallback

### Recommendation
Keep the `os.environ.pop("GOOGLE_API_KEY")` approach. Add one guard: also pop only AFTER confirming `self.gemini_key` is truthy (already done).

---

## Topic 2: Empty Response Causes

### `response.text` Behavior (Current SDK)

Source: `types.py` lines 5996-6036

`response.text` property calls `_get_text()` which returns **`None`** (NOT ValueError) when:
- No candidates exist
- Candidate content is None
- Candidate parts list is empty

**NOTE:** The old SDK raised `ValueError` on blocked content. Current SDK returns `None`. Mekong's existing `try/except (ValueError, AttributeError)` at line 220 is safe but the `ValueError` path won't trigger in this SDK version.

### FinishReason Values

Source: `types.py` lines 280-299

| Value | Meaning |
|-------|---------|
| `STOP` | Normal completion |
| `MAX_TOKENS` | Hit output limit |
| `SAFETY` | Content blocked by safety filters |
| `RECITATION` | Stopped for potential plagiarism |
| `LANGUAGE` | Unsupported language |
| `OTHER` | Catch-all |
| `FINISH_REASON_UNSPECIFIED` | Unknown |

### Common Empty Response Scenarios

1. **Safety block** -- `finish_reason=SAFETY`, no parts returned
2. **Recitation block** -- `finish_reason=RECITATION`, partial or no content
3. **Transient server error** -- 500/503, SDK retries internally
4. **Rate limit** -- 429, SDK retries internally via tenacity
5. **Empty prompt** -- user error, SDK sends request, API returns empty

---

## Topic 3: SDK Built-in Retry

Source: `_api_client.py` lines 444-489, 724-727

**The SDK already has built-in retry via tenacity:**
- 5 attempts (including initial)
- Exponential backoff: 1s, 2s, 4s, 8s
- Max delay: 60s
- Jitter: 1s random
- Retried HTTP codes: 408, 429, 500, 502, 503, 504
- Configurable via `HttpRetryOptions`

**Implication for Mekong:** The manual retry loop in `_vertex_chat()` (lines 204-289) is **redundant** for HTTP-level errors. SDK retries 429/500/503 automatically. However, Mekong's retry handles a different case: **empty response content** (not HTTP errors), which the SDK does NOT retry.

### Recommendation
- Remove manual retry for HTTP errors (SDK handles them)
- Keep manual retry only for empty content responses
- OR disable SDK retry and do all retrying manually for more control

Better approach: **Keep both layers.** SDK retries transport errors; Mekong retries semantic failures (empty text). Current code is fine, just be aware of double-retry on 429.

---

## Topic 4: Multi-Provider Failover

### Recommended Pattern for Mekong

```
Priority chain: Gemini -> Proxy -> OpenAI -> Offline
```

Current implementation already does this in `__init__`. Improvement areas:

### Circuit Breaker Pattern

Track consecutive failures per provider. After N failures, skip that provider for a cooldown period:

```python
@dataclass
class ProviderHealth:
    failures: int = 0
    last_failure: float = 0
    cooldown_secs: float = 60

    @property
    def is_healthy(self) -> bool:
        if self.failures < 3:
            return True
        return (time.time() - self.last_failure) > self.cooldown_secs
```

**When to trip breaker:** 3+ consecutive non-retryable failures (auth errors, invalid key, persistent 403).
**When NOT to trip:** Single 429/503 (transient, SDK retries handle these).

### Rate Limit Handling with Jitter

For manual backoff (beyond SDK), use exponential backoff + full jitter:

```python
delay = min(max_delay, base_delay * (2 ** attempt))
jitter = random.uniform(0, delay)  # full jitter
time.sleep(jitter)
```

Full jitter is better than equal jitter for distributed systems (reduces thundering herd).

### Runtime Failover (NOT just init-time)

Current code selects provider at init. Improvement: if Gemini fails after exhausting retries, fall through to proxy/OpenAI before returning offline.

```python
def chat(self, messages, ...):
    providers = self._get_ordered_providers()  # [vertex, proxy, openai]
    for provider in providers:
        if not provider.health.is_healthy:
            continue
        try:
            return provider.call(messages, ...)
        except FatalProviderError:
            provider.health.record_failure()
            continue
    return self._offline_response(messages)
```

---

## Summary of Findings

| Issue | Status | Action |
|-------|--------|--------|
| GOOGLE_API_KEY conflict | **Fixed** in current code | Pop is correct, keep it |
| Empty response handling | **Adequate** | `_get_text()` returns None, not ValueError in current SDK |
| Manual retry loop | **Partially redundant** | SDK retries HTTP errors; manual retry needed only for empty content |
| Multi-provider failover | **Init-time only** | Should add runtime fallthrough |
| Circuit breaker | **Missing** | Add for production resilience |
| Jitter in backoff | **Missing** | Add `random.uniform` to manual retry delays |

## Unresolved Questions

1. **Double retry concern:** SDK retries 429 internally (5 attempts), then Mekong retries 3 more times. Could this cause up to 15 attempts on a rate-limited endpoint? Need to decide: disable SDK retry OR remove Mekong-level retry for HTTP errors.
2. **SDK version pinning:** Current SDK version not checked. `response.text` behavior differs between versions (old raises ValueError, new returns None). Should pin `google-genai>=1.0` in requirements.
3. **`GOOGLE_API_KEY` source:** Where is this env var being set? Shell profile? `.env` file? If it's from a different Google service, popping it could break that service.
