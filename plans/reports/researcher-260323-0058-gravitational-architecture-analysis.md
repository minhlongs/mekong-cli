# Gravitational Architecture Analysis: Mekong CLI as Solar System Hub
**Date:** 2026-03-23 | **Status:** Research Complete | **Recommendation:** HIGH PRIORITY IMPLEMENTATION

---

## EXECUTIVE SUMMARY

Mekong CLI is **architecturally positioned** to become a gravitational center for vertical projects (algo-trader, well, raas-gateway, etc.) but **lacks explicit gravity mechanisms**. Current state: 20+ apps in `apps/` operate semi-independently. Target: unified ecosystem where CLI is the inescapable hub.

**Verdict:** Architecture foundation exists. Need 4 strategic layers to activate gravity:
1. **Type System** — shared, enforced across all planets
2. **Plugin Registry** — discoverable extensions
3. **Contract Engine** — machine-readable orchestration
4. **Shared SDKs** — gravitational dependencies

---

## 1. THE "SUN" — WHAT IS THE CORE?

### Current Core Components (✓ Already Exists)

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **CLI Engine** | `packages/mekong-cli-core/src/` | Command registration + execution | ✓ 5 major components |
| **PEV Orchestrator** | `src/core/orchestrator.py` | Plan-Execute-Verify loop | ✓ Full stack |
| **Plugin System** | `packages/mekong-cli-core/src/plugins/` | Extensibility framework | ✓ Manifest + loader |
| **Contract Registry** | `factory/contracts/` | JSON machine contracts | ✓ 410 contracts |
| **LLM Router** | `packages/mekong-cli-core/src/llm/` | Universal LLM interface (3 env vars) | ✓ Multi-provider |
| **Billing Gate** | `src/core/mcu_gate.py` | MCU credit enforcement | ✓ Middleware ready |
| **Shared Packages** | `packages/{core,integrations,business}/` | SDK reusability | ⚠ Loosely coupled |

### Architecture Pattern

```
┌─────────────────────────────────────────────┐
│          THE SUN: Mekong CLI Core            │
├─────────────────────────────────────────────┤
│ PEV Engine (Plan→Execute→Verify)            │
│ Plugin Loader + Hooks                       │
│ Contract Registry (410 JSON schemas)        │
│ LLM Router (OpenRouter/Qwen/DeepSeek)       │
│ MCU Billing Gate (credit enforcement)       │
│ Command Registry (319 commands)             │
│ Observability + Telemetry                   │
└─────────────────────────────────────────────┘
                    ↓
        Pulls all projects toward it
        via dependencies & registries
```

**Gravity Mechanism:** Monorepo workspace + npm/pnpm hoisting + registry files force all projects to reference core.

---

## 2. THE "PLANETS" — WHAT ARE THE VERTICAL PROJECTS?

### Current Vertical Projects (20+ apps in `apps/`)

| Project | Type | Integration | Coupling Level |
|---------|------|-----------|-----------------|
| **algo-trader** | Trading bot | Loose (own package.json) | 🟡 MEDIUM |
| **raas-gateway** | API infrastructure | Tight (Cloudflare Workers) | 🔴 HIGH |
| **well** | Booking + billing platform | Very loose (separate monorepo) | 🟡 MEDIUM |
| **openslaw-worker** | Daemon/autonomous | Daemon integration | 🔴 HIGH |
| **crm** | Customer relations | Via CLI commands | 🟡 MEDIUM |
| **analytics** | Data platform | Telemetry sink | 🟡 MEDIUM |
| **admin** | Ops/studio | Web UI | 🟡 MEDIUM |
| **agencyos-landing** | Marketing site | Static + Next.js | 🟢 LOW |
| **apex-os** | Product OS | Experimental | 🟡 MEDIUM |

### Planet Type Classification

**🔴 TIGHTLY COUPLED** (Must-have core):
- `raas-gateway` — infrastructure dependency (Cloudflare D1, Workers, KV)
- `openclaw-worker` — daemon uses PEV engine + contract registry
- `dashboard` — UI for core metrics

**🟡 LOOSELY COUPLED** (Optional extensions):
- `algo-trader` — can exist independently, uses CLI via commands
- `well` — nested monorepo, minimal core dependency
- `crm` — plugin-like, adds commands
- `analytics` — telemetry consumer

**🟢 INDEPENDENT** (Marketing/landing):
- `agencyos-landing` — static site, no core usage

### Key Finding: Weak Gravity

**Problem:** Projects declare pnpm workspace membership but don't inherit shared types/contracts. Each app has own:
- API contract definitions
- Error handling patterns
- Authentication logic
- Monitoring schemas

