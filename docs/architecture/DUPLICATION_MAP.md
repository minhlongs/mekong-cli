# Duplication Map

Refreshed: 2026-08-23 · HEAD: 0878f966f

## Active Duplications

### 1. Duplicated AgentBase / AgentRegistry Abstractions

**Status:** UNCHANGED (2026-08-23)

**Current:** Three `AgentBase` definitions and three registry implementations
coexist: `src/core/agent_base.py` + `src/core/agent_registry.py` (canonical,
used by gateway and commands), `src/seed/agents/` (foundational auth/DB agent
stack), and `src/mekongcli/` swarm abstractions. The CLI runs a mixed stack:
some commands resolve agents through `AgentRegistry`, others through
`src/mekongcli/` internals.

**Why:** Each stack was built for a different orchestration context (core
recipes, seed foundation, goal-engine swarm). No convergence pass has run.

**Recommendation:** Adopt `src/core/protocols.py` Protocols as the single
contract; migrate registries to adapters. Blocked until orchestration stacks
(item 1 below in the audit sense — see item 8 here) converge.

**Risk:** MEDIUM — Three live stacks; wrong move breaks `mekong cook`,
`mekong swarm`, and gateway agent resolution.

---

### 2. Billing / Payment Duplication

**Status:** IMPROVED (2026-08-23) — storage converged; route and config duality remains

**Current:** The former duplicate core (`raas/billing_core.py`) was deleted
in PR #2. `src/billing/` is now a pure re-export facade — every module forwards
to the canonical `src/raas/` implementation:

| Facade module | Forwards to |
|---|---|
| `src/billing/engine.py` | `src/raas/billing_engine.py` |
| `src/billing/proration.py` | `src/raas/billing_proration.py` |
| `src/billing/idempotency.py` | `src/raas/billing_idempotency.py` |
| `src/billing/reconciliation.py` | `src/raas/billing_audit.py` |
| `src/billing/audit_trail.py`, `src/billing/event_emitter.py` | corresponding `src/raas/` modules |

MCU storage has CONVERGED: `MCUBilling` (`src/core/mcu_billing.py`) is now
backed by `CreditStore` (`src/raas/credits.py`) via SQLite WAL — the former
parallel MCU ledger is gone.

**Remaining duplication:**

1. **Tier-config duality** — `Tier` enum in `engine/billing/tier_config.py`
   vs `TierKey`/`TierConfig` in `src/seed/config/tiers.py` (plus DB-backed
   `TierConfig` in `src/db/tier_config_repository.py` for rate-limit config).
   Three tier vocabularies for one concept.
2. **Four payment route families mounted in the gateway** (`src/gateway.py`):
   `src/api/billing_routes.py` (Polar), `src/api/vn_payments_routes.py`
   (VietQR), `src/raas/nowpayments_router.py` (crypto), and
   `src/raas/revenue_router.py` (webhooks). NOWPayments is mounted directly,
   bypassing the `PaymentProvider` Protocol.
3. **Orphaned CLI module** — `src/cli/billing_commands.py` is a complete Typer
   app never registered in `src/cli/app_setup.py` (0 importers).

**Recommendation:** Collapse tier vocabularies onto `src/seed/config/tiers.py`;
route NOWPayments through the `PaymentProvider` Protocol; delete or register
`src/cli/billing_commands.py`.

**Risk:** MEDIUM — Payment routes are live revenue paths; consolidate behind
feature flags with webhook replay tests.

---

### 3. Memory Store — Three-Way Split

**Status:** OPEN (2026-08-23) — former shim fully deleted, split remains

**Current:** The old backward-compat shim (the former 4-line `memory.py`
re-exporting `memory_canonical.py`) was deleted in PR #2. Three memory systems
now coexist with no shim between them:

| System | Backend | Consumers |
|---|---|---|
| `src/core/memory_store.py` | JSONL | `src/design_intelligence/design_memory.py`, `src/core/agent_dispatcher.py`, `src/cli/commands/memory.py`, `src/core/runtime_adapter.py` |
| `src/core/memory_canonical.py` | YAML + vector (`VectorMemoryStore`) | ~20 consumers (13 direct src importers + tests) |
| `MemoryStore` Protocol in `src/core/protocols.py` | — | ZERO exact conformers (`store`/`retrieve`/`delete`/`search` signature match: none) |

Additionally, `ScopedMemoryStore` in `src/core/memory_separation.py` provides
per-mission scoping (Memory Separation gap closed), wrapping a concrete store.

**Why:** The Protocol was defined aspirationally; neither concrete store was
retrofitted to conform exactly, so dependency-injection points
(`src/core/learner.py` takes a `MemoryStore` parameter) bind by convention,
not by verified conformance.

**Recommendation:** Retrofit `memory_canonical.py` to satisfy the Protocol
exactly, add a runtime conformance test, then migrate the 4 JSONL consumers or
formalize JSONL as a second conforming backend.

**Risk:** MEDIUM — Both stores are live; design_intelligence deliberately binds
to the JSONL store (concrete binding, does not import `src/core/protocols.py`).

---

### 4. Observability Assets (Grafana Dashboards / Provisioning)

**Status:** UNCHANGED (2026-08-23)

**Current:** Three copies of the same dashboard JSON exist:

1. Root `observability/dashboards/` (+ `observability/provisioning/`)
2. `src/harness/observability/dashboards/`
3. `src/harness/observability/dashboards/dashboards/` — a nested duplicate
   directory

