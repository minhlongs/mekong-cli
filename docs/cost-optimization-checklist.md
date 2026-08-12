# Cost Optimization Checklist

**Target:** Mekong CLI / ZenOS Platform  
**Last Updated:** 2026-06-20  
**Status:** Active

---

## Overview

This checklist covers cost optimization across all layers of the Mekong platform:
- **LLM API Costs** (MCU credits via OpenRouter/Anthropic)
- **Cloudflare Infrastructure** (free tier maintenance)
- **Local Resource Usage** (CPU/Memory on developer machines)
- **CI/CD Pipeline** (GitHub Actions minutes)
- **Database & Storage** (D1, R2, KV usage)

---

## 1. LLM API Cost Optimization

### 1.1 Model Selection Strategy

- [ ] **Use cheapest capable model** for each task type
  - Simple search/grep: `claude-haiku-4-5` (fast/cheap)
  - Standard coding: `claude-sonnet-4-6`
  - Deep analysis/architecture: `claude-opus-4-7` only when necessary
  - CEO orchestration: `claude-opus-4-8` (main agent only)

- [ ] **Implement model routing based on task complexity**
  ```python
  # Example routing logic
  if task_type in ["search", "grep", "list"]:
      model = "haiku-4-5"
  elif task_type in ["code", "test", "review"]:
      model = "sonnet-4-6"
  elif task_type in ["architecture", "security-audit"]:
      model = "opus-4-7"
  ```

- [ ] **Set up fallback chains** to cheaper providers when available
  - Priority: OpenRouter (best rates) → DeepSeek → Anthropic → OpenAI → Ollama (local, $0)

- [ ] **Cache LLM responses** for idempotent operations
  - Cache key: `sha256(prompt + context)`
  - TTL: 24h for development, 7d for production
  - Storage: Cloudflare KV (free tier)

### 1.2 Prompt Engineering

- [ ] **Minimize context window usage**
  - Use `rg` (ripgrep) instead of loading entire files
  - Pass only relevant file sections (max 200 lines per file)
  - Use file path references instead of embedding content when possible

- [ ] **Implement context budget limits**
  - Hard limit: 100K tokens per planning phase
  - Soft limit: 50K tokens for execution phases
  - Warning at 80% of limit

- [ ] **Use concise, structured prompts**
  - Bad: "Please analyze this code and tell me what you think about it in detail with all your considerations"
  - Good: "Analyze `src/agents/git_agent.py` for: 1) bugs 2) security issues 3) performance. Format: bullet points"

- [ ] **Implement early stopping** when task completes before max tokens
  - Monitor `stop_reason` in API response
  - Don't request unnecessary additional tokens

### 1.3 MCU Billing Controls

- [ ] **Enforce credit limits per user/tier**
  ```
  Starter: 200 credits/mo → soft limit at 180, hard at 200
  Growth: 1000 credits/mo → soft at 900, hard at 1000
  Pro: 5000 credits/mo → soft at 4500, hard at 5000
  ```

- [ ] **Implement usage metering with warnings**
  ```python
  if user.credits_remaining < user.monthly_allocation * 0.1:
      send_warning("Only 10% credits remaining")
  ```

- [ ] **Track MCU cost per command** in `usage_events.jsonl`
  - Include: command name, model used, input tokens, output tokens, MCU cost
  - Daily aggregation for trend analysis

- [ ] **Set up credit balance alerts**
  - 7 days remaining at current rate
  - Suspicious usage spike (3x average daily)

---

## 2. Cloudflare Infrastructure Optimization

### 2.1 Free Tier Maintenance

- [ ] **Monitor free tier limits** (never exceed)
  | Service | Free Limit | Current Usage | Alert at |
  |---------|------------|---------------|----------|
  | Workers | 100,000 req/day | | 80K |
  | Pages | Unlimited | | N/A |
  | D1 | 5GB storage | | 4GB |
  | D1 | 25K reads/day | | 20K |
  | D1 | 2K writes/day | | 1.6K |
  | R2 | 10GB storage | | 8GB |
  | R2 | 1M Class A ops/mo | | 800K |
  | R2 | 1M Class B ops/mo | | 800K |
  | KV | 100K reads/day | | 80K |
  | KV | 1K writes/day | | 800 |

- [ ] **Implement rate limiting** before hitting free tier caps
  ```javascript
  // wrangler.toml
  [[routes]]
  pattern = "api/*"
  rate_limiting = { requests = 1000, period_seconds = 60 }
  ```

- [ ] **Cache aggressively** to reduce D1 reads
  - Session data: KV TTL 1h
  - User profiles: KV TTL 5m
  - Static config: KV TTL 1d
  - API responses: KV TTL varies by endpoint

- [ ] **Batch database writes** to stay under D1 write limits
  - Queue writes when < 100 writes/day remaining
  - Consolidate multiple updates into single transaction

### 2.2 Resource Cleanup

- [ ] **Implement TTL on temporary data**
  - Pilot credits history: archive after 90 days
  - Usage events: hot 30 days, archive older to R2
  - Log files: rotate daily, keep 7 days locally

