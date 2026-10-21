# Mekong Engine — Invited Pilot Go-Live Brief

**Status:** Readiness-Gated, Invite-Only Pilot (Up to 5 Partners) | **Scope:** Synthetic Data & Test Integrations Only

---

## Executive Summary

Mekong Engine is launching a **readiness-gated, invite-only pilot** for up to **5 design partners**:

- **MekongMind Site:** `https://mekongmind.com` (existing public site, verified)
- **Engine API:** `https://api.cashclaw.cc` (`packages/mekong-engine`)
- **Dashboard Demo:** `https://ide.mekongmind.com` (`apps/dashboard` on Cloudflare Workers via `vinext`, synthetic demo data only)
- **Python CLI:** Local-first CLI released through GitHub Release / PyPI, gated on release checks (no CLI-to-cloud bridge in this pilot)

> **Pilot Scope Notice:** This release is an invite-only pilot using synthetic data and test integrations only. It does **not** include commercial pricing tiers, formal uptime SLAs, real tax/accounting filings, live payment processing, live outbound messaging, or ZenOS particle migration.

---

## Core Pilot Journey

1. **Operator Issues Single-Use Invite Code (Max 5 Partners)**
   - Operator calls `POST /billing/invites` with `Authorization: Bearer <SERVICE_TOKEN>`.
   - Engine generates a single-use `mk_inv_...` code, stores only its SHA-256 `code_hash` in `pilot_invites`, and returns the plaintext invite code once.
2. **Partner Redeems Invite Code & Creates Tenant**
   - Partner calls `POST /billing/tenants` or `POST /v1/onboard/signup` with `{ "name": "...", "invite_code": "mk_inv_..." }`.
   - The invite is consumed atomically with tenant creation (`status = 'redeemed'`), and the tenant `api_key` (`mk_...`) is returned **once**.
   - Public signup without a valid single-use `invite_code` is rejected (`403 PILOT_INVITE_REQUIRED` / `PILOT_INVITE_INVALID` / `PILOT_INVITE_ALREADY_USED`).
3. **LLM-Only Mission Submission & Queued Execution**
   - Partner submits a mission via `POST /v1/tasks`.
   - Engine deducts pilot credits idempotently (`mission_credit_events`), inserts the `pending` mission (`201 Created`) and `mission_outbox` record, and publishes to Cloudflare Queue (`MISSION_QUEUE`).
   - Queue consumer processes the mission through `RecipeOrchestrator` restricted to **LLM-only** steps (`api` and `shell` steps are rejected in pilot mode with `PILOT_STEP_MODE_REJECTED`).
   - Transient failures retry up to **3 times** (`max_retries = 3`) before routing to `mekong-mission-dlq`. Terminal failures trigger an idempotent **one-time credit refund**.
4. **Status & Result Review**
   - Partner polls `GET /v1/tasks/:id` or streams `GET /v1/tasks/:id/stream` to inspect status transitions (`pending` → `running` → `completed` / `failed`) and structured LLM output.

---

## Pilot Partner Expectations

- **Cohort Size:** Up to 5 invited partners
- **Usage Target:** 5 missions per partner per week
- **Feedback SLA (Partner Commitment):** Feedback on mission quality, UX, or bugs within 48 hours
- **Data Policy:** Synthetic data and test integrations only; dashboard at `https://ide.mekongmind.com` displays labeled synthetic demo data and does not expose partner mission data.

---

## Pilot Quick Start

### 1. Issue Invite Code (Operator Only)

```bash
curl -X POST https://api.cashclaw.cc/billing/invites \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"partner_name":"Partner Alpha","partner_email":"alpha@example.com"}'
```

### 2. Redeem Invite & Create Tenant (Partner)

```bash
curl -X POST https://api.cashclaw.cc/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Partner Alpha","invite_code":"mk_inv_..."}'
```

**Response (`201 Created` — API key shown once):**
```json
{
  "tenant_id": "tnt_abc123",
  "name": "Partner Alpha",
  "api_key": "mk_xxx_secret_key",
  "api_key_display_once": true,
  "tier": "free",
  "credits": 10,
  "invite_redeemed": true,
  "message": "Save your API key - it is displayed only once and cannot be recovered if lost!"
}
```

### 3. Submit LLM-Only Pilot Mission

```bash
curl -X POST https://api.cashclaw.cc/v1/tasks \
  -H "Authorization: Bearer mk_xxx_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Summarize synthetic Q1 partner onboarding feedback","params":{"complexity":"simple"}}'
```

### 4. Review Mission Status & Result

```bash
curl https://api.cashclaw.cc/v1/tasks/<mission_id> \
  -H "Authorization: Bearer mk_xxx_secret_key"
```

---

## Pilot Guardrails & Non-Goals

- **No Public Signup:** Every tenant creation path requires a valid single-use `invite_code` when `PILOT_INVITE_ONLY=true`.
- **LLM-Only Execution:** `api` and `shell` steps are blocked in pilot mode (`PILOT_LLM_ONLY=true`).
- **Idempotent Delivery & Credits:** Queue delivery is at-least-once; `mission_credit_events` and `mission_outbox` guarantee each mission is debited at most once and refunded at most once on terminal failure.
- **No Commercial SLA or Paid Billing:** Pilot tenants receive synthetic test credits; commercial pricing and uptime SLAs are deferred until post-pilot evaluation.
