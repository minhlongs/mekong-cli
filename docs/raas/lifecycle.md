# RaaS Mission Lifecycle

> **From Submission to Completion** — Every mission follows this journey.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MISSION LIFECYCLE                                     │
│                                                                          │
│  1. INITIATION ──▶ 2. VALIDATION ──▶ 3. PLANNING ──▶ 4. QUEUED          │
│       │                                                                   │
│       ▼                                                                   │
│  5. EXECUTION ──▶ 6. VERIFICATION ──▶ 7. COMPLETION ──▶ 8. NOTIFICATION │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Average Duration:** 2-10 minutes (varies by complexity)

---

## Phase 1: Mission Initiation

### User Submits Mission

**Entry Point:** Dashboard UI, API, or CLI

```bash
# API Call
POST /v1/missions
Authorization: Bearer mk_abc123...
Content-Type: application/json

{
  "goal": "Generate Q1 revenue report as CSV",
  "complexity": "standard",  // optional: auto-detected from goal length
  "context": {
    "repository": "my-company/revenue-data",
    "branch": "main"
  }
}
```

### Goal Complexity Detection

| Complexity | Goal Length | Credits | Auto-Detect |
|------------|-------------|---------|-------------|
| **Simple** | < 50 chars | 1 | `"Fix typo in README"` (19 chars) → Simple |
| **Standard** | 50-149 chars | 3 | `"Add user login with email/password and session management"` (62 chars) → Standard |
| **Complex** | ≥ 150 chars | 5 | `"Build complete authentication system with OAuth2, JWT tokens, session management, password reset flow, email verification, and 2FA support"` (156 chars) → Complex |

**Response:**

```json
{
  "mission": {
    "id": "msn_abc123def456",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "goal": "Generate Q1 revenue report as CSV",
    "complexity": "standard",
    "status": "queued",
    "credits_cost": 3,
    "created_at": "2026-03-19T10:30:00Z",
    "estimated_duration_seconds": 120
  }
}
```

---

## Phase 2: Validation

### Auth & Authorization

```typescript
// apps/raas-gateway/src/middleware/auth.ts
async function validateRequest(request: Request): Promise<AuthResult> {
  // 1. Extract API key from Authorization header
  const apiKey = extractApiKey(request.headers.get('Authorization'));

  // 2. Hash and lookup in D1
  const keyHash = await sha256(apiKey);
  const key = await DB.prepare(
    'SELECT * FROM api_keys WHERE key_hash = ? AND revoked = FALSE'
  ).bind(keyHash).first();

  if (!key) return { valid: false, reason: 'invalid_key' };

  // 3. Load tenant
  const tenant = await DB.prepare(
    'SELECT * FROM tenants WHERE id = ?'
  ).bind(key.tenant_id).first();

  if (!tenant) return { valid: false, reason: 'tenant_not_found' };

  // 4. Update last_used_at
  await DB.prepare(
    'UPDATE api_keys SET last_used_at = ? WHERE id = ?'
  ).bind(new Date().toISOString(), key.id).run();

  return { valid: true, tenant, apiKey: key };
}
```

### Credit Balance Check

```typescript
// apps/raas-gateway/src/middleware/mcu-check.ts
async function checkMcuBalance(tenantId: string, missionCost: number): Promise<MCUResult> {
  const tenant = await DB.prepare(
    'SELECT credit_balance, tier FROM tenants WHERE id = ?'
  ).bind(tenantId).first();

  if (tenant.credit_balance < missionCost) {
    return {
      ok: false,
      reason: 'insufficient_credits',
      current: tenant.credit_balance,
      required: missionCost,
      upgrade_url: 'https://agencyos.network/billing'
    };
  }

  return { ok: true, remaining: tenant.credit_balance - missionCost };
}
```

### Rate Limiting

