# Master Plan: Money Layer Integration (Stripe + Ledger)

**Status:** Draft
**Priority:** Critical
**Date:** 2026-02-06
**Context:** Phase 2 of AgencyOS RaaS Platform

## Overview
This plan focuses on building the "Money Layer" of the AgencyOS platform. This layer is responsible for handling user credits, processing payments via Stripe, and maintaining a strict double-entry ledger for all financial transactions. The service will be built using Python/FastAPI.

## Phases

### [Phase 1: Scaffold FastAPI Service](./phase-01-scaffold-fastapi.md)
**Goal:** Initialize the project structure, Docker environment, and basic connectivity.
- Setup `apps/api` directory with Python/FastAPI.
- Configure Docker and Docker Compose.
- Setup PostgreSQL connection (Async SQLAlchemy).
- Implement Health Check endpoint.

### [Phase 2: Ledger Schema Design](./phase-02-ledger-schema.md)
**Goal:** Implement the database schema for strict financial tracking.
- Design `Wallet`, `CreditPack`, and `Transaction` models.
- Implement Alembic migrations.
- Ensure "Double-Entry" logic (no balance updates without transactions).

### [Phase 3: Stripe Integration](./phase-03-stripe-integration.md)
**Goal:** Enable payments and automatic credit handling.
- Implement `POST /checkout/create` for Stripe Sessions.
- Implement `POST /webhooks/stripe` for secure event handling.
- Handle Idempotency to prevent double-crediting.

### [Phase 4: Integration Testing](./phase-04-integration-testing.md)
**Goal:** Verify financial correctness.
- Write Pytest suite.
- Mock Stripe API interactions.
- Test concurrency and race conditions on the ledger.

## Dependencies
- **Engine Layer:** `apps/engine` (Already implemented).
- **Database:** Shared PostgreSQL instance.
- **Stripe:** API Keys (Test Mode).

## Success Criteria
- [ ] Users can purchase Credit Packs via Stripe.
- [ ] Credits are automatically applied to the user's wallet upon payment success.
- [ ] Every credit change is recorded in the `Transaction` table.
- [ ] No race conditions found during concurrent usage tests.
