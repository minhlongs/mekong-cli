# LLM Router Cost Optimization Guide

## Executive Summary

The Mekong CLI LLM router already implements several cost optimization features. This guide documents current capabilities and provides enhancement recommendations for further cost reduction.

---

## 1. Model Selection Strategy (Cheapest Capable)

### Current Implementation

The system uses `src/core/model_selector.py` with:

- **Routing matrix**: `MODEL_ROUTING_MATRIX` maps (agent_role, complexity, requires_reasoning, data_sensitivity) → model
- **Tier overrides**: `TASK_TIER_OVERRIDE` forces cheap models for mechanical/integration tasks
- **Tenant-based**: Starter tier gets cheaper models automatically
- **Local preference**: Sensitive data routes to local models only

**Existing cost-aware selection:**
```python
# model_selector.py lines 278-321
TASK_TIER_OVERRIDE: dict[str, str | None] = {
    "mechanical": "ollama:qwen3.6-35b",      # fast: simple tasks via Rapid-MLX
    "integration": "ollama:qwen3.6-35b",     # coding/agentic workflows
    "architecture": "ollama:qwen3.6-35b",    # broad reasoning + content
}
```

### Optimization Recommendations

**1.1 Dynamic Cost-Weighted Selection**

Add real-time cost comparison in `select_model()`:

```python
def _select_by_cost_optimization(
    profile: TaskProfile,
    candidates: list[str],
    state: SystemState
) -> str:
    """Select cheapest capable model from candidates."""
    capability_scores = {
        "simple": 1,
        "standard": 2,
        "complex": 3,
    }
    
    min_score = capability_scores[profile.complexity]
    if profile.requires_reasoning:
        min_score += 1
    
    scored = []
    for model in candidates:
        if model.startswith("ollama:"):
            cost = 0.0
        else:
            costs = COST_TABLE.get(model, (999, 999))
            cost = (costs[0] + costs[1]) / 2
        
        if _meets_capability_threshold(model, profile, min_score):
            scored.append((cost, model))
    
    return min(scored)[1] if scored else candidates[0]
```

---

## 2. Response Caching (Redis/CF KV)

### Current Implementation

`src/core/llm_cache.py` provides in-memory LRU caching:

```python
LLMCache(
    max_entries=1000,
    default_ttl=3600,
    cost_per_hit=0.001
)
```

**Features:**
- Hash-based keys (messages + model + temperature)
- TTL support with expiration cleanup
- LRU eviction
- Hit rate tracking

### Optimization: Distributed Cache Backend

**2.1 Redis Configuration**

```yaml
# config/cache.yaml
cache:
  backend: "redis"
  
  redis:
    url: "${REDIS_URL:-redis://localhost:6379}"
    password: "${REDIS_PASSWORD:}"
    db: 0
    key_prefix: "mekong:llm:"
    
    max_connections: 50
    socket_timeout: 2.0
    
    ttls:
      expensive: 86400    # Claude Opus - 24h
      standard: 43200     # Claude Sonnet/GPT-4o - 12h
      cheap: 3600         # Gemini Flash/MLX - 1h
      local: 1800         # Local models - 30min
    
    compression: true
    compression_threshold: 1024
```

**2.2 Enhanced LLMCache with Redis Backend**

```python
# src/core/llm_cache_redis.py - New file
import redis
import pickle
import zlib

class RedisLLMCache(LLMCache):
    """Redis-backed LLM cache with compression."""
    
    def __init__(
        self,
        redis_url: str,
        max_entries: int = 10000,
        default_ttl: int = 3600,
        compression: bool = True,
    ) -> None:
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=False,
            max_connections=50,
        )
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.compression = compression
        self.key_prefix = "mekong:llm:"
        self.stats = CacheStats()
```

---

## 3. Prompt Compression

### 3.1 Context Window Optimization

```python
# src/core/prompt_compressor.py - New file
class PromptCompressor:
    """Compress prompts to reduce token usage."""
    
    def __init__(
        self,
        llm_client=None,
        target_ratio: float = 0.7,
        preserve_system: bool = True,
        preserve_last_n_exchanges: int = 3,
    ) -> None:
        self.llm = llm_client or get_client()
        self.target_ratio = target_ratio
        self.preserve_system = preserve_system
        self.preserve_last_n = preserve_last_n_exchanges
```

---

## 4. Batching Similar Requests

### 4.1 Batch Processor Implementation

```python
# src/core/batch_processor.py - New file
class BatchRequest:
    """A request waiting to be batched."""
    
    messages: list[dict[str, str]]
    model: str
    temperature: float
    max_tokens: int
    future: asyncio.Future
    created_at: float = field(default_factory=time.time)

class BatchProcessor:
    """Deduplicates and batches concurrent LLM requests."""
    
    def __init__(self, llm_client: LLMClient, config: BatchConfig | None = None) -> None:
        self.llm = llm_client
        self.config = config or BatchConfig()
        self._pending: dict[str, list[BatchRequest]] = defaultdict(list)
```

---

## 5. Fallback Chain Optimization

### 5.1 Dynamic Fallback Reordering

