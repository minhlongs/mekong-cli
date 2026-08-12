# Command Execution Flow

## Overview

This document details the complete command execution pipeline from CLI invocation to result delivery, including the Plan-Execute-Verify (PEV) engine, billing integration, and error handling.

## Execution Stages

```
CLI Invocation
    │
    ▼
[1] API Gateway ───────────────────────────────┐
    │  - Auth (JWT/API key)                     │
    │  - Rate limit (Redis)                     │
    │  - Billing check (credits)                │
    ▼                                           │
[2] Command Registry ──────────────────────────┤
    │  - Lookup command definition              │
    │  - Load plugin if needed                  │
    ▼                                           │
[3] PEV Engine ────────────────────────────────┤
    │  - Plan (decompose into steps)            │
    │  - Execute (run steps with tools)         │
    │  - Verify (check outcome)                 │
    ▼                                           │
[4] Billing Service ───────────────────────────┤
    │  - Deduct credits (atomic)                │
    │  - Log transaction                       │
    ▼                                           │
[5] Response ──────────────────────────────────┘
```

## Stage 1: API Gateway

### Request Flow

```python
# src/api/middleware.py
@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    start_time = time.time()

    # 1. CORS preflight
    if request.method == "OPTIONS":
        return await handle_cors(request)

    # 2. Authentication
    user = await authenticate(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    # 3. Rate limiting (skip for health check)
    if not request.url.path.startswith("/health"):
        rate_key = f"rate:{user.id}:{int(time.time() // 60)}"
        current = await redis.incr(rate_key)
        if current == 1:
            await redis.expire(rate_key, 60)
        if current > 1000:  # Per-minute limit
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "60"},
                content={"error": "rate_limited"}
            )

    # 4. Route and process
    response = await call_next(request)

    # 5. Logging
    duration_ms = int((time.time() - start_time) * 1000)
    await log_request(user.id, request.url.path, response.status_code, duration_ms)

    return response
```

### Billing Middleware

```python
# src/api/billing_middleware.py
@app.middleware("http")
async def billing_middleware(request: Request, call_next):
    # Only apply to command execution endpoints
    if not request.url.path.startswith("/api/v1/commands/"):
        return await call_next(request)

    # Extract command name from path
    command_name = request.url.path.split("/")[-1]

    # Get command cost from registry (cached)
    cmd = await command_registry.get(command_name)
    if not cmd:
        return JSONResponse(status_code=404, content={"error": "command_not_found"})

    # Check balance before execution
    balance = await billing_service.get_balance(request.user.id)
    if balance < cmd.credit_cost:
        return JSONResponse(
            status_code=402,
            content={
                "error": "insufficient_credits",
                "required": cmd.credit_cost,
                "balance": balance
            }
        )

    # Execute command
    response = await call_next(request)

    # If success, billing already handled in PEV engine
    return response
```

## Stage 2: Command Registry Lookup

```python
# src/commands/registry.py
class CommandRegistry:
    """Singleton registry for command discovery and lookup"""

    _instance: Optional['CommandRegistry'] = None
    _commands: Dict[str, CommandDefinition] = {}
    _plugins: Dict[str, Plugin] = {}
    _cache: LRUCache = LRUCache(maxsize=1000)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get(self, name: str) -> Optional[CommandDefinition]:
        """Get command definition with caching"""
        # L1: in-memory cache
        if name in self._commands:
            return self._commands[name]

        # L2: Redis cache
        cached = await redis.get(f"cmd:{name}")
        if cached:
            cmd = CommandDefinition.from_dict(json.loads(cached))
            self._commands[name] = cmd
            return cmd

        # L3: Database lookup
        row = await db.fetchrow(
            "SELECT * FROM commands WHERE name = $1 AND enabled = true",
            name
        )
        if row:
            cmd = CommandDefinition.from_row(row)
            self._commands[name] = cmd
            await redis.setex(f"cmd:{name}", 3600, json.dumps(cmd.to_dict()))
            return cmd

        return None

    def register_plugin(self, plugin: Plugin):
        """Register all commands from a plugin"""
        self._plugins[plugin.id] = plugin
        for cmd in plugin.commands:
            full_name = f"{plugin.id}:{cmd.name}"
            self._commands[full_name] = cmd
```

