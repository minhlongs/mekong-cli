# System Architecture: Mekong CLI v6.0.0 (OpenClaw v2026.4.16)

**Last Updated:** 2026-04-16 | **Status:** Production

### Platform Endpoints

| Service | URL | Type |
|---------|-----|------|
| Landing | www.mekongmind.com | CF Pages (project: mekongmind) |
| Use Cases | www.mekongmind.com/{slug}/ | CF Pages (project: mekongmind) |
| IDE App | ide.mekongmind.com | CF Pages (project: mekong-ide) |
| Guide | www.mekongmind.com/guide/ | CF Pages (project: mekongmind) |
| API Gateway | mekong-engine.mekongmind.workers.dev | Cloudflare Workers (Hono + D1) |
| Webhook | api.cashclaw.cc/webhook/polar | Polar.sh payment events |
| Docs | www.mekongmind.com/docs | CF Pages (project: mekongmind) |
| LLM | localhost:11434 | Ollama (M1 Max, 5 models, 95GB) |

## 1. High-Level Overview

Mekong CLI v6.0 features a 4-phase "Hạt giống → Cây → Rừng → Đất" (Seed → Tree → Forest → Land) architecture. Phase 01-04 (Seed) is complete, establishing the foundation for autonomous agent orchestration with Plan-Execute-Verify (PEV), pluggable LLM providers, parallel task execution via DAG scheduling, and multi-tenant billing.

### Architecture Phases (2026 Roadmap)

**Phase 01 (Seed - COMPLETE):** Local CLI + Python stdlib agents + memory (ChromaDB + SQLite)
**Phase 02 (Tree):** Telegram bot + Web UI (htmx) + single-tenant expansion
**Phase 03 (Forest):** Multi-tenant JWT + Docker isolation + Redis queue
**Phase 04 (Land):** Temporal workflow engine + 5-gate CI/CD + Signals loop + Clipmart

### Architecture Layers

```
┌──────────────────────────────────────────────────────────┐
│              CLI / REST API / Edge Gateway               │
│   (Typer CLI + Hono Router + Cloudflare Workers)       │
│           + RaaS Auth Middleware + Billing              │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│            Orchestration Layer + RaaS Router             │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │   Planner    │ │  Executor    │ │ Verifier + Gate │  │
│  │  (LLM)       │ │ (DAG Sched)  │ │ (Quality Check) │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RaaS Router (/api/v1/missions, /api/v1/tasks)  │   │
│  │  - Mission lifecycle (submit, status, cancel)    │   │
│  │  - Task store (persistent queue)                 │   │
│  │  - Rate limiter (per-tenant fair-use)           │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│        Agent & Provider System + Founder OS             │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ GitAgent     │ │ FileAgent    │ │ Founder OS      │  │
│  │ ShellAgent   │ │ RecipeCrawler│ │ (13 modules)    │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │OpenAIProvider│ │GeminiProvider│ │OfflineProvider │  │
│  │ (circuit-br) │ │ (circuit-br) │ │ (local models) │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ RaaS Auth: JWT validation, Tenant isolation      │  │
│  │ RaaS Billing: Credit ledger, Quota enforcement   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│         Persistence & Billing + Edge Cache              │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │SQLite Store  │ │ Credit Ledger│ │ Mission Journal │  │
│  │(Tenants,     │ │ (per-tenant) │ │ (audit trail)   │  │
│  │Missions)     │ │              │ │                 │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ RaaS Gateway: Cloudflare KV (rate limiting cache) │  │
│  │ Polar.sh Webhooks: payment → license + credit allocation    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│           Health Monitoring System (Phase 1-5)           │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │HealthEndpoint│ │CrashDetector │ │LicenseMonitor   │  │
│  │ (port 9192)  │ │ (exit codes) │ │ (threshold)     │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │AnomalyDetector││AlertRouter   │ │AutoRecovery     │  │
│  │ (Z-score)    │ │ (Telegram)   │ │ (recovery)      │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ EventBus: Real-time event pub/sub                 │  │
│  │ - Health:HEALTH_CRITICAL → AlertRouter            │  │
│  │ - License:LICENSE_CRITICAL → AutoRecovery         │  │
│  │ - Crash:detected → AutoRecovery                   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Architecture Layers

```
┌──────────────────────────────────────────────────────────┐
│              CLI / REST API / Edge Gateway               │
│   (Typer CLI + Hono Router + Cloudflare Workers)       │
│           + RaaS Auth Middleware + Billing              │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│            Orchestration Layer + RaaS Router             │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │   Planner    │ │  Executor    │ │ Verifier + Gate │  │
│  │  (LLM)       │ │ (DAG Sched)  │ │ (Quality Check) │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RaaS Router (/api/v1/missions, /api/v1/tasks)  │   │
│  │  - Mission lifecycle (submit, status, cancel)    │   │
│  │  - Task store (persistent queue)                 │   │
│  │  - Rate limiter (per-tenant fair-use)           │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│        Agent & Provider System + Founder OS             │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ GitAgent     │ │ FileAgent    │ │ Founder OS      │  │
│  │ ShellAgent   │ │ RecipeCrawler│ │ (13 modules)    │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │OpenAIProvider│ │GeminiProvider│ │OfflineProvider │  │
│  │ (circuit-br) │ │ (circuit-br) │ │ (local models) │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ RaaS Auth: JWT validation, Tenant isolation      │  │
│  │ RaaS Billing: Credit ledger, Quota enforcement   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│         Persistence & Billing + Edge Cache              │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │SQLite Store  │ │ Credit Ledger│ │ Mission Journal │  │
│  │(Tenants,     │ │ (per-tenant) │ │ (audit trail)   │  │
│  │Missions)     │ │              │ │                 │  │
│  └──────────────┘ └──────────────┘ └─────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ RaaS Gateway: Cloudflare KV (rate limiting cache) │  │
│  │ Polar.sh Webhooks: payment → license + credit allocation    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 1.5. Seed Layer (Phase 01 - COMPLETE 2026-04-25)

Minimal standalone AI agent runtime using Python stdlib (no external LLM SDKs):

