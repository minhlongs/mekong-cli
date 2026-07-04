---
description: "Sign up for Mekong CLI — start 14-day trial with 50 MCU credits"
argument-hint: "[--email <email>]"
---

# /signup — Start Your Trial

## Usage
```
/signup                             # Interactive email prompt
/signup --email founder@myco.com    # Non-interactive
```

## Flow
1. Enter email
2. 14-day trial starts automatically
3. 50 MCU credits provisioned
4. Run `/tutorial` to get started
5. Subscribe before trial ends: `/subscribe --tier starter`

## Implementation
Execute: `node scripts/trial-manager.cjs start <email>`

Then show welcome message with next steps.