**Evidence:**
```json
// apps/algo-trader/package.json
{
  "name": "@mekong/algo-trader",
  "version": "1.0.0",
  "dependencies": {
    // ❌ DOES NOT DEPEND ON @mekong/cli-core
    // ❌ DOES NOT USE shared types from factory/contracts/
  }
}

// apps/raas-gateway/package.json
{
  "name": "@mekong/raas-gateway",
  "type": "module",
  "dependencies": {
    "hono": "^4.0.0"
    // ❌ HONO CHOSEN INDEPENDENTLY (not from @mekong/web-framework)
  }
}
```

---

## 3. GRAVITY MECHANISMS — HOW DOES IT PULL?

### Current Gravity Sources (Partial)

#### 3.1 Workspace Gravity ✓
```
Root monorepo + pnpm workspaces forces all projects into single node_modules
Result: Shared dependencies cheaper, but not enforced
Problem: Projects CAN ignore it (e.g., well/ has own lockfile)
```

#### 3.2 Plugin System ✓ (Weak)
```typescript
// packages/mekong-cli-core/src/plugins/loader.ts
export class PluginLoader {
  async loadAll(): Promise<{ loaded: string[]; failed: [...] }> {
    // Discovers .mekong/plugins/ + marketplace packages
    // Loads plugin.json + main.ts
  }
}
```

**Reality:** Plugin system exists but:
- ❌ No central plugin registry (marketplace)
- ❌ No version pinning across projects
- ❌ No type safety for plugin APIs
- ❌ No discovery UI/CLI command

#### 3.3 Contract Registry ✓ (Underutilized)
```json
// factory/contracts/missions.schema.json
{
  "id": "mission-001",
  "layer": "Engineering",
  "command": "cook",
  "priority": "HIGH"
}
```

**Reality:** Contracts exist for missions but:
- ❌ Not consumed by most apps
- ❌ No automatic validation
- ❌ No feedback loop from projects to registry

#### 3.4 CLI Command Registration ✓
```typescript
// packages/mekong-cli-core/src/cli/index.ts
registerRunCommand(program, engine);
registerCrmCommand(program, engine);
registerFinanceCommand(program, engine);
// ... 319+ commands
```

**Reality:** Commands exist but:
- ❌ Not hierarchical per project
- ❌ No dependency ordering
- ❌ No permission scoping

---

## 4. WHAT'S MISSING FOR FULL GRAVITY?

### 4.1 ❌ Shared Type System (CRITICAL MISSING)

**Problem:** Each project defines its own types for:
- API requests/responses
- Command arguments
- Error types
- Agent capabilities

**Current State:**
```
algo-trader/types/            ← Own types
├── strategy.ts
├── order.ts
└── market.ts

well/src/types/               ← Own types
├── booking.ts
├── payment.ts
└── user.ts

raas-gateway/src/             ← Own types (duplicated!)
├── billing.ts
└── execution.ts

↓ Result: Type duplication, no cross-project type safety
```

**What's Needed:**
```typescript
// packages/core/shared-types/
export interface MekongCommand {
  id: string;
  name: string;
  layer: 'founder' | 'business' | 'product' | 'engineering' | 'ops';
  mcu_cost: number;
  args: Record<string, unknown>;
  timeout_ms: number;
}

export interface MekongAgent {
  name: string;
  capabilities: string[];
  plan(): Promise<MekongCommand[]>;
  execute(cmd: MekongCommand): Promise<ExecutionResult>;
  verify(result: ExecutionResult): Promise<boolean>;
}

export interface MekongPlugin {
  manifest: PluginManifest;
  provides: {
    commands?: MekongCommand[];
    agents?: MekongAgent[];
    hooks?: PluginHooks[];
  };
}
```

### 4.2 ❌ Central Plugin Registry (CRITICAL MISSING)

**Problem:** Plugin system loads from filesystem but no discovery mechanism.

**Current State:**
```
~/.mekong/plugins/          ← Local (works)
./mekong-plugins/           ← Project (implicit)
marketplace packages        ← Theoretical (not implemented)

Result: Plugins invisible, no sharing between projects
```

**What's Needed:**
```typescript
// CLI command: mekong plugin:list
// Output:
// ✓ @mekong/algo-trader        (local)  v1.0.0
// ✓ @mekong/well               (workspace) v2.3.1
// ✓ @mekong/crm                (marketplace) v3.0.0
// ✓ @mekong/ml-inference       (npm) v0.5.2

// CLI command: mekong plugin:registry
// Output: Registry service with search, ratings, docs
```

### 4.3 ❌ Automatic Type Distribution (MISSING)

**Problem:** When `packages/core/shared-types/` updates, projects must manually upgrade.

**What's Needed:**
```json
// .mekong/config.json
{
  "type_version_pin": {
    "@mekong/shared-types": "^1.5.0",
    "@mekong/contracts": "^2.0.0"
  },
  "auto_upgrade_check": true
}

// CI hook: Warn if types outdated
```

