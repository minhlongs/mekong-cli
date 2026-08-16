# Architecture Audit Plan — Mekong CLI to Autonomous Agent Runtime

**Date:** 2026-08-17
**Status:** READY FOR EXECUTION
**Scope:** Read-only audit. No production code changes.

---

## 1. Reframed Problem

The Mekong CLI repository is a 973-file Python monolith (`src/core/` alone is 171 files / 45,527 lines) that has grown organically from a CLI tool into a CEO Solo Agentic Harness Engineering Platform. It contains at least three competing orchestration systems (PEV engine, swarm/dispatch daemon, harness TypeScript runtime), multiple overlapping agent registries, duplicated tier/billing abstractions (Tier enum defined in 6+ places), and two disconnected CLI entrypoints. The goal is NOT to rewrite this code. The goal is to map exactly what exists, identify what must become "Mekong Core" primitives, what must be adapter-ized for Buzz integration, what must be deprecated, and what interfaces are missing for MCP capability bus and x402/MPP economic bus integration — all while preserving the three working business funnels (Zalo OA, Tax/Accounting, AI Video Factory).

---

## 2. Work Checklist

### Phase A: Directory Mapping (Steps 1-4)

#### Step 1: Top-Level Structure Map
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Complete file/directory inventory of all 49 top-level directories and key root files. Classification of each as: Core, Adapter, Config, Dead, Orphan, or External.

**Actions:**
- List all top-level directories with file counts and total line counts
- Classify each: `src/` (Core), `engine/` (Core billing), `harness/` (TypeScript, potential dead), `cli/` (Core CLI), `factory/` (Adapter/scaffold), `integrations/` (Adapter), `cloudflare-skills/` (Adapter), `recipes/` (Config), `workflows/` (Config), `observability/` (Infrastructure), `specs/` (Specs), `tests/` (Tests), `dna/` (Config), `agents/` (Config), `sops/` (Config), `mekong/` (ZenOS constitution layer), `harness/` (TypeScript runtime — check if still used)
- Flag root-level Python scripts (`apply_all_fixes.py`, `fix_indent.py`, etc.) as likely dead/orphaned

#### Step 2: Core Module Deep Map
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Every file in `src/core/` classified into one of: Agent Runtime, LLM Routing, Billing/Metering, Orchestration, Security/Auth, Observability, CLI Support, Business Logic, Dead Code.

**Actions:**
- Read all `src/core/*.py` files (171 files)
- For each file: note class names, key functions, imports from other `src/core/` modules
- Identify the 9 ALGO pipeline (classify, MCU lock, model select, agent load, build messages, execute with fallback, verify, MCU confirm, emit) and which files implement each stage
- Flag files >200 lines (YAGNI rule violation candidates)
- Flag circular import risks

#### Step 3: PEV Engine Map
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Complete picture of `src/harness/pev/` — what it implements, what it imports from `src/core/`, what state it manages, and how it connects to the CLI entrypoint.

**Actions:**
- Read every `.py` file in `src/harness/pev/` (17 source files)
- Trace the orchestration pipeline: parser -> planner -> executor -> verifier
- Map dependencies on `src/core/` modules (memory_bridge, llm_client, etc.)
- Check `src/harness/pev/orchestrator.py` — this is the PEV glue layer
- Identify what `src/core/pev_*.py` files duplicate vs. what `src/harness/pev/` provides

#### Step 4: Harness TypeScript Runtime Map
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Determine if `harness/` (TypeScript) is still actively used, how it relates to the Python harness, and whether it should be deprecated.

**Actions:**
- Read `harness/package.json`, `harness/tsconfig.json`
- Read all 9 TypeScript source files in `harness/src/`
- Check if `harness/src/core/` files duplicate `src/harness/core/` Python files
- Check if any CLI commands or entrypoints reference the TypeScript harness
- Check `package.json` root for build scripts referencing harness/

---

### Phase B: Execution Path Tracing (Steps 5-9)

