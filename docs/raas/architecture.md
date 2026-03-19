# RaaS Platform Architecture

> **100% Serverless, Global Edge, Enterprise-Grade**

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE EDGE                              │
│     WAF + DDoS Protection + 275+ Data Centers Worldwide         │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌─────────────────┐           ┌─────────────────┐
│  Cloudflare     │           │  Cloudflare     │
│  Workers        │           │  Pages          │
│  (API Gateway)  │           │  (Dashboard)    │
│                 │           │                 │
│  • Auth         │           │  • React UI     │
│  • Rate Limit   │           │  • SSE Stream   │
│  • Routing      │           │  • Real-time    │
└────────┬────────┘           └─────────────────┘
         │
         ▼
┌─────────────────┐
│  RaaS Gateway   │
│  (Edge API)     │
├─────────────────┤
│  • MCU Check    │
│  • Tenant Auth  │
│  • Mission Queue│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PEV Engine     │
│  (Core Orchestrator) │
├─────────────────┤
│  • Planner      │
│  • Executor     │
│  • Verifier     │
│  • Orchestrator │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌───────┐ ┌───────┐ ┌──────────┐
│ D1    │ │ R2    │ │ KV       │
│ (DB)  │ │ (Store)│ │ (Cache)  │
└───────┘ └───────┘ └──────────┘
```

---

## Infrastructure Layers

### Layer 1: Global Edge (Cloudflare)

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **WAF** | OWASP Top 10 protection | Managed ruleset + custom rules |
| **DDoS Protection** | L3/L4/L7 attack mitigation | Auto-scaling, always-on |
| **CDN** | Static asset delivery | 275+ data centers, HTTP/2, Brotli |
| **SSL/TLS** | Encryption in transit | TLS 1.3, Auto HTTPS, HSTS |

**Key Metrics:**
- TTFB: <50ms (edge), <200ms (origin)
- Cache hit rate: >95% (static assets)
- DDoS mitigation: Unlimited (L3/L4), 10M rps (L7)

---

### Layer 2: Edge Compute (Cloudflare Workers)

#### API Gateway Worker

```typescript
// apps/raas-gateway/src/index.ts
export default {
  async fetch(request: Request): Promise<Response> {
    // 1. Auth check (JWT/API key)
    const auth = await validateAuth(request);
    if (!auth.valid) return unauthorized();

    // 2. Rate limiting (per tenant)
    const rateLimit = await checkRateLimit(auth.tenantId);
    if (!rateLimit.ok) return rateLimited();

    // 3. MCU balance check
    const mcuCheck = await checkMcuBalance(auth.tenantId);
    if (mcuCheck.balance === 0) return paymentRequired();

    // 4. Route to appropriate handler
    return routeRequest(request, auth);
  }
};
```

**Key Endpoints:**

| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/v1/missions` | POST | `missions.create` | Submit new mission |
| `/v1/missions/:id` | GET | `missions.get` | Get mission status |
| `/v1/missions/:id/cancel` | POST | `missions.cancel` | Cancel queued mission |
| `/v1/dashboard/stream` | GET | `dashboard.sse` | SSE real-time stream |
| `/v1/credits/balance` | GET | `credits.balance` | Check credit balance |

#### Dashboard Worker (Cloudflare Pages)

| Feature | Technology | Description |
|---------|------------|-------------|
| **Mission List** | React 19 + SWR | Paginated list with filters |
| **Real-time Updates** | SSE (Server-Sent Events) | Live mission status |
| **Credit Dashboard** | Recharts | Credit usage visualization |
| **Settings** | React Hook Form | API keys, webhooks, billing |

---

### Layer 3: Core Engine (PEV)

