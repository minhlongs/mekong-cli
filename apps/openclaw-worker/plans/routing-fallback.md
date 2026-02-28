# Emergency API Fallback: Strategic Routing

Approved plan to harden the CTO routing logic and ensure zero-downtime when Claude Pro hits rate limits.

## Implementation Steps
1. **Detect Pro Limit**: Pattern match "You've hit your limit" in CC CLI terminal.
2. **Persistence**: Use system-status-registry.js to track pro_limit_hit state.
3. **Hybrid Fallback**: If Pro is hit, force 9Router API (Port 20128) even for planning.
4. **Strategic Mandate**: Strictly enforce /plan only for Pro sessions. Use mandatePrefix with DESIGN ONLY instructions.
5. **Worker Stability**: Ensure wrangler dev is running reliably on Port 8787.

## Verification
- Confirm routing logs show FALLBACK when Pro limit is set.
- Confirm mandatePrefix in mission-dispatcher.js is shortened as per Chairman request.