## Stage 3: PEV Engine

### Planning Phase

```python
# src/core/pev_engine.py
class PEVEngine:
    """Plan-Execute-Verify orchestration"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def plan(self, command_name: str, args: Dict, context: ExecutionContext) -> ExecutionPlan:
        """Decompose command into executable steps using LLM"""
        cmd = await command_registry.get(command_name)

        prompt = f"""
You are a task planner. Create an execution plan for this command:

Command: {command_name}
Description: {cmd.description}
Arguments: {json.dumps(args, indent=2)}

Return a JSON plan with:
{{
  "steps": [
    {{
      "id": "step_1",
      "description": "What to do",
      "tool": "llm|shell|api|database",
      "params": {{...}},
      "requires_approval": false,
      "critical": true
    }}
  ],
  "estimated_duration": 30,
  "rollback_steps": [...]
}}
"""

        response = await self.llm.chat(prompt, temperature=0.2)
        plan_data = json.loads(response)
        return ExecutionPlan.from_dict(plan_data)

    async def execute(self, plan: ExecutionPlan, context: ExecutionContext) -> ExecutionResult:
        """Execute all steps in order"""
        results = []

        for step in plan.steps:
            # Approval gate
            if step.requires_approval and not context.auto_approve:
                approved = await request_approval(step, context.user_id)
                if not approved:
                    return ExecutionResult(
                        success=False,
                        error="rejected_by_user",
                        step=step.id
                    )

            # Execute step
            result = await self.execute_step(step, context)
            results.append(result)

            # Critical step failure → abort
            if not result.success and step.critical:
                return ExecutionResult(
                    success=False,
                    error=f"step_failed: {step.id}",
                    details=result.error,
                    partial_results=results
                )

        return ExecutionResult(success=True, results=results)

    async def verify(self, result: ExecutionResult, context: ExecutionContext) -> VerificationResult:
        """Verify execution met expectations"""
        if not result.success:
            return VerificationResult(passed=False, issues=["execution_failed"])

        # Run verification checks (LLM-based or deterministic)
        checks = await self.run_verification_checks(result, context)

        if checks.failed:
            # Attempt auto-recovery
            recovery = await self.attempt_recovery(result, checks.issues)
            if recovery.success:
                return VerificationResult(passed=True, recovery=recovery)
            return VerificationResult(passed=False, issues=checks.issues)

        return VerificationResult(passed=True)

    async def run(self, command_name: str, args: Dict, context: ExecutionContext) -> CommandResult:
        """Full PEV cycle"""
        # 1. PLAN
        plan = await self.plan(command_name, args, context)
        context.plan = plan

        # 2. EXECUTE
        exec_result = await self.execute(plan, context)
        if not exec_result.success:
            return CommandResult(
                success=False,
                error=exec_result.error,
                details=exec_result.details
            )

        # 3. VERIFY
        verify_result = await self.verify(exec_result, context)
        if not verify_result.passed:
            return CommandResult(
                success=False,
                error="verification_failed",
                details={"issues": verify_result.issues}
            )

        return CommandResult(success=True, data=verify_result.outputs)
```

### Tool Execution

