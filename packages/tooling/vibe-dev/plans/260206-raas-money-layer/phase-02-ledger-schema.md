# Phase 2: Ledger Schema Design

**Status:** Pending
**Priority:** Critical
**Context:** The core of the financial system.

## Context Links
- [Master Plan](./plan.md)

## Overview
The integrity of the Money Layer depends entirely on the database schema. We will use a "Double-Entry Ledger" approach where the user's balance is a computed aggregation of their transaction history (or a cached value strictly updated via transactions).

## Requirements
- **ORM:** SQLAlchemy 2.0 (Async).
- **Migration:** Alembic.
- **Constraints:**
    - `Wallet` must be unique per `user_id`.
    - `Transaction` must have a valid `type` (DEPOSIT, WITHDRAW, etc.).
    - `reference_id` should be indexed for lookups (e.g., preventing duplicate stripe sessions).

## Schema Design

### 1. `users` (Reference)
*Note: Depending on architecture, this might be a local table synced from the Engine or a view.*
- `id`: UUID (Primary Key)
- `email`: String

### 2. `wallets`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, Unique)
- `balance`: BigInteger (Cached balance in lowest denomination, e.g., 'credits')
- `created_at`: DateTime
- `updated_at`: DateTime
- `version`: Integer (Optimistic locking)

### 3. `credit_packs`
- `id`: UUID (Primary Key)
- `name`: String (e.g., "Starter Pack")
- `credit_amount`: Integer (e.g., 500)
- `price_cents`: Integer (e.g., 1000 for $10.00)
- `stripe_price_id`: String (Stripe Price ID)
- `is_active`: Boolean

### 4. `transactions` (The Ledger)
- `id`: UUID (Primary Key)
- `wallet_id`: UUID (Foreign Key -> wallets.id)
- `amount`: BigInteger (Positive for deposit, negative for usage)
- `balance_after`: BigInteger (Snapshot of balance after tx)
- `type`: Enum (`DEPOSIT`, `USAGE`, `REFUND`, `BONUS`)
- `description`: String
- `reference_id`: String (Indexed, Unique for deposits - e.g., `cs_test_123`)
- `meta`: JSONB (Additional details)
- `created_at`: DateTime

## Implementation Steps

1.  **Define Models**
    - Create `src/models.py`.
    - Define SQLAlchemy classes for the tables above.

2.  **Generate Migrations**
    - Run `alembic revision --autogenerate -m "initial_money_schema"`.
    - Review the generated script.

3.  **Apply Migrations**
    - Run `alembic upgrade head`.

4.  **Seed Data**
    - Create a script to seed initial `credit_packs`.

## Todo List
- [ ] Define SQLAlchemy models.
- [ ] Generate Alembic migration script.
- [ ] Apply migration to local DB.
- [ ] Verify schema in `psql`.
