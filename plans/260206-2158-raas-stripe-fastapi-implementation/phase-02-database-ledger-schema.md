# Phase 2: Database Ledger Schema Implementation

**Status:** Pending
**Priority:** Critical

## Overview
Implement the "Double-Entry Bookkeeping Lite" schema to track user credits securely. This phase ensures that every credit change is recorded as a transaction, providing a complete audit trail.

## Schema Design

### 1. Wallets
- `id`: UUID (PK)
- `user_id`: UUID (Unique, Indexed)
- `balance`: BigInteger (default 0) - *Using BigInt to avoid float issues*
- `version`: Integer (for Optimistic Concurrency Control)
- `updated_at`: DateTime

### 2. Transactions (Ledger)
- `id`: UUID (PK)
- `wallet_id`: UUID (FK -> Wallets)
- `amount`: BigInteger (Positive = Credit, Negative = Debit)
- `type`: Enum (`DEPOSIT`, `USAGE`, `REFUND`, `BONUS`)
- `reference_id`: String (Unique constraint with `type` for idempotency)
- `description`: String
- `balance_after`: BigInteger (Snapshot)
- `created_at`: DateTime

## Implementation Steps

1.  **Define Models (`app/models/ledger.py`)**
    - Implement SQLAlchemy models for `Wallet` and `Transaction`.

2.  **Alembic Setup**
    - Initialize Alembic: `alembic init alembic`.
    - Configure `alembic/env.py` to import `Base` and load env vars.
    - Generate initial migration: `alembic revision --autogenerate`.

3.  **Ledger Service (`app/services/ledger_service.py`)**
    - `create_wallet(user_id)`
    - `get_wallet(user_id)`
    - `record_transaction(user_id, amount, type, reference_id, description)`:
        - Start DB transaction.
        - Lock Wallet row (`with_for_update`).
        - Check for existing `reference_id` (Idempotency).
        - Update balance.
        - Create Transaction record.
        - Commit.

## Todo List
- [ ] Create `app/models/ledger.py`
- [ ] Initialize Alembic and generate migration script
- [ ] Apply migration to DB
- [ ] Implement `LedgerService` with atomic transaction logic