```python
# src/core/tools.py
class ToolExecutor:
    """Executes different tool types"""

    async def execute(self, step: ExecutionStep, context: ExecutionContext) -> StepResult:
        """Dispatch to appropriate tool handler"""
        if step.tool == "llm":
            return await self.execute_llm(step, context)
        elif step.tool == "shell":
            return await self.execute_shell(step, context)
        elif step.tool == "api":
            return await self.execute_api(step, context)
        elif step.tool == "database":
            return await self.execute_database(step, context)
        else:
            raise ValueError(f"Unknown tool: {step.tool}")

    async def execute_llm(self, step: ExecutionStep, context: ExecutionContext) -> StepResult:
        """Execute LLM with tool calling"""
        response = await context.llm.chat(
            messages=[{"role": "user", "content": step.params["prompt"]}],
            tools=step.params.get("tools", []),
            temperature=step.params.get("temperature", 0.3)
        )

        return StepResult(
            success=True,
            output=response.content,
            tokens_used=response.usage.total_tokens
        )

    async def execute_shell(self, step: ExecutionStep, context: ExecutionContext) -> StepResult:
        """Execute shell command in sandbox"""
        cmd = step.params["command"]
        timeout = step.params.get("timeout", 30)

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/tmp"  # Sandbox directory
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            return StepResult(
                success=proc.returncode == 0,
                output=stdout.decode(),
                error=stderr.decode() if proc.returncode != 0 else None,
                exit_code=proc.returncode
            )
        except asyncio.TimeoutError:
            return StepResult(success=False, error=f"timeout after {timeout}s")

    async def execute_api(self, step: ExecutionStep, context: ExecutionContext) -> StepResult:
        """Make HTTP API call"""
        import httpx

        url = step.params["url"]
        method = step.params.get("method", "GET")
        headers = step.params.get("headers", {})

        # Add authentication if needed
        if "api_key" in step.params:
            headers["Authorization"] = f"Bearer {step.params['api_key']}"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=step.params.get("body"),
                    timeout=30.0
                )
                return StepResult(
                    success=resp.status_code < 400,
                    output=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                    status_code=resp.status_code
                )
            except Exception as e:
                return StepResult(success=False, error=str(e))
```

## Stage 4: Billing Service

### Atomic Credit Deduction

```python
# src/billing/service.py
class BillingService:
    """Handle credit deductions and balance management"""

    async def deduct_credits(
        self,
        user_id: UUID,
        amount: int,
        command_name: str,
        idempotency_key: Optional[str] = None
    ) -> bool:
        """Atomically deduct credits from user balance"""
        async with db.transaction(isolation="serializable") as txn:
            # Lock user subscription row
            sub = await txn.fetchrow(
                """
                SELECT id, current_balance
                FROM user_subscriptions
                WHERE user_id = $1 AND status = 'active'
                FOR UPDATE
                """,
                user_id
            )

            if not sub:
                return False

            if sub['current_balance'] < amount:
                return False

            # Check idempotency (avoid double charge)
            if idempotency_key:
                existing = await txn.fetchval(
                    "SELECT id FROM credit_transactions WHERE idempotency_key = $1",
                    idempotency_key
                )
                if existing:
                    return True  # Already deducted

            # Deduct and record
            new_balance = sub['current_balance'] - amount
            await txn.execute(
                """
                UPDATE user_subscriptions
                SET current_balance = $1, updated_at = NOW()
                WHERE id = $2
                """,
                new_balance, sub['id']
            )

            await txn.execute(
                """
                INSERT INTO credit_transactions
                (user_id, type, amount, balance_after, command_name, idempotency_key)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_id, 'deduction', -amount, new_balance,
                command_name, idempotency_key
            )

        return True

    async def get_balance(self, user_id: UUID) -> int:
        """Get current credit balance"""
        row = await db.fetchval(
            """
            SELECT current_balance
            FROM user_subscriptions
            WHERE user_id = $1 AND status = 'active'
            """,
            user_id
        )
        return row or 0
```

### Payment Webhook Processing

```python
# src/api/webhooks.py
@app.post("/api/v1/webhooks/payment")
async def payment_webhook(request: Request):
    """Handle payment provider webhooks"""
    provider = request.headers.get("X-Provider", "stripe")
    payload = await request.json()
    event_id = payload.get("id")

    # Idempotency check
    existing = await db.fetchval(
        "SELECT id FROM payment_webhooks WHERE provider = $1 AND event_id = $2",
        provider, event_id
    )
    if existing:
        return {"status": "duplicate"}

    # Log webhook
    webhook_id = await db.fetchval(
        """
        INSERT INTO payment_webhooks (provider, event_id, event_type, payload)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        provider, event_id, payload.get("type"), payload
    )

    # Process asynchronously
    await process_webhook.delay(webhook_id)

    return {"status": "received"}
```

