# Backend Developer Report — Mekong CLI
*Role: Backend Developer | Date: 2026-03-11*

---

## Backend Architecture Overview

Mekong CLI's backend spans two runtime environments:

1. **Python CLI process** (`src/`) — local execution, PEV engine, agents
2. **Cloudflare Workers** (`apps/`) — edge API, auth gateway, Tôm Hùm daemon

These are deliberately separate: the Python layer handles LLM orchestration and
local tasks; the CF layer handles auth, billing, and async job dispatch.

---

## Python Backend Patterns

### PEV Engine Internals

```python
# src/core/orchestrator.py — simplified flow
class Orchestrator:
    def run(self, goal: str) -> MissionResult:
        steps = self.planner.decompose(goal)          # LLM call
        completed = []
        for step in steps:
            result = self.executor.run(step)          # shell/LLM/API
            if not self.verifier.check(result):       # quality gate
                self.rollback(completed)              # LIFO rollback
                raise MissionFailed(step, result)
            completed.append(step)
        return MissionResult(success=True, steps=completed)

    def rollback(self, completed: list[ExecutionStep]) -> None:
        for step in reversed(completed):              # LIFO order
            if step.params.get("rollback"):
                self.executor.run_rollback(step)
```

### Executor Step Types

```python
# src/core/executor.py — dispatch table
STEP_HANDLERS = {
    "shell":    self._run_shell,     # subprocess.run()
    "llm":      self._run_llm,       # llm_client.complete()
    "file":     self._run_file,      # read/write/delete
    "api":      self._run_api,       # httpx async request
    "parallel": self._run_parallel,  # asyncio.gather()
}
```

Adding a new step type: add handler to `STEP_HANDLERS` + test in `tests/test_executor.py`.

### LLM Client Pattern

```python
# src/core/llm_client.py
class LLMClient:
    def __init__(self):
        self.base_url, self.api_key, self.model = self._resolve_provider()

    def _resolve_provider(self) -> tuple[str, str, str]:
        # Try env vars in priority order
        for key, url in PROVIDER_CHAIN:
            if os.environ.get(key):
                return url, os.environ[key], os.environ.get("LLM_MODEL", DEFAULT_MODEL)
        return OLLAMA_URL, "", OLLAMA_DEFAULT_MODEL  # free local fallback

    async def complete(self, prompt: str, **kwargs) -> str:
        # Single entry point for all LLM calls
        # Add retry here: see tech debt section
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/chat/completions", ...)
            return resp.json()["choices"][0]["message"]["content"]
```

**Critical:** All LLM calls MUST go through this client. No exceptions.

---

## Cloudflare Workers Backend

### raas-gateway (`apps/raas-gateway/index.js`)

Handles: auth validation, MCU balance check, request routing.

```javascript
// Pattern: check balance before execution
export default {
  async fetch(request, env) {
    const user = await validateAuth(request, env);
    if (!user) return new Response("Unauthorized", { status: 401 });

    const balance = await env.KV.get(`credits:${user.id}`);
    if (parseInt(balance) <= 0) {
      return new Response("Payment Required", { status: 402 });
    }

    // Route to mission handler
    return handleMission(request, env, user);
  }
}
```

Key bindings required in `wrangler.toml`:
```toml
kv_namespaces = [{ binding = "KV", id = "..." }]
d1_databases = [{ binding = "DB", database_id = "..." }]
```

### D1 Database Patterns

D1 is SQLite-compatible. Use parameterized queries only — never string interpolation.

```typescript
// Good — parameterized
const result = await env.DB.prepare(
  "SELECT balance FROM credits WHERE user_id = ?"
).bind(userId).first();

// Bad — SQL injection risk
const result = await env.DB.prepare(
  `SELECT balance FROM credits WHERE user_id = '${userId}'`
).first();
```

D1 migrations live in `src/db/migrations/`. Run via:
```bash
wrangler d1 migrations apply mekong-db --remote
```

### KV Cache Patterns (`src/jobs/cloudflare-kv-cache-adapter.ts`)

KV is eventually consistent — suitable for: session tokens, credit balances (with
short TTL), LLM response caches.

```typescript
// Cache LLM response for identical prompts (cost optimization)
const cacheKey = `llm:${hashPrompt(prompt)}`;
const cached = await env.KV.get(cacheKey);
if (cached) return JSON.parse(cached);

const response = await callLLM(prompt);
await env.KV.put(cacheKey, JSON.stringify(response), { expirationTtl: 3600 });
return response;
```

### R2 Storage Patterns (`src/jobs/cloudflare-r2-storage-adapter.ts`)

R2 for: backtest reports, generated artifacts, mission output files.

```typescript
// Store mission artifact
await env.R2.put(`missions/${missionId}/output.json`, JSON.stringify(result));

// Retrieve with presigned URL (7-day expiry)
const url = await env.R2.createPresignedUrl(`missions/${missionId}/output.json`, {
  expiresIn: 604800
});
```

### Queues Pattern (`src/jobs/cloudflare-queues-producer-consumer.ts`)

Tôm Hùm daemon uses CF Queues for mission dispatch:

```typescript
// Producer (API handler)
await env.QUEUE.send({ missionId, goal, userId, priority: "normal" });

// Consumer (Tôm Hùm daemon)
export default {
  async queue(batch: MessageBatch, env: Env) {
    for (const msg of batch.messages) {
      const { missionId, goal } = msg.body;
      await runMission(missionId, goal, env);  // claude -p call
      msg.ack();
    }
  }
}
```

---

## API Design Standards

All API endpoints in `src/api/` follow:

```
POST /v1/missions          — Submit new mission
GET  /v1/missions/{id}     — Get mission status
GET  /v1/missions          — List missions (paginated)
GET  /v1/credits/balance   — Check MCU balance
POST /v1/webhooks/polar    — Polar.sh payment webhook
```

Response format (always):
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2026-03-11T20:29:00Z"
}
```

Error response:
```json
{
  "success": false,
  "data": null,
  "error": { "code": "INSUFFICIENT_CREDITS", "message": "MCU balance is 0" },
  "timestamp": "2026-03-11T20:29:00Z"
}
```

---

## Tech Debt: Backend Priority Items

1. **No retry in `llm_client.py`** — Add `tenacity` with 3 retries, exponential backoff
2. **Untracked CF adapters** — `src/jobs/cloudflare-*.ts` not imported anywhere — integrate or remove
3. **No D1 migration automation** — Must run `wrangler d1 migrations apply` manually post-deploy
4. **KV credit balance race condition** — Use D1 transactions for atomic balance deductions, not KV
5. **No request validation** — Add `zod` schema validation to all CF Worker API endpoints

---

## Q2 Backend Actions

- [ ] Add `tenacity` retry to `llm_client.py` (3 attempts, exponential backoff)
- [ ] Integrate `src/jobs/cloudflare-*.ts` into the CF adapter layer
- [ ] Migrate credit balance from KV → D1 (atomic transactions)
- [ ] Add `zod` validation to all CF Worker API endpoints
- [ ] Automate D1 migration execution in GitHub Actions deploy workflow
- [ ] Add structured logging via `structlog` (Python) and `console.log` JSON (CF Workers)
