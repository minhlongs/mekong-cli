# Phase 3: Stripe Integration

**Status:** Pending
**Priority:** Critical
**Context:** Payment processing.

## Context Links
- [Master Plan](./plan.md)

## Overview
We need to accept payments to fund the wallets. We will use Stripe Checkout in `payment` mode (one-time purchases). The critical part is the webhook handler, which must be secure and idempotent.

## Requirements
- **Stripe SDK:** `stripe` python package.
- **Flow:**
    1.  Frontend requests Checkout Session (`POST /checkout`).
    2.  API returns `url`.
    3.  Frontend redirects user to Stripe.
    4.  User pays.
    5.  Stripe sends `checkout.session.completed` webhook.
    6.  API verifies signature, checks `reference_id` (idempotency), creates `Transaction`, updates `Wallet`.

## Implementation Steps

1.  **Stripe Configuration**
    - Add `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` to `config.py`.

2.  **Checkout Service**
    - Implement `src/services/payment_service.py`.
    - Method `create_checkout_session(user_id, pack_id)`:
        - Fetch `credit_pack`.
        - Create Stripe Session with `client_reference_id=user_id` and `metadata={'pack_id': pack_id}`.

3.  **Webhook Handler**
    - Implement `POST /webhooks/stripe`.
    - Verify signature.
    - Extract event data.
    - If `checkout.session.completed`:
        - Extract `user_id`, `amount_total`, `metadata`.
        - Call `LedgerService.deposit()`.

4.  **Ledger Service (Deposit Logic)**
    - Implement `deposit(user_id, amount, reference_id)`:
        - **Transaction:** Check if `reference_id` exists in `transactions`. If yes, return (Idempotency).
        - **DB Transaction:**
            - Insert `Transaction` record.
            - Update `Wallet` balance (`wallet.balance += amount`).
            - Commit.

## Todo List
- [ ] Configure Stripe credentials.
- [ ] Implement `create_checkout_session`.
- [ ] Implement Webhook signature verification.
- [ ] Implement `LedgerService` with idempotency check.
- [ ] Connect Webhook to Ledger Service.