#### Step 5: CLI Entrypoint -> Command Dispatch
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Two complete traces — one for `src/main.py` (primary) and one for `cli/entrypoint.py` (secondary) — documenting how a user command reaches its handler.

**Actions:**
- Trace `src/main.py` -> `src/cli/app_setup.py` -> command registration -> individual command modules
- Trace `cli/entrypoint.py` -> typer app -> command sub-apps -> handler functions
- Identify overlap between `src/commands/` (63 files) and `cli/commands/` (12+ files)
- Map which commands exist in both places

#### Step 6: LLM Router & Agent Dispatcher
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Complete map of how a task flows from classification through model selection to LLM execution.

**Actions:**
- Trace `src/harness/core/router.py` (the 9-stage ALGO pipeline)
- Map all 3 agent dispatch mechanisms:
  1. `src/harness/agents/dispatcher.py` (harness agent layer)
  2. `src/core/agent_dispatcher.py` (core ALGO 8)
  3. `src/daemon/dispatcher.py` (daemon layer)
- Trace `src/core/task_classifier.py` -> `src/core/model_selector.py` -> `src/core/cost_estimator.py` -> `src/core/mcu_gate.py` -> `src/core/fallback_chain.py`
- Map LLM provider abstraction: `src/harness/core/providers.py` vs. `src/core/providers.py` vs. `src/core/llm_client.py` vs. `src/seed/llm_client.py`

#### Step 7: Tool Execution & Verification
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Map of how tools are registered, dispatched, and verified.

**Actions:**
- Read `src/core/tool_registry.py` (19.1K lines)
- Read `src/core/tool_permission_registry.py` (4.6K lines)
- Read `src/harness/pev/verifier.py` (16.2K lines)
- Trace how `mekong cook` command flows through PEV pipeline to tool execution
- Identify the recipe system (`src/harness/pev/parser.py`, `src/harness/recipes/`)

#### Step 8: Billing & Payment Paths
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Complete map of all billing/payment/metering code, identifying duplications and which system is "live."

**Actions:**
- Map 3 billing implementations:
  1. `src/core/mcu_billing.py` + `src/core/mcu_gate.py` (MCU credit system)
  2. `engine/billing/` (Tier-based rate limiting — ROIaaS Phase 6)
  3. `engine/payments/` (Usage metering service)
- Map `src/seed/config/tiers.py` (canonical TierKey enum) vs. `engine/billing/tier_config.py` (different Tier enum: FREE/TRIAL/PRO/ENTERPRISE) vs. 6+ other Tier class definitions found
- Trace `src/api/billing_endpoints.py` (27.6K) and `src/api/billing_routes.py` (10.9K)
- Map Polar.sh integration (`src/services/polar_client.py`) and PayOS/VietQR integration
- Identify the license system: `engine/license/` vs. `src/core/license_*.py` vs. `src/middleware/license_gate.py`

#### Step 9: Observability & State
**Agent:** explorer (single Explore agent)
**Acceptance criteria:** Map of all observability, telemetry, and state/memory systems.

**Actions:**
- Map `src/harness/observability/` (collector, health, metrics, tracing)
- Map `src/observability/` (if it exists — may be duplicate)
- Map `observability/` (root level — dashboards, provisioning)
- Map state/memory systems:
  - `src/harness/pev/memory.py`
  - `src/core/memory.py` + `src/core/memory_bridge.py` + `src/core/memory_client.py` + `src/core/memory_store.py` + `src/core/memory_scope.py`
  - `harness/src/memory-layer.ts` (TypeScript)
  - `src/seed/memory.py`
  - `src/core/vector_memory_store.py` (12.2K lines)
  - `.mekong/memory.yaml` + `.mekong/memory.jsonl`
- Identify which memory system is canonical vs. experimental

---

### Phase C: Issue Identification (Step 10)

#### Step 10: Issue Classification
**Agent:** scout (or multiple researchers in parallel)
**Acceptance criteria:** Every issue categorized as one of: Duplication, Dead Code, Conflict, Missing Interface, Unsafe Path, or Missing Gate.