```typescript
// apps/raas-gateway/src/middleware/rate-limit.ts
async function checkRateLimit(tenantId: string): Promise<RateLimitResult> {
  const key = `rate_limit:${tenantId}`;
  const current = await RATE_LIMITS.get(key);

  if (current === null) {
    // First request in window
    await RATE_LIMITS.put(key, '1', { expirationTtl: 60 });
    return { ok: true, remaining: 999, resetIn: 60 };
  }

  const count = parseInt(current);
  if (count >= 1000) {
    return { ok: false, remaining: 0, retryAfter: 60 };
  }

  await RATE_LIMITS.put(key, String(count + 1), { expirationTtl: 60 });
  return { ok: true, remaining: 1000 - count - 1, resetIn: 60 };
}
```

**Validation Errors:**

| Error | HTTP Status | Response |
|-------|-------------|----------|
| Invalid API key | 401 Unauthorized | `{"error": "Invalid API key"}` |
| Revoked key | 401 Unauthorized | `{"error": "API key has been revoked"}` |
| Tenant not found | 404 Not Found | `{"error": "Tenant not found"}` |
| Insufficient credits | 402 Payment Required | `{"error": "Insufficient credits", "upgrade_url": "..."}` |
| Rate limit exceeded | 429 Too Many Requests | `{"error": "Rate limit exceeded", "retry_after": 60}` |

---

## Phase 3: Planning

### LLM Decomposition

```python
# packages/mekong-engine/src/core/planner.py
class Planner:
    SYSTEM_PROMPT = """You are a mission planner. Break down goals into executable steps.

Available actions:
- shell: Run shell commands (npm, git, bash)
- llm: LLM-powered tasks (code generation, analysis)
- api: HTTP API calls (deploy, create PR, send email)
- file: File operations (read, write, modify)

Return steps in JSON format with action type and parameters."""

    async def plan(self, goal: str, complexity: str) -> List[Step]:
        prompt = f"""
Goal: {goal}
Complexity: {complexity}

Break this into executable steps."""

        response = await self.llm.generate(
            system=self.SYSTEM_PROMPT,
            user=prompt,
            response_format="json"
        )

        return self.parse_steps(response.json())
```

### Example Plan Output

**Mission:** "Generate Q1 revenue report as CSV"

```json
{
  "steps": [
    {
      "id": 1,
      "action": "shell",
      "command": "git clone https://github.com/my-company/revenue-data.git /tmp/mission-abc123",
      "description": "Clone repository with revenue data"
    },
    {
      "id": 2,
      "action": "file",
      "operation": "read",
      "path": "/tmp/mission-abc123/data/q1_transactions.csv",
      "description": "Read Q1 transaction data"
    },
    {
      "id": 3,
      "action": "llm",
      "task": "Aggregate transactions by month, calculate totals",
      "input": "q1_transactions.csv",
      "output": "q1_summary.json",
      "description": "Process and aggregate data"
    },
    {
      "id": 4,
      "action": "llm",
      "task": "Generate CSV report from summary data",
      "input": "q1_summary.json",
      "output": "q1_revenue_report.csv",
      "description": "Generate final CSV report"
    },
    {
      "id": 5,
      "action": "file",
      "operation": "upload",
      "path": "/tmp/mission-abc123/output/q1_revenue_report.csv",
      "destination": "r2://tenants/{tenant_id}/exports/q1_revenue_report.csv",
      "description": "Upload report to tenant storage"
    }
  ]
}
```

### Plan Validation

```python
async def validate_plan(steps: List[Step]) -> ValidationResult:
    errors = []

    # Check for empty plan
    if len(steps) == 0:
        errors.append("Plan must have at least one step")

    # Check for valid actions
    valid_actions = {"shell", "llm", "api", "file"}
    for step in steps:
        if step.action not in valid_actions:
            errors.append(f"Invalid action: {step.action}")

    # Check for dangerous commands
    dangerous = ["rm -rf /", "DROP TABLE", "chmod 777"]
    for step in steps:
        if step.action == "shell":
            for cmd in dangerous:
                if cmd in step.command:
                    errors.append(f"Dangerous command detected: {cmd}")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors
    )
```

---

## Phase 4: Queued

