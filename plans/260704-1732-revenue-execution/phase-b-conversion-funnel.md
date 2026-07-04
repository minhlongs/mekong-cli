# Phase B: Conversion Funnel — Signup + Trial + Onboarding

**Goal:** CLI-based signup → 14-day trial → paid conversion.

## Steps

### B1. Signup Command
**Create:** `.claude/commands/signup.md`
```
mekong signup                    # Email + password prompt
mekong signup --email a@b.com   # Non-interactive
```
- Stores credentials in `~/.mekong/auth.json`
- Starts 14-day trial → 50 MCU credits
- Calls HubSpot API (from Phase C) to create contact

### B2. Trial Logic
- New users get 50 MCU credits free
- `MCUBilling.add_credits("user-id", 50, source="trial")`
- Trial expiry tracked in SQLite
- Warning when credits < 10 remaining
- `mekong subscribe` on credit exhaustion

### B3. Graceful Degradation
- When MCU=0: `mekong` shows "Credits exhausted. Subscribe: mekong subscribe"
- Read-only commands (help, status, audit) still free
- All execution commands require credits

### B4. Onboarding Flow
```
mekong init              # Setup wizard
mekong tutorial          # Interactive 5-step walkthrough
  Step 1: Set API keys
  Step 2: Choose agents
  Step 3: Run first workflow
  Step 4: View results  
  Step 5: Invite (referral)
mekong status            # Show credits, agent count, next steps
```

## Files
- Create: `.claude/commands/signup.md`
- Create: `.claude/commands/tutorial.md`
- Modify: `mekong/bootstrap/index.cjs` (add signup check)
- Create: `scripts/trial-manager.cjs`

## Dependencies
- Phase A complete (Stripe → credits flow)
- Phase C complete (HubSpot contact creation)
