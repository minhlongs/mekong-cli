# Phase 4: NeuralMemory Upgrade

## Context Links

- Source: `/Users/macbookprom1/mekong-cli/src/core/memory_client.py` (90 lines)
- Research: [Memory Decay](research/researcher-02-agi-loop-memory-decay.md)

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 1h

Add decay parameter to queries, health check caching, configurable timeout, and dynamic context budget hint. No server-side changes assumed.

## Key Insights

- `is_available` hits `/health` endpoint on every first call but caches result (line 24-32) -- no TTL on cache
- `query_memory()` has no decay/recency weighting (line 55-78)
- Hardcoded 5s timeout everywhere (lines 44, 65) -- should be configurable
- No memory consolidation hint (server may support it but client doesn't pass)

## Requirements

- Health check cache with TTL (default 30s)
- Configurable timeout via constructor param
- `query_memory()` accepts optional `decay_weight` param passed to server
- `add_memory_deduped()` method: query before add, boost existing if similar
- Dynamic context budget: pass `max_chars` hint to caller

## Architecture

No new classes. Extend `NeuralMemoryClient` with:
- `_health_checked_at: float` for TTL cache
- `timeout` constructor param
- `decay_weight` param on `query_memory()`

## Related Code Files

- **Modify**: `src/core/memory_client.py`

## Implementation Steps

1. Add `import time` at top (after `import logging`, line 2)

2. Update `__init__` (lines 16-21) to add timeout and health cache TTL:
   ```python
   def __init__(
       self, base_url: str = "http://localhost:8000",
       brain_id: str = "default",
       timeout: float = 5.0,
       health_ttl: float = 30.0,
   ):
       self.base_url = base_url
       self.brain_id = brain_id
       self.timeout = timeout
       self.health_ttl = health_ttl
       self._available = None
       self._health_checked_at = 0.0
   ```

3. Update `is_available` property (lines 24-32) to respect TTL:
   ```python
   @property
   def is_available(self) -> bool:
       now = time.time()
       if self._available is not None and (now - self._health_checked_at) < self.health_ttl:
           return self._available
       try:
           resp = requests.get(f"{self.base_url}/health", timeout=1.0)
           self._available = resp.status_code == 200
       except Exception:
           self._available = False
       self._health_checked_at = now
       return self._available
   ```

4. Replace hardcoded `timeout=5.0` in `add_memory()` (line 44) with `self.timeout`

5. Replace hardcoded `timeout=5.0` in `query_memory()` (line 65) with `self.timeout`

6. Add `decay_weight` param to `query_memory()`:
   ```python
   def query_memory(self, query: str, depth: int = 1, decay_weight: float = 0.0) -> Optional[str]:
   ```
   Update payload (line 63) to include decay if nonzero:
   ```python
   payload = {"query": query, "depth": depth, "max_tokens": 2000}
   if decay_weight > 0:
       payload["decay_weight"] = decay_weight
   ```

7. Add `add_memory_deduped()` method after `add_memory()`:
   ```python
   def add_memory_deduped(self, content: str, metadata: Optional[Dict] = None) -> bool:
       """Add memory, boosting existing if similar content found."""
       if not self.is_available:
           return False
       existing = self.query_memory(content[:100], depth=1)
       if existing and len(existing) > 10:
           logger.info("Similar memory exists, skipping duplicate")
           return True  # Don't add duplicate
       return self.add_memory(content, metadata)
   ```

8. Add `invalidate_health()` method for manual cache reset:
   ```python
   def invalidate_health(self):
       """Force re-check on next is_available call."""
       self._available = None
       self._health_checked_at = 0.0
   ```

## Todo List

- [ ] Add `import time`
- [ ] Add `timeout` and `health_ttl` constructor params
- [ ] Add `_health_checked_at` field
- [ ] Update `is_available` with TTL cache logic
- [ ] Replace hardcoded timeouts with `self.timeout`
- [ ] Add `decay_weight` param to `query_memory()`
- [ ] Add `add_memory_deduped()` method
- [ ] Add `invalidate_health()` method
- [ ] Run `python3 -m pytest tests/ -v` -- all tests pass

## Success Criteria

- Health check only hits server once per 30s (not every call)
- `query_memory()` passes `decay_weight` to server when specified
- `add_memory_deduped()` prevents duplicate memory entries
- Timeout configurable at construction

## Risk Assessment

- **Server ignores `decay_weight`**: If server doesn't support it, param is silently ignored (POST body, not required). No breakage
- **Dedup false positives**: `query_memory` may return unrelated results on short queries. Mitigated by requiring `len(existing) > 10`

## Security Considerations

- No auth changes. HTTP client to localhost only

## Next Steps

- AGI loop (Phase 3) can use `add_memory_deduped()` in `_memorize()`