### Mission Queue

```typescript
// apps/raas-gateway/src/queues/mission-queue.ts
interface QueuedMission {
  id: string;
  tenant_id: string;
  goal: string;
  plan: Step[];
  priority: number;  // Based on tenant tier
  queued_at: string;
}

// Priority queue by tenant tier
const PRIORITY = {
  enterprise: 1,  // Highest priority
  pro: 2,
  starter: 3,
  free: 4  // Lowest priority
};

async function enqueueMission(mission: QueuedMission): Promise<void> {
  const tenant = await getTenant(mission.tenant_id);
  const priority = PRIORITY[tenant.tier];

  await MISSION_QUEUE.send({
    ...mission,
    priority,
    queued_at: new Date().toISOString()
  });
}
```

### Queue Status (Dashboard View)

```
┌─────────────────────────────────────────────────────────┐
│  YOUR MISSIONS                                          │
├─────────────────────────────────────────────────────────┤
│  ID       Status      Queue Position  Est. Wait         │
│  ────────────────────────────────────────────────────── │
│  abc123   ⏳ Queued   #3              ~2 minutes        │
│  def456   🔄 Running  —               In progress       │
│  ghi789   ✅ Done     —               Completed         │
└─────────────────────────────────────────────────────────┘
```

### Queue Metrics

| Metric | Value |
|--------|-------|
| Average wait time (Free) | 2-5 minutes |
| Average wait time (Pro) | 30-60 seconds |
| Average wait time (Enterprise) | <10 seconds |
| Queue depth (normal) | 10-50 missions |
| Queue depth (peak) | 100-500 missions |

---

## Phase 5: Execution

### Executor Loop

```python
# packages/mekong-engine/src/core/executor.py
class Executor:
    async def execute(self, steps: List[Step], context: Context) -> List[Result]:
        results = []

        for i, step in enumerate(steps):
            # Update mission status
            await self.update_status(f"executing_step_{i+1}")

            # Execute step
            result = await self.run_step(step, context)
            results.append(result)

            # Stream log to client via SSE
            await self.stream_log({
                "type": "step_complete",
                "step_id": step.id,
                "status": result.status,
                "output": result.output[:1000]  # Truncate for streaming
            })

            # Fail fast on error
            if result.status == "failed":
                await self.stream_log({
                    "type": "error",
                    "message": f"Step {i+1} failed: {result.error}"
                })
                break

        return results

    async def run_step(self, step: Step, context: Context) -> Result:
        if step.action == "shell":
            return await self.run_shell(step, context)
        elif step.action == "llm":
            return await self.run_llm(step, context)
        elif step.action == "api":
            return await self.run_api(step, context)
        elif step.action == "file":
            return await self.run_file(step, context)
        else:
            return Result(status="failed", error=f"Unknown action: {step.action}")
```

### Execution Log (SSE Stream)

```
event: mission.start
data: {"mission_id": "msn_abc123", "started_at": "2026-03-19T10:32:00Z"}

event: step.start
data: {"step_id": 1, "action": "shell", "command": "git clone..."}

event: step.log
data: {"output": "Cloning into '/tmp/mission-abc123'...\n"}

event: step.complete
data: {"step_id": 1, "status": "success", "duration_ms": 1500}

event: step.start
data: {"step_id": 2, "action": "file", "operation": "read"}

event: step.complete
data: {"step_id": 2, "status": "success", "duration_ms": 50}

...

event: mission.complete
data: {"mission_id": "msn_abc123", "status": "completed", "total_duration_ms": 125000}
```

---

## Phase 6: Verification

### Quality Gates