- [ ] **Clean up old R2 objects automatically**
  ```bash
  # Script to delete objects older than 90 days
  npx wrangler r2 bulk delete --recursive --older-than 90d
  ```

- [ ] **Prune unused KV namespaces**
  - Audit quarterly
  - Delete namespaces not accessed in 30+ days

### 2.3 CDN & Edge Optimization

- [ ] **Set appropriate cache headers**
  ```javascript
  // Static assets: cache 1 year
  // API responses: cache 5m (vary by Authorization)
  // HTML pages: cache 1h (no-cache for authenticated)
  ```

- [ ] **Enable Brotli compression** for all text responses
- [ ] **Use Cloudflare Polish** for image optimization (free)
- [ ] **Implement edge-side includes** for common headers/footers

---

## 3. Code Efficiency

### 3.1 PEV Engine Optimization

- [ ] **Minimize LLM calls per command**
  - Planning phase: 1-3 calls max
  - Execution phase: batch related operations
  - Verification phase: reuse planning context where possible

- [ ] **Implement result caching** for expensive operations
  - Schema validation results
  - Dependency resolution
  - Git diff analysis

- [ ] **Parallelize independent operations**
  - Multiple files read: parallel fetch
  - Independent tests: concurrent execution
  - But respect rate limits (see above)

### 3.2 Database Query Optimization

- [ ] **Use prepared statements** for all D1 queries
- [ ] **Add indexes on frequently queried columns**
  - `user_id` (all tables)
  - `created_at` (time-range queries)
  - `status` (filtering)

- [ ] **Implement query result caching**
  ```python
  @cached(ttl=300)  # 5 minutes
  def get_user_credits(user_id):
      return db.query("SELECT credits FROM users WHERE id = ?", user_id)
  ```

- [ ] **Use connection pooling** (D1 auto-pooling, but monitor)
- [ ] **Avoid N+1 queries** — use JOINs or batch fetches

### 3.3 Memory Management

- [ ] **Stream large file operations** instead of loading into memory
  - Use chunked reading for files > 10MB
  - Process line-by-line for log parsing

- [ ] **Implement lazy loading** for agent skills
  - Load skill definitions only when first used
  - Unload unused skills after 1h of inactivity

- [ ] **Set memory limits** for subprocesses
  ```python
  import resource
  resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, -1))  # 512MB max
  ```

---

## 4. CI/CD Cost Optimization

### 4.1 GitHub Actions

- [ ] **Use self-hosted runners** for frequent builds
  - Cost: $0 (use existing M1 Mac)
  - Savings: 2,000 free minutes/mo on GitHub

- [ ] **Optimize workflow triggers**
  - `paths-ignore` for docs-only changes
  - Skip tests for pure documentation updates
  - Use `workflow_dispatch` for manual expensive jobs

- [ ] **Cache dependencies aggressively**
  ```yaml
  - uses: actions/cache@v3
    with:
      path: |
        node_modules
        .venv
        ~/.cache/pip
      key: ${{ runner.os }}-deps-${{ hashFiles('pnpm-lock.yaml', 'pyproject.toml') }}
  ```

- [ ] **Run tests in parallel** (already using pytest-xdist)
  - `pytest -n auto` uses all CPU cores
  - Split test suites by module

- [ ] **Cancel redundant runs** on PR updates
  ```yaml
  concurrency:
    group: ${{ github.ref }}
    cancel-in-progress: true
  ```

### 4.2 Build Optimization

- [ ] **Use incremental builds** (turbo/repo)
  - Already enabled via `turbo.json`
  - Ensure proper pipeline dependencies

- [ ] **Skip unnecessary builds**
  - Only build changed packages
  - Skip typecheck for documentation-only changes

---

## 5. Local Development Costs

### 5.1 LLM Usage During Development

- [ ] **Use local models for development** (Ollama)
  ```bash
  export LLM_BASE_URL=http://localhost:11434/v1
  export LLM_MODEL=qwen2.5-coder:14b
  ```
  - Savings: ~$0 vs $0.50-5.00/1K tokens for cloud
  - Performance: slower but adequate for dev

- [ ] **Switch to cheap models for iterative tasks**
  - Debugging loop: use Haiku until final verification
  - Code generation: Sonnet (good quality/cost ratio)

- [ ] **Implement dry-run mode** for planning
  - `/cook --dry-run` → show plan without executing
  - No LLM costs for failed plans

### 5.2 Resource Monitoring

- [ ] **Monitor local CPU/memory** during development
  - Use `top` or `htop` to watch agent processes
  - Kill runaway processes (>8GB memory)

- [ ] **Limit parallel agent count** based on available resources
  ```python
  import psutil
  max_agents = min(8, psutil.cpu_count() // 2)
  ```

---

## 6. Monitoring & Alerting

### 6.1 Cost Dashboards

