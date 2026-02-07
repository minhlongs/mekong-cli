# Phase 4: Integration Testing

**Status:** Pending
**Priority:** High
**Context:** Verification of the financial system.

## Context Links
- [Master Plan](./plan.md)

## Overview
Financial systems require rigorous testing. We cannot rely on manual testing alone. We need automated tests that verify the ledger balances are always correct, even under race conditions or duplicate webhook events.

## Requirements
- **Test Runner:** `pytest`.
- **Async Support:** `pytest-asyncio`.
- **Database:** Use a separate test database or rollback transactions.

## Test Scenarios

### 1. Ledger Logic
- **Deposit:** Verify balance increases and transaction is recorded.
- **Idempotency:** Call deposit twice with same `reference_id`. Verify balance only increases ONCE.
- **Concurrency:** (Advanced) Run parallel deposit requests for the same wallet (if relevant).

### 2. Stripe Integration
- **Checkout:** Verify session creation calls Stripe API (Mocked).
- **Webhook:** Simulate a valid `checkout.session.completed` payload. Verify it triggers the ledger deposit.
- **Invalid Signature:** Verify webhook rejects invalid signatures with 400/401.

## Implementation Steps

1.  **Test Setup**
    - Configure `conftest.py` for Async SQLAlchemy session management.
    - Setup `test_db` fixture.

2.  **Write Tests**
    - `tests/test_ledger.py`: Unit tests for `LedgerService`.
    - `tests/test_stripe.py`: Integration tests for Webhook endpoint.

3.  **CI Integration**
    - Ensure tests run in `make test` or GitHub Actions.

## Todo List
- [ ] Setup Pytest and Asyncio fixtures.
- [ ] Write `test_ledger_deposit`.
- [ ] Write `test_ledger_idempotency`.
- [ ] Write `test_stripe_webhook_flow` (with Mock).
