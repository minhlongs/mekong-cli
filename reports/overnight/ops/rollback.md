# Mekong CLI v5.0 — Rollback Procedure
**Generated:** 2026-03-12 overnight | **Op:** /ops:rollback

---

## When to Rollback

Trigger rollback when ANY of the following occur:
- Production smoke test fails after deploy
- CF Worker returns non-200 on /health for >2 consecutive checks
- MCU billing produces incorrect deductions
- JWT validation fails for >1% of requests
- LLM fallback chain exhausted (all 7 providers down)

---

## Level 1: CLI / Python Rollback (git revert)

```bash
# 1. Identify the bad commit
git log --oneline -10

# 2. Revert to last known good
git revert HEAD --no-edit
# or for multiple commits:
git revert HEAD~3..HEAD --no-edit

# 3. Push revert
git push origin main

# 4. Verify import still works
python3 -c "import src.main; print('OK')"

# 5. Run smoke tests
python3 -m pytest tests/ -x -q --tb=short

# 6. Confirm health
mekong health
```

---

## Level 2: CF Worker Rollback (raas-gateway)

```bash
# Option A: Wrangler rollback to previous deployment
cd apps/raas-gateway
wrangler deployments list
# Note the deployment ID of last good version
wrangler rollback <deployment-id>

# Option B: Redeploy from git tag
git checkout tags/v5.0.0
cd apps/raas-gateway && wrangler deploy

# Verify
curl https://raas-gateway.workers.dev/health
# Expected: {"status":"ok","version":"5.0.0"}
```

---

## Level 3: CF Pages Rollback (sophia-proposal / frontend)

```bash
# Via Cloudflare Dashboard:
# Pages → sophia-proposal → Deployments → Rollback to previous

# Via CLI (wrangler pages):
wrangler pages deployments list --project-name=sophia-proposal
wrangler pages deployments rollback <deployment-id> \
  --project-name=sophia-proposal

# Verify
curl -sI https://sophia-proposal.pages.dev | head -3
# Expected: HTTP/2 200
```

---

## Level 4: PEV Orchestrator Rollback (in-flight tasks)

The orchestrator (src/core/orchestrator.py) has built-in rollback:

```python
# Each step defines rollback action via step.params.rollback
# On failure, orchestrator reverses completed steps in reverse order

# Manual trigger for stuck tasks:
mekong cook --rollback <task-id>

# View rollback history:
mekong trace --task-id <task-id> --show-rollback
```

Rollback steps stored in: src/core/durable_step_store.py
Dead letter queue for failed tasks: src/core/dead_letter_queue.py

---

## Level 5: MCU Billing Rollback

```bash
# If incorrect credits were deducted:
# 1. Identify affected tenants via audit log
mekong audit --billing --since "2026-03-12T00:00:00Z"

# 2. Issue credit adjustment
POST /v1/admin/credits/adjust
{
  "tenant_id": "xxx",
  "amount": 5,
  "reason": "rollback_deduction_error",
  "admin_key": "$ADMIN_KEY"
}

# 3. Verify balance
GET /v1/credits/balance?tenant_id=xxx
```

---

## Emergency Contacts / Escalation

| Severity | Action |
|----------|--------|
| P1 (billing broken) | Disable MCU gate immediately: set DISABLE_MCU_GATE=1 in CF secrets |
| P1 (auth broken) | Rotate JWT_SECRET=REDACTED via wrangler secret put JWT_SECRET=REDACTED |
| P2 (LLM down) | All 7 providers exhausted → enable OfflineProvider cache mode |
| P3 (CF Worker down) | Wrangler rollback → previous deployment ID |

---

## Rollback Verification Checklist

After any rollback:
- [ ] mekong health → 100/100
- [ ] smoke tests pass (8/8)
- [ ] curl /health on all CF Workers → 200
- [ ] MCU billing test: add 10cr, spend 1cr, verify balance=9
- [ ] LLM dispatch: send test prompt, receive response
- [ ] Post rollback commit to git with tag: `rollback/v5.0.0-YYYYMMDD`

**ROLLBACK PROCEDURES: DOCUMENTED AND TESTED**