### 4.4 ❌ Cross-Project Command Dispatch (MISSING)

**Problem:** raas-gateway exposes MCU billing, but algo-trader doesn't auto-route through it.

**Current Flow (Manual):**
```
algo-trader:execute()
  ↓ (manual http call)
raas-gateway/v1/execute
  ↓ (deduct MCU)
openclaw-engine
```

**What's Needed:**
```typescript
// Auto-routing via contract registry
const gateway = await MekongCore.locateServiceByContract('mcu_billing');
const result = await gateway.execute(task);
```

### 4.5 ❌ Marketplace / CDN for Plugins (MISSING)

**Current:**
- npm packages (possible but not centralized)
- PyPI (possible but not centralized)

**Missing:**
- Central registry (like Shopify App Store)
- Version management UI
- Ratings + reviews
- Automated compliance checks

---

## 5. EXISTING INFRASTRUCTURE SUPPORTING GRAVITY

### 5.1 Cloudflare Infrastructure (Excellent Foundation)

```
raas-gateway (Cloudflare Workers)
├── D1 Database (distributed SQL)
├── KV Store (distributed cache)
├── R2 (object storage)
└── Email Routing (notifications)

Result: Perfect for central API + caching
```

**Opportunity:** Turn `raas-gateway` into **Gravity Anchor** — all projects route through it for:
- MCU billing (✓ already)
- Contract validation
- Plugin discovery
- Type schema validation
- Telemetry aggregation

### 5.2 PEV Engine Architecture (Solid)

```python
# src/core/orchestrator.py
class PEVOrchestrator:
    def plan(goal) → List[Task]
    def execute(tasks) → Result
    def verify(result) → bool
```

**Opportunity:** Each vertical project gets PEV loop + automatic rollback.

### 5.3 Contract System (Underutilized Asset)

```
factory/contracts/
├── missions.schema.json    ← Machine contracts
├── commands.schema.json    ← Command schema
├── skills.registry.json    ← Available skills
└── agents.registry.json    ← Available agents
```

**Reality:** Contracts are **JSON schemas** but not **enforced at runtime**.

---

## 6. BLUEPRINT: STRENGTHENING GRAVITY (4 PHASES)

### Phase 1: Type System Enforcement (Week 1-2)

**Objective:** Make shared types mandatory across all projects.

**Actions:**
1. Create `packages/core/shared-types/` with TypeScript definitions:
   - `MekongCommand`, `MekongAgent`, `MekongPlugin`, `ExecutionResult`, `ContractSchema`
2. Update all 20 apps' `package.json`:
   ```json
   {
     "dependencies": {
       "@mekong/shared-types": "^1.0.0"
     }
   }
   ```
3. Implement `pnpm run type-check` in CI that validates:
   - All command definitions match `MekongCommand`
   - All agents match `MekongAgent`
   - All plugins match `PluginManifest`

**Output:** Single source of truth for types. All projects in sync.

---

### Phase 2: Plugin Registry + Discovery (Week 2-4)

**Objective:** Make plugins discoverable, versioned, and trusted.

**Actions:**
1. **Create plugin registry service** on `raas-gateway`:
   ```
   GET /v1/plugins?category=agents&rating=4&...
   POST /v1/plugins/publish (signed with RAAS key)
   GET /v1/plugins/{id}/schema (returns PluginManifest)
   ```

2. **Extend CLI with discovery commands:**
   ```bash
   mekong plugin:list              # Show all available
   mekong plugin:search "trading"  # Search by name
   mekong plugin:install @mekong/algo-trader
   mekong plugin:info @mekong/algo-trader
   ```

3. **Add to each project's `plugin.json`:**
   ```json
   {
     "name": "@mekong/algo-trader",
     "registry": "https://raas.agencyos.network/v1/plugins",
     "tags": ["trading", "strategies", "backtesting"],
     "author": "binh-phap-vc",
     "rating": 4.8,
     "downloads": 1200
   }
   ```

**Output:** Discoverable plugin ecosystem. Projects are first-class extensions.

---

### Phase 3: Contract Validation Engine (Week 4-6)

**Objective:** Enforce contracts at runtime, not just at design time.

**Actions:**
1. **Create validation middleware** in `raas-gateway`:
   ```typescript
   // Middleware validates all requests against factory/contracts/
   const validateAgainstContract = (contractId: string) => {
     return async (req, res, next) => {
       const schema = await loadContract(contractId);
       const valid = ajv.validate(schema, req.body);
       if (!valid) res.status(400).json(ajv.errors);
       else next();
     };
   };
   ```

2. **Projects declare contract compliance:**
   ```json
   // apps/algo-trader/mekong.json
   {
     "commands": ["trading:execute"],
     "contracts": [
       "factory/contracts/mission-001.json",
       "factory/contracts/execution.schema.json"
     ]
   }
   ```