```
┌──────────────────────────────────────────────────────────┐
│  seed/main.py — Entry point (python seed/main.py "task") │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────┐  ┌──────────────────────────┐  │
│  │  Agent Layer         │  │  LLM Router              │  │
│  │  - ceo.py (planning) │  │  - ollama via urllib     │  │
│  │  - developer.py      │  │  - stream-based parsing  │  │
│  │  - tester.py         │  │  - fallback to offline   │  │
│  │  - base.py (base)    │  └──────────────────────────┘  │
│  └──────────────────────┘                                 │
│                                                           │
│  ┌──────────────────────┐  ┌──────────────────────────┐  │
│  │  Memory (Hybrid)     │  │  Tools                   │  │
│  │  - ChromaDB semantic │  │  - file_system.py        │  │
│  │  - SQLite persistence│  │  - browser.py            │  │
│  └──────────────────────┘  └──────────────────────────┘  │
│                                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Config — ENV-based: OLLAMA_BASE_URL, LLM_MODEL     │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Key Design:**
- Pure Python (no requests/httpx) — `urllib` + streaming
- Stdlib-only agents (CEO, Developer, Tester)
- Memory: ChromaDB vectors + SQLite backing
- Config via environment: `OLLAMA_BASE_URL`, `LLM_MODEL`
- Testing: 69 unit tests in `tests/seed/` (mock LLM, no Ollama required)

**Quick Start:**
```bash
export OLLAMA_BASE_URL=http://localhost:11434
python3 seed/main.py "Create a Python script to fetch weather"
```

**Testing:**
```bash
# Run all 69 seed tests (no Ollama needed)
pytest tests/seed/ -v

# Gated in CI/CD via Gate 5 (`.github/workflows/ai-native-ci.yml`)
```

**Files Added (Phase 01):**
- `seed/main.py` — Orchestrator entry point
- `seed/agents/{ceo,developer,tester,base}.py` — Agent implementations + @timed decorator
- `seed/llm_client.py` — Ollama urllib client
- `seed/memory.py` — ChromaDB + SQLite hybrid
- `seed/config.py` — Environment configuration
- `tests/seed/` — 69 unit tests (mock LLM, no Ollama)
- `tools/{file_system,browser}.py` — Capability tools
- `apps/web/mission-control.html` — htmx UI (Phase 02)
- `apps/api/{server,gateway}.py` — FastAPI single/multi-tenant
- `worker/main.py` — Redis queue worker
- `integrations/telegram_bot.py` — Telegram integration (Phase 02)
- `observability/agent_metrics.py` — Metrics decorator + observability
- `feedback/signals_loop.py` — Weekly LLM analysis
- `clipmart/marketplace_api.py` — Agent template marketplace
- `.github/workflows/ai-native-ci.yml` — 5-gate CI/CD (Gate 5 runs pytest)
- `docker-compose.seed.yml` + `Dockerfile.seed` — Containerization (copies seed/ tools/ worker/ apps/ integrations/ clipmart/ observability/ feedback/)
- `requirements.seed.txt` — Dependencies (chromadb, fastapi, uvicorn, redis, pytest)

## 2. Core Modules

### 2.1 Orchestrator (`src/core/orchestrator.py`)

Coordinates Plan → Execute → Verify pipeline:

1. **Plan** — LLM decomposes goal into ordered steps with dependencies
2. **Execute** — DAG scheduler runs steps in parallel (respecting dependencies)
3. **Verify** — Quality gate validates results (type checks, tests, assertions)
4. **Rollback** — Failed verification reverses completed steps atomically

**Key Methods:**
- `cook(goal: str) → ExecutionResult` — Full PEV pipeline
- `plan(goal: str) → Recipe` — Planning only (dry-run)
- `execute_recipe(recipe: Recipe) → ExecutionResult` — Run pre-planned recipe

### 2.2 Planner (`src/core/planner.py`)

LLM-powered task decomposition:

- Input: High-level goal (string)
- Output: Recipe (structured steps with dependencies)
- Process: Sends goal to LLM provider, parses response into Task objects
- Fallback: Generates fallback recipe if LLM fails

**Recipe Structure:**
```python
@dataclass
class Recipe:
    goal: str
    steps: List[RecipeStep]
    total_credits: int

@dataclass
class RecipeStep:
    order: int  # Execution order
    dependencies: List[int]  # Task IDs this depends on
    description: str
    cmd: str  # Shell, LLM, or API mode
    verify: Dict[str, str]  # Verification checks
```

### 2.3 Executor (`src/core/executor.py`)

Multi-mode task runner:

- **Shell Mode** — Runs `bash` or `sh` commands (default subprocess, or isolated Docker when `FOREST_WORKER_EXECUTOR=docker`)
- **LLM Mode** — Sends prompts to LLM provider
- **API Mode** — Calls HTTP endpoints (future)
- **Agent Mode** — Dispatches to registered agents

**Docker Isolation (Phase 3 Land):** Agent-forest workers can execute inside isolated Docker containers via env vars `FOREST_WORKER_EXECUTOR`, `FOREST_DOCKER_IMAGE` (default `agent-core:latest`), and `FOREST_DOCKER_TIMEOUT_SECONDS` (default 300). Non-root uid 1000, requires `docker>=7` extra.

**Execution Result:**
```python
@dataclass
class ExecutionResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    metadata: Dict
```

### 2.4 DAG Scheduler (`src/core/dag_scheduler.py`)

Parallel task execution with dependency management:

- **Topological Sort** — Identifies ready steps (all deps completed)
- **Thread Pool** — Runs independent steps concurrently (default 4 workers)
- **Failure Handling** — Marks failed steps, cancels downstream dependents
- **Timeout** — Per-step timeout (default 30s)

**Execution Timeline:**
```
Step 1 (order=1):       ↓  (no deps)
Step 2 (deps=[1]):  ─────↓  (waits for 1)
Step 3 (deps=[1]):  ─────↓  (parallel with 2)
```

### 2.5 Verifier (`src/core/verifier.py`)

Quality gate validation:

- **Exit Code Checks** — Verify exit code matches expected
- **File Checks** — Assert files exist/don't exist
- **Content Checks** — Pattern matching in output
- **LLM Assessment** — Re-run verification via LLM (expensive, optional)

**Failed verification triggers rollback:**
```python
if not verified:
    orchestrator.rollback(completed_steps)
    return ExecutionResult(success=False, ...)
```

### 2.6 LLM Provider System (`src/core/providers.py`)

Abstract LLM interface with pluggable backends:

**Provider Interface:**
```python
class LLMProvider(ABC):
    @property
    def name(self) -> str: ...

    def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False
    ) -> LLMResponse: ...
```

**Built-in Providers:**
1. **OpenAICompatibleProvider** — Works with OpenAI API and compatible services
2. **GeminiProvider** — Google Gemini API
3. **OfflineProvider** — Local models (via Ollama/LlamaCPP)

**Local LLM Configuration (M1 Max):**
- **Endpoint:** 192.168.11.111:11434 (Ollama)
- **Models Deployed:**
  - qwen2.5-coder:32b (coding tasks)
  - qwen3:32b (reasoning tasks)
- **Usage:** Fallback provider when cloud API unavailable

**Failover Strategy:**
- Primary provider unavailable → Try next in chain
- Circuit breaker (quota errors) → Backoff + retry other providers
- All providers down → Return error to user

### 2.7 Agent Protocol (`src/core/protocols.py`)

Runtime-checkable interface for pluggable agents:

```python
class AgentProtocol(Protocol):
    @property
    def name(self) -> str: ...

    def plan(self, input: str) -> List[Task]:
        """Decompose goal into tasks"""

    def execute(self, task: Task) -> Result:
        """Execute single task"""

    def verify(self, result: Result) -> bool:
        """Validate result"""

    def execute_stream(self, task: Task) -> Iterator[str]:
        """Optional: streaming output"""