**Issue categories to scan:**

| Category | What to look for |
|----------|-----------------|
| **Duplicated orchestration** | PEV engine vs. swarm vs. daemon dispatcher vs. harness TypeScript |
| **Dead code** | Root-level .py scripts, `src/core/binh_phap_escapation.py` (0B), `.bak2/.bak3` files, `cli/main.py.new` |
| **Conflicting agent abstractions** | `agents/registry.yaml` vs. `src/core/agent_registry.py` vs. `src/harness/agents/` vs. `src/agents/` |
| **Duplicated CLI surfaces** | `src/main.py` vs. `cli/entrypoint.py`, `src/commands/` (63 files) vs. `cli/commands/` (12+ files) |
| **Duplicated billing** | MCU billing vs. engine/billing tier system vs. 6+ Tier enum definitions |
| **Cloudflare hardcoding** | `src/commands/deploy.py` (hardcoded cloudflare deploy) — should become adapter |
| **Missing MCP interfaces** | `src/core/mcp_server.py` (43.8K) exists but check if it exposes a standard MCP tool schema |
| **Missing x402/MPP abstraction** | No payment protocol abstraction layer found — billing is Stripe/Polar/PayOS-specific |
| **Unsafe autonomous paths** | `src/core/autonomous.py`, `src/core/agi_loop.py`, `src/core/swarm.py` — check for approval gates |
| **Missing Buzz integration interfaces** | No `MekongRuntimeAdapter` or `MekongCoreContract` interface found |
| **State/memory ownership** | 6+ memory systems — unclear which is canonical |
| **ZENOS/Mekong layer** | `mekong/` directory, `src/governance/`, `src/mekong/` — check if constitutional layer conflicts with core runtime |

---

### Phase D: Deliverable Production (Steps 11-16)

#### Step 11: CURRENT_ARCHITECTURE.md
**Agent:** docs-manager
**Acceptance criteria:** Complete map of what exists today, with directory diagrams, module descriptions, and data flow arrows. No opinions, no recommendations — just facts.

**Content:**
- Repository topology diagram
- Module classification table (Core / Adapter / Config / Dead)
- CLI entrypoint traces (both `src/main.py` and `cli/entrypoint.py`)
- LLM routing pipeline diagram (9-stage ALGO)
- Agent layer diagram (all 3 dispatch mechanisms)
- Billing system diagram (all 3 implementations)
- Memory/state system diagram
- Observability pipeline diagram
- Key file sizes and complexity indicators

#### Step 12: DEPENDENCY_MAP.md
**Agent:** docs-manager
**Acceptance criteria:** Complete import graph for all modules. Every cross-module import documented. Circular dependencies flagged.

**Content:**
- Module-level dependency graph (who imports whom)
- Circular dependency chains
- External dependency inventory (from pyproject.toml)
- Which modules are leaf nodes (safe to deprecate)
- Which modules are high-fan-out (risk to change)

#### Step 13: DUPLICATION_MAP.md
**Agent:** docs-manager
**Acceptance criteria:** Every instance of duplicated code/interface identified, with severity (Critical / Warning / Cosmetic).

**Content:**
- Tier enum duplication table (6+ definitions, which is canonical)
- LLM client duplication table (4 implementations)
- Agent dispatcher duplication table (3 implementations)
- Memory system duplication table (6+ implementations)
- CLI command surface duplication table
- Observability duplication table
- License/billing duplication table

#### Step 14: DEPRECATION_MAP.md
**Agent:** docs-manager
**Acceptance criteria:** Every file/directory recommended for deprecation, with rationale and migration path.

**Content:**
- Root-level dead scripts (apply_all_fixes.py, fix_indent.py, etc.)
- `.bak2/.bak3` files
- `cli/main.py.new`
- `src/core/binh_phap_escapation.py` (0 bytes)
- `polar_webhook.py.legacy`
- TypeScript harness if confirmed dead
- Duplicate agent dispatch systems (which one to keep)
- Duplicate billing systems (which one to keep)
- Deprecated imports and their replacements