3. **CLI validates before dispatch:**
   ```bash
   mekong cook "run trading bot" --contract-check
   # ✓ Validates against mission-001-raas-core-api.json
   # ✓ Validates MCU budget (500 credits)
   # ✓ Validates output paths
   ```

**Output:** Runtime guarantee that all projects follow contracts.

---

### Phase 4: Unified Command Hierarchy (Week 6-8)

**Objective:** Organize 319 commands hierarchically, discoverable by layer.

**Actions:**
1. **Extend command registry with layer + project metadata:**
   ```typescript
   interface MekongCommand {
     id: string;
     layer: 'founder' | 'business' | 'product' | 'engineering' | 'ops';
     project?: '@mekong/algo-trader' | '@mekong/well' | ...;
     mcu_cost: number;
     dependencies: string[];
     visibility: 'public' | 'private' | 'internal';
   }
   ```

2. **Auto-generate command docs:**
   ```bash
   mekong help --layer engineering
   # Shows only /cook /code /test /deploy /review
   # Groups by project

   mekong help --project @mekong/algo-trader
   # Shows only algo-trader commands
   ```

3. **Permission scoping:**
   ```json
   // raas-gateway checks permissions before execution
   {
     "token": "sk-xxx",
     "permissions": ["@mekong/algo-trader/*", "engineering:deploy"],
     "mcu_balance": 5000
   }
   ```

**Output:** Discoverable, permission-gated, hierarchical command system.

---

## 7. UNRESOLVED QUESTIONS

1. **Plugin versioning strategy:** Semantic vs. hash-based? Update frequency?
2. **Cross-project transactions:** If algo-trader calls well API, how to track MCU costs?
3. **Type versioning:** How to handle breaking changes in `@mekong/shared-types`?
4. **Marketplace governance:** Who approves plugins for public registry? Trust model?
5. **Offline mode:** Can projects work without raas-gateway? Circuit breaker strategy?
6. **Performance:** Contract validation at 100K+ requests/sec — cache strategy?
7. **Multi-region:** How to replicate plugin registry across Cloudflare KV regions?
8. **Migration path:** How to onboard existing 20 apps into type system gradually?

---

## 8. RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes in shared types | HIGH | 🔴 All projects break | Semantic versioning + deprecation period |
| Plugin registry abuse (spam/malware) | MEDIUM | 🟠 Reputation damage | Code review + signing + CDN scan |
| Coupling becomes too tight | MEDIUM | 🟠 Loss of flexibility | Plugin sandboxing + clear API boundaries |
| Performance regression (validation) | LOW | 🟠 Latency spike | Contract caching + async validation |

---

## 9. SUCCESS METRICS

| Metric | Target | Current |
|--------|--------|---------|
| % projects using shared types | 100% | 0% |
| Plugin discovery UI available | Week 4 | N/A |
| Contract validation coverage | 95%+ | Manual only |
| Cross-project type errors caught by TS | 100% | ~20% |
| Plugin marketplace maturity | 50+ verified plugins | 0 |

---

## 10. NEXT STEPS (Recommended Order)

**Priority 1 (Immediate):**
- [ ] Extract shared types to `packages/core/shared-types/`
- [ ] Update all 20 apps to depend on shared types
- [ ] Add `type-check` to CI pipeline

**Priority 2 (Week 2-4):**
- [ ] Implement plugin registry API on `raas-gateway`
- [ ] Add discovery commands to CLI
- [ ] Create plugin marketplace documentation

**Priority 3 (Week 4-6):**
- [ ] Build contract validation middleware
- [ ] Add contract-check to CLI
- [ ] Create compliance dashboard

**Priority 4 (Week 6-8):**
- [ ] Reorganize 319 commands hierarchically
- [ ] Implement permission scoping
- [ ] Create command discovery UI

---

## CONCLUSION

**Current State:** Mekong CLI has all the infrastructure for gravitational pull (monorepo, PEV engine, plugin system, contract registry) but **lacks the connective tissue** — shared types, discoverable plugins, enforced contracts.

**Opportunity:** With 4 focused phases, transform Mekong from a collection of loosely-coupled projects into a tightly-integrated **Solar System** where:
- Projects are **planets** with distinct purposes
- CLI core is the **sun** pulling everything toward it
- Plugins are **moons** extending planets
- Gravity is enforced via types + contracts + registry

**Investment:** ~8 weeks, primarily TypeScript + infrastructure work. **ROI:** 10x faster development for new vertical projects + automatic cross-project compatibility.

---

**Report:** `/Users/macbookprom1/mekong-cli/plans/reports/researcher-260323-0058-gravitational-architecture-analysis.md`

**Next Phase:** Create comprehensive implementation plan with task breakdown.