```

**Built-in Agents:**
- `GitAgent` — Git operations (status, diff, commit, branch)
- `FileAgent` — File operations (find, read, tree, grep)
- `ShellAgent` — Shell command execution
- `RecipeCrawler` — Recipe file discovery

### 2.8 Agent Registry & Plugin System

**Agent Registry (`src/agents/__init__.py`):**
Global registry with 10 built-in agents:

| Agent | Key | Description |
|-------|-----|-------------|
| GitAgent | `git` | Git operations (commit, push, branch) |
| FileAgent | `file` | File operations (read, write, delete) |
| ShellAgent | `shell` | Shell command execution |
| DatabaseAgent | `database`, `db` | Database operations |
| LeadHunter | `lead` | Lead discovery & scraping |
| ContentWriter | `content` | Content generation |
| RecipeCrawler | `crawler` | Recipe file discovery |
| WorkspaceAgent | `workspace`, `google` | Google Workspace integration |
| MonitorAgent | `monitor` | System monitoring |
| NetworkAgent | `network` | Network operations |

**Registration Pattern:**
```python
# src/agents/__init__.py
registry = AgentRegistry()
registry.register("git", GitAgent)
registry.register("file", FileAgent)
# ... 10 agents total
```

**Plugin System (`src/core/plugin_loader.py`):**
Discover and load custom agents/providers:

**Discovery Methods:**
1. **Entry Points** — PyPI packages with `[project.entry-points."mekong.agents"]`
2. **Local Plugins** — `.py` files in `~/.mekong/plugins/`

**Plugin Registration:**
```python
# ~/.mekong/plugins/my_agent.py
class MyAgent:
    name = "my-agent"
    def plan(self, input: str) -> List[Task]: ...
    def execute(self, task: Task) -> Result: ...
    def verify(self, result: Result) -> bool: ...

def register(registry):
    registry.register("my-agent", MyAgent)