#### PEV Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PEV ENGINE                                │
├───────────────┬───────────────┬───────────────┬─────────────┤
│   PLANNER     │   EXECUTOR    │   VERIFIER    │ ORCHESTRATOR│
│               │               │               │             │
│ LLM decomposes│ Run steps via │ Quality gates │ Coordinate  │
│ goal into     │ Shell/LLM/API │ + rollback    │ PEV loop    │
│ executable    │               │               │             │
│ steps         │               │               │             │
└───────────────┴───────────────┴───────────────┴─────────────┘
```

#### Planner Module

**Input:** Natural language goal
**Output:** Ordered list of executable steps

```python
# packages/mekong-engine/src/core/planner.py
class Planner:
    async def plan(self, goal: str, complexity: str) -> List[Step]:
        prompt = f"""Break down this goal into executable steps:
        Goal: {goal}
        Complexity: {complexity}

        Return steps as JSON array."""

        response = await self.llm.generate(prompt)
        return self.parse_steps(response)
```

**Example Output:**
```json
{
  "steps": [
    {"id": 1, "action": "shell", "command": "npm run build"},
    {"id": 2, "action": "shell", "command": "npm test"},
    {"id": 3, "action": "api", "endpoint": "deploy", "method": "POST"}
  ]
}
```

#### Executor Module

**Input:** List of steps
**Output:** Execution logs, step results

```python
# packages/mekong-engine/src/core/executor.py
class Executor:
    async def execute(self, steps: List[Step], context: Context) -> List[Result]:
        results = []
        for step in steps:
            result = await self.run_step(step, context)
            results.append(result)
            if result.status == "failed":
                break  # Fail fast
        return results
```

**Step Types:**

| Type | Description | Example |
|------|-------------|---------|
| `shell` | Execute shell command | `npm run build`, `git push` |
| `llm` | LLM-powered task | Code generation, text analysis |
| `api` | HTTP API call | Deploy to Vercel, create PR |
| `file` | File operations | Read, write, modify files |

#### Verifier Module

**Input:** Execution results
**Output:** Pass/fail decision, rollback trigger

```python
# packages/mekong-engine/src/core/verifier.py
class Verifier:
    GATES = {
        "build": lambda ctx: run_command("npm run build"),
        "test": lambda ctx: run_command("npm test"),
        "lint": lambda ctx: run_command("npm run lint"),
    }

    async def verify(self, results: List[Result], context: Context) -> Verification:
        for gate_name, gate_fn in self.GATES.items():
            if gate_name in context.required_gates:
                passed = await gate_fn(context)
                if not passed:
                    return Verification(status="failed", rollback=True)
        return Verification(status="passed", rollback=False)
```

**Quality Gates:**

| Gate | Command | Required For |
|------|---------|--------------|
| Build | `npm run build` | All frontend missions |
| Test | `npm test` | Code change missions |
| Lint | `npm run lint` | Code quality missions |
| Security | `npm audit` | Dependency missions |

#### Orchestrator Module

**Coordinates the PEV loop:**

```python
# packages/mekong-engine/src/core/orchestrator.py
class Orchestrator:
    async def run_mission(self, mission: Mission) -> MissionResult:
        # 1. Plan
        steps = await self.planner.plan(mission.goal, mission.complexity)

        # 2. Execute
        results = await self.executor.execute(steps, mission.context)

        # 3. Verify
        verification = await self.verifier.verify(results, mission.context)

        # 4. Handle outcome
        if verification.rollback:
            await self.executor.rollback()
            return MissionResult(status="failed", rolled_back=True)

        return MissionResult(status="completed", results=results)
```

---

## Data Layer

### D1 Database (SQLite at Edge)

#### Schema Overview

```sql
-- Tenants (organizations)
CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'starter', 'pro', 'enterprise')),
  credit_balance INTEGER DEFAULT 5,
  settings JSON
);

-- API Keys
CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  key_hash TEXT NOT NULL,
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_used_at DATETIME,
  revoked BOOLEAN DEFAULT FALSE
);

