# RaaS Platform: Stripe Credits & Scalable FastAPI Research

**Date:** 2026-02-06
**Status:** Complete
**Context:** Research for Robot-as-a-Service (RaaS) platform implementation.

## 1. Stripe Integration for Pre-paid Credits

To implement a "Pre-paid Credits" system (Pay-as-you-go) instead of subscriptions:

### Strategy: One-Time Payments
*   **Product Setup:** Create "Credit Pack" products in Stripe (e.g., "$10 for 100 Credits", "$50 for 600 Credits").
*   **Checkout Flow:**
    1.  User selects a pack in your UI.
    2.  Backend creates a **Stripe Checkout Session** with `mode='payment'`.
    3.  Pass `client_reference_id` (your user ID) and `metadata` (e.g., `credits_amount: 100`) to the session.
    4.  Redirect user to Stripe hosted page.
*   **Fulfillment (Webhooks):**
    *   Listen for `checkout.session.completed`.
    *   **Crucial:** Do not fulfill credits immediately on the frontend success URL. Only fulfill upon receiving the secure webhook event.

### Key Stripe Concepts
*   **Payment Intent:** Underlying object tracking the transaction.
*   **Metadata:** Use this to carry "credit value" through the transaction lifecycle.
*   **Idempotency:** Stripe sends events multiple times. Your webhook handler MUST be idempotent (see Section 3).

## 2. FastAPI Stripe Best Practices

### Recommended Libraries
*   **`stripe` (Official Python SDK):** The gold standard. Always use the latest version.
*   **`pydantic-settings`:** For managing `STRIPE_API_KEY` and `STRIPE_WEBHOOK_SECRET`.

### Webhook Handling Pattern
Create a dedicated webhook endpoint that verifies signatures before parsing.

```python
# Pseudo-code pattern
from fastapi import APIRouter, Request, HTTPException, Header
import stripe

router = APIRouter()

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # TRIGGER SERVICE: await credit_service.add_credits(session)

    return {"status": "success"}
```

## 3. Credit Ledger Database Schema

**Golden Rule:** Never just store a "balance". Always use a **Double-Entry Ledger** or at least an **Append-Only Transaction Log**.

### Recommended Schema (PostgreSQL)

#### Table 1: `wallets` (Snapshot/Cache)
Stores the current usable balance for fast reads.
*   `id`: UUID
*   `user_id`: UUID (Foreign Key)
*   `balance`: Integer (Atomic updates only!)
*   `version`: Integer (Optimistic locking)

#### Table 2: `transactions` (The Truth)
Immutable history of every change.
*   `id`: UUID
*   `wallet_id`: UUID
*   `amount`: Integer (Positive for credit, Negative for usage)
*   `type`: Enum ('DEPOSIT', 'USAGE', 'REFUND', 'BONUS')
*   `reference_id`: String (e.g., Stripe Session ID `cs_test_...` or Job ID `job_123`)
*   `idempotency_key`: String (Unique constraint) - **Critical for Webhooks**
*   `created_at`: Timestamp
*   `metadata`: JSONB (Debug info)

### Idempotency Logic
1.  **Stripe Webhook arrives:** Extract `session.id` as the `idempotency_key`.
2.  **DB Transaction:**
    *   Try INSERT into `transactions`.
    *   If violation (duplicate key) -> Return 200 OK (Already processed).
    *   Else -> UPDATE `wallets` balance = balance + amount.
    *   Commit.

## 4. Scalable FastAPI Structure (2025/2026 Standard)

Adopt a **Service-Repository** pattern to separate concerns (clean architecture).

```
src/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── payments.py   # Webhooks & Checkout creation
│   │   │   │   ├── jobs.py       # RaaS Job execution
│   │   │   └── router.py
│   │   └── deps.py               # Dependency Injection (User, DB)
│   ├── core/
│   │   ├── config.py             # Settings (Pydantic)
│   │   └── security.py
│   ├── db/
│   │   ├── session.py            # SQLAlchemy/AsyncPG setup
│   │   └── base.py
│   ├── models/                   # SQLAlchemy Models
│   │   ├── user.py
│   │   └── ledger.py
│   ├── schemas/                  # Pydantic DTOs
│   │   ├── payment.py
│   │   └── credit.py
│   ├── services/                 # BUSINESS LOGIC (The "Brain")
│   │   ├── payment_service.py    # Handle Stripe logic
│   │   └── ledger_service.py     # Handle atomic credit updates
│   └── main.py
├── alembic/                      # Migrations
├── tests/
└── pyproject.toml
```

### Key Components
1.  **Routers (`api/`)**: Only handle HTTP request/response, validation, and auth. Delegate logic to Services.
2.  **Services (`services/`)**: Contain the business rules (e.g., "If user buys credits, log transaction and email receipt").
3.  **Repositories/CRUD**: (Optional in smaller apps, but good for scale) abstraction over raw SQL queries.

## Unresolved Questions
1.  **Concurrency:** How many concurrent RaaS jobs per user? (Affects database locking strategy on `wallets` table).
2.  **Currency:** Will credits be 1:1 with USD cents, or abstract tokens? (Abstract tokens recommended for flexibility).
3.  **Negative Balances:** Do we allow jobs to run if balance < cost (post-paid overage), or strict pre-paid enforcement?

## Sources
*   [Stripe Checkout API Docs](https://stripe.com/docs/api/checkout/sessions)
*   [Stripe Webhook Signatures](https://stripe.com/docs/webhooks/signatures)
*   [FastAPI Project Generation](https://github.com/tiangolo/full-stack-fastapi-template)
*   [Double Entry Bookkeeping for SaaS](https://news.ycombinator.com/item?id=23389824)
