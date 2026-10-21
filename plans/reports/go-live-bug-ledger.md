# Go-live Bug Ledger

Snapshot: 2026-10-18  
Candidate: `feat/trade-transport-remedies-suite-phases-163-166`

This ledger separates confirmed behavior bugs from architecture findings and
release gates. “No confirmed bug” means the current evidence has not shown an
incorrect behavior; it does not prove the absence of latent defects.

## GitHub issue trackers

| Tracker | Live check | Disposition |
|---|---|---|
| [minhlongs/mekong-cli issues](https://github.com/minhlongs/mekong-cli/issues) | GitHub page showed **0 open issues** on 2026-10-18. | No open issue reported by the canonical repository tracker. |
| [longtho638-jpg/mekong-cli issues](https://github.com/longtho638-jpg/mekong-cli/issues) | GitHub returned **404** on 2026-10-18. | This is a stale repository URL, not a readable second tracker. Root/package-manager metadata and install links have been corrected to the canonical `minhlongs/mekong-cli` repository. |

The 404 is not treated as evidence that the legacy tracker has zero issues.
The currently configured Git remotes, README, PyPI metadata, and support links
all identify `minhlongs/mekong-cli` as the canonical repository.

## Architecture audit IDs (`ISS-001` through `ISS-027`)

Source report: [`step10-issue-classification.md`](step10-issue-classification.md).
The report dates from 2026-08-17 and contains stale paths and claims; each row
below reflects a current-tree check on 2026-10-18.

| ID | Current classification | Current evidence and disposition |
|---|---|---|
| ISS-001 | Resolved duplicate claim; architecture debt remains | `src/harness/agents/dispatcher.py` is absent. `src/core/agent_dispatcher.py` remains; `src/daemon/dispatcher.py` is a separate worker-pool component. No divergent runtime failure is confirmed. |
| ISS-002 | Resolved duplicate claim | `src/harness/pev/orchestrator_pkg/runner.py` is absent. The remaining PEV orchestration module is still present as a compatibility/runtime layer. |
| ISS-003 | Resolved | `src/harness/observability/collector.py` is absent; the canonical collector is under `src/core/telemetry_collector.py`. |
| ISS-004 | Resolved | `src/harness/observability/health.py` is absent; the canonical reporter is under `src/core/health_reporter.py`. |
| ISS-005 | Resolved | `src/harness/observability/telemetry/` is absent; runtime telemetry implementation remains under `src/core/telemetry/`. |
| ISS-006 | Resolved | `src/harness/core/router.py` is absent; `src/core/hybrid_router.py` remains. |
| ISS-007 | Architecture debt; no behavioral mismatch confirmed | SQLite CLI usage tracking and PostgreSQL engine usage metering both remain. They serve separate runtime paths. Billing correctness still requires the release's staging/sandbox billing checks. |
| ISS-008 | Architecture debt; no billing defect confirmed | MCU billing and engine payment/tier components remain with distinct responsibilities. The unused tier-rate middleware is deleted. Billing consolidation/protocol tests pass in the targeted run. |
| ISS-009 | Resolved for shared tier configuration | `engine/billing/tier_config.py` re-exports the canonical tier symbols. Polymarket keeps a separate domain-specific tier type. `tests/test_billing_consolidation.py` checks symbol identity and aliases. |
| ISS-010 | Resolved | `src/core/pev_errors.py` is absent. `src/core/exceptions.py` owns domain exceptions; API `ErrorResponse` remains a separate response model. |
| ISS-011 | Architecture debt; no registry behavior bug confirmed | Harness `registry.py` re-exports `src.core.agent_registry`; a separate `AgentFactory` still loads `agents/registry.yaml`. Tests must continue to cover both consumer paths. |
| ISS-012 | Resolved | Legacy `cli/entrypoint.py` is absent; `src/main.py` remains the primary entry point. |
| ISS-013 | Architecture debt; no routing failure confirmed | `src/daemon/llm_router.py` is absent. A daemon classifier remains for worker tasks; this is a separate dispatch path. |
| ISS-014 | Audit claim corrected | Several listed PEV files are absent, while live compatibility modules such as `src/harness/pev/memory.py` and `telemetry.py` remain. They are not removed as “dead” code. |
| ISS-015 | Resolved except one empty placeholder | `plugins/`, `sample/`, `cloudflare-skills/`, and `agy-marketplace/` are absent. `models/` remains empty; this is repository hygiene, not a runtime defect. |
| ISS-016 | Resolved | No root `fix_*.py`, `apply_*.py`, or `verify_*.py` scripts remain. |
| ISS-017 | Open pending triage | `scripts/mcp_server.py` contains JSON-RPC 2.0 `tools/list` and `tools/call`, but the whole-repository run currently reports 6 failures in `tests/test_antigravity_mcp.py`. Do not close this issue until the failure traceback and standard/fallback paths are rechecked. |
| ISS-018 | Resolved at protocol level | `src/core/protocols.py` defines `MekongCoreRuntime`; `src/core/runtime_adapter.py` provides `MekongCoreRuntimeImpl`. |
| ISS-019 | Resolved at protocol level | `src/core/protocols.py` defines `PaymentProvider`; `NowPaymentsProvider` and `BillingAdapter` are covered by `tests/test_billing_consolidation.py`. |
| ISS-020 | Confirmed defect fixed | `AGILoop` defaults to manual approval and gates execution. `tests/test_agi_loop.py`: 34 passed. |
| ISS-021 | Confirmed defect fixed | All swarm routes use `require_swarm_token`. `tests/core/gateway/test_gateway_main.py` passed in the targeted run (55 tests). |
| ISS-022 | Resolved as an unused-control defect | The never-mounted `engine/billing/tier_rate_limit_middleware.py` was removed. Tier configuration routes and middleware conformance are covered by current billing tests. |
| ISS-023 | Resolved for the canonical memory contract | `MemoryBridge`, `MemoryStoreBridge`, and `memory_canonical.MemoryStore` remain; the targeted protocol suite passed. Full release-suite evidence is still pending. |
| ISS-024 | Architecture debt; no telemetry loss defect confirmed | Duplicate harness telemetry copies and `src/observability/` are absent. Remaining code, package, and infra directories have different runtime/deployment roles. |
| ISS-025 | Architecture debt; no duplicated LLM router remains | The daemon-specific LLM router is absent. Its background worker pool and dispatcher remain separate components. |
| ISS-026 | Resolved | `src/harness/pev/telemetry.py` is a re-export shim to `src.core.telemetry_collector`, not a third implementation. |
| ISS-027 | Intentional domain separation | Polymarket's tier type is local to that integration; no shared billing behavior is routed through it. |

## Confirmed fixes and checks

| Finding | Fix/check | Result |
|---|---|---|
| Repository and issue links pointed at a 404 GitHub owner | Updated package metadata, install links, generated package-manager metadata, and corresponding assertions to `minhlongs/mekong-cli`. | `tests/test_command_fabric_package_managers.py`: 2 passed. |
| AGI loop could execute without approval | Approval gate in current code. | `tests/test_agi_loop.py`: 34 passed. |
| Swarm endpoints lacked header authentication | Fail-closed `X-API-Key` dependency on swarm routes. | Gateway test module passed in targeted run. |
| Public VietQR simulator could imply real settlement | No HMAC key in `site/public/_worker.js`; simulator response is `demo_only: true`, `verified: false`, and explicitly says no payment or MCU credit occurred. Regression checks cover static pages, JS, and React API. | `tests/test_site_demo_safety.py`: 3 passed. |

## Remaining release gates (not bug closures)

- Full Python suite and all target package checks have not completed on this
  snapshot yet.
- Dashboard worker build is unverified locally because `vinext` is not
  installed; dependency installation previously failed on DNS resolution.
- Staging D1 migration rehearsal, service-backed smoke tests, payment sandbox
  check, production promotion, and 30-minute monitoring have not run. GitHub
  CLI authentication is invalid and the Cloudflare session/network is
  unavailable in this environment.
- The worktree contains 1,783 changed paths at this snapshot and has not been
  reviewed as a release candidate. No files have been staged, committed, or
  deployed by this ledger work.