#### Step 15: AUTONOMY_GAPS.md
**Agent:** docs-manager (informed by researcher subagent for MCP/x402/Buzz research)
**Acceptance criteria:** Complete list of what is missing for Mekong to function as an autonomous agent runtime pluggable into Buzz.

**Content (must research external systems first):**
- **Buzz Integration:** What interface does Buzz expect from a "runtime adapter"? What contract must Mekong implement?
- **MCP Gap:** What MCP tool/resource schema is needed? Does `src/core/mcp_server.py` expose standard MCP protocol or custom?
- **x402/MPP Gap:** What payment protocol abstraction is needed? Is there a standard x402/MPP interface to implement?
- **Autonomous Execution Gaps:**
  - Missing approval gates for high-risk autonomous actions
  - Missing goal/context/plan/delegate/execute/observe/verify/repair/remember/commit primitives
  - Missing risk scoring for autonomous decisions
  - Missing rollback interfaces
- **Provider Agnosticism Gaps:**
  - Where is Cloudflare hardcoded vs. abstracted?
  - Where is Buzz hardcoded vs. abstracted?
  - What must change to keep Mekong Core provider-agnostic?
- **State Management Gaps:**
  - Which memory system becomes canonical?
  - What state interfaces does Buzz expect?

#### Step 16: MEKONG_CORE_CONTRACT.md
**Agent:** docs-manager (informed by brainstormer for interface design)
**Acceptance criteria:** The target interface contract that "Mekong Core" must expose. Not implementation — just the API surface.

**Content:**
- `MekongCoreRuntime` interface (the Buzz adapter contract)
- `LLMRouter` interface (provider-agnostic)
- `ToolRegistry` interface (MCP-compatible)
- `AgentDispatcher` interface (the single canonical dispatch)
- `BillingMeter` interface (x402/MPP-compatible)
- `MemoryStore` interface (the single canonical memory)
- `ObservabilitySink` interface (OTel-compatible)
- `VerificationEngine` interface
- `GoalEngine` interface (Goal -> Plan -> Execute -> Verify cycle)

---

## 3. Risks & Gates

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **src/core/ is too large to trace in one pass** | Incomplete mapping | Split into sub-exploration: Agent Runtime (files with agent/dispatch in name), LLM Layer (llm/provider/model/router), Billing (billing/tier/meter), Core Infrastructure (config/hooks/governance) |
| **Circular imports mask true dependencies** | Incorrect dependency map | Run `pylint --import-graph` or manual grep for cross-module imports |
| **TypeScript harness is actually used somewhere we haven't found** | Premature deprecation | Search package.json scripts, .github/workflows, any CI config that builds harness/ |
| **ZENOS/mekong layer is partially implemented** | Incorrect classification | Check if any runtime code imports from `mekong/` or `src/governance/` |
| **Agent registry files are stale (no one uses them)** | Incorrect agent layer map | Check if any Python code imports/loads `agents/registry.yaml` at runtime |
| **Buzz/MCP/x402 specs are not yet public** | Autonomy gaps are speculative | Research phase (Step 15) explicitly separates "known gaps" from "speculative gaps based on assumed interfaces" |

### Quality Gates
- Gate 1 (after Phase A): Directory map must be complete — every top-level dir classified
- Gate 2 (after Phase B): All 10 execution paths must be traced with file:line references
- Gate 3 (after Phase C): Issue list must be reviewed by reviewer agent for completeness
- Gate 4 (before Phase D): All 6 deliverables must be peer-reviewed for accuracy

---

## 4. Agent Assignments