```python
def get_fallback_models(
    model_id: str,
    attempted: list[str],
    data_sensitivity: str = "public",
    optimize_for_cost: bool = True,
) -> list[str]:
    """Get fallback models, optionally reordered by cost."""
    fallbacks = FALLBACK_HIERARCHY.get(model_id, [])
    candidates = [m for m in fallbacks if m not in attempted]
    
    if data_sensitivity == "sensitive":
        candidates = [m for m in candidates if m.startswith("ollama:")]
    
    if optimize_for_cost:
        def model_cost_key(m: str) -> float:
            if m.startswith("ollama:"):
                return 0.0
            costs = COST_TABLE.get(m, (999, 999))
            return (costs[0] + costs[1]) / 2
        
        candidates.sort(key=model_cost_key)
    
    return candidates
```

### 5.2 Adaptive Fallback Chain

```python
# src/core/adaptive_fallback.py - New file
class ModelMetrics:
    """Performance metrics for a model."""
    
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def effective_cost_score(self) -> float:
        base_cost = get_model_base_cost(self.model_id)
        latency_penalty = self.avg_latency_ms / 1000.0 * 0.1
        return base_cost + latency_penalty

class AdaptiveFallbackChain:
    """Dynamically optimize fallback order based on metrics."""
```

---

## 6. Token Budgeting & Quotas

### 6.1 Per-Task Token Budgets

```python
MAX_TOKENS_BY_COMPLEXITY = {
    "simple": 2000,
    "standard": 8000,
    "complex": 32000,
}
```

### 6.2 Tenant-Level Quotas

```python
# src/core/token_quota.py - New file
@dataclass
class QuotaConfig:
    daily_token_limit: int = 100000
    monthly_token_limit: int = 1000000
    burst_limit: int = 50000
    overage_allowed: bool = False
    overage_rate: float = 0.0

class TokenQuotaManager:
    """Manages token quotas per tenant."""
```

---

## 7. Async Concurrency Limits

### 7.1 Global Concurrency Semaphore

```python
class RateLimitedLLMClient(LLMClient):
    def __init__(self, *args, max_concurrent: int = 10, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._semaphore = asyncio.Semaphore(max_concurrent)
```

### 7.2 Per-Provider Rate Limiting

```python
# src/core/rate_limiter.py - New file
class TokenBucket:
    """Token bucket for rate limiting."""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity

class ProviderRateLimiter:
    configs = {
        "anthropic": {"rate": 10, "capacity": 20},
        "google": {"rate": 60, "capacity": 100},
        "local-llm": {"rate": 100, "capacity": 200},
    }
```

---

## 8. Metrics & Alerts

### 8.1 Prometheus Metrics

```python
# src/core/cost_metrics.py - New file
from prometheus_client import Counter, Gauge

LLM_COST_TOTAL = Counter('mekong_llm_cost_usd_total', 'Total LLM cost', ['model', 'provider'])
CACHE_HIT_RATE = Gauge('mekong_cache_hit_rate', 'Cache hit rate percentage')

class MetricsCollector:
    def __init__(self, port: int = 9090):
        start_http_server(port)
```

---

## 9. Complete Configuration

```yaml
# config/llm-router.yaml
llm_router:
  model_selection:
    strategy: "cheapest_capable"
  
  cache:
    backend: "redis"
    redis:
      url: "${REDIS_URL}"
      max_entries: 10000
      ttls:
        expensive: 86400
        standard: 43200
  
  compression:
    enabled: true
    target_ratio: 0.7
  
  batching:
    enabled: true
    batch_window_ms: 50
    max_batch_size: 10
  
  quotas:
    enabled: true
    default_daily_limit: 100000
  
  rate_limits:
    global_max_concurrent: 20
```

---

## 10. Implementation Checklist

### Phase 1: Quick Wins (1-2 days)

- [ ] Enable Redis cache backend
- [ ] Add time-based TTL per model category
- [ ] Implement cost-weighted fallback ordering
- [ ] Add per-tenant token quotas
- [ ] Enable Prometheus metrics

### Phase 2: Medium Complexity (3-5 days)

- [ ] Implement prompt compression module
- [ ] Add batch processor for concurrent requests
- [ ] Create adaptive fallback chain
- [ ] Build cost dashboard (Grafana)
- [ ] Add alerting rules

### Phase 3: Advanced (1-2 weeks)

- [ ] Cloudflare KV integration
- [ ] Time-of-day routing
- [ ] Cache-aware model selection
- [ ] Token budgeting predictions
- [ ] Multi-region optimization

---

## 11. Expected Savings

| Optimization | Estimated Savings | Effort |
|-------------|-------------------|--------|
| Redis cache | 30-50% | Low |
| Prompt compression | 15-25% | Medium |
| Batching | 20-40% | Medium |
| Cost-weighted fallback | 5-15% | Low |
| Quotas + alerts | Prevent overages | Low |
| **Total potential** | **50-80%** | - |

---

## 12. Monitoring Commands

```bash
# Cache hit rate
curl http://localhost:9090/metrics | grep mekong_cache_hit_rate

# Cost breakdown
python -c "from src.core.cost_tracker import get_cost_tracker; print(get_cost_tracker().get_summary())"
```

---

**Files to Create:**
- `src/core/llm_cache_redis.py`
- `src/core/prompt_compressor.py`
- `src/core/batch_processor.py`
- `src/core/adaptive_fallback.py`
- `src/core/token_quota.py`
- `src/core/rate_limiter.py`
- `src/core/cost_metrics.py`
- `config/llm-router.yaml`
- `config/cache.yaml`
- `docs/cost-optimization.md`