```

**Plugin Validator (`src/core/plugin_validator.py`):**
AST-based security scanning:

- **Dangerous Imports:** Blocks `subprocess`, `os.system`, `eval`, `exec`, `__import__`, `pickle`, `marshal`
- **Secret Detection:** Regex scan for hardcoded API keys, tokens, passwords
- **Validation Result:** `PluginValidationResult(is_safe: bool, errors: List[str], warnings: List[str])`

**Safety:** Plugin failures logged as warnings (never crash CLI)

### 2.8a RaaS Plugin (`plugins/mekong-raas/`)

Tenant authentication, credit metering, and billing middleware for Cloudflare Workers deployment:

**Components:**
- `tenant-auth.ts` — JWT validation, tenant context extraction, API key rotation
- `credit-meter.ts` — Per-tenant credit ledger, quota enforcement, usage tracking
- `billing-logger.ts` — Audit trail for all missions, webhook logging, reconciliation
- `types.ts` — TenantContext, BillingRecord, CreditMeterage interfaces
- `index.ts` — Worker middleware chain for request/response transformation

**Workflow:**
1. Request arrives with Authorization header
2. `tenant-auth` validates JWT → extracts tenant_id
3. `credit-meter` checks balance → reserves credits
4. Mission executes
5. `billing-logger` records completion → deducts credits

**Integration Point:** Wrapped around `/api/v1/missions` and `/api/v1/tasks` endpoints

### 2.8b Tasks DAG Plugin (`plugins/mekong-tasks/`)

Background task scheduling via DAG recipe executor for asynchronous mission execution:

**Components:**
- `dag-executor.ts` — Parallel task scheduling with dependency resolution
- `dag-step-runner.ts` — Individual step execution with retries and timeouts
- `recipe-loader.ts` — YAML recipe loading and validation
- `recipe-to-steps.ts` — Recipe dependency graph transformation to DAG steps
- `types.ts` — RecipeNode, DAGStep, ExecutionContext, StepStatus interfaces
- `index.ts` — Task queue processor and lifecycle manager

**Workflow:**
1. Mission creates Recipe with steps + dependencies
2. `recipe-to-steps` converts to DAG representation
3. `dag-executor` schedules steps (respects dependencies, runs parallel independents)
4. `dag-step-runner` executes each step with circuit breaker
5. Status updates published to mission journal (audit trail)

**Integration Point:** `POST /api/v1/tasks` enqueues recipes; `GET /api/v1/tasks/:id` polls status

### 2.8c Skills/Mekong Package (`skills/mekong/`)

Multi-department command catalog with 22 ClawHub packages for enterprise team structures:

**Structure:**
- `SKILL.md` — Skill meta-definition (discovery, dependencies, SLAs)
- `manifest.json` — 348 commands across 22 departments + free/paid tier breakdown
- `clawhub-packages/` — 22 JSON configs (audit, board, business, corpdev, data, devops, engineering, esg, finance, founder, hr, intel, intl, ipo, legal, marketing, ops, product, risk, sales, security, studio)
- `packages/` — Individual department package definitions (26 files)

**Department Breakdown:**
- **Business Ops:** finance, sales, marketing, hr, legal (5 free commands each, 25 total)
- **Technical Ops:** engineering (8 free), devops (5 free), data (5 free), security (5 free), product (5 free) = 28 free
- **Strategy:** studio (3 free), founder (3 free), ipo (2 free), intel (3 free) = 11 free
- **Other:** audit, board, corpdev, esg, intl, risk (5 free each) = 30 free
- **Total:** 348 commands, 117 free (PLG tier), 231 premium (paid)

**Usage:** `mekong list skills` displays all 22 departments; `mekong run studio/announce` executes studio command

### 2.9 Credit System (`src/raas/`)

Multi-tenant billing with SQLite backend:

**Components:**
- `tenant.py` — Tenant management (create, list, rotate API keys)
- `credits.py` — Credit ledger (add, deduct, check balance)
- `missions.py` — Mission lifecycle (create, execute, complete, cancel)
- `billing.py` — Polar.sh webhook receiver
- `sdk.py` — Python client SDK
- `rate_limiter.py` — Fair-use rate limiting per tenant

**Credit Model:**
| Complexity | Cost | Example |
|-----------|------|---------|
| Simple | 1 | Single file edit |
| Standard | 3 | Multi-step feature |
| Complex | 5 | Full-stack with tests |

**Workflow:**
1. User creates tenant → gets API key
2. User purchases credits via Polar.sh checkout
3. User submits mission via API
4. Mission plan estimates credits → reserved
5. Execution completes → credits deducted
6. Failed execution → credits refunded

### 2.9a Use-Case Tenant System (Marketing Personas)

**Purpose:** Single Mekong IDE product with 13 customizable landing pages + department filtering for different use cases.

**Architecture:**
- **Use-case tenants** (marketing personas): JSON configs in `tenants/` directory
- **Billing tenants** (payment accounts): SQLite database (separate from use-case tenants)
- **Orthogonal systems**: Use-case persona filtering is independent from billing auth

**Use-Case Tenants (13 Personas):**
```
├── trading-desk.json          # Algorithmic trading
├── model-router.json          # LLM provider management
├── content-studio.json        # Content generation & publishing
├── legal-counsel.json         # Legal document automation
├── dev-agency.json            # Software development teams
├── growth-engine.json         # Growth & marketing ops
├── compliance-vault.json      # Regulatory compliance
├── business-intelligence.json # Data analytics & reporting
├── hr-operations.json         # Human resources management
├── sales-operations.json      # Sales automation & CRM
├── design-studio.json         # Design & creative tools
├── venture-studio.json        # Venture capital operations
└── operations-center.json     # Business operations hub
```

**Components:**
- `src/api/tenant_config_loader.py` — LRU-cached JSON loader with schema validation
- `src/raas/tenant_use_case_router.py` — API endpoints for tenant data
- `landing/` — Jinja2 template + Python build script for 13 static pages
- `landing/dist/` — Generated landing pages (one per tenant + hub index)
- `.github/workflows/deploy-landing.yml` — CF Pages auto-deploy on tenant changes

**Config Schema** (`tenants/_schema.json`):
```json
{
  "name": "AI Trading Desk",
  "slug": "trading-desk",
  "tagline": "Algo-trading with AI agents",
  "description": "Run quantitative analysis, backtest strategies...",
  "featured_departments": ["finance", "analyst", "data"],
  "featured_commands": ["finance-budget-plan", "analyst-report", ...],
  "branding": {
    "accent_color": "#10B981",
    "icon": "chart-line"
  },
  "limits": {
    "max_credits_per_mission": 5,
    "default_model": "auto"
  },
  "polar_checkout_url": null,
  "target_audience": "Algo-traders and quant teams",
  "use_cases": [
    "Backtest trading strategies with AI analysis",
    "Generate daily P&L and risk reports"
  ]
}
```

**API Endpoints:**
```
GET    /v1/tenants                  # List all 13 use-case tenants
GET    /v1/tenants/{slug}           # Get tenant config by slug
GET    /v1/departments?tenant=slug  # List departments for tenant
GET    /v1/pricing?tenant=slug      # Pricing with tenant-specific checkout URL
```

**Landing Page Flow:**
1. User visits `mekongmind.com` → hub page (13 tenant cards)
2. Clicks tenant card → redirects to `mekongmind.com/use-cases/{slug}/`
3. Tenant landing page renders with personalized departments + pricing
4. Clicks "Subscribe" → Polar.sh with tenant-specific checkout URL
5. After payment → onboard to billing tenant (separate from use-case)

**Build Process:**
1. `landing/build.py` loads all `tenants/*.json` configs
2. For each tenant:
   - Renders `landing/template.html` with tenant context
   - Writes to `landing/dist/{slug}/index.html`
3. Generates hub page at `landing/dist/index.html`
4. Creates `_redirects` file for Cloudflare Pages clean URLs
5. GitHub Actions deploys to CF Pages on push to `tenants/` or `landing/`

**Key Design Decisions:**
- **Static generation** — All pages built at deploy time (no runtime rendering)
- **JSON-driven** — Add new persona by creating `tenants/{slug}.json` + redeploying
- **Orthogonal** — Use-case tenants don't create database records; only for UX filtering
- **Billing separation** — Polar payment creates *billing* tenant, not use-case tenant
- **No runtime cost** — Pages served directly from CF Pages (no serverless compute)

### 2.10 RaaS API Layer (`src/api/`)

Production-grade REST API with authentication & billing enforcement:

**Components:**
- `raas_router.py` — Mission endpoints (POST /api/v1/missions, GET /api/v1/missions/:id)
- `raas_task_models.py` — Pydantic schemas (MissionRequest, TaskResponse, etc.)
- `raas_task_store.py` — Persistent task queue (FIFO, transactional)
- `raas_auth_middleware.py` — JWT validation + tenant extraction
- `raas_billing_middleware.py` — Credit reservation & quota enforcement
- `raas_billing_service.py` — MCU metering + plan management

**API Endpoints:**
```
POST   /api/v1/missions         # Submit goal, estimate credits
GET    /api/v1/missions/:id     # Get mission status + result
DELETE /api/v1/missions/:id     # Cancel mission (refund credits)
GET    /api/v1/tasks            # List pending tasks (rate-limited)
POST   /api/v1/tasks/:id/result # Worker submits completion
GET    /api/v1/billing/usage    # Get tenant usage metrics
```

**MCU (Mission Complexity Unit) Pricing:**
| MCU Range | Cost (credits) | Complexity |
|-----------|---|---|
| 1-10 MCU | 1 | Simple (single step) |
| 11-30 MCU | 3 | Standard (multi-step) |
| 31-60 MCU | 5 | Complex (parallel tasks) |
| 61+ MCU | 8 | Critical (advanced) |

**Billing Tiers:**
- Starter: 200 MCU/month, $49/mo (via Polar.sh)
- Growth: 1,000 MCU/month, $149/mo (via Polar.sh)
- Pro: 5,000 MCU/month, $499/mo (via Polar.sh)

### 2.11 RaaS Gateway (`apps/raas-gateway/`)

Cloudflare Workers edge gateway with distributed rate limiting:

**Features:**
- **Edge Auth** — JWT validation at Cloudflare edge (before reaching origin)
- **KV Rate Limiter** — Distributed rate limiting cache (Cloudflare KV)
- **Webhook Handler** — Polar.sh payment events → license + credit allocation
- **Edge Computing** — Process requests globally without database latency

**Architecture:**
```
Client
  ↓ (request + JWT)
Cloudflare Edge (auth + rate limit)
  ├─ Valid JWT + within quota → route to origin
  └─ Invalid/rate-limited → reject immediately (no origin hit)
```

**Webhook Flow:**
```
Polar.sh subscription.created
  → POST /webhook/polar
  → Verify HMAC-SHA256 signature + timestamp
  → Generate license key + allocate credits
  → Return 200 (idempotent)
```

### 2.12 Founder Complete OS (`src/core/founder_*/`)

End-to-end founder toolkit covering full company lifecycle from inception to post-IPO operations.

**Components:**

**A. VC Module** (`src/core/founder_vc/`) — 5 modules:
- `founder_vc_bootstrap.py` — Pre-seed/seed deck creation, angel outreach, SAFEs
- `founder_vc_term_sheet.py` — Term sheet analysis, valuation negotiation, equity modeling
- `founder_vc_cap_table.py` — Cap table management, dilution modeling, ESOP allocation
- `founder_vc_negotiate.py` — Deal negotiation strategies, investor relations
- `founder_vc_map.py` — VC landscape mapping, fund discovery, pattern matching

**B. Secondary Markets** (`src/core/founder_secondary.py`) — 1 module:
- Secondary stock sales, liquidity events, employee buyback planning

**C. IPO Module** (`src/core/founder_ipo/`) — 7 modules + 3 data files:
- `founder_pre_ipo.py` + `founder_pre_ipo_data.py` — Pre-IPO prep, audit readiness
- `founder_s1.py` + `founder_s1_data.py` — S-1 narrative, MD&A, risk disclosure
- `founder_roadshow.py` + `founder_roadshow_data.py` — Investor roadshow planning
- `founder_ipo_day.py` — IPO day logistics, lock-up periods
- `founder_public_co.py` — Public company compliance (SOX, quarterly reporting)
- `founder_insider.py` — Insider trading windows, Form 4 filings
- `founder_succession.py` — CEO succession planning, board evolution

**D. Operational Modules** (root level) — 6 modules:
- `founder_validate.py` — Startup validation, PMF assessment
- `founder_pitch.py` — Pitch deck generation, investor positioning
- `founder_hire.py` — Hiring playbooks, comp benchmarking
- `founder_grow.py` — Growth strategy, unit economics, LTV/CAC
- `founder_brand.py` — Brand positioning, GTM narratives
- `founder_week.py` — Weekly planning, KPI tracking, governance

**Test Coverage:** 146 tests across all modules covering:
- VC funding scenarios and term sheet negotiations
- Cap table dilution and equity modeling
- Pre-IPO compliance and disclosure requirements
- IPO roadshow and pricing strategies
- Post-IPO governance and investor relations
- Hiring, growth, and operational KPIs

**Key Features:**
- LLM-powered analysis and recommendation generation
- Real-world templates (term sheets, pitch decks, S-1 sections)
- Interactive negotiation simulations
- Compliance validation against SEC rules
- Historical precedent matching for benchmarking

### 2.13 Mekong Engine (`packages/mekong-engine/`)

Serverless PEV engine running on Cloudflare Workers, exposing core Mekong functionality as a production-grade API.

**Stack:**
- **Runtime:** Cloudflare Workers (TypeScript)
- **Framework:** Hono.js (lightweight HTTP router)
- **Database:** Cloudflare D1 (SQLite)
- **Cache:** Cloudflare KV (distributed rate limiting)
- **LLM:** Workers AI (Llama 3.1 8B) + OpenAI-compatible fallback

**Production URL:** `https://mekong-engine.mekongmind.workers.dev`

