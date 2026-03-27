---
name: polymarket-api
description: Polymarket CLOB API reference for the CashClaw trading bot. Trigger when working on order placement, market scanning, position tracking, or fee calculations in the algo-trader submodule. Contains the actual API gotchas that cause silent failures — rate limits, GTC order persistence, dynamic fee categories, and the March 30 2026 fee expansion.
---

# Polymarket CLOB API

## Overview
CashClaw trades on Polymarket's Central Limit Order Book. The API has critical quirks that cause real money loss if ignored.

## Key Knowledge

### Order Types
- `GTC` (Good-Till-Cancelled) — DEFAULT. Persists after bot crash. MUST cancel on shutdown.
- `GTD` (Good-Till-Date) — Safer. Set expiry timestamp. Preferred for maker orders.
- `FOK` (Fill-Or-Kill) — Taker order. Fills immediately or cancels entirely.

### Fee Structure (March 30, 2026 expansion)
- Maker: 0% with rebates (20-50% by category)
- Taker: Dynamic 0.15%-1.80% based on category + probability distance from 50%
- See `references/fee-categories.md` for full table

### Rate Limits
- Order placement: 3,500 per 10 seconds (burst)
- Sustained: 60/second
- Batch: up to 15 orders per request via `/batch-orders`
- Market data: generous but respect 429s

## Scripts
- `scripts/check-open-orders.sh` — List all open orders (safety check)
- `scripts/cancel-all.sh` — Emergency cancel all open orders

## References
- `references/fee-categories.md` — Full fee table by category
- `references/api-endpoints.md` — CLOB endpoint reference
- `references/order-examples.md` — Working order placement examples

## Gotchas
- GTC orders SURVIVE bot crashes. Always register SIGTERM handler to cancel.
- `outcomePrices` from Gamma API are STRINGS not numbers. Parse with `parseFloat()`.
- Order `size` is in SHARES not USD. Calculate: `usd_amount / price = shares`.
- The `nonce` field must be unique per order. Use timestamp + random suffix.
- Testnet does NOT exist. Use `DRY_RUN` mode with real API reads + simulated writes.
- Dynamic fees depend on probability: a 95% market has HIGHER taker fees than a 55% market.
