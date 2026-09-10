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

**Status:** RESOLVED (2026-09-10) — canonical store & JSONL adapter both satisfy protocols.MemoryStore

**Resolution:**
- `src/core/memory_canonical.py:MemoryStore` retrofitted with `store()`, `retrieve()`, `delete()`, and `search()`, satisfying `protocols.MemoryStore` runtime checkable protocol natively.
- Byte-exact base64 encoding guarantees arbitrary binary preservation across storage/retrieval.
- TTL expiry support integrated via `expires_at` metadata in entry context.
- Point deletion from `VectorMemoryStore` synchronized on `delete(key)`.
- `src/core/adapters/jsonl_memory_adapter.py:JsonlMemoryAdapter` formalizes JSONL as a second conformant backend.
- `MemoryStoreAdapter` and `MemoryStoreConformant` unified to delegate directly to canonical methods.
- Runtime conformance tests in `tests/test_memory.py` and `tests/ports/test_memory_store_conformance.py` pass 100%.

---

### 4. Observability Assets (Grafana Dashboards / Provisioning)

**Status:** IMPROVED (2026-09-10) — nested duplicate directories pruned

**Current:** Previously, three copies of the same dashboard JSON and provisioning YAML existed.
The accidental nested duplicate directories (`src/harness/observability/dashboards/dashboards/`
and `src/harness/observability/provisioning/provisioning/`) have been removed.

Root `observability/dashboards/` and `src/harness/observability/dashboards/` remain as
canonical and harness-adjacent copies. Compose and collector configs:
root `observability/docker-compose.observability.yml` + `prometheus.yml` + `otel-collector-config.yaml`
vs `src/harness/observability/docker-compose.yml` + `prometheus.yml` + `otel-collector.yaml`.

**Recommendation:** Maintain root `observability/` as canonical; keep harness copies aligned.

**Risk:** LOW — Static assets; verified zero references to nested directories.

---

### 5. LLM Routing & PEV Engine Convergence

**Status:** RESOLVED (2026-09-10) — harness PEV duplicates merged into core

**Resolution:**
- `src/harness/pev/planner.py` deleted; consumers import canonical `src/core/planner.py`.
- `src/harness/pev/verifier.py` merged into `src/core/verifier.py:RecipeVerifier` and deleted.
- `src/harness/pev/dag_scheduler.py` unified to delegate directly to `src/core/dag_scheduler.py:DAGScheduler`.

---

### 6. CLI Command Surfaces

**Status:** RESOLVED (2026-09-10) — unified on `src/cli/app_setup.py` & `workflow_commands.py`

**Resolution:**
- Canonical single aggregator is `src/cli/app_setup.py` (Typer-based, 39 registered groups, 128 commands).
- Natural language bilingual (VI/EN) router ported directly into canonical `src/cli/workflow_commands.py:ask_cmd`, dispatching leaf subcommands (`cook`, `debug`) and gracefully falling through for command groups (`plan`, `deploy`).
- `src/commands/core_commands.py` converted to backward-compatible deprecation shim forwarding to `src.cli.app_setup.build_app()`.
- `tests/integration/test_ask_routing.py` repointed directly to canonical `src.cli.app_setup.build_app()`.
- `src/commands/COMMAND_REGISTRY.md` updated to match `build_app()` command tree (39 groups, 128 commands).
- `billing_commands`, `pev_commands`, and `usage_commands` verified registered in `src/cli/app_setup.py`.

---

### 7. Verification Layers

**Status:** RESOLVED (2026-09-10) — RecipeVerifier unified into core and integrated into autonomous runtime execution loop

**Resolution:**
- `RecipeVerifier` merged into canonical `src/core/verifier.py` (PR #14, Super Command #8).
- Merged into `MekongCoreRuntimeImpl.verify()` via `_criteria_to_verifier_dict` and `_ExecResultLike` adapter, validating exit codes, pattern regexes, and file presence.
- Autonomous loop implements full `execute -> verify -> repair` cycle with four strategies (`RETRY`, `FALLBACK`, `ESCALATE`, `ROLLBACK`).
- Downstream task cancellation wired through `DAGScheduler.mark_failed` to prevent cascading runs on upstream verification failures.
Remaining verification layers:

| Layer | Location | Role |
|---|---|---|
| `RecipeVerifier` | `src/core/verifier.py` | Canonical verifier for orchestrator and runtime |
| `VerificationPipeline` | `src/mekongcli/core/verification/` | Goal-engine verification gates |
| `PostGate` | `src/daemon/gate.py` | Daemon post-execution gate |

---

### 8. Orphan Command Modules in src/commands/

**Status:** RESOLVED (2026-09-10) — dead stubs deleted, funnels reconnected, core shimmed

**Resolution:**
- Reconnected Vietnam business funnels (`zalo_oa.py`, `thue_dnvn.py`, `ke_toan.py`) to the CLI binary via `src/cli/funnel_commands.py` (`zalo-oa`, `thue`, `ke-toan`).
- Pruned zero-reference empty dead stubs `src/commands/ci.py` and `src/commands/env.py`.
- Deprecated `src/commands/core_commands.py` to forward to canonical `src.cli.app_setup:build_app()`.
