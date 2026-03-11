# Scope Definition — RaaS Credit Checkout + Stripe/Polar Integration

**Feature:** Revenue-as-a-Service (RaaS) credit checkout system
**Version target:** v5.1 | **Author:** Product | **Date:** March 2026
**Status:** Scoping phase — not yet in engineering sprint

---

## Problem Statement

Mekong CLI's MCU billing model requires a way to sell credits. Currently there is no automated checkout — early testers are on manual invoicing or test accounts. Before scaling to public launch on Product Hunt, we need a working checkout flow: user visits site, picks a plan, pays, gets credits, starts using the CLI.

This scope document defines exactly what we're building and what we're explicitly not building in this iteration.

---

## Business Context

**Tiers:**
| Tier | Credits/month | Price | Primary segment |
|------|--------------|-------|----------------|
| Starter | 200 MCU | $49/mo | Solo founders |
| Pro | 1,000 MCU | $149/mo | Agencies, dev teams |
| Enterprise | Unlimited | $499/mo | Multi-team, white-label |

**Payment rule (from CLAUDE.md):** Polar.sh is the ONLY payment provider. PayPal references must be removed. Stripe is considered as a secondary option for Enterprise invoicing only (annual contracts).

**Credit delivery:** After successful Polar.sh webhook → API creates account → issues API key → credits provisioned to account → user can run CLI commands.

---

## In Scope (MVP)

### Checkout Flow
- Polar.sh subscription checkout for all 3 tiers (Starter, Pro, Enterprise)
- Polar.sh Standard Webhooks: `subscription.created`, `subscription.updated`, `subscription.canceled`
- On `subscription.created`: create user account in DB, provision credits, send welcome email with API key
- On `subscription.updated`: adjust credit balance for tier change (upgrade/downgrade)
- On `subscription.canceled`: flag account as canceled, allow usage until period end, then revoke API key

### CLI Authentication After Purchase
- User runs `mekong auth --key sk-mekong-xxxx` after receiving API key via email
- Key stored in `~/.mekong/config.json` (not in project directory, never committed to git)
- CLI reads key on every command, checks balance before executing
- If balance = 0: HTTP 402 response from API gateway with message "Out of credits. Top up at agencyos.network/billing"

### Credit Deduction
- Deduct MCU credits ONLY after successful task delivery (not on attempt)
- Verify step in PEV must pass before deduction triggers
- Failed tasks: 0 MCU charged
- Partial tasks (user cancels mid-run): 0 MCU charged (all-or-nothing per task)
- Audit trail: every deduction logged to `mcu_transactions` table with task ID, command, MCU cost, timestamp

### Admin Dashboard (minimal)
- `/admin/accounts` — list accounts, credit balance, last active
- `/admin/transactions` — credit deduction log
- Manual credit top-up for support/beta users
- Not a full billing portal — just enough for ops

---

## Out of Scope (explicitly excluded from this iteration)

### Stripe Integration
- Stripe is NOT in scope for MVP checkout
- Enterprise annual invoicing via Stripe will be addressed in v5.2
- Reason: Polar.sh handles subscription management cleanly; adding Stripe now adds complexity with no immediate revenue benefit

### Self-Service Credit Top-Up
- User cannot buy ad-hoc credit packs in v5.1 (only monthly subscriptions)
- "Buy 500 extra credits" feature deferred to v5.2
- Reason: Subscription model simplifies revenue recognition; credit packs add inventory management complexity

### Usage-Based Billing / Variable MCU Pricing
- All commands cost fixed MCU amounts (1–5 MCU per command, predefined)
- Dynamic pricing based on actual LLM token usage is NOT in scope
- Reason: Predictability for users is more important than margin optimization at current scale

### White-Label Billing
- Agencies reselling Mekong under their own brand → billing through their own Polar account is out of scope
- White-label billing requires tenant isolation and sub-account management
- Deferred to Enterprise tier v5.2

### In-App Billing Portal
- Users cannot change plans from within the CLI or dashboard in v5.1
- Plan changes go through Polar.sh customer portal (link provided in dashboard)
- Reason: Building a full billing portal is weeks of engineering for a problem Polar.sh already solves

