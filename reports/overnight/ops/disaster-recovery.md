# Disaster Recovery Plan — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** ops-disaster-recovery, rollback, crisis

---

## Infrastructure Overview

| Layer | Platform | Recovery Method |
|-------|----------|----------------|
| Frontend (landing) | Cloudflare Pages | Redeploy from git push |
| Edge API / Engine | Cloudflare Workers | `wrangler deploy` from `packages/mekong-engine` |
| Backend API | Fly.io (`agencyos-gateway`) | `fly deploy` or git push |
| Database | SQLite on Fly volume (`agencyos_data`) | Fly volume snapshots |
| Code | GitHub (`main` branch) | git history, tags |

---

## Recovery Time Objectives

| Scenario | RTO | RPO | Method |
|----------|-----|-----|--------|
| CF Pages/Workers outage | < 5 min | 0 | Auto-redeploy via git push |
| Fly.io app crash | < 2 min | 0 | Auto-restart (`auto_start_machines = true`) |
| Bad deploy (regression) | < 10 min | 0 | Git revert + push |
| DB corruption (SQLite) | < 4 hours | < 24 hours | Restore from Fly volume snapshot |
| Full infra loss | < 2 hours | < 24 hours | Scaffold new infra + restore DB |
| Secret compromise | < 30 min | N/A | Rotate via CF/Fly dashboards |

---

## Rollback Procedures

### 1. Application Rollback (Cloudflare Workers)

```bash
# List recent deployments
wrangler deployments list --name mekong-engine

# Roll back to previous deployment
wrangler rollback [deployment-id] --name mekong-engine

# Or redeploy specific git commit
git checkout <previous-sha>
cd packages/mekong-engine && wrangler deploy
git checkout main
```

### 2. Cloudflare Pages Rollback

```bash
# Via Cloudflare dashboard: Pages → Project → Deployments → Rollback
# Or force-redeploy previous commit:
git revert HEAD && git push origin main
```

### 3. Fly.io App Rollback

```bash
# Check release history
fly releases -a agencyos-gateway

# Roll back to previous release
fly deploy --image registry.fly.io/agencyos-gateway:<previous-version>

# Or via fly.io dashboard: App → Releases → Rollback
```

### 4. Database Rollback (SQLite / Fly Volume)

```bash
# Fly volume snapshots (check availability)
fly volumes list -a agencyos-gateway
fly volumes snapshots list <volume-id>

# Restore: stop app, restore volume, restart
fly scale count 0 -a agencyos-gateway
# Restore volume from snapshot via Fly dashboard
fly scale count 1 -a agencyos-gateway
```

### 5. Application-Level Rollback (PEV Orchestrator)

Built-in rollback logic in `src/core/orchestrator.py`:
- Reverses completed steps via `step.params.rollback`
- Triggered automatically on verification failure in strict mode
- CLI flag: `mekong cook --no-rollback` to disable

---

## PEV Rollback Flow

```
Plan → Execute Step 1 → Execute Step 2 → FAILURE
                                         ↓
                         Verify fails → rollback Step 2 → rollback Step 1
```

Code path: `orchestrator.py` → `verifier.py` → rollback sequence

---

## Migration Rollback

Database migrations (`src/db/migrations/`):
```
001_create_users_table.sql
002_add_roles_to_licenses.sql
003_create_user_sessions.sql
004_add_role_to_users.sql
005_create_tier_configs.sql
006_create_rate_limit_events.sql
007_add_license_enforcement_events.sql
008_billing_system.sql
```
- No `down` migrations present — **gap: no automated rollback for schema changes**
- Manual rollback requires restoring from snapshot before migration was applied

---

## Crisis Playbook

### P0: Production Completely Down

1. Check CF status: `curl -sI https://www.cloudflarestatus.com`
2. Check Fly.io status: `curl -sI https://status.fly.io`
3. `fly status -a agencyos-gateway` — check machine state
4. `fly logs -a agencyos-gateway` — tail recent logs
5. If app crashed: `fly scale count 0 && fly scale count 1 -a agencyos-gateway`
6. If deploy broke: `fly releases -a agencyos-gateway` → rollback
7. Alert via Telegram bot (`src/core/telegram_bot.py`) if available

### P1: API Returning 5xx

1. `fly logs -a agencyos-gateway -n 100` — check error logs
2. Check `logs/api.error.log` for patterns
3. If DB issue: `fly ssh console -a agencyos-gateway` → check SQLite
4. If code issue: `git revert HEAD && git push` → triggers redeploy

### P2: LLM Provider Down

- Fallback chain in `src/core/llm_client.py`:
  `OPENROUTER_API_KEY → DASHSCOPE_API_KEY → DEEPSEEK_API_KEY → ANTHROPIC_API_KEY → OPENAI_API_KEY → GOOGLE_API_KEY → OLLAMA_BASE_URL → OfflineProvider`
- Action: set working provider in `.env` / Fly secrets
- `fly secrets set LLM_API_KEY=<new-key> -a agencyos-gateway`

### P3: Compromised Secrets

1. **Immediately rotate:**
   - `fly secrets set CLOUDFLARE_API_TOKEN=<new> -a agencyos-gateway`
   - Rotate via CF dashboard
   - Update GitHub Actions secrets
2. Audit: `git log --all --full-history -- .env` — confirm .env never committed
3. Scan history: `trufflehog git file://. --only-verified`

---

## Backup Gaps (Current State)

| Item | Gap | Recommendation |
|------|-----|---------------|
| SQLite DB | No automated backup | Add `fly volumes snapshots` scheduled via nightly workflow |
| DB down migrations | Missing | Add rollback SQL files for each migration |
| DR drill | Not documented | Schedule quarterly DR drill |
| Backup verification | Not tested | Add monthly restore test to `nightly-reconciliation.yml` |

---

## Contacts & Access

| Resource | Access Method |
|----------|--------------|
| Cloudflare | Dashboard + `CLOUDFLARE_API_TOKEN` (GitHub secret) |
| Fly.io | `flyctl` + `FLY_API_TOKEN` |
| GitHub | Repository admin |
| LLM Providers | Per-provider API keys in Fly secrets |

---

## Status: PARTIAL

DR framework exists (PEV rollback, auto-restart, fallback LLM chain) but missing:
- Automated DB backups
- DB down-migrations
- Documented DR drill schedule
