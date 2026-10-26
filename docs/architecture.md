# Mekong Architecture — Autonomous Runtime v6.0 (25-Step Open-Core + Cloud RaaS)

> Refreshed: 2026-10-26 · Scope: v6.0 25-Step Open-Core & Cloud RaaS convergence
> ("one verifier, one DAG order, strict MIT vs RaaS boundary" — see
> [IMPLEMENTATION_PLAN.md](./architecture/IMPLEMENTATION_PLAN.md) and
> `src/core/opencore/phase_559_opencore_25_step_catalog.py`).

Mekong CLI is an open-source autonomous runtime for Solo Companies, Solo
Vibe Coders, and Vietnamese SMEs: one operator delegates goals to AI agents
that plan, execute, verify, repair, and pay for tools — on your own
infrastructure (MIT Open-Core) or via the managed Cloud RaaS Control Plane.

## Component map (text diagram)

```text
 External callers                CLI surface (39 Typer groups via build_app())
 ───────────────                 ─────────────────────────────────────────────
 Buzz / webhook payload ──┐      mekong run --goal "..."  [src/commands/run.py]
                          │                  │
                          ▼                  ▼
        ┌──────────────────────────────────────────────────────────┐
        │            MekongCoreRuntimeImpl (MIT Open-Core)         │
        │            src/core/runtime_adapter.py                   │
        │                                                          │
        │  goal → plan → delegate → execute → observe → verify     │
        │        → repair (≤3) → remember → commit                 │
        │                                                          │
        │  run()           : plain text entry, idempotent mission   │
        │  run_from_payload(): Buzz entry, pre-assigned mission_id │
        │  execute() gates : governance → capability → cost        │
        └───────┬──────────────────┬──────────────────┬─────────────┘
                ▼                  ▼                  ▼
   ┌────────────────────┐ ┌─────────────────┐ ┌──────────────────────┐
   │ CapabilityBus      │ │ Governance      │ │ PaymentProvider      │
   │ InMemory impl;     │ │ ONE decision    │ │ MCUBilling (HTTP 402)│
   │ BUILTIN/CLI/MCP    │ │ path: risk map  │ │ Dual-Rail Checkout:  │
   │ sources via        │ │ + audit + loud  │ │ vietqr (Napas 247) + │
   │ adapters           │ │ auto-approve    │ │ nowpayments (USDT)   │
   └────────────────────┘ └─────────────────┘ └──────────────────────┘
                │                  │                  │
                ▼                  ▼                  ▼
   ┌────────────────────┐ ┌─────────────────┐ ┌──────────────────────┐
   │ ToolRegistry / MCP │ │ LocalExecution  │ │ Cloud RaaS Control   │
   │ adapter            │ │ Runtime:        │ │ Plane (src/raas/):   │
   │ (sync_from_mcp)    │ │ subprocess +    │ │ HMAC-SHA256 License  │
   └────────────────────┘ │ sandboxed fs    │ │ Verifier + Credit    │
                          └─────────────────┘ │ Store + RBAC/Audit   │
                                              └──────────────────────┘
```

## 25-Step Open-Core Boundary & RaaS Control Plane

Mekong CLI enforces a strict 25-step Open-Core boundary defined in
`src/core/opencore/phase_559_opencore_25_step_catalog.py` (`TWENTY_FIVE_OPENCORE_STEPS`)
and verified at 100.0% readiness by
`src/core/opencore/phase_560_opencore_saas_readiness_engine.py` (`OpenCoreSaasReadinessEngine.audit_repository(".")` → `PUBLIC_GITHUB_SAAS_READY`):

