# 25-Step Open-Core Public GitHub + SaaS Monetization Architecture
# Kiến Trúc 25 Bước Mã Nguồn Mở Public GitHub + Thu Tiền SaaS

**Version:** 6.0 | **Date:** 2026-10-17 | **License:** MIT (Core/CLI) + Commercial SLA (Cloud Control Plane)

---

## 1. Overview / Tổng Quan

**EN:** Mekong CLI separates its local-first MIT runtime (`src/core/`, `src/cli/`) from its hosted Cloud SaaS Control Plane (`src/api/`, `src/middleware/license_gate.py`, `src/core/mcu_billing.py`, `src/raas/payos_webhook_handler.py`). Developers clone and run the CLI on GitHub for free using their own API keys (BYOK), while teams and solo founders upgrade to managed tiers (`BASIC`, `PREMIUM`, `ENTERPRISE`, `MASTER`) and top up MCU credits via VietQR / PayOS or NOWPayments.

**VN:** Mekong CLI tách biệt hoàn toàn lõi MIT chạy local (`src/core/`, `src/cli/`) khỏi Cloud SaaS Control Plane (`src/api/`, `src/middleware/license_gate.py`, `src/core/mcu_billing.py`, `src/raas/payos_webhook_handler.py`). Lập trình viên có thể clone từ GitHub và dùng miễn phí với API key cá nhân (BYOK), trong khi doanh nghiệp/solo-founder nâng cấp lên gói trả phí (`BASIC`, `PREMIUM`, `ENTERPRISE`, `MASTER`) và nạp tín dụng MCU qua VietQR / PayOS hoặc NOWPayments.

---

## 2. 5 Phases × 25 Steps Summary / Tóm Tắt 5 Giai Đoạn × 25 Bước

1. **Phase 1 — Split & Hygiene (`PHASE_1_SPLIT_AND_HYGIENE`, Steps 1–5):**
   - `git-history-secret-purge`, `oss-vs-ee-directory-split`, `gitignore-quarantine-lock`, `env-example-byok-template`, `mit-license-and-sbom`
   - Quarantine `apps/`, `billing/`, `.orchestrate/`, `*.pem`, `.env*` (`git ls-files apps/ billing/` == `0`).
2. **Phase 2 — Core Boundary & Seams (`PHASE_2_PLUGIN_AND_SEAMS`, Steps 6–10):**
   - `capability-bus-interfaces`, `byok-local-adapters`, `cloud-bridge-webhooks`, `local-sandbox-runtime`, `versioned-openapi-sdk`
   - 100% provider-neutral `src/core/` (enforced by `tests/test_core_boundary.py`).
3. **Phase 3 — Cloud Control Plane (`PHASE_3_CLOUD_CONTROL_PLANE`, Steps 11–15):**
   - `jwt-license-gate`, `mcu-credit-metering`, `tiered-rate-limiting`, `managed-worker-queues`, `encrypted-key-vault`
   - HS256 JWT validation + SQLite/Cloud `MCUBilling` returning `HTTP 402 Payment Required` when credits reach `0`.
4. **Phase 4 — Enterprise Security & Billing (`PHASE_4_ENTERPRISE_MONETIZATION`, Steps 16–20):**
   - `multi-tenant-rbac-isolation`, `compliance-audit-ledger`, `always-on-cloud-daemon`, `strategy-recipe-marketplace`, `payment-webhook-activation`
   - SHA-256 tamper-evident `AuditLedger` + HMAC-SHA256 PayOS/NOWPayments anti-replay webhooks.
5. **Phase 5 — PLG Growth & CI Gates (`PHASE_5_PLG_GROWTH_AND_GOVERNANCE`, Steps 21–25):**
   - `sixty-second-quickstart`, `cli-to-cloud-upsell-prompt`, `ci-leak-and-loc-gate`, `public-benchmark-trust-badge`, `cla-and-trademark-policy`
   - Automated $\le 185\text{ LOC}$ module gate, secret-leak scanner, and CLA/Trademark protection.

---

## 3. CLI & API Reference / Lệnh CLI & API

### CLI Commands
```bash
# Run full /idea pipeline with --deep Brainstorm Contract & 25-step synthesis
python3 -m src.main idea run "25 bước tái cấu trúc thành dự án mã nguồn mở public github nhưng vẫn thu được SaaS" --deep --json

# Emit bounded 4-field Brainstorm Contract & SHA-256 contract_digest
python3 -m src.main idea brainstorm --deep
python3 -m src.main opencore-saas brainstorm --deep

# Audit live filesystem hygiene, 25 steps, and blueprint synchronization
python3 -m src.main opencore-saas steps
python3 -m src.main opencore-saas hygiene
python3 -m src.main opencore-saas audit --verify-fs
python3 -m src.main opencore-saas blueprint
```

### FastAPI Endpoints (`src/api/opencore_status_routes.py`)
- `GET /api/open-core/status` — Live readiness verdict (`PUBLIC_GITHUB_SAAS_READY`), filesystem hygiene, and 25-step blueprint synchronization status.
- `GET /api/open-core/brainstorm?deep=true` — Full 4-field Brainstorm Contract, 3-option YAGNI/KISS/DRY matrix, Tri-Layer analysis, and SHA-256 `contract_digest`.
