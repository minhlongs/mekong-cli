---
description: "Subscribe to Mekong CLI — Stripe Checkout payment"
argument-hint: "[--tier starter|growth|pro | --list | --status]"
---

# /subscribe — Subscribe to Mekong CLI

## Usage
```
/subscribe --tier starter     # Open Stripe Checkout for Starter ($49/mo)
/subscribe --list             # Show available plans
/subscribe --status           # Show current subscription status
```

## Plans
| Tier | Price | MCU Credits/mo |
|------|-------|----------------|
| Starter | $49 | 200 |
| Growth | $149 | 1,000 |
| Pro | $499 | 5,000 |

## Flow
1. Run `/subscribe --list` to see plans
2. Run `/subscribe --tier starter` to open Stripe Checkout
3. Complete payment in browser
4. Credits appear in `mekong status` within 1 minute

## Implementation
Execute: `node scripts/stripe-checkout.cjs --tier <tier>`