1. **`PHASE_1_SPLIT_AND_HYGIENE` (Steps 1–5):** `git-history-secret-purge`, `oss-vs-ee-directory-split`, `gitignore-quarantine-lock`, `env-example-byok-template`, `mit-license-and-sbom` (CycloneDX 1.5).
2. **`PHASE_2_PLUGIN_AND_SEAMS` (Steps 6–10):** `capability-bus-interfaces`, `byok-local-adapters`, `cloud-bridge-webhooks`, `local-sandbox-runtime`, `versioned-openapi-sdk`.
3. **`PHASE_3_CLOUD_CONTROL_PLANE` (Steps 11–15):** `jwt-license-gate` (`MEKONG-RAAS-v1` / `SOPHIA-RAAS-v1` HMAC-SHA256 in `src/core/raas_license_verifier.py`), `mcu-credit-metering` (`HTTP 402 Payment Required`), `tiered-rate-limiting` (`BASIC`, `PREMIUM`, `ENTERPRISE`, `MASTER`), `managed-worker-queues`, `encrypted-key-vault`.
4. **`PHASE_4_ENTERPRISE_MONETIZATION` (Steps 16–20):** `multi-tenant-rbac-isolation`, `compliance-audit-ledger` (immutable SHA-256 chain), `always-on-cloud-daemon`, `strategy-recipe-marketplace`, `payment-webhook-activation` (Dual-Rail `vietqr` + `nowpayments`; legacy `POST /webhook/polar` returns `HTTP 410 Gone`).
5. **`PHASE_5_PLG_GROWTH_AND_GOVERNANCE` (Steps 21–25):** `sixty-second-quickstart`, `cli-to-cloud-upsell-prompt`, `ci-leak-and-loc-gate` (`<= 185 LOC` per Open-Core module), `public-benchmark-trust-badge`, `cla-and-trademark-policy`.

### Commercial RaaS Tiers (`src/raas/checkout_router.py`)

| Tier | USD | VND | MCU Quota |
|------|-----|-----|-----------|
| `BASIC` | $199 | 4,975,000 | 1,500 MCU |
| `PREMIUM` | $399 | 9,975,000 | 4,000 MCU |
| `ENTERPRISE` | $799 | 19,975,000 | 10,000 MCU |
| `MASTER` | $4,999 | 124,975,000 | 100,000 MCU |

## The four buses in one page

| Bus | Doc | Entry class | v6.0 state |
|-----|-----|-------------|------------|
| Lifecycle (core contract) | [core-contract.md](./core-contract.md) | `MekongCoreRuntimeImpl` | Wired; pinned by contract tests |
| Capabilities | [capability-bus.md](./capability-bus.md) | `InMemoryCapabilityBus` | Injected into `mekong run` by default |
| Economic & RaaS | [economic-bus.md](./economic-bus.md) | `PaymentProvider` + `CreditStore` | Dual-Rail (`vietqr` + `nowpayments`) + HMAC-SHA256 license verifier |
| Buzz/runtime | [buzz-runtime-adapter.md](./buzz-runtime-adapter.md) | `BuzzRuntimeAdapter` | Versioned `v0.1`, in-process |

Execution isolation is documented in
[runtime-adapters.md](./runtime-adapters.md); the risk/approval model in
[autonomy-model.md](./autonomy-model.md).

## Design rules enforced by tests

1. **One lifecycle engine** — no second goal→commit loop outside
   `runtime_adapter.py` (`tests/test_core_lifecycle_contract.py`).
2. **Provider-neutral core** — no vendor SDK imports in `src/core/`
   (`tests/test_core_boundary.py`; `llm_client.py` is the single documented
   transitional exception).
3. **One policy decision path** — every execution decision flows through
   `Governance.classify_risk` with mandatory audit entries.
4. **Cryptographic RaaS Entitlement & Dual-Rail** — `RAAS_LICENSE_KEY` tokens are
   signed and verified with stdlib-pure HMAC-SHA256 (`src/core/raas_license_verifier.py`),
   and license activation credits `CreditStore` idempotently (`act_<sha256>`).
5. **Immutable 25-Step Catalog** — `src/core/opencore/phase_559_opencore_25_step_catalog.py`
   is locked byte-for-byte (`tests/test_durian_grab_honest_diagnosis.py`).

