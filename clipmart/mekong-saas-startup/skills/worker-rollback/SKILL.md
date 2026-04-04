---
name: worker-rollback
description: "Rollback to previous known-good state"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Rollback to previous known-good state"
argument-hint: [commit-hash or steps]
---

# /worker-rollback — Worker Operation

Safely rollback changes.

1. Identify rollback target
2. Create backup of current state
3. `git revert` or `git reset` (prefer revert)
4. Verify build passes after rollback

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