### Multi-User Teams
- One Polar subscription → one API key → one account
- Team seat sharing, role-based access, per-seat billing all deferred
- Reason: Current target is solo founders and small agencies; team features are a v5.3 investment

---

## MVP Requirements

### Functional Requirements

**F1:** User can subscribe to any tier via Polar.sh checkout embedded on agencyos.network/pricing
**F2:** Within 60 seconds of `subscription.created` webhook: account created, API key emailed, credits provisioned
**F3:** CLI command `mekong auth --key [key]` stores credentials and verifies with server
**F4:** Every CLI command checks credit balance before executing; returns HTTP 402 if balance = 0
**F5:** MCU deducted only after PEV Verify step completes successfully
**F6:** `mekong balance` command returns current MCU balance and tier name
**F7:** On subscription cancellation: account active until period end, then API key revoked
**F8:** All MCU transactions logged with full audit trail

### Non-Functional Requirements

**NF1:** Webhook processing latency < 5 seconds (user gets API key email within 60 seconds of payment)
**NF2:** Credit check adds < 50ms to CLI command latency
**NF3:** Zero credits double-charged or lost due to race conditions (transactions must be ACID)
**NF4:** API key never appears in logs, git history, or error messages
**NF5:** Webhook endpoint validates Polar.sh signature before processing (security)

---

## Technical Constraints

### Stack
- **API Gateway:** FastAPI (`src/api/`) — existing, extend with `/webhooks/polar` endpoint
- **Database:** PostgreSQL — add `accounts`, `mcu_transactions` tables
- **Webhook handler:** `src/api/webhooks.py` (new file)
- **Credit service:** `src/core/credit_service.py` (new file)
- **Auth middleware:** extend existing `src/api/middleware.py`

### Polar.sh Integration Points
- Webhook URL: `https://api.agencyos.network/webhooks/polar`
- Events to handle: `subscription.created`, `subscription.updated`, `subscription.canceled`, `order.created`
- Signature verification: `Webhook-Signature` header, HMAC-SHA256
- Reference: https://docs.polar.sh/developers/webhooks

### Database Schema (new tables)

```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    polar_subscription_id TEXT UNIQUE,
    tier TEXT CHECK (tier IN ('starter', 'pro', 'enterprise')),
    mcu_balance INTEGER NOT NULL DEFAULT 0,
    api_key TEXT NOT NULL UNIQUE,
    api_key_hash TEXT NOT NULL,  -- store hash, not plaintext
    status TEXT CHECK (status IN ('active', 'canceled', 'suspended')),
    period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE mcu_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    command TEXT NOT NULL,
    task_id TEXT,
    mcu_cost INTEGER NOT NULL,
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    status TEXT CHECK (status IN ('charged', 'refunded', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Success Criteria (Definition of Done)

- [ ] Polar.sh webhook processes `subscription.created` in staging environment
- [ ] New subscriber receives API key email within 60 seconds
- [ ] `mekong auth --key [key]` stores key and prints "Authenticated. Balance: 200 MCU (Starter)"
- [ ] Running `mekong cook "hello world"` with valid key deducts correct MCU and logs transaction
- [ ] Running any command with 0 balance returns HTTP 402 with human-readable message
- [ ] `mekong balance` returns correct balance in real-time
- [ ] Cancellation flow: account stays active through period end, then key revoked
- [ ] All edge cases tested: duplicate webhooks (idempotency), webhook signature invalid (reject), network timeout mid-transaction (rollback)

---

## Open Questions

1. **API key format:** `sk-mekong-[32 hex chars]` or UUID? Preference for opaque token that signals the product name.
2. **Welcome email sender:** Polar.sh can send or we send via Resend.com — who owns the email template?
3. **Balance refresh cadence:** Does CLI check balance on every command (adds latency) or cache for 60s?
4. **Tier change timing:** On upgrade, do new credits provision immediately or at next billing cycle?
5. **Enterprise checkout:** Polar.sh can handle $499/mo subscription but Enterprise should have a "contact us" option for custom contracts — in scope or out?