**Core Features:**
1. **PEV Pipeline** — `/cmd` endpoint for direct PEV execution (no auth)
2. **RaaS API** — `/v1/tasks/*` for multi-tenant missions with streaming
3. **Agent Operations** — `/v1/agents/:name/run` for direct agent dispatch
4. **Billing Integration** — `/billing/webhook/polar` for payment events
5. **Rate Limiting** — Per-tenant quotas via Cloudflare KV

**Key Endpoints:**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/cmd` | PEV pipeline (public) |
| POST | `/v1/tasks` | Create mission |
| GET | `/v1/tasks/:id` | Get mission status |
| GET | `/v1/tasks/:id/stream` | Stream updates (SSE) |
| POST | `/v1/tasks/:id/cancel` | Cancel mission |
| POST | `/v1/agents/:name/run` | Run agent |
| GET | `/v1/agents` | List agents |
| POST | `/billing/webhook/polar` | Polar payment webhook |
| GET | `/billing/plans` | List subscription plans |

**Database:** 3 tables (tenants, credits, missions) — same schema as RaaS backend, optimized for Cloudflare D1.

**Authentication:** Bearer token (API key) → SHA-256 hash lookup in tenants table.

**Rate Limiting:** Cloudflare KV stores per-tenant quota state. Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

**Deployment:** `wrangler deploy` from `packages/mekong-engine/`. Bindings (D1, KV, AI) configured in `wrangler.toml`.

### 2.14 Dashboard App (`apps/dashboard/`)

Single-page analytics dashboard for monitoring onboarding metrics and user engagement. Built with modern frontend stack.

**Stack:**
- **Runtime:** Vite (dev) / Static hosting (prod)
- **Framework:** React 19 + React Router v7
- **Styling:** Tailwind CSS v4
- **Charting:** Recharts (charts, funnels, tables)
- **Language:** TypeScript 5.6
- **Deployment:** Cloudflare Pages / `wrangler pages deploy`

**Features:**
1. **Onboarding Analytics** (`/onboarding/analytics`) — Comprehensive user journey metrics
   - Funnel chart: Step-by-step conversion visualization
   - Conversion metrics: Stage-wise conversion rates with trends
   - Drop-off analysis: Identify abandonment points
   - Time-to-complete: Distribution of onboarding duration
   - Cohort analysis: Daily/weekly/monthly retention metrics
2. **Time Period Controls** — 30/60/90-day lookback windows
3. **Real-time Data** — Parallel API calls for efficient loading

**API Client** (`lib/analytics-client.ts`):
- Type-safe endpoints for analytics queries
- Async data fetching with error handling
- Support for multiple time periods and cohort groupings

**Build & Deploy:**
```bash
# Development
cd apps/dashboard && npm run dev

# Production build
npm run build && npm run deploy
```

**Endpoints Consumed:**
- `GET /analytics/funnel` — User conversion funnel data
- `GET /analytics/conversion-rates` — Stage conversion percentages
- `GET /analytics/dropoffs` — Abandonment point analysis
- `GET /analytics/time-to-complete` — Duration metrics
- `GET /analytics/cohorts` — Cohort retention data

## 3. Data Flow

### Full PEV Pipeline

```
User Input ("Create a FastAPI app")
    ↓
Orchestrator.cook()
    ↓
├─ PLAN: Planner → LLM → Recipe
│  (5 steps identified)
│
├─ EXECUTE: DAG Scheduler
│  ├─ Step 1: mkdir src/      (order=1)
│  ├─ Step 2: create main.py  (order=2, deps=[1])
│  ├─ Step 3: add routes      (order=3, deps=[2])
│  ├─ Step 4: write tests     (order=3, deps=[2], parallel)
│  └─ Step 5: verify build    (order=4, deps=[3,4])
│
├─ VERIFY: Verifier
│  ├─ Check: pytest passes
│  ├─ Check: mypy clean
│  └─ Check: type-coverage > 90%
│
└─ RESULT: ExecutionResult
   success=True, credits_used=3
```

### API Mission Workflow

```
POST /missions {"goal": "Build landing page"}
    ↓
Tenant → Credit check → Plan (estimate cost)
    ↓
Reserve credits → Execute pipeline
    ↓