- [ ] **Create Grafana dashboard** with metrics:
  - Daily MCU consumption (by user, by command, by model)
  - Cloudflare usage (Workers requests, D1 ops, KV ops)
  - API response times (p50, p95, p99)
  - Error rates (4xx, 5xx)

- [ ] **Daily cost report** (cron job)
  ```
  Cost Summary - 2026-06-20
  =========================
  LLM Costs: $X.XX (X MCU used)
  Cloudflare: $0.00 (free tier)
  GitHub Actions: YY minutes used
  
  Top 5 Expensive Commands:
  1. /cook (complex): 50 MCU
  2. /cto-review: 30 MCU
  ...
  
  Alerts:
  - ⚠️ User abc123 at 85% monthly limit
  - ✅ All systems within budget
  ```

### 6.2 Alert Thresholds

- [ ] **Configure alerts** for:
  - Daily spend > 50% of monthly budget
  - Single user consuming > 20% of total credits
  - Cloudflare free tier > 70% used
  - API error rate > 5%
  - Response time p95 > 5s

### 6.3 Anomaly Detection

- [ ] **Detect usage spikes** (3x moving average)
- [ ] **Flag suspicious patterns**
  - Single command executed 100x in 1h
  - Same prompt cached hit rate < 10%
  - High retry rates (LLM failures)

---

## 7. Operational Best Practices

### 7.1 Command Design

- [ ] **Assign accurate MCU costs** to commands
  - Base: 1 MCU for simple operations
  - +1 MCU per LLM call required
  - +2 MCU for multi-step workflows
  - Review quarterly

- [ ] **Implement command-specific optimizations**
  - `/cook`: Use cached dependency resolution
  - `/test`: Skip tests with unchanged code
  - `/deploy`: Only rebuild changed packages

### 7.2 Agent Efficiency

- [ ] **Reuse agent instances** instead of spawning new
  - Keep agent pool alive between tasks
  - Connection reuse for API calls

- [ ] **Implement agent timeouts**
  - Hard timeout: 300s per agent
  - Graceful degradation on timeout

- [ ] **Batch agent requests** when possible
  - Multiple file operations in single GitAgent call
  - Aggregate health checks

### 7.3 Data Retention

- [ ] **Archive old usage data** to R2 (cheap storage)
  - Keep 90 days hot in D1
  - Move >90 days to R2 as JSONL

- [ ] **Implement data compression**
  - Gzip R2 objects (90% reduction)
  - Rotate logs hourly with compression

- [ ] **Delete ephemeral data** after TTL
  - Session tokens: 24h
  - Cache misses: 1h
  - Temporary files: process exit

---

## 8. Regular Audits

### Monthly Checklist

- [ ] Review MCU consumption by command (top 10)
- [ ] Analyze user credit usage patterns
- [ ] Check Cloudflare billing forecast
- [ ] Identify commands with high cache miss rates
- [ ] Review agent execution times (slowest 5)
- [ ] Audit for orphaned KV namespaces/R2 buckets

### Quarterly Checklist

- [ ] Rebalance MCU costs across commands
- [ ] Negotiate better rates with LLM providers (volume discounts)
- [ ] Review and optimize database schema
- [ ] Update model routing based on new model releases
- [ ] Benchmark alternative LLM providers
- [ ] Clean up unused skills/commands

---

## 9. Quick Wins (Priority Order)

1. **Enable Ollama for development** → ~$0 vs $50-100/mo per dev
2. **Cache LLM responses** → 30-50% reduction in repeat queries
3. **Implement rate limiting** → prevent runaway costs
4. **Optimize context window** → 20-40% token reduction
5. **Use self-hosted GitHub runners** → 2,000 free minutes/mo
6. **Archive old data to R2** → 90% storage cost reduction
7. **Parallelize tests** → 50% CI time reduction
8. **Implement credit warnings** → prevent surprise bills

---

## 10. Cost Optimization ROI Tracking

| Initiative | Implementation Time | Monthly Savings | ROI Period |
|------------|-------------------|-----------------|------------|
| Local LLM for dev | 2h | $100/developer | Immediate |
| Response caching | 4h | $50 | 1 month |
| Rate limiting | 2h | Prevents overages | Immediate |
| Self-hosted runners | 1h | $0 (2K free min) | Immediate |
| Data archiving | 3h | $10 | 3 months |

**Total Potential Savings:** $200-500/month for small team

---

## Appendix: Useful Commands

```bash
# Check current Cloudflare usage
npx wrangler metrics --namespace us

# List all KV namespaces
npx wrangler kv namespace list

# List R2 buckets
npx wrangler r2 bucket list

# View D1 database size
npx wrangler d1 info <database-name>

# Calculate MCU usage (from logs)
jq -r '.mcu_cost' ~/.mekong/usage_events.jsonl | awk '{sum+=$1} END {print sum}'

# Find top expensive commands
jq -r '"\(.command) \(.mcu_cost)"' ~/.mekong/usage_events.jsonl | \
  sort -k2 -rn | head -20
```

---

**Owner:** CTO / Engineering  
**Review Cycle:** Monthly  
**Next Review:** 2026-07-20