| Step | Agent Type | Rationale |
|------|-----------|-----------|
| 1. Top-Level Structure Map | `Explore` | Fast file system scan, no deep analysis needed |
| 2. Core Module Deep Map | `Explore` | Read-only deep scan of 171 files — needs to be systematic |
| 3. PEV Engine Map | `Explore` | Targeted scan of one subsystem |
| 4. Harness TypeScript Map | `Explore` | Small codebase (9 files), quick to determine if dead |
| 5. CLI Entrypoint Trace | `Explore` | Code tracing, needs to follow import chains |
| 6. LLM Router Trace | `Explore` | Complex trace through 9-stage pipeline |
| 7. Tool Execution Trace | `Explore` | Trace recipe system + tool registry |
| 8. Billing Path Trace | `Explore` | Cross-module trace across 3 billing systems |
| 9. Observability & State | `Explore` | Multi-location scan |
| 10. Issue Classification | `researcher` | Needs judgment on severity and categorization |
| 11-16. Deliverable Writing | `docs-manager` | Synthesize findings into structured docs |

### Parallelization Strategy
- Steps 1-4 (Phase A) can run in parallel — independent directory scans
- Steps 5-9 (Phase B) can run in parallel — independent execution paths
- Step 10 depends on all of Phase A+B being complete
- Steps 11-16 (Phase D) can partially overlap: 11+12 can run in parallel, 13+14 can run in parallel, 15 needs external research, 16 depends on 15

---

## 5. Ship Plan

### Execution Order

```
Wave 1 (parallel):  Steps 1, 2, 3, 4
   ↓ Gate 1: Directory map complete
Wave 2 (parallel):  Steps 5, 6, 7, 8, 9
   ↓ Gate 2: All execution paths traced
Wave 3:            Step 10 (Issue Classification)
   ↓ Gate 3: Issues reviewed
Wave 4 (parallel):  Steps 11+12, 13+14
Wave 5:            Step 15 (needs external research)
   ↓ Gate 4: All deliverables peer-reviewed
Wave 6:            Step 16 (MEKONG_CORE_CONTRACT)
```

### Output Location
All 6 deliverables go to `/Users/macbook/mekong-cli/plans/reports/`:
1. `CURRENT_ARCHITECTURE.md`
2. `DEPENDENCY_MAP.md`
3. `DUPLICATION_MAP.md`
4. `DEPRECATION_MAP.md`
5. `AUTONOMY_GAPS.md`
6. `MEKONG_CORE_CONTRACT.md`

### Report Format
Each deliverable follows this structure:
- **Header**: Title, date, audit scope, author (agent type)
- **Summary**: 3-5 sentence executive summary
- **Findings**: Structured tables, diagrams (ASCII), file:line references
- **Confidence Level**: HIGH (verified by reading code) / MEDIUM (inferred from imports) / LOW (needs manual verification)
- **Cross-references**: Links to other deliverables

### Estimated Scope
- **Phase A**: ~200 files read, ~800K bytes scanned
- **Phase B**: ~50 files traced in depth, ~300K bytes
- **Phase C**: ~20 issues identified across 6 categories
- **Phase D**: ~600 lines of documentation across 6 files

---

## 6. Assumptions

| Assumption | Confidence | What would change the answer |
|------------|-----------|------------------------------|
| `src/main.py` is the primary CLI entrypoint and `cli/entrypoint.py` is a secondary/legacy entrypoint | HIGH | If `pyproject.toml` scripts point to `cli/entrypoint.py`, it becomes primary |
| The TypeScript `harness/` is legacy/dead code from a prior rewrite | MEDIUM | If CI/CD builds it, it must be treated as active |
| `src/core/` is the de facto "Mekong Core" but lacks a clean interface boundary | HIGH | If `src/harness/core/` was intended to be the clean core, the audit priority shifts |
| The 3 billing systems coexist for different subsystems (CLI vs. API vs. engine) | MEDIUM | If they're all wired to the same request path, the duplication is more urgent |
| `agents/registry.yaml` is a design document, not a runtime-loaded config | HIGH | If it's loaded at runtime, it becomes part of the agent layer contract |
| `src/governance/` and `mekong/` (ZenOS layer) are aspirational, not operational | MEDIUM | If any runtime code imports from them, they must be included in the core contract |
| Buzz integration requires a specific adapter interface that we can define post-audit | LOW | If Buzz already ships a runtime SDK, we should implement that instead |