## Stage 5: Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    "invoice_id": "inv_abc123",
    "total": 1500,
    "sent_at": "2025-06-20T12:34:56Z"
  },
  "credits_remaining": 48,
  "executed_at": "2025-06-20T12:34:56Z",
  "duration_ms": 1250
}
```

### Error Response

```json
{
  "success": false,
  "error": "insufficient_credits",
  "details": {
    "required": 2,
    "balance": 1
  },
  "credits_remaining": 1
}
```

### Approval Required Response

```json
{
  "status": "awaiting_approval",
  "approval_id": "uuid-here",
  "message": "This command requires approval. Check your dashboard."
}
```

## Component Interaction Diagram

```mermaid
graph TB
    CLI[TypeScript CLI]
    GW[FastAPI Gateway]
    AUTH[Auth Middleware]
    RATE[Rate Limiter]
    BILL[ billing Middleware]
    REG[Command Registry]
    PLUG[Plugin Manager]
    PEV[PEV Engine]
    TOOL[Tool Executor]
    LLM[LLM Provider]
    DB[(PostgreSQL)]
    CACHE[(Redis)]

    CLI -->|HTTPS + JWT| GW
    GW --> AUTH
    AUTH --> DB
    GW --> RATE
    RATE --> CACHE
    GW --> BILL
    BILL --> CACHE
    GW --> REG
    REG --> CACHE
    REG --> DB
    alt Plugin Command
        GW --> PLUG
        PLUG --> PLUG_INST[Plugin Instance]
    end
    GW --> PEV
    PEV --> TOOL
    TOOL --> LLM
    TOOL -->|shell| SHELL[Shell]
    TOOL -->|api| EXTERNAL[External API]
    PEV --> DB
    PEV --> CACHE

    style GW fill:#e1f5fe
    style PEV fill:#f3e5f5
    style PLUG fill:#e8f5e8
    style DB fill:#fff3e0
```

**Legend:**
- **Blue** = Gateway layer (request routing)
- **Purple** = Core engine (orchestration)
- **Green** = Plugin system (extensibility)
- **Orange** = Persistence layer

## Error Handling

### Retry Policy

| Error Type | Retry | Backoff |
|------------|-------|---------|
| LLM timeout | 2 | exponential |
| LLM rate limit | 3 | 1s, 2s, 4s |
| Network error | 2 | exponential |
| Database deadlock | 1 | immediate retry |

### Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_llm_provider(...):
    ...
```

## Monitoring Spans

```python
# OpenTelemetry spans
with tracer.start_as_current_span("command.execute") as span:
    span.set_attribute("command.name", command_name)
    span.set_attribute("user.id", user_id)

    with span.start_span("pev.plan") as plan_span:
        plan = await pev.plan(...)
        plan_span.set_attribute("steps.count", len(plan.steps))

    with span.start_span("pev.execute") as exec_span:
        result = await pev.execute(plan, context)

    with span.start_span("billing.deduct") as bill_span:
        await billing.deduct(...)

    span.set_attribute("credits.cost", cmd.credit_cost)
    span.set_attribute("duration.ms", duration)
    span.set_status(Status(StatusCode.OK))
```

## Related Documents

| Document | Purpose |
|----------|---------|
| [System Architecture](system-architecture.md) | High-level layered architecture overview |
| [Plugin Architecture](plugin-architecture.md) | Plugin system design and isolation |
| [Data Models](data-models.md) | Database schema for command logs, billing |
| [API Specification](api-spec.yaml) | Full OpenAPI spec for command endpoints |
| [ADR Index](adr-index.md) | Architecture decision records |

## Next Steps

1. Implement PEV engine with actual LLM integration
2. Add comprehensive unit tests for each stage
3. Benchmark end-to-end latency (target: <500ms without LLM)
4. Add request tracing with correlation IDs
