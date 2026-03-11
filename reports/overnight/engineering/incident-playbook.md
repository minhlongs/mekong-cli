# Incident Response Playbook — Mekong CLI

**Date:** 2026-03-11
**Scope:** CF Worker outages, gateway failures, LLM failures, billing incidents, rollback procedures

---

## 1. Severity Levels

| Level | Definition | Response Time |
|-------|-----------|---------------|
| P0 | Production down, all users affected | Immediate |
| P1 | Billing/auth broken, subset users affected | < 30 min |
| P2 | Feature degraded, workaround exists | < 2 hours |
| P3 | Minor issue, cosmetic or edge case | Next sprint |

---

## 2. Incident Checklist (All Severities)

```
[ ] 1. Confirm incident scope (which service, which users)
[ ] 2. Check health endpoints
[ ] 3. Check GitHub Actions for recent failed deploys
[ ] 4. Check CF Worker logs (Cloudflare dashboard → Workers → Logs)
[ ] 5. Identify last known good commit
[ ] 6. Decide: hotfix or rollback
[ ] 7. Execute fix
[ ] 8. Verify production GREEN
[ ] 9. Write post-mortem
```

---

## 3. Health Check Commands

```bash
# RaaS Gateway
curl -sI https://raas.agencyos.network/health | head -3

# CF Worker engine
curl -sI https://mekong-engine.<account>.workers.dev/health | head -3

# Local orchestrator health endpoint
curl -s http://127.0.0.1:9192/health | python3 -m json.tool

# Check recent GitHub Actions
gh run list -L 5 --json status,conclusion,name,createdAt
```

---

## 4. Scenario: CF Worker Gateway Down (P0)

**Symptoms:** All CLI commands fail with connection error or HTTP 5xx.

```bash
# Step 1: Verify scope
curl -sI https://raas.agencyos.network/health
# Expected: HTTP 200 {"status":"ok"}

# Step 2: Check CF status
open https://www.cloudflarestatus.com

# Step 3: Check Worker logs
# Cloudflare Dashboard → Workers & Pages → raas-gateway → Logs tab

# Step 4: Identify bad deploy
wrangler deployments list --name raas-gateway

# Step 5a: Rollback Worker
wrangler rollback <previous-deployment-id> --name raas-gateway

# Step 5b: OR revert + redeploy
cd apps/raas-gateway
git revert HEAD
wrangler deploy

# Step 6: Verify
curl -sI https://raas.agencyos.network/health
```

---

## 5. Scenario: LLM Provider Failures (P1/P2)

**Symptoms:** `cook` / `plan` commands hang or return empty results.

```bash
# Step 1: Check which provider is failing
# Orchestrator health endpoint shows provider status:
curl -s http://127.0.0.1:9192/health | python3 -m json.tool

# Step 2: Test provider directly
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  "$LLM_BASE_URL/models"

# Step 3: Circuit breaker auto-recovers after 15s cooldown
# Wait 15s then retry — orchestrator will failover to next provider

# Step 4: Force provider override
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-...
export LLM_MODEL=anthropic/claude-sonnet-4

# Step 5: If all providers down — CLI still works in offline mode
# Rule-based decomposition activates automatically, LLM steps skipped
```

**LLM failover chain:**
```
LLM_BASE_URL → OpenRouter → AgentRouter → DashScope →
DeepSeek → Anthropic → OpenAI → Gemini → Ollama → Offline
```

---

## 6. Scenario: MCU Billing Broken / HTTP 402 (P1)

**Symptoms:** All authenticated requests return `HTTP 402 Payment Required`.

```bash
# Step 1: Verify it's not legitimate (user really has balance)
# Check KV store for user's MCU balance:
# Cloudflare Dashboard → Workers & Pages → KV → mekong-quota → search userId

# Step 2: Check quota sync
# Gateway uses KV bucket: key = "quota:{userId}:{YYYY-MM}"
# If corrupted, delete and let it regenerate on next request

# Step 3: Check raas_gate.py logs
grep "402\|quota\|mcu" ~/.mekong/logs/gateway.log | tail -50

# Step 4: Emergency override (P0 only)
# Set env var BYPASS_MCU_GATE=1 (undocumented emergency escape hatch)
# Document incident and restore billing after fix

# Step 5: If billing sync failed
cd /Users/macbookprom1/mekong-cli
python3 -m src.jobs.nightly_reconciliation --force-user <userId>
```

---

## 7. Scenario: Failed GitHub Actions / Broken CI (P2)

**Symptoms:** Push to main, CI fails, deploy blocked.

```bash
# Step 1: View failed run
gh run list -L 3
gh run view <run-id> --log-failed

# Step 2: Common failures
# a) ruff lint error → fix locally: ruff check src/ tests/ --fix
# b) pytest failure → python3 -m pytest tests/ -q --tb=short
# c) Import error → python3 -m py_compile src/core/*.py

# Step 3: Hotfix commit
git add <fixed-files>
git commit -m "fix: resolve CI failure in <component>"
git push origin main

# Step 4: Monitor
gh run watch
```

---

## 8. Scenario: Orchestrator Self-Healing Loop (P2)

**Symptoms:** `mekong cook` keeps retrying the same command, high LLM API usage.

**Root cause:** Self-healing in `StepExecutor` sends failing command to LLM for correction, retries — if LLM returns same/broken command, loops.

```bash
# Step 1: Kill the process
Ctrl+C  # or kill -9 <pid>

# Step 2: Run with rollback disabled
mekong cook "goal" --no-rollback

# Step 3: Run with dry-run to inspect plan before execution
mekong cook "goal" --dry-run

# Step 4: Check if bug is StepExecutor.console AttributeError
# symptom: AttributeError in stderr, self-healing never actually fires
# fix: add self.console = Console() to StepExecutor.__init__
```

---

## 9. Rollback Procedures

### Python Package Rollback
```bash
# Pin to last known good version
pip install mekong-cli==<last-good-version>

# Or from git directly
pip install git+https://github.com/org/mekong-cli@<commit-sha>
```

### Git Revert (triggers redeploy)
```bash
git revert HEAD --no-edit
git push origin main
# Wait for CI/CD GREEN then verify production
```

### Cloudflare Worker Rollback (instant, no CI)
```bash
wrangler deployments list
wrangler rollback <deployment-id>
```

---

## 10. Post-Mortem Template

```markdown
## Incident: [Title]

**Date:** YYYY-MM-DD
**Duration:** Xh Ym
**Severity:** P0/P1/P2/P3
**Services Affected:** [gateway/engine/cli/billing]

### Timeline
- HH:MM — Incident detected
- HH:MM — Root cause identified
- HH:MM — Fix applied
- HH:MM — Production verified GREEN

### Root Cause
[1-2 sentences]

### Fix Applied
[What changed]

### Prevention
- [ ] Action item 1
- [ ] Action item 2

### Build: ✅/❌ | Tests: ✅/❌ | CI/CD: ✅/❌ | Production: ✅/❌ HTTP 200
```

---

## 11. Key Contact Points

| Component | Owner | How to Access |
|-----------|-------|---------------|
| CF Workers | Cloudflare Dashboard | cloudflare.com/dashboard |
| GitHub Actions | GitHub | github.com/org/mekong-cli/actions |
| LLM providers | API dashboards | per-provider dashboard |
| PyPI | PyPI account | pypi.org/manage |
| Wrangler CLI | Local tool | `wrangler whoami` |