ON SUCCESS: Deduct credits → Return result
ON FAILURE: Refund credits → Return error
```

## 4. Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_BASE_URL` | `http://localhost:9191` | LLM provider endpoint |
| `LLM_PROVIDER` | `openai` | Active provider (openai/gemini/offline) |
| `LLM_API_KEY` | (required) | API key for provider |
| `MEKONG_PLUGIN_DIR` | `~/.mekong/plugins/` | Local plugin directory |
| `RAAS_DB_PATH` | `~/.mekong/raas/tenants.db` | SQLite database path |
| `LOG_LEVEL` | `info` | Logging level (debug/info/warning/error) |
| `CF_API_TOKEN` | (optional) | For Cloudflare Pages/Workers deployments |

### Database Schema

**tenants table:**
```
id, name, api_key, created_at, credits_balance
```

**missions table:**
```
id, tenant_id, goal, status, credits_cost,
result, created_at, completed_at
```

**credit_ledger table:**
```
id, tenant_id, amount, transaction_type,
description, created_at
```

## 5. Deployment

### Local Development
```bash
pip install -e .
mekong cook "Create a Python calculator"
```

### API Server
```bash
uvicorn src.core.gateway:app --host 0.0.0.0 --port 8000
```

### Docker (Optional)
```bash
docker build -t mekong-cli .
docker run -e LLM_API_KEY=sk-... mekong-cli mekong cook "goal"
```

## 6. Extension Points

### Adding a Custom Agent
```python
# ~/.mekong/plugins/my_research_agent.py
class ResearchAgent:
    name = "research"

    def plan(self, input: str) -> List[Task]:
        return [Task(description=f"Research: {input}")]

    def execute(self, task: Task) -> Result:
        # Call search API, return results
        return Result(success=True, output="...")

    def verify(self, result: Result) -> bool:
        return len(result.output) > 100

def register(registry):
    registry.register("research", ResearchAgent)
```

### Adding a Custom Provider
```python
# src/core/custom_provider.py
from src.core.providers import LLMProvider, LLMResponse

class CustomProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "custom"

    def chat(self, messages, model, **kwargs) -> LLMResponse:
        # Your implementation
        return LLMResponse(content="...", model=model)
```

## 7. Performance Characteristics

| Operation | Target | Actual |
|-----------|--------|--------|
| CLI startup | < 1s | ~0.8s |
| Plan generation | < 2s | ~1.5s |
| Execute simple step | < 5s | ~2s |
| Execute complex step | < 30s | ~15s |
| Verify + rollback | < 5s | ~2s |
| Database query | < 100ms | ~50ms |

## 8. Memory Architecture

- **Context Management**: `src/core/context_manager.py` maintains conversation context across interactions
- **Prompt Caching**: `src/core/prompt_cache.py` provides intelligent prompt caching with similarity matching
- **Learning Tracking**: `src/core/learning_tracker.py` tracks AI learning patterns and identifies knowledge gaps
- **Cross-Session Intelligence**: `src/core/cross_session_intelligence.py` maintains intelligence across different sessions
- **Decision Making**: `src/core/decision_maker.py` enhances decision-making with historical context and precedents
- **Fallback Mechanisms**: All modules implement dual storage (vector + local file backup) for robustness
- **User Isolation**: Each module properly scopes data by user_id for tenant isolation
- **Integration**: Seamlessly integrates with existing MemoryFacade system

## 9. Security Considerations

- **Secrets**: No API keys in source code (via env vars)
- **Input Validation**: All inputs validated with Pydantic
- **Type Safety**: 100% type hints, zero `any` types
- **Audit Trail**: All missions logged with tenant isolation
- **Isolation**: Multi-tenant credit system prevents cross-tenant access

## 10. Authentication Layer

### 10.1 Overview

The authentication layer implements OAuth2-based user authentication with JWT session management, RBAC for authorization, and Stripe integration for subscription-based role provisioning.

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Layer                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────┐    ┌───────────────────────────┐   │
│  │   OAuth2 Providers  │    │   JWT Session Manager     │   │
│  │  - GoogleOAuth2     │    │   - Token generation      │   │
│  │  - GitHubOAuth2     │    │   - Token validation      │   │
│  │  - PKCE Support     │    │   - Cookie management     │   │
│  └─────────┬───────────┘    └───────────────────────────┘   │
│            │                                                  │
│            │            ┌───────────────────────────┐       │
│            └────────────►   User Repository        ────────┘
│                         │   - User CRUD             │
│                         │   - Session tracking      │
│                         └───────────────────────────┘
│
│  ┌───────────────────────────────────────────────────────┐
│  │              RBAC Middleware                          │
│  │  - Role hierarchy enforcement                         │
│  │  - Permission decorators                              │
│  │  - Request context injection                          │
│  └───────────────────────────────────────────────────────┘
│
│  ┌───────────────────────────────────────────────────────┐
│  │         Stripe Webhook Integration                    │
│  │  - Subscription event handling                        │
│  │  - Role auto-provisioning                             │
│  │  - Webhook signature verification                     │
│  └───────────────────────────────────────────────────────┘
│
└─────────────────────────────────────────────────────────────┘
```

### 10.2 OAuth2 Providers

#### Google OAuth2
- Uses OAuth2 authorization code flow with PKCE
- Scopes: `openid`, `email`, `profile`
- Offline access for refresh tokens

#### GitHub OAuth2
- OAuth2 authorization code flow
- Requests `user:email` scope
- Primary email fallback if available

### 10.3 Session Management

```
┌─────────────────────────────────────────────────────────────┐
│                   Session Flow                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. User Authentication → 2. Generate JWT Tokens            │
│     Users id, email, role →    - Access token (30min)       │
│     → 3. Create UserSession                       →          │
│     - Access token hash                           →          │
│     - Expires at (7 days)                         →          │
│     → 4. Store in DB + Set HTTPOnly Cookie                  │
│                                                               │
│  Token Format (JWT):                                         │
│  {                                                            │
│    "sub": "user-uuid",                                       │
│    "email": "user@example.com",                              │
│    "role": "member",                                         │
│    "type": "access",                                         │
│    "iat": timestamp,                                         │
│    "exp": timestamp,                                         │
│    "jti": "unique-token-id"                                  │
│  }                                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Session Features
- **HTTPOnly Cookie**: Prevents XSS token theft
- **JWT Signature**: Tamper-proof token validation
- **Database Backed**: Revocable sessions
- **Refresh Token**: Extend sessions without re-authentication