```python
# packages/mekong-engine/src/core/verifier.py
class Verifier:
    GATES = {
        "build": {"command": "npm run build", "timeout": 120},
        "test": {"command": "npm test", "timeout": 300},
        "lint": {"command": "npm run lint", "timeout": 60},
        "security": {"command": "npm audit --audit-level=high", "timeout": 60},
    }

    async def verify(self, results: List[Result], context: Context) -> Verification:
        required_gates = self.determine_gates(context)
        gate_results = {}

        for gate_name in required_gates:
            gate_config = self.GATES[gate_name]

            # Run gate command
            exit_code, output = await run_command(
                gate_config["command"],
                timeout=gate_config["timeout"]
            )

            gate_results[gate_name] = {
                "passed": exit_code == 0,
                "output": output
            }

            if exit_code != 0:
                # Gate failed - trigger rollback
                return Verification(
                    status="failed",
                    failed_gate=gate_name,
                    rollback=True,
                    gate_results=gate_results
                )

        return Verification(
            status="passed",
            rollback=False,
            gate_results=gate_results
        )
```

### Rollback Procedure

```python
async def rollback(context: Context) -> RollbackResult:
    """Rollback changes if verification fails."""

    rollback_steps = [
        "git checkout -- .",  # Revert file changes
        "git clean -fd",       # Remove untracked files
        "git stash pop",       # Restore stashed changes (if any)
    ]

    for cmd in rollback_steps:
        exit_code, output = await run_command(cmd, cwd=context.repo_path)
        if exit_code != 0:
            return RollbackResult(
                success=False,
                error=f"Rollback failed at: {cmd}",
                partial=True
            )

    return RollbackResult(success=True, partial=False)
```

### Verification Outcomes

| Outcome | Action | Credits |
|---------|--------|---------|
| All gates pass | Mission complete | Deducted |
| Gate fails, rollback success | Mission failed, rolled back | Refunded |
| Gate fails, rollback partial | Mission failed, partial rollback | Refunded |
| Timeout | Mission failed | Refunded |

---

## Phase 7: Completion

### Status Transitions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MISSION STATUS STATES                                 │
│                                                                          │
│  queued ──▶ planning ──▶ executing ──▶ verifying ──▶ completed          │
│     │            │           │            │                              │
│     │            │           │            └──────▶ failed (refund)      │
│     │            │           │                                          │
│     │            │           └────────────────▶ failed (error)          │
│     │            │                                                      │
│     │            └──────────────────────────▶ failed (planning error)   │
│     │                                                                │
│     └────────────────────────────▶ cancelled (user, refund if queued)  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Credit Transaction

```python
# packages/mekong-engine/src/billing/credits.py
async def process_credit_transaction(mission: Mission, result: MissionResult):
    if result.status == "completed":
        # Deduct credits
        await DB.execute("""
            INSERT INTO credit_transactions
            (tenant_id, amount, type, mission_id, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            mission.tenant_id,
            -mission.credits_cost,
            "mission",
            mission.id,
            f"Mission {mission.id[:8]}... completed"
        ))

        await DB.execute("""
            UPDATE tenants SET credit_balance = credit_balance - ?
            WHERE id = ?
        """, (mission.credits_cost, mission.tenant_id))

    elif result.status == "failed" and result.rolled_back:
        # Refund credits
        await DB.execute("""
            INSERT INTO credit_transactions
            (tenant_id, amount, type, mission_id, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            mission.tenant_id,
            mission.credits_cost,
            "refund",
            mission.id,
            f"Mission {mission.id[:8]}... failed, rolled back"
        ))

    # Update mission record
    await DB.execute("""
        UPDATE missions
        SET status = ?, completed_at = ?, error_message = ?
        WHERE id = ?
    """, (result.status, datetime.now(), result.error, mission.id))
```

### Final State

```json
{
  "mission": {
    "id": "msn_abc123def456",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "goal": "Generate Q1 revenue report as CSV",
    "complexity": "standard",
    "status": "completed",
    "credits_cost": 3,
    "created_at": "2026-03-19T10:30:00Z",
    "completed_at": "2026-03-19T10:32:05Z",
    "duration_seconds": 125,
    "error_message": null,
    "output": {
      "export_url": "https://storage.agencyos.network/tenants/.../exports/q1_revenue_report.csv",
      "expires_at": "2026-04-18T10:32:05Z"
    }
  }
}
```

