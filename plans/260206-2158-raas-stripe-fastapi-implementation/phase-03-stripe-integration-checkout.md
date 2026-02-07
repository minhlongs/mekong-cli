# Phase 3: Stripe Integration (Checkout)

**Status:** Pending
**Priority:** High

## Overview
Enable users to purchase "Credit Packs" via Stripe Checkout. This involves creating a service wrapper for Stripe and an API endpoint to generate checkout sessions.

## Stripe Configuration
- **Mode:** `payment` (One-time purchase)
- **Products:** Defined in Stripe Dashboard or created programmatically (e.g., "100 Credits" for $10).

## Implementation Steps

1.  **Stripe Service (`app/services/stripe_service.py`)**
    - Initialize `stripe.api_key` from config.
    - Method `create_checkout_session(user_id, amount_credits, price_id, success_url, cancel_url)`:
        - Metadata: `{"user_id": user_id, "credits": amount_credits}`
        - Client Reference ID: `user_id`

2.  **API Schemas (`app/schemas/billing.py`)**
    - `CheckoutSessionCreate`: Input schema (pack_id or amount).
    - `CheckoutSessionResponse`: Output schema (url).

3.  **API Endpoint (`app/api/v1/endpoints/billing.py`)**
    - `POST /billing/checkout`:
        - Authenticate user.
        - Call `StripeService.create_checkout_session`.
        - Return session URL.

## Todo List
- [ ] Implement `app/services/stripe_service.py`
- [ ] Define Pydantic schemas for billing
- [ ] Create `app/api/v1/endpoints/billing.py`
- [ ] Register router in `api.py`
