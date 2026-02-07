# Phase 5: API Endpoints & Testing

**Status:** Pending
**Priority:** Medium

## Overview
Expose endpoints for the frontend to display current credit balance and transaction history. Validate the entire flow with robust tests.

## Implementation Steps

1.  **Wallet Endpoints (`app/api/v1/endpoints/wallet.py`)**
    - `GET /wallet/balance`: Return current balance.
    - `GET /wallet/transactions`: Return paginated list of transactions (audit log).

2.  **Unit Tests**
    - Test `LedgerService` logic (locking, idempotency, negative balance checks).
    - Test Stripe Webhook signature verification (using mock headers).

3.  **Integration Tests**
    - Simulate full flow:
        1. Create Wallet.
        2. Mock Stripe Webhook -> Credit Wallet.
        3. Verify Balance via API.
        4. Replay Webhook -> Verify Balance unchanged (Idempotency).
        5. Spend Credits -> Verify Balance decrease.

## Todo List
- [ ] Implement `app/api/v1/endpoints/wallet.py`
- [ ] Register wallet router
- [ ] Setup `pytest` and `httpx`
- [ ] Write unit tests for Ledger
- [ ] Write integration tests for Webhooks and API