`cmp` confirms the root copies are byte-identical to the nested
`dashboards/dashboards/` copies (e.g. `cost-analysis.json`,
`agent-performance.json`, `m1max-health.json`). Compose and collector configs
are also duplicated: root `observability/docker-compose.observability.yml` +
`prometheus.yml` + `otel-collector-config.yaml` vs
`src/harness/observability/docker-compose.yml` + `prometheus.yml` +
`otel-collector.yaml`.

**Recommendation:** Pick one canonical location (root `observability/`),
delete the nested `dashboards/dashboards/` directory, symlink or generate the
harness copy.

**Risk:** LOW — Static assets; verify which compose file ops actually runs
before deleting.

---

### 5. LLM Routing

**Status:** RESOLVED (old item) — NEW duplication found in harness (2026-08-23)

**Old item — resolved:** The phantom `llm_router.py` reference in the previous
map never existed in git history; only `src/core/llm_router_adapter.py` (the
live adapter wrapping `src/core/llm_client.py` behind the `LLMRouter`
Protocol) and `src/daemon/llm_router.py` (now dead, 0 importers — see
DEPRECATION_MAP) ever existed. No routing duplication remains in `src/core/`.

**NEW duplication:**

| Pair | State |
|---|---|
| `src/harness/pev/planner.py` vs `src/core/planner.py` | BYTE-IDENTICAL (`cmp` verified) |
| `src/harness/pev/verifier.py` (493 lines) vs `src/core/verifier.py` (517 lines) | Near-duplicate; harness version adds `explain()` + quality gates |
| `src/harness/pev/dag_scheduler.py` (19 lines, always-True stub) vs `src/core/dag_scheduler.py` (220 lines, real scheduler) | Stub masks the real implementation |

**Recommendation:** Delete `src/harness/pev/planner.py` and import from
`src/core/planner.py`; merge the harness verifier's `explain()`/quality gates
into `src/core/verifier.py`; point harness at the real
`src/core/dag_scheduler.py`.

**Risk:** LOW-MEDIUM — Harness PEV stack is live for `mekong swarm`; the stub
scheduler silently changes behavior when swapped for the real one (test first).

---

### 6. CLI Command Surfaces

**Status:** IMPROVED (2026-08-23) — registry duplication resolved; orphan modules remain

**Current:** The former dual registry (`commands_registry.py`, deleted in PR
#2) is gone. The single aggregator is now `src/cli/app_setup.py` (Typer-based,
28 `add_typer`/command registrations, 53 live commands, zero duplicate command
names).

**Remaining duplication:**

1. **Orphan command modules** — `src/commands/core_commands.py` defines its
   own `ask` and `cook` commands duplicating the registered
   `src/cli/cook_command.py` surface, but is never imported by
   `src/cli/app_setup.py`.
2. **Stale registry doc** — `src/commands/COMMAND_REGISTRY.md` claims 43 wired
   commands including 16 that are MISSING from the live CLI (`vn-setup`,
   `billing`, `trace`, `license`, `tier-admin`, `monitor`, `usage`, `auth`,
   `raas`, `sync-raas`, `activate`, `deploy-all`, `test`, `lint`, `clean`,
   `ci`).
3. **Unregistered Typer apps** — `src/cli/billing_commands.py`,
   `src/cli/pev_commands.py`, `src/cli/usage_commands.py` are complete apps
   never registered (see DEPRECATION_MAP).

**Recommendation:** Delete or merge `src/commands/core_commands.py`; rewrite
`src/commands/COMMAND_REGISTRY.md` from the live `src/cli/app_setup.py` tree.

**Risk:** LOW — Orphans have 0 importers; doc rewrite is mechanical.

---

### 7. Verification Layers

**Status:** UNCHANGED (2026-08-23)

**Current:** `RecipeVerifier` exists in BOTH `src/harness/pev/verifier.py` AND
`src/core/verifier.py` — near-identical implementations, both actively
imported (see item 5). Two further verification layers exist downstream:

| Layer | Location | Role |
|---|---|---|
| `RecipeVerifier` (copy 1) | `src/core/verifier.py` | Canonical verifier for `src/core/orchestrator/` |
| `RecipeVerifier` (copy 2) | `src/harness/pev/verifier.py` | Harness PEV verifier (+`explain()`, quality gates) |
| `VerificationPipeline` | `src/mekongcli/core/verification/` | Goal-engine verification gates |
| `PostGate` | `src/daemon/gate.py` | Daemon post-execution gate |

**Recommendation:** Converge the two `RecipeVerifier` copies first (item 5);
then evaluate whether `VerificationPipeline` and `PostGate` can delegate to
the canonical verifier instead of re-implementing checks.

**Risk:** MEDIUM — All four layers are live in different execution paths.

---

### 8. Orphan Command Modules in src/commands/

**Status:** STALE COUNT FIXED (2026-08-23)

**Current:** `src/commands/` contains **37** `.py` files (previous map said
20). Of these, 16 modules have zero references from the live CLI — including
`src/commands/core_commands.py` (duplicates registered `ask`/`cook`, see item
6) and funnel modules like `src/commands/zalo_oa.py` which is intact and
tested but reachable only via `python -m`, not through `mekong`.

**Recommendation:** Audit the 16 zero-reference modules: register the ones
that are real features (Zalo OA funnel), delete the rest.

**Risk:** LOW — Deletion candidates have 0 importers; registration candidates
need `src/cli/app_setup.py` wiring + smoke tests.
