# Phase A: Payment Gateway — Stripe + MCU Connector

**Goal:** Connect Stripe Checkout → webhook → MCU credit provisioning using existing billing code.

## Steps

### A1. Stripe Checkout Integration
**Create:** `scripts/stripe-checkout.cjs`
- Uses Stripe SDK to create Checkout Session
- Accepts `--tier starter|growth|pro` flag
- Returns checkout URL → opens in browser
- Maps tiers: starter=$49/50 credits, growth=$149/200, pro=$499/1000

### A2. Stripe Webhook Endpoint
**Create:** `scripts/stripe-webhook.cjs`
- Express server (optional) hoặc serverless function
- Verifies Stripe signature
- On `checkout.session.completed`: provisions MCU credits via `MCUBilling.add_credits()`
- On `customer.subscription.deleted`: marks customer as churned

### A3. CLI Subscribe Command
**Create:** `.claude/commands/subscribe.md`
```
mekong subscribe --tier starter    # Opens Stripe Checkout
mekong subscribe --list            # Show plans
mekong status                      # Balance, tier, renew date
```

### A4. Connect to Existing Code
- Import `from src.core.mcu_billing import MCUBilling` in webhook
- SQLite path: `~/.mekong/mcu_ledger.db`
- Test: `node scripts/stripe-webhook.cjs --test` provisions credits

## Files
- Create: `scripts/stripe-checkout.cjs`
- Create: `scripts/stripe-webhook.cjs`  
- Create: `.claude/commands/subscribe.md`
- Modify: `src/core/mcu_billing.py` (ensure add_credits() works standalone)

## Dependencies
- Stripe account + API keys (test mode first)
- `npm install stripe`