### 10.4 RBAC Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RBAC Layer                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  RoleHierarchy:                                              │
│    owner ──► admin ──► member ──► viewer                    │
│    (inherited permissions)                                   │
│                                                               │
│  PermissionMatrix:                                           │
│    - VIEW_DASHBOARD (all roles)                              │
│    - EXPORT_DATA (owner, admin, member)                     │
│    - CREATE_RESOURCES (owner, admin, member)                │
│    - UPDATE_RESOURCES (owner, admin, member)                │
│    - DELETE_RESOURCES (owner, admin)                         │
│    - MANAGE_USERS (owner, admin)                             │
│    - MANAGE_BILLING (owner)                                  │
│    - SYSTEM_CONFIG (owner)                                   │
│                                                               │
│  Decorators:                                                 │
│    - @require_role(Role.ADMIN, Role.OWNER)                  │
│    - @require_permission(Permission.MANAGE_USERS)           │
│    - get_current_user(request) → user info                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Role Hierarchy
| Role | Inherits | Max Permissions |
|------|----------|-----------------|
| owner | admin, member, viewer | All |
| admin | member, viewer | Delete, Manage Users, Settings |
| member | viewer | Create, Update, Export |
| viewer | none | View only |

### 10.5 Stripe Integration

```
┌─────────────────────────────────────────────────────────────┐
│              Stripe Webhook Flow                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Stripe (Subscription Event)                                │
│     ↓ (POST /webhooks/stripe + signature)                  │
│  ┌────────────────────────────────┐                         │
│  │  Verify Webhook Signature      │                         │
│  └──────────────┬─────────────────┘                         │
│                 ↓                                            │
│  ┌────────────────────────────────┐                         │
│  │  Parse Event Data              │                         │
│  │  - event_type                  │                         │
│  │  - price_id                    │                         │
│  │  - customer_info               │                         │
│  └──────────────┬─────────────────┘                         │
│                 ↓                                            │
│  ┌────────────────────────────────┐                         │
│  │  Map Price ID → Role           │                         │
│  │  price_pro → admin             │                         │
│  │  price_trial → member          │                         │
│  │  price_free → viewer           │                         │
│  └──────────────┬─────────────────┘                         │
│                 ↓                                            │
│  ┌────────────────────────────────┐                         │
│  │  Update User Role in DB        │                         │
│  └──────────────┬─────────────────┘                         │
│                 ↓                                            │
│  ┌────────────────────────────────┐                         │
│  │  Return 200 OK                 │                         │
│  └────────────────────────────────┘                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Supported Events
| Event | Action |
|-------|--------|
| `customer.subscription.created` | Provision role from price tier |
| `customer.subscription.updated` | Update role if price tier changed |
| `customer.subscription.deleted` | Downgrade to `viewer` |
| `customer.deleted` | Revoke access |

#### Webhook Verification
- HMAC SHA-256 signature verification
- Timestamp validation
- Idempotency handling (prevent duplicate processing)

### 10.6 Security Measures

1. **OAuth2 Security**
   - PKCE code challenge/verifier for public clients
   - State parameter CSRF protection
   - Redirect URI validation

2. **JWT Security**
   - HS256 signature with server-side secret
   - Token blacklist via UserSession table
   - Expiration enforcement

3. **Cookie Security**
   - `HttpOnly`: Prevents JavaScript access
   - `Secure`: HTTPS-only in production
   - `SameSite`: mitigates CSRF attacks

4. **Stripe Security**
   - Webhook signature verification
   - Event type validation
   - Idempotent webhook processing

### 10.7 API Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/auth/login` | Render login page | No |
| POST | `/auth/dev-login` | Dev mode quick login | Dev only |
| GET | `/auth/google/login` | Initiate Google OAuth | No |
| GET | `/auth/google/callback` | Google OAuth callback | No |
| GET | `/auth/github/login` | Initiate GitHub OAuth | No |
| GET | `/auth/github/callback` | GitHub OAuth callback | No |
| POST | `/auth/logout` | Logout user | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| GET | `/auth/refresh` | Refresh access token | Yes |
| GET | `/auth/admin` | Admin dashboard (admin+) | Yes |
| POST | `/auth/webhook/stripe` | Stripe webhook | Webhook secret |

### 10.8 Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `AUTH_ENVIRONMENT` | `dev` | `dev`, `staging`, `production` |
| `JWT_SECRET=REDACTED` | (auto-generated) | JWT signing secret |
| `JWT_ACCESS_EXPIRY_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_EXPIRY_DAYS` | `7` | Refresh token lifetime |
| `SESSION_MAX_AGE_SECONDS` | `604800` | Session cookie age |
| `GOOGLE_CLIENT_ID` | (required) | Google OAuth client ID |
| `GITHUB_CLIENT_ID` | (required) | GitHub OAuth client ID |
| `STRIPE_SECRET_KEY` | (optional) | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | (optional) | Stripe webhook secret |

## 11. Layer 2: Observability & Feedback Loop

**Added 2026-04-16.** Self-hosted observability stack + signals for model evaluation + SDLC scaffold.

### Observability (OTel → Prometheus → Grafana)

**Stack:** OpenTelemetry collector → Prometheus (M1 Max) → Grafana (CF Tunnel `m1max.cashclaw.cc`)

**Metrics tracked:**
- `agent.invocation_ms` — Agent latency
- `agent.token_cost_usd` — Token consumption cost
- `agent.retry_total` — Retry attempts
- `agent.model_drift_score` — LLM consistency
- `mlx.gpu_utilization_percent` — M1 Max GPU

**Dashboards:** `observability/dashboards/` (agent-performance.json, m1max-health.json, cost-analysis.json)

### Signals Loop (SQLite evals + Statsig/PostHog)

**Phases:** Offline evals (SQLite) → Online A/B tests (Statsig) → Amplitude analytics (deferred >50 customers)

**Location:** `.mekong/phases/signals/canary_flags.json` (feature gate state)

### Enforcement Gates (5 GitHub Actions)

**`.github/workflows/gates.yml`:** Runs on every PR to main.
- g1-validation: Type checks, syntax validation
- g2-security: Secret scanning, dependency audit
- g3-quality: Linting, coverage > 80%
- g4-dependency: Dependency freshness
- g5-deploy: CF Pages deploy test

---

## 12. Health Monitoring System

> **Phase 1-5 Monitoring Architecture** — Real-time detection, alerting, and automated recovery

### 11.1 Overview

The Health Monitoring System provides comprehensive system health visibility with five integrated phases:

| Phase | Component | Purpose |
|-------|-----------|---------|
| 1 | Health Endpoint + Crash Detection | HTTP health check + crash event tracking |
| 2 | License Failure Monitoring | License validation failure tracking with threshold alerting |
| 3 | Usage Anomaly Detection | Statistical anomaly detection using Z-score analysis |
| 4 | Alert Routing + Telegram | Centralized alert routing with deduplication and throttling |
| 5 | Auto-Recovery Actions | Automated recovery with exponential backoff |

### 11.2 Monitoring Components

#### Health Endpoint (`src/core/health_endpoint.py`)

FastAPI-based HTTP health endpoint providing real-time system status.

| Feature | Description |
|---------|-------------|
| Port | 9192 (default) |
| Endpoints | `/health`, `/ready`, `/live` |
| Format | JSON with component statuses |

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Full health status with component checks |
| `/ready` | GET | Kubernetes-style readiness probe |
| `/live` | GET | Kubernetes-style liveness probe |

