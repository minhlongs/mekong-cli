# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Identity

Mekong CLI v6.0 — AI-operated business platform for Vietnamese one-person companies and SMEs. MIT licensed Open-Core + Cloud RaaS Control Plane (25-Step `/idea` blueprint at 100.0% `PUBLIC_GITHUB_SAAS_READY`). Public repo.

Core funnels:
1. Zalo OA (`zalo_oa`) — customer communication automation
2. Tax & Accounting (`thue_dnvn`, `ke_toan`) — TNCN/TNDN/GTGT compliance + TT78 invoices
3. AI Video Factory (`sophia`) — AI video generation on CF Workers

## Commands

Run from repo root. 39 command groups wired via `build_app()`
(`python3 -c "from src.cli.app_setup import build_app; print(len(build_app().registered_groups))"`).

- Design intelligence: `mekong ui {audit,study,redesign,build,approve,benchmark}`
  (see `docs/design-intelligence.md`)
- Python tests: `python3 -m pytest tests/ -v`
- Open-Core & RaaS boundary gate:
  `python3 -m pytest tests/test_opencore_saas_25_step_suite.py tests/test_core_boundary.py tests/test_dual_rail_checkout.py tests/test_raas_license_verifier.py tests/test_durian_grab_honest_diagnosis.py tests/test_idea_run_blueprint_writing.py tests/test_opencore_git_boundary_guard.py tests/test_github_content_25_step_sync.py -v`
- Lint: `python3 -m ruff check src/core/opencore/ tests/`
- Single test file: `python3 -m pytest tests/<path> -v`

## Architecture

mekong (CLI) / api-gateway (FastAPI:8000)
- `src/core/` — autonomous runtime core: lifecycle (`runtime_adapter`), Governance, capability bus, protocols, MCU billing, `exec_runtime` sandbox, adapters (tool/MCP/payment/buzz), `raas_license_verifier.py` (HMAC-SHA256 `MEKONG-RAAS-v1` / `SOPHIA-RAAS-v1`), and `src/core/opencore/` (25-step catalog + readiness engine, strictly `<= 185 LOC` per module)
- `src/raas/` — Cloud RaaS Control Plane: `checkout_router.py` (Dual-Rail `vietqr` + `nowpayments`), `revenue_router.py` (`POST /webhook/polar` returns `HTTP 410 Gone`), `credits.py` (SQLite WAL `CreditStore` with replay-safe idempotency), `tenant.py`
- `src/commands/` — command modules behind the 39 CLI groups
- `src/cli/` — Typer app assembly (`app_setup.build_app`), build wizard
- `src/harness/` — PEV engine (plan-execute-verify), agents, observability
- `src/api/` — REST routes (raas, billing, gateway)
- `src/middleware/` — `license_gate` (HMAC-SHA256 / JWT + MCU balance check)
- `src/services/` — org service and clients
- `src/mekongcli/` — GoalEngine service (cook/goal/implement consumers)
- `src/seed/` — foundational auth, DB, config, types
- `src/daemon/` — scheduler with fail-closed command sanitizer

Autonomous runtime docs: `docs/architecture.md`, `docs/core-contract.md`,
`docs/capability-bus.md`, `docs/economic-bus.md`, `docs/buzz-runtime-adapter.md`,
`docs/runtime-adapters.md`, `docs/autonomy-model.md`

## Billing & Commercial RaaS (Dual-Rail)

- MCU: 1 MCU = 1 credit (`MCUBilling` + `CreditStore` atomic SQLite WAL ledger, `HTTP 402 Payment Required` on depletion)
- Dual-Rail Checkout (`src/raas/checkout_router.py`):
  - `vietqr` — Domestic Vietnam Napas 247 instant transfer (`VietQrEngine` EMVCo dynamic QR)
  - `nowpayments` — International USDT / Crypto IPN webhook → instant tier & credit activation
  - Legacy `POST /webhook/polar` is permanently decommissioned (`HTTP 410 Gone`, `polar_rail_decommissioned`)
- Cryptographic License Keys: `MEKONG-RAAS-v1.<payload_b64>.<sig>` and `SOPHIA-RAAS-v1.<payload_b64>.<sig>` activated via `POST /v1/license/activate`
- Commercial Tiers (`COMMERCIAL_TIERS`):
  - `BASIC`: $199 / 4,975,000 VND / 1,500 MCU
  - `PREMIUM`: $399 / 9,975,000 VND / 4,000 MCU
  - `ENTERPRISE`: $799 / 19,975,000 VND / 10,000 MCU
  - `MASTER`: $4,999 / 124,975,000 VND / 100,000 MCU

## Quality & Invariants

- Python: ruff, mypy, pytest
- Never modify `src/core/opencore/phase_559_opencore_25_step_catalog.py` (byte-for-byte invariant enforced by `tests/test_durian_grab_honest_diagnosis.py`)
- Open-Core modules in `src/core/opencore/` and `src/core/raas_license_verifier.py` must remain `<= 185 LOC`
- No console statements in production
- Tests must pass before push

## Public Repo Boundary

- `apps/` — private client projects (except public dashboard scaffolds explicitly tracked)
- `.env*` — never commit (only `.env.example` placeholder template)
- `app/` — private client projects
- `billing/` — internal workspace (dịch vụ, không public)
