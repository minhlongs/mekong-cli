# Phase 4: Webhook Handling & Idempotency

**Status:** Pending
**Priority:** Critical

## Overview
Handle the `checkout.session.completed` event from Stripe to actually credit the user's wallet. This must be secure (signature verification) and idempotent (prevent double crediting).

## Implementation Steps

1.  **Webhook Endpoint (`app/api/v1/endpoints/webhooks.py`)**
    - Route: `POST /webhooks/stripe`
    - **Signature Verification**:
        - Read raw body.
        - Get `Stripe-Signature` header.
        - Use `stripe.Webhook.construct_event`.

2.  **Event Processing Logic**
    - Check event type: `checkout.session.completed`.
    - Extract `metadata` (credits amount) and `client_reference_id` (user_id).
    - Extract `id` (Stripe Session ID).

3.  **Integration with Ledger Service**
    - Call `LedgerService.record_transaction`:
        - `user_id`: from payload
        - `amount`: from metadata
        - `type`: `DEPOSIT`
        - `reference_id`: Stripe Session ID (**Crucial for Idempotency**)
    - If `record_transaction` raises "AlreadyExists" error, return 200 OK (idempotent success).

## Todo List
- [ ] Create `app/api/v1/endpoints/webhooks.py`
- [ ] Implement signature verification logic
- [ ] Implement event handler for `checkout.session.completed`
- [ ] Connect webhook handler to `LedgerService`
- [ ] Test with Stripe CLI (`stripe trigger checkout.session.completed`)