**Component Status Values:**

| Status | Meaning |
|--------|---------|
| `healthy` | Component is functioning normally |
| `degraded` | Component has partial issues but operational |
| `unhealthy` | Component is not functioning |
| `unknown` | No health check registered |

#### Crash Detector (`src/core/crash_detector.py`)

Real-time crash detection monitoring CLI execution exit codes.

**Features:**
- Exit code monitoring and crash event emission
- Crash frequency tracking (crashes per hour)
- Crash history persistence to `.mekong/crashes/`
- Auto-recovery triggering on crash detection

**Event:** `health:critical` with metadata

#### License Monitor (`src/core/license_monitor.py`)

Tracks license validation failures with threshold alerting and grace period support.

**Features:**
- Failure recording with metadata (error_code, timestamp, retry_count)
- Threshold alerting (>3 failures in 5min → emit `license:critical`)
- Grace period for new installations (24h)
- Failure history persistence to `.mekong/license_failures.json`

**Event:** `license:critical` on threshold exceeded

#### Anomaly Detector (`src/core/anomaly_detector.py`)

Statistical anomaly detection for usage metrics using Z-score analysis.

**Features:**
- 7-day rolling baseline calculation
- Z-score detection (|z| > 3.0 = anomaly)
- Anomaly types: spike, drop, pattern_break
- Severity levels: low, medium, high, critical

**Event:** `usage:anomaly_detected` with category and metric

#### Alert Router (`src/core/alert_router.py`)

Centralized alert routing with deduplication, throttling, and severity-based routing.

**Features:**
- Deduplication window: 10 minutes
- Throttling limit: 10 alerts/hour (except critical)
- Telegram integration with markdown formatting
- Severity routing: critical/warning/info

**Subscribed Events:**
- `health:critical`
- `license:critical`
- `halt_triggered`
- `governance_blocked`

**Event:** `alert:sent`/`alert:deduplicated`/`alert:throttled`

#### Auto Recovery (`src/core/auto_recovery.py`)

Automated recovery actions with exponential backoff.

**Recovery Types:**

| Type | Description |
|------|-------------|
| `license:recovery` | License validation failure recovery |
| `crash:recovery` | Process crash recovery |
| `health:endpoint_recovery` | Health endpoint restart |
| `proxy:recovery` | Proxy service restart |

**Backoff Strategy:** min(base × 2^(attempt-1), max)
- Attempt 1: 1s delay
- Attempt 2: 2s delay
- Attempt 3: 4s delay
- Attempt 4+: 10s (capped)

**Events:** `recovery:started`/`recovery:success`/`recovery:failed`

### 11.3 Event Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                        EventBus Pub/Sub                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │   Health Events  │    │  License Events  │    │  Usage Events │  │
│  │  health:critical │    │ license:critical │    │  usage:anomaly│  │
│  │  recovery:*      │    │  license:*       │    │  usage:anomaly│  │
│  └────────┬─────────┘    └────────┬─────────┘    └───────┬───────┘  │
│           │                       │                        │         │
│           │                       │                        │         │
│           ▼                       ▼                        ▼         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      AlertRouter                               │ │
│  │  - Deduplication (10min)                                       │ │
│  │  - Throttling (10/hr non-critical)                             │ │
│  │  - Telegram Delivery                                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                     │                                │
│                                     ▼                                │
│                            ┌──────────────────┐                      │
│                            │  Telegram Alert  │                      │
│                            │  - Markdown      │                      │
│                            │  - Emoji prefix  │                      │
│                            │  - Timestamp     │                      │
│                            └──────────────────┘                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 11.4 Event Types Reference

| Event Type | Phase | Description |
|------------|-------|-------------|
| `health:critical` | 1 | Critical health issue detected |
| `health:warning` | 1 | System health degraded |
| `recovery:started` | 5 | Recovery action started |
| `recovery:attempted` | 5 | Recovery attempt in progress |
| `recovery:success` | 5 | Recovery succeeded |
| `recovery:failed` | 5 | Recovery failed |
| `license:validation_failed` | 2 | License validation failed |
| `license:critical` | 2 | License threshold exceeded |
| `license:grace_period_active` | 2 | Grace period active |
| `usage:anomaly_detected` | 3 | Anomaly detected |
| `usage:api_call` | 3 | API call recorded |
| `usage:agent_spawn` | 3 | Agent spawn recorded |
| `alert:deduplicated` | 4 | Alert suppressed (duplicate) |
| `alert:throttled` | 4 | Alert suppressed (throttle) |
| `alert:sent` | 4 | Alert sent successfully |

### 11.5 Health Endpoint API

```python
from src.core.health_endpoint import (
    start_health_server,
    stop_health_server,
    register_component_check,
    get_health_url,
)

# Register a health check for a component
def license_check():
    from src.core.license_monitor import get_monitor
    monitor = get_monitor()
    if monitor.is_critical():
        return ComponentStatus(status="unhealthy", message="License critical")
    return ComponentStatus(status="healthy")

register_component_check("license", license_check)

# Start health server
server = start_health_server(host="127.0.0.1", port=9192)

# Check health
curl "http://127.0.0.1:9192/health"
```

### 11.6 File Locations

| File | Purpose |
|------|---------|
| `.mekong/license_failures.json` | License failure history |
| `.mekong/usage_baseline.json` | Anomaly detection baselines |
| `.mekong/recovery_history.json` | Recovery attempt history |
| `.mekong/crashes/*.json` | Crash event history |
| `.mekong/health_endpoint.log` | Health endpoint logs |

### 11.7 Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HEALTH_ENDPOINT_HOST` | `127.0.0.1` | Health endpoint hostname |
| `HEALTH_ENDPOINT_PORT` | `9192` | Health endpoint port |
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token for alerts |
| `TELEGRAM_OPS_CHANNEL_ID` | - | Telegram ops channel ID |

### 11.8 Monitoring Integration Points

**In Orchestrator:**
```python
# After execution fails
from src.core.crash_detector import get_crash_detector
detector = get_crash_detector()
detector.record_crash(exit_code=result.exit_code, command=step.cmd)
```

**In License Validation:**
```python
# On validation failure
from src.core.license_monitor import record_failure
record_failure(
    error_code="invalid_signature",
    key_id=key_id,
    command="mekong run",
)
```

**In Usage Tracking:**
```python
# Record usage metrics
from src.core.anomaly_detector import get_detector, AnomalyCategory
detector = get_detector()
detector.record_metric(AnomalyCategory.API_CALLS, "requests", 100.0)
```

**In Alert Triggers:**
```python
# Emit_CRITICAL event
from src.core.event_bus import get_event_bus, EventType
event_bus = get_event_bus()
event_bus.emit(EventType.LICENSE_CRITICAL, {"data": ...})
```
