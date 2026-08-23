# Deprecation Map

Refreshed: 2026-08-23 · HEAD: 0878f966f

## Resolved by Deletion (PR #2, 0878f966f)

| Former candidate | Resolution |
|---|---|
| Basic MemoryStore shim (former `core/memory.py`) | **DONE** — the 4-line shim re-exporting `src/core/memory_canonical.py` was fully deleted in PR #2. Importers now bind directly to `src/core/memory_canonical.py` or `src/core/memory_store.py` (see DUPLICATION_MAP item 3). |
| `raas/billing_core.py` | **DONE** — deleted in PR #2. `src/billing/` is now a pure re-export facade over `src/raas/billing_engine.py`, `billing_proration.py`, `billing_idempotency.py`, `billing_audit.py`. |
| `core/llm_router.py` | **N/A — PHANTOM** — never existed in git history. Only `src/core/llm_router_adapter.py` (live) and `src/daemon/llm_router.py` (dead, see candidates below) ever existed. Reference removed. |
| `commands_registry.py` (former cli-package registry) | **DONE** — deleted in PR #2. Aggregator is now `src/cli/app_setup.py` (Typer-based). |

---

## Candidates for Deprecation

### 1. Direct LLM Client Calls (src/core/llm_client.py)

**Status:** WRAPPED (2026-08-21) — re-verified at HEAD

**Current:** `LLMRouterAdapter` (`src/core/llm_router_adapter.py`) delegates to
`LLMClient` for all generation methods (`generate`, `stream`,
`structured_output`). `LLMClient` retains its real production logic (provider
failover, caching, hooks, circuit breaker) and its public API is unchanged.
~32 caller files continue to use `LLMClient` directly — they are not yet
migrated to the Protocol interface.

**Migration path:** Future — migrate remaining callers from `LLMClient` direct
imports to the `LLMRouter` Protocol via `LLMRouterAdapter`. Adapter is ready;
callers are the remaining work.

**Risk:** LOW — Adapter wrapping is live; caller migration deferred.

---

### 2. Dict-Based Prompt Storage (DEFAULT_PROMPTS in agent_dispatcher.py)

**Status:** DEFERRED (2026-08-20) — re-verified at HEAD

**Current:** `DEFAULT_PROMPTS` lives in `src/core/agent_dispatcher.py`. Live
importers: `src/core/agent_registry.py`, `src/core/agent_dispatcher.py`, and
tests. `.mekong/agents/` is empty/nonexistent.

**Migration path:** Create `.mekong/agents/*.md` as the single source of
truth, then auto-generate `DEFAULT_PROMPTS` at build time. Deferred — no
markdown source exists yet.

**Risk:** LOW — Deferred until markdown prompt files exist.

---

### 3. Legacy Billing Routes (vn_pilot_billing.py, vn_payments_routes.py)

**Status:** DEFERRED — MEDIUM RISK (2026-08-20) — re-verified at HEAD

**Current:** Four billing route families remain mounted in `src/gateway.py`:
`src/api/billing_routes.py` (Polar), `src/api/raas_billing_service.py`,
`src/api/vn_pilot_billing.py`, `src/api/vn_payments_routes.py` (VietQR) — plus
`src/raas/nowpayments_router.py` and `src/raas/revenue_router.py` (see
DUPLICATION_MAP item 2). All live with distinct importers.

**Migration path:** Merge `vn_pilot_billing.py` + `vn_payments_routes.py` into
`billing_routes.py`. Update imports. Deferred — requires dedicated review.

**Risk:** MEDIUM — VN pilot and payments routes are live revenue paths.

---

### 4. Legacy Polar Webhook Artifacts

**Status:** DELETE — LOW RISK (2026-08-23)

**Current:** `src/api/polar_webhook.py.legacy` and
`tests/api/test_polar_webhook.py.legacy` still exist at HEAD. 0 importers.
Superseded by `src/api/webhooks/router.py` → `src/raas/revenue_router.py`
(mounted in `src/gateway.py`; the old `polar_webhook_router` mount is already
commented out at `src/gateway.py:100`).

**Migration path:** Delete both `.legacy` files. No import updates needed.

