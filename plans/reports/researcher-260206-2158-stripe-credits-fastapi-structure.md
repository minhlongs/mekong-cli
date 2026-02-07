# Research Report: RaaS Stripe Credits & FastAPI Architecture

**Date:** 260206
**Status:** Complete
**Context:** Robot-as-a-Service (RaaS) Platform Implementation

## Executive Summary

This report outlines the architecture for a "Pre-paid Credits" system using Stripe and FastAPI. The recommended approach utilizes Stripe Checkout for one-time payments, a double-entry ledger system for robust credit tracking, and a Domain-Driven Design (DDD) structure for the FastAPI service to ensure scalability.

## 1. Stripe Integration Strategy (Pre-paid Credits)

To implement a "pay-as-you-go" credit system (buying packs of credits), avoid the Subscriptions API. Instead, use **Stripe Checkout** in `payment` mode.

### Workflow
1.  **Product Setup:** Create "Credit Pack" products in Stripe (e.g., "100 Credits" for $10).
2.  **Checkout Session:**
    *   Backend creates a Stripe Checkout Session with `mode='payment'`.
    *   Pass `client_reference_id` (User ID) and `metadata` (e.g., `{"credits": 100}`) to track the purchase context.
3.  **Fulfillment (Webhooks):**
    *   Listen for `checkout.session.completed` webhook.
    *   Verify the payment status is `paid`.
    *   Extract User ID and Credit amount from the payload.
    *   **Crucial:** Use the Stripe Event ID as an idempotency key to prevent double-crediting if Stripe retries the webhook.

### Code Snippet (Concept)
```python
# Create Session
session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price_data': {
            'currency': 'usd',
            'product_data': {'name': '100 Credits'},
            'unit_amount': 1000, # $10.00
        },
        'quantity': 1,
    }],
    mode='payment',
    client_reference_id=user_id,
    metadata={'credits_amount': 100}
)
```

## 2. FastAPI Stripe Integration Best Practices

### Library
Use the official **`stripe`** Python library. It is robust, strictly typed, and maintained by Stripe.

### Webhook Handling in FastAPI
Do not use generic JSON parsing. You must verify the signature to prevent replay attacks and spoofing.

**Pattern:**
1.  Create a dedicated endpoint: `POST /api/v1/webhooks/stripe`.
2.  Read the raw request body (bytes).
3.  Get the `Stripe-Signature` header.
4.  Use `stripe.Webhook.construct_event()` to verify and parse.

**FastAPI Implementation Detail:**
```python
from fastapi import APIRouter, Request, HTTPException, Header
import stripe

router = APIRouter()

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    if event['type'] == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])

    return {"status": "success"}
```

## 3. Credit Ledger Database Schema

**Recommendation: Double-Entry Bookkeeping Lite**

Do not just update a simple `balance` column on the User table. This leads to race conditions and audit nightmares. Use a **Ledger** table to record every movement.

### Schema Design (PostgreSQL/SQLAlchemy)

**1. `wallets` Table** (Current State)
*   `id`: UUID
*   `user_id`: UUID (Foreign Key)
*   `balance`: Integer (Current available credits)
*   `updated_at`: Timestamp
*   `version`: Integer (For optimistic locking)

**2. `transactions` Table** (Audit Log / Ledger)
*   `id`: UUID
*   `wallet_id`: UUID (Foreign Key)
*   `amount`: Integer (Positive for credit, Negative for usage)
*   `type`: Enum (`DEPOSIT`, `USAGE`, `REFUND`, `BONUS`)
*   `reference_id`: String (e.g., Stripe Session ID, Job ID) - **Unique Constraint** for Idempotency
*   `description`: String
*   `created_at`: Timestamp
*   `balance_after`: Integer (Snapshot of balance after this transaction)

### Idempotency Strategy
*   For Stripe Webhooks: Use the `stripe_session_id` as the `reference_id` in the transaction.
*   Database Constraint: `UNIQUE(reference_id, type)` prevents processing the same Stripe event twice.

## 4. Scalable FastAPI Structure

Adopt a modular, service-oriented architecture tailored for Python/FastAPI.

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── auth.py
│       │   ├── billing.py      # Stripe endpoints
│       │   └── tasks.py        # RaaS job triggers
│       └── api.py              # Router aggregation
├── core/
│   ├── config.py               # Env vars (Pydantic Settings)
│   └── security.py             # JWT, Hashing
├── db/
│   ├── base.py                 # SQLAlchemy declarative base
│   └── session.py              # DB Engine & SessionLocal
├── models/
│   ├── user.py
│   └── ledger.py               # Wallet & Transaction models
├── schemas/                    # Pydantic DTOs
│   ├── billing.py
│   └── common.py
├── services/                   # Business Logic Layer (Crucial)
│   ├── stripe_service.py       # Interacts with Stripe API
│   └── ledger_service.py       # Handles DB transactions, locking
└── main.py
```

### Key Pattern: Service Layer
Keep routers thin. Move logic to `services/`.
*   **Router:** Validates input, checks permissions.
*   **Service:** Performs logic (e.g., `LedgerService.add_credits(user_id, amount, ref_id)`).
*   **Repo/Model:** Handles DB queries.

## Unresolved Questions / Next Steps
1.  **Concurrency:** For high-frequency "usage" (e.g., streaming usage per second), simple row locking might bottleneck. Do we need Redis for hot-wallet caching?
2.  **Pricing Model:** Are credits 1:1 with currency, or abstracted (e.g., $10 = 1000 credits)?
3.  **Negative Balances:** Should we allow overdrafts for running jobs?

## Sources
*   [Stripe Checkout Documentation](https://stripe.com/docs/payments/checkout)
*   [FastAPI Documentation](https://fastapi.tiangolo.com/)
*   [Double-Entry Bookkeeping for Developers](https://ledger-cli.org/3.0/doc/ledger3.html#Principles)
*   [Cosmic Python (Architecture Patterns)](https://www.cosmicpython.com/)
