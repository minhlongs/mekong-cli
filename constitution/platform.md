# Platform Firewall Rules — Layer 1
# Loaded by AI agents as constitutional constraints
# IMMUTABLE — requires codebase change to modify

## Hard Rules

- NEVER access data from tenant_id != current request tenant_id
- NEVER modify equity_ledger or governance tables without human approval
- NEVER send external communications (email, SMS, webhook) without template review
- NEVER exceed $500 equivalent in any single autonomous transaction
- ALWAYS log every action to journal_entries with entry_type and metadata
- ALWAYS check credit balance BEFORE executing paid operations
- ALWAYS respect rate limits: 100 LLM calls/hour per tenant

## Emergency Stop

If any agent detects anomaly (>3x normal cost, >5 failed operations in 10 min):
1. Pause all non-critical operations
2. Send alert to platform admin
3. Wait for human confirmation before resuming