**Risk:** LOW — 0 importers; replacement path verified live.

---

### 5. src/old/ (Dead a2ui Copy)

**Status:** DELETE — LOW RISK (2026-08-23)

**Current:** `src/old/` contains a 4-file copy of a2ui. 0 importers; the live
implementation is `src/a2ui/`.

**Migration path:** Delete `src/old/` outright.

**Risk:** LOW — 0 importers; exact duplicate of live code.

---

### 6. Empty Package Shells (founder_vc, founder_ipo, sops-engine)

**Status:** DELETE — LOW RISK (2026-08-23)

**Current:** PR #2 deleted all modules inside these packages, leaving
docstring-only shells: `src/core/founder_vc/__init__.py`,
`src/core/founder_ipo/__init__.py` (0 importers each). Separately,
`src/harness/sops-engine/` contains only a 125-byte `__init__.py` stub.

**Migration path:** Delete the three shell directories.

**Risk:** LOW — 0 importers; no code inside.

---

### 7. Daemon LLM Router and Config

**Status:** DELETE — LOW RISK (2026-08-23)

**Current:** `src/daemon/llm_router.py` and `src/daemon/llm_config.py` have 0
importers post-f7d420c75 (verified by grep across `src/` and `tests/`). The
live routing path is `src/core/llm_router_adapter.py` → `src/core/llm_client.py`.

**Migration path:** Delete both files.

**Risk:** LOW — 0 importers verified.

---

### 8. Harness raas_auth Stub

**Status:** DELETE — LOW RISK (2026-08-23)

**Current:** `src/harness/observability/raas_auth/` is an always-False stub
(single `__init__.py`). The real client is the `src/core/raas_auth/` package
(`raas_auth_client.py` + `auth_gateway_mixin.py`) with 9+ importers
(`permission_registry.py`, `feature_gates.py`, `command_authorizer.py`,
`gateway_client/`, `activate_commands.py`, and more).

**Migration path:** Delete `src/harness/observability/raas_auth/`. Any harness
code importing it should import `src/core/raas_auth/` instead (none found).

**Risk:** LOW — Stub returns always-False; real client is the live surface.

---

### 9. src/core/tracing.py

**Status:** DEPRECATE → DELETE (2026-08-23)

**Current:** Only consumer is `tests/test_tracing.py` (test-only). Overlaps
`src/core/telemetry_collector.py`, which is the live trace-collection path.

**Migration path:** Port any unique assertions from `tests/test_tracing.py`
onto `src/core/telemetry_collector.py`, then delete both files.

**Risk:** LOW — Test-only consumer; overlap with live collector verified.

---

### 10. setup_telemetry (src/core/telemetry/sdk_setup.py)

**Status:** DEPRECATE → DELETE (2026-08-23)

**Current:** `setup_telemetry()` is exported from
`src/core/telemetry/__init__.py` but never called anywhere. The gateway uses
`init_telemetry()` from `src/core/telemetry_init.py` instead
(`src/gateway.py:60,64`).

**Migration path:** Remove `setup_telemetry` from the `__init__.py` exports
and delete `sdk_setup.py` (or fold its logic into `telemetry_init.py` if any
unique setup remains).

**Risk:** LOW — Exported but never invoked.

---

### 11. Root cli/ Package

**Status:** KEEP-BUT-FLAG (2026-08-23)

**Current:** The root `cli/` package (commands/, handlers/, tui/, ui/) has
exactly 2 importers, one of which is BROKEN: `src/command_fabric/router.py:25`
imports `cli.tui.router` which does not exist (the real module is
`src/cli/tui/router.py`) → ModuleNotFoundError at import time. The other
importer is `tests/test_tui_streaming.py` (test-only use of
`cli/tui/streaming.py`).

**Migration path:** Fold `cli/tui/` into `src/cli/tui/` (which already exists
with the real `router.py`), fix the `src/command_fabric/router.py` import to
point at `src/cli/tui/router.py`, update `tests/test_tui_streaming.py`, then
delete root `cli/`.

**Risk:** MEDIUM — Broken import means `src/command_fabric/router.py` is
already dead at runtime; migration must land atomically with the import fix.

---

### 12. src/mekong/ vs src/mekongcli/