-- Missions
CREATE TABLE missions (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  goal TEXT NOT NULL,
  complexity TEXT CHECK(complexity IN ('simple', 'standard', 'complex')),
  status TEXT CHECK(status IN ('queued', 'planning', 'executing', 'verifying', 'completed', 'failed', 'cancelled')),
  credits_cost INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  error_message TEXT
);

-- Mission Logs
CREATE TABLE mission_logs (
  id UUID PRIMARY KEY,
  mission_id UUID REFERENCES missions(id),
  step_id INTEGER,
  message TEXT,
  level TEXT CHECK(level IN ('info', 'warn', 'error')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Credit Transactions
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  amount INTEGER NOT NULL,
  type TEXT CHECK(type IN ('purchase', 'mission', 'refund', 'rollover', 'adjustment')),
  mission_id UUID REFERENCES missions(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);
```

#### Indexes

```sql
CREATE INDEX idx_missions_tenant ON missions(tenant_id, created_at DESC);
CREATE INDEX idx_missions_status ON missions(status);
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_transactions_tenant ON credit_transactions(tenant_id, created_at DESC);
```

---

### R2 Storage (S3-Compatible Object Storage)

#### Bucket Structure

```
raas-storage/
├── tenants/
│   └── {tenant_id}/
│       ├── backups/
│       │   └── {date}/
│       │       └── db-snapshot.sqlite
│       ├── uploads/
│       │   └── {filename}
│       └── exports/
│           └── {report_name}.csv
├── missions/
│   └── {mission_id}/
│       ├── artifacts/
│       │   └── {generated_files}
│       └── logs/
│           └── execution.log
└── global/
    └── templates/
        └── {template_name}.json
```

#### Lifecycle Policies

| Path | Expiration | Purpose |
|------|------------|---------|
| `tenants/*/backups/` | 30-90 days (tier-based) | Backup retention |
| `missions/*/artifacts/` | 7 days | Temporary artifacts |
| `missions/*/logs/` | 1 year (standard), 7 years (enterprise) | Audit compliance |
| `tenants/*/exports/` | 30 days | Downloaded reports |

---

### KV Storage (Edge Key-Value Cache)

#### Namespaces

| Namespace | Purpose | TTL |
|-----------|---------|-----|
| `sessions` | User session data | 24 hours |
| `rate_limits` | Per-tenant rate limiting | 1 minute |
| `mcu_cache` | Credit balance cache | 5 minutes |
| `feature_flags` | A/B test flags | No expiration |
| `config` | Runtime configuration | No expiration |

#### Example Usage

```typescript
// Rate limiting with KV
async function checkRateLimit(tenantId: string): Promise<RateLimitResult> {
  const key = `rate_limit:${tenantId}`;
  const current = await RATE_LIMITS.get(key);

  if (current === null || current < 1000) {
    await RATE_LIMITS.put(key, String((parseInt(current) || 0) + 1), { expirationTtl: 60 });
    return { ok: true, remaining: 1000 - (parseInt(current) || 0) };
  }

  return { ok: false, remaining: 0, retryAfter: 60 };
}
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: NETWORK SECURITY                                  │
│  • WAF (OWASP Top 10)                                       │
│  • DDoS Protection (L3/L4/L7)                               │
│  • Rate Limiting (per tenant, per API key)                  │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: APPLICATION SECURITY                              │
│  • JWT/API Key Authentication                               │
│  • RBAC (Viewer, Developer, Admin, Owner)                   │
│  • Input Validation (Zod schemas)                           │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: DATA SECURITY                                     │
│  • TLS 1.3 (in transit)                                     │
│  • AES-256 (at rest)                                        │
│  • HMAC-SHA256 (API key hashing)                            │
├─────────────────────────────────────────────────────────────┤
│  LAYER 4: OPERATIONAL SECURITY                              │
│  • Audit Logging (all mutations)                            │
│  • Monitoring (SIEM, alerting)                              │
│  • Backup & DR (daily backups, quarterly drills)            │
└─────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  API Gateway │───▶│   RaaS      │───▶│   D1/KV     │
│             │    │  (Worker)    │    │   Gateway   │    │   (Auth)    │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
     │                    │                    │                    │
     │ 1. API Key         │                    │                    │
     │───────────────────▶│                    │                    │
     │                    │ 2. Hash & Lookup   │                    │
     │                    │───────────────────▶│                    │
     │                    │                    │ 3. Query D1        │
     │                    │                    │───────────────────▶│
     │                    │                    │ 4. Tenant + Rate   │
     │                    │                    │◀───────────────────│
     │                    │ 5. Valid + Credits │                    │
     │                    │◀───────────────────│                    │
     │ 6. Auth + MCU OK   │                    │                    │
     │◀───────────────────│                    │                    │
     │                    │                    │                    │
     │ 7. Process Mission │                    │                    │
     │───────────────────▶│                    │                    │
```

---

## Scaling Architecture

### Auto-Scaling Triggers

| Component | Trigger | Scale Action |
|-----------|---------|--------------|
| Workers | Request volume | Automatic (global edge) |
| D1 | Query volume | Read replicas |
| R2 | Storage volume | Unlimited (S3-compatible) |
| KV | Cache hits | Automatic (edge caching) |

### Global Distribution

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE GLOBAL                         │
│                                                             │
│  NAM (North America)     EU (Europe)        APAC (Asia)     │
│  • Dallas, TX            • Frankfurt, DE    • Singapore     │
│  • Ashburn, VA           • Amsterdam, NL    • Tokyo, JP     │
│  • San Francisco, CA     • London, UK       • Sydney, AU    │
│                                                             │
│  Total: 275+ data centers worldwide                         │
└─────────────────────────────────────────────────────────────┘
```

### Failover Strategy

| Failure Type | Detection | Failover Action |
|--------------|-----------|-----------------|
| Region failure | Health check timeout (30s) | DNS failover to next region |
| D1 corruption | Write error | Restore from backup (R2) |
| Worker error | Exception rate >1% | Rollback to previous deployment |
| KV outage | Cache miss rate >50% | Fallback to D1 direct reads |

---

## Monitoring & Observability

### Metrics Collected

| Category | Metrics | Retention |
|----------|---------|-----------|
| **Performance** | Latency (p50, p95, p99), TTFB, Duration | 90 days |
| **Reliability** | Error rate, Success rate, Uptime | 1 year |
| **Usage** | Requests/sec, Credits consumed, Active tenants | 2 years |
| **Business** | MRR, Churn, Expansion | 7 years |

### Alerting Rules

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| API Error Rate | >1% for 5 min | P1 | PagerDuty |
| Latency p99 | >1s for 10 min | P2 | Slack |
| Backup Failure | Any failure | P1 | PagerDuty + Phone |
| Credit Balance | Tenant reaches 0 | P3 | Email |
| DDoS Attack | Detected | P1 | PagerDuty + Security |

---

## Cost Architecture

### Infrastructure Costs (Monthly Estimate)

| Service | Free Tier | Starter | Pro | Enterprise |
|---------|-----------|---------|-----|------------|
| Workers (requests) | $0.50 | $5 | $50 | $200 |
| D1 (reads/writes) | $0.50 | $2 | $10 | $50 |
| R2 (storage + egress) | $0.20 | $1 | $5 | $20 |
| KV (operations) | $0.10 | $0.50 | $2 | $10 |
| **Total Infra Cost** | **$1.30** | **$8.50** | **$67** | **$280** |
| **Revenue** | $0 | $29 | $199 | $599+ |
| **Margin** | N/A | 71% | 66% | 53%+ |

---

**Document Version**: 1.0
**Last Updated**: March 19, 2026
**Next Review**: June 19, 2026
**Owner**: Engineering Team

---

© 2026 AgencyOS. *Confidential — Internal Use Only*