## Runtime behavior

### `verify()` delegates to `RecipeVerifier`

`MekongCoreRuntimeImpl.verify()` (at `src/core/runtime_adapter.py`) delegates
to the same `RecipeVerifier` the harness (`PEVOrchestrator`, `RecipeOrchestrator`)
uses — collapsing two divergent quality bars into one:

- `_ExecResultLike` — bridges core `Result` (output/error/metadata) to the
  `ExecutionResult`-shaped object `RecipeVerifier.verify()` reads.
- `_criteria_to_verifier_dict` — maps core `CheckSpec` kinds (`exit_code`,
  `output_pattern`) to the criteria-dict keys `RecipeVerifier` consumes.
- `_report_to_verification` — maps `VerificationReport` back to core
  `Verification`, propagating FAILED/WARNING checks and `report.errors`.

### `_run_goal` executes multi-step plans in topological (DAG) order

`_run_goal` iterates tasks in dependency-respecting order via:

- `_plan_has_dependencies(plan)` — fast-path check for single-step plans.
- `_topological_task_order(tasks)` — Kahn's algorithm keyed by
  `task.step.id`, raising `RuntimeError` on cycles.

Full historical gap analysis: [architecture/ARCHITECTURE_AFTER_PHASE_2.md](./architecture/ARCHITECTURE_AFTER_PHASE_2.md).

## OPC Global Platform Layer (`src/opc/`)

The OPC (One-Person Company) platform subsystem provides a neutral, verifiable runtime layer for solo consultants, technical freelancers, and independent agencies worldwide while keeping 100% backwards compatibility with existing Mekong CLI contracts:

- **Neutral Core Runtime (`src/core/runtime_adapter.py`)**: `MekongCoreRuntimeImpl` accepts injectable `role_agent_map` and `intent_keywords` so business packs can execute with custom roles (e.g., `solo_consultant`, `technical_freelancer`) without hardcoded C-Suite titles.
- **Declarative Pack Manifest (`src/opc/manifest.py`, `opc-pack/v1`)**: Static JSON manifest validated as pure data (`compatible_runtime`, `capabilities`, `input_schema`, `output_schema`, `approval_requirements`, `cost_policy`) without dynamic code execution.
- **Payload-Bound Approval Engine (`src/opc/approval.py`)**: Binds human approval tokens to a canonical SHA-256 `action_digest` computed over `(principal, capability, connector, recipient, content, parameters, attachments, budget_amount, budget_currency, expires_at)`. Any payload mutation invalidates the approval; tokens enforce single-use consumption, TTL expiration, and revocation.
- **SQLite WAL State & Idempotency (`src/opc/state.py`)**: Persists workflow runs (`opc_runs`), approval tokens (`opc_approvals`), and external connector actions (`opc_actions`) keyed by `idempotency_key`. Uncertain external effects are flagged as `reconciliation_required` rather than silently retried.
- **Honest Usage Economics (`src/opc/usage.py`)**: Tracks `estimated`, `reserved`, `actual`, and `unknown` cost events in `opc_usage_events`. Unknown costs (`stage="unknown"` or `amount=None`) are preserved as `has_unknown_costs=True` and never coerced to `0`.
- **Reference Pack (`src/opc/packs/client-proposal-followup/`) & Country Pack (`src/opc/packs/vn-sme-ops/`)**: End-to-end offline 2-Goal workflow (`Goal 1: intake_to_draft`, `Goal 2: decision_to_followup`) runnable via `mekong opc validate-pack`, `mekong opc proposal --wait-approval`, `mekong opc decide`, `mekong opc status`, or `mekong run --pack <pack_id>`. Country packs encapsulate jurisdiction-specific legal references (`Decree 123/2020/ND-CP`, `Circular 78/2021/TT-BTC`) behind AST-isolated boundaries without polluting the neutral core.