**Status:** KEEP BOTH (2026-08-23)

**Current:** Despite similar names, the two packages are verified DISTINCT
domains with zero subdirectory-name overlap:

| Package | Domain |
|---|---|
| `src/mekong/` (40 files) | cells, commons, constitution, founder, graph, treasury, zenpay |
| `src/mekongcli/` (22 files) | goal_engine, governance, memory, orchestrator, swarm, telemetry, verification |

`src/mekongcli/` is live — imported by `src/cli/cook_command.py`,
`src/cli/goal_commands.py`, and `src/cli/commands/implement/`.

**Migration path:** None — keep both. Add a naming note to
CURRENT_ARCHITECTURE.md so future readers don't treat them as duplicates.

**Risk:** LOW — No action required.

---

### 13. Unregistered CLI Apps (Decision Needed)

**Status:** UNREGISTERED (2026-08-23)

**Current:** Three complete Typer apps are never registered in
`src/cli/app_setup.py` and have 0 importers:

| File | Decision options |
|---|---|
| `src/cli/billing_commands.py` | Register in `app_setup.py` OR delete |
| `src/cli/pev_commands.py` | Register in `app_setup.py` OR delete |
| `src/cli/usage_commands.py` | Register in `app_setup.py` OR delete |

**Migration path:** Product decision required — if the commands are wanted
(note: `billing` and `usage` are among the 16 commands advertised in
`src/commands/COMMAND_REGISTRY.md` but missing from the live CLI), register
them; otherwise delete.

**Risk:** LOW either way — 0 importers; registration needs smoke tests.

---

## Completed (Historical)

### Duplicate NOWPayments Module (nowpayments-checkout.py)

**Status:** DONE (2026-08-20)

Deleted the hyphenated `nowpayments-checkout.py` and
`nowpayments-webhook-handler.py`; verified byte-identical to the underscore
versions (`src/raas/nowpayments_checkout.py`,
`src/raas/nowpayments_webhook_handler.py`) via `diff`/`md5`. Tests updated to
load the canonical underscore versions. Risk: LOW.

### Governance Binary Classification

**Status:** DONE (2026-08-20)

`Governance` has `ActionClass` enum (SAFE/REVIEW_REQUIRED/FORBIDDEN) in
`src/core/governance.py`; `GovernanceDecision` carries `action_class`,
`reason`, `requires_approval`, `approved`. Both `autonomous.py` and
`src/core/runtime_adapter.py` gate on `decision.action_class`. Risk: LOW.

### AgentDispatcher Protocol (duplicate definition)

**Status:** DONE (2026-08-20)

Removed the `AgentDispatcher` Protocol from `src/core/protocols.py` entirely
(0 importers). `AgentRegistry` (`src/core/agent_registry.py`) is the canonical
dispatch surface (`get()`, `list_agents()`, `discover()`, `get_meta()`);
`build_message_chain()` and `load_agent_prompt()` live in
`src/core/agent_dispatcher.py` as standalone functions. Risk: LOW.

---

## Not Deprecated (Keep As-Is)

| Component | Reason |
|-----------|--------|
| `src/core/memory_client.py` | NeuralMemoryClient may have unique vector features |
| `src/strategies/polymarket/` | Separate domain, not conflicting (empty shell — `__init__.py` only) |
| `src/studio/` | Video studio is a product vertical (scaffold: `models.py` only) |
| `src/mekong/` | Distinct domain from `src/mekongcli/` — verified, see item 12 |
| `src/mekongcli/` | Live goal-engine stack — imported by cook/goal/implement commands |
| `src/core/orchestrator/` | LIVE package (modularized in 8f4a62633: models, display, rollback, step_executor, agi, runner) — canonical for `mekong cook`, gateway, raas_router, telegram; 15+ importers. Removed from deprecation candidates. |
| `src/commands/` | 37 command modules; aggregator is `src/cli/app_setup.py` (53 live commands) |
| `src/db/tier_config_repository.py` | Rate-limiting config (DB-backed), distinct from `src/seed/config/tiers.py` pricing/credits |
| `src/core/llm_client.py` | Real production LLM client with failover/caching; wrap behind adapter, do not replace |