---

## Phase 8: Notification

### Notification Channels

| Channel | Trigger | Content |
|---------|---------|---------|
| **SSE Stream** | Real-time (during execution) | Step-by-step logs |
| **Email** | Mission complete/failed | Summary + output link |
| **Webhook** | Mission complete/failed | POST to customer's endpoint |
| **Dashboard** | Always | Mission list updates |

### Webhook Payload

```json
// POST https://customer.com/webhooks/raas
{
  "event": "mission.completed",
  "timestamp": "2026-03-19T10:32:05Z",
  "data": {
    "mission_id": "msn_abc123def456",
    "goal": "Generate Q1 revenue report as CSV",
    "status": "completed",
    "credits_cost": 3,
    "duration_seconds": 125,
    "output": {
      "export_url": "https://storage.agencyos.network/.../q1_revenue_report.csv"
    }
  },
  "signature": "hmac_sha256_signature"
}
```

### Email Template

```
Subject: ✅ Mission Completed: "Generate Q1 revenue report"

Hi there,

Your mission has been completed successfully!

MISSION SUMMARY
───────────────
ID: msn_abc123def456
Goal: Generate Q1 revenue report as CSV
Status: ✅ Completed
Duration: 2 minutes 5 seconds
Credits: 3

OUTPUT
──────
Download: https://agencyos.network/dashboard/exports/q1_revenue_report.csv
(Expires: April 18, 2026)

VIEW FULL LOGS → https://agencyos.network/dashboard/missions/msn_abc123def456

Need help? Reply to this email or visit our support center.

— The RaaS Team
```

---

## Metrics & SLAs

### Phase Duration Benchmarks

| Phase | Simple | Standard | Complex |
|-------|--------|----------|---------|
| Initiation | <1s | <1s | <1s |
| Validation | <100ms | <100ms | <100ms |
| Planning | 5-15s | 15-30s | 30-60s |
| Queued (Enterprise) | <10s | <10s | <10s |
| Queued (Pro) | 30-60s | 30-60s | 30-60s |
| Queued (Free) | 2-5 min | 2-5 min | 2-5 min |
| Execution | 30-60s | 2-5 min | 5-10 min |
| Verification | 30-60s | 1-2 min | 2-3 min |
| Completion | <1s | <1s | <1s |
| Notification | <5s | <5s | <5s |

### SLA Targets

| Metric | Target | Actual (Q1 2026) |
|--------|--------|------------------|
| Mission success rate | >95% | 97.3% |
| Average duration | <5 min | 3.2 min |
| Queue time (Enterprise) | <30s | 8s |
| Queue time (Pro) | <2 min | 45s |
| Notification latency | <10s | 3.5s |
| Rollback success rate | 100% | 100% |

---

## Error Handling

### Error Categories

| Category | Examples | Recovery |
|----------|----------|----------|
| **Authentication** | Invalid API key, Revoked key | User must regenerate key |
| **Authorization** | Insufficient credits, Rate limit | Upgrade plan or wait |
| **Planning** | Goal too vague, Invalid context | User must refine goal |
| **Execution** | Command failed, Timeout | Auto-retry (3x), then rollback |
| **Verification** | Build failed, Tests failed | Rollback + refund |
| **System** | Database error, Worker crash | Auto-retry, failover to backup |

### Retry Logic

```python
async def execute_with_retry(step: Step, context: Context) -> Result:
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            result = await run_step(step, context)
            if result.status == "success":
                return result

            # Retry on transient errors
            if result.error in ["timeout", "network_error", "rate_limited"]:
                retry_count += 1
                await sleep(2 ** retry_count)  # Exponential backoff
                continue

            return result  # Non-retryable error

        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                return Result(status="failed", error=str(e))
            await sleep(2 ** retry_count)
```

---

**Document Version**: 1.0
**Last Updated**: March 19, 2026
**Next Review**: June 19, 2026
**Owner**: Engineering Team

---

© 2026 AgencyOS. *Confidential — Internal Use Only*
