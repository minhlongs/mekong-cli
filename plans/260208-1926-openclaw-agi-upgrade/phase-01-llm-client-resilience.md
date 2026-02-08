# Phase 1: LLM Client Resilience

## Context Links

- Source: `/Users/macbookprom1/mekong-cli/src/core/llm_client.py` (360 lines)
- Research: [Gemini Retry Patterns](research/researcher-01-gemini-retry-patterns.md)

## Overview

- **Priority**: P1 (foundation for all other phases)
- **Status**: pending
- **Effort**: 1.5h

Add jitter to backoff, runtime provider failover, circuit breaker, and improved empty response logging.

## Key Insights

- SDK already retries HTTP 429/500/503 via tenacity (5 attempts, 1s jitter)
- Manual retry (lines 204-289) is only needed for empty content responses
- `response.text` returns `None` (not ValueError) in current SDK -- existing try/except is safe
- Init-time provider selection (lines 69-87) prevents runtime failover

## Requirements

- Jitter on manual backoff delays (lines 242-244, 280-285)
- `ProviderHealth` dataclass tracking consecutive failures per provider
- `chat()` method tries providers in order, skipping unhealthy ones
- Better logging when empty response detected (include finish_reason, model, attempt)
- GOOGLE_API_KEY cleanup at call time too (edge case: env var set after init)

## Architecture

```
chat() --> _get_ordered_providers() --> [vertex, proxy, openai]
  for each healthy provider:
    try call --> success --> return
    except --> record_failure --> next provider
  all failed --> _offline_response()
```

## Related Code Files

- **Modify**: `src/core/llm_client.py`
- **Create**: None (all changes in existing file)

## Implementation Steps

1. Add `import random` at line 16 (after `import re`)

2. Add `ProviderHealth` dataclass after `LLMResponse` (after line 38):
   ```python
   @dataclass
   class ProviderHealth:
       failures: int = 0
       last_failure: float = 0.0
       cooldown_secs: float = 60.0

       @property
       def is_healthy(self) -> bool:
           if self.failures < 3:
               return True
           return (time.time() - self.last_failure) > self.cooldown_secs

       def record_failure(self):
           self.failures += 1
           self.last_failure = time.time()

       def record_success(self):
           self.failures = 0
   ```

3. In `LLMClient.__init__` (after line 59), add health trackers:
   ```python
   self._provider_health = {
       "vertex": ProviderHealth(),
       "proxy": ProviderHealth(),
       "openai": ProviderHealth(),
   }
   ```

4. Add `_get_ordered_providers()` method returning list of available provider names, filtering unhealthy ones

5. Refactor `chat()` (lines 94-163): iterate providers from `_get_ordered_providers()`. For each provider, attempt the call. On success, `record_success()`. On failure, `record_failure()` and continue to next provider

6. In `_vertex_chat()` line 242-244, add jitter:
   ```python
   base_delay = 2 ** attempt
   delay = random.uniform(0, base_delay)  # full jitter
   time.sleep(delay)
   ```

7. Same jitter at lines 280-285 (exception retry backoff)

8. Add GOOGLE_API_KEY cleanup check at start of `_vertex_chat()`:
   ```python
   if "GOOGLE_API_KEY" in os.environ:
       os.environ.pop("GOOGLE_API_KEY")
   ```

9. Improve empty response logging at line 236-239 to include model name and prompt length

## Todo List

- [ ] Add `import random`
- [ ] Add `ProviderHealth` dataclass
- [ ] Add health trackers to `__init__`
- [ ] Add `_get_ordered_providers()` method
- [ ] Refactor `chat()` for runtime failover
- [ ] Add jitter to both backoff locations in `_vertex_chat()`
- [ ] Add GOOGLE_API_KEY guard in `_vertex_chat()`
- [ ] Improve empty response log messages
- [ ] Run `python3 -m pytest tests/ -v` -- all 62 tests pass

## Success Criteria

- `chat()` tries vertex -> proxy -> openai at runtime (not just init)
- After 3 vertex failures, proxy is used automatically
- Backoff delays have random jitter
- All existing tests pass

## Risk Assessment

- **Double retry**: SDK retries HTTP errors internally + manual retry for empty content. Acceptable; document in docstring
- **Provider state leak**: `ProviderHealth` is per-instance. Singleton `get_client()` means shared state -- correct behavior

## Security Considerations

- GOOGLE_API_KEY cleanup prevents key leakage to unintended SDK components
- No new secrets introduced

## Next Steps

- Phase 2 builds on the improved LLM client for NLP Commander retry
