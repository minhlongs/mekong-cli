# Invite-Only Pilot Runbook & Checklist — Real Vietnamese SME Customer #1

> **BOUNDARY NOTICE:** This is a pre-deployment operational checklist for the Founder. **No production deployment, live Zalo message, or live payment was executed by Supreme Command #08.** Execute these steps only after reviewing and merging the hardened PR.

---

## Stage A — Founder Pre-Flight & Secret Provisioning (Before Contacting Customer #1)

- [ ] **A1. Merge Reviewed PR & Deploy Isolated Single-Node Pilot Stack (HTTPS Only):**
  - Confirm TLS (`https://`) is active on both Dashboard and FastAPI Gateway (`window.crypto.subtle` and `Secure` session cookies require HTTPS).
  - Set `MEKONG_ENV=production` and `MEKONG_PUBLIC_GATEWAY=1` on FastAPI Gateway; verify `MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK` is **unset**.
- [ ] **A2. Generate Strong Server-Only Secrets (`>= 32` random bytes each, stored in secret manager / `0600` server env):**
  - `MEKONG_APPROVAL_SECRET` (`openssl rand -hex 32`)
  - `RAAS_LICENSE_SECRET` (`openssl rand -hex 32`)
  - `MEKONG_DASHBOARD_SESSION_SECRET` (`openssl rand -hex 32`)
  - `MEKONG_DASHBOARD_OWNER_LOGIN_TOKEN` (`openssl rand -hex 24`)
- [ ] **A3. Zero-Cloud-PII Default Check:**
  - Keep Tier-3 Cloud LLM fallback disabled (`cloud_fallback_fn=None`, no external LLM keys mounted in Pilot A worker) for Customer #1 unless a Decree 13 Article 25 Cross-Border TIA dossier is prepared, ensuring 100% of customer messages stay inside Vietnam via Deterministic Python + Local MLX.
- [ ] **A4. Enable Automated Hourly SQLite WAL Backups:**
  - Configure cron/systemd timer running `sqlite3 <file> ".backup ..."` for `MEKONG_PILOT_A_DB_DIR` and `MEKONG_VIETQR_DB`, retaining 14 days of encrypted snapshots.

---

## Stage B — Customer #1 Qualification & Legal Consent Gate

- [ ] **B1. Verify Entry Criteria:**
  - Customer has an active paid Zalo Official Account (`Growth` / `Enterprise` tier) with OA Admin rights.
  - Customer provides a fixed VND price sheet of `5–30` standard products/services and receiving Napas 247 bank BIN + account number.
  - Customer signs a 1-page Pilot Design-Partner Agreement acknowledging:
    1. Outbound quotes require 1-tap Shop Owner approval before sending.
    2. Exported accounting files are **pre-accounting drafts (`DRAFT_PENDING_TVAN`)** requiring review and digital signing in MISA meInvoice / Sapo Invoice.
- [ ] **B2. Configure Decree 13/2023/NĐ-CP Customer Privacy Notice:**
  - Update Customer #1's Zalo OA greeting / auto-reply notice to disclose automated quote drafting and right to request data deletion (`< 72h`).

---

## Stage C — Technical Tenant Onboarding (`~25 Minutes`)

- [ ] **C1. Provision Isolated Tenant on Gateway Host:**
  - Run:
    `mekong opc provision-tenant --tenant-id <customer_slug> --business-name "<Tên Công Ty>" --owner-name "<Tên Chủ Shop>" --sme-tier pilot_a --bank-id <MB|VCB|TCB|...> --account-no <STK>`
  - Confirm `<customer_slug>.db`, `<customer_slug>_vietqr.db`, `<customer_slug>_privacy.db`, and `<customer_slug>.tenant.json` have `0600` file permissions.
- [ ] **C2. Bind Server-Only BFF Key (`0` `NEXT_PUBLIC_*`):**
  - Register `{"<customer_slug>": "<mk_opc_...>"}` in server-only `MEKONG_TENANT_KEYS_JSON` and `{"ws_<customer_slug>": ["<customer_slug>"]}` in `MEKONG_WORKSPACE_TENANTS_JSON` on the Dashboard server.
- [ ] **C3. Bind Merchant Zalo OA & Bank Webhook Secrets:**
  - Set `ZALO_OA_SECRET_KEY`, `ZALO_OA_ACCESS_TOKEN`, and `VIETQR_WEBHOOK_SECRET` from Customer #1's Zalo Developer Console and Sepay/Casso webhook panel.
- [ ] **C4. Execute Controlled Internal Smoke Test (Founder's Personal Phone as Buyer):**
  1. Send 1 Zalo message from Founder's personal Zalo account to Customer #1's OA.
  2. Have Shop Owner review the `<15KB` approval card / `/dashboard/opc` cockpit and tap **Duyệt & Gửi Báo Giá + VietQR**.
  3. Transfer `10,000 VND` real test amount via banking app scanning the generated VietQR.
  4. Confirm `/v1/opc/pilot-a/webhook/vietqr` reconciles the `bank_tx_id` and Customer #1's bookkeeper successfully opens the exported `DRAFT_PENDING_TVAN` CSV/XML in MISA/Sapo.
  5. Test negative check: send 1 ambiguous message ("Tư vấn dự án đặc biệt chưa có giá") and confirm it routes to `HANDOFF_ZALO_OA_MANAGER` without sending an automated quote.

---

## Stage D — Week-1 Hypercare & Go/Hold Criteria

- [ ] **D1. Daily Audit Check (Days 1–7):**
  - Inspect `GET /v1/opc/pilot-a/runs/<run_id>` economics & status logs daily; verify `0` `RECONCILIATION_REQUIRED` stuck runs, `0` `401/403` anomalies, and `< 3 min` median owner approval time.
- [ ] **D2. Collect Paid Subscription (`990,000 VND` `pilot_a` Tier):**
  - Create order via `POST /v1/checkout` (`tier="pilot_a"`, `rail="vietqr"`, `org_id="<customer_slug>"`), have customer pay via Napas 247, verify settlement with `X-Checkout-Secret`, and activate `MEKONG-RAAS-v1` license (`500` workflows/month).
- [ ] **D3. Gate to Customer #2–#5:**
  - Proceed to invite Customers #2–#5 **only after** Customer #1 completes `>= 20` real approved quotes with `0` billing/pricing incidents and `< 15%` manual draft rewrites.
