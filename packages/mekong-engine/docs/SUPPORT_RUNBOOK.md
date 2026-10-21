# Mekong Engine — Pilot Support & Go-Live Runbook

**Status:** Readiness-Gated, Invite-Only Pilot (Up to 5 Partners)

## Quick Reference

| Item | Value |
|------|-------|
| **Public Site** | `https://mekongmind.com` |
| **Engine API (Production)** | `https://api.cashclaw.cc` |
| **Dashboard Demo (Production)** | `https://ide.mekongmind.com` (Synthetic Demo Only) |
| **Production D1 / KV / Queue** | `mekong-db` / `RATE_LIMIT_KV` / `mekong-mission-queue` (`mekong-mission-dlq`) |
| **Staging D1 / KV / Queue** | `mekong-db-staging` / `RATE_LIMIT_KV` (staging) / `mekong-mission-queue-staging` (`mekong-mission-dlq-staging`) |

> **Pilot Disclaimer:** This environment supports an invite-only pilot for up to 5 partners using synthetic data and test integrations only. No commercial SLAs, paid tiers, real filings, live payments, or outbound customer messages are active.

---

## 1. Staging Rehearsal & Migration Order

Always rehearse additive D1 migrations in order against isolated staging resources before applying to production:

```bash
cd packages/mekong-engine

# 1. Apply additive migrations in order on staging D1
for f in $(ls migrations/*.sql | sort); do
  npx wrangler d1 execute mekong-db-staging --env staging --remote --file="$f"
done

# 2. Deploy staging Engine Worker
npx wrangler deploy --env staging

# 3. Verify full staging flow: invite -> tenant -> mission -> result
# 3a. Issue invite
INVITE_CODE=$(curl -s -X POST "$STAGING_URL/billing/invites" \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"partner_name":"Staging Smoke Partner"}' | jq -r '.invite_code')

# 3b. Redeem invite & create tenant
API_KEY=$(curl -s -X POST "$STAGING_URL/billing/tenants" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Staging Smoke Partner\",\"invite_code\":\"$INVITE_CODE\"}" | jq -r '.api_key')

# 3c. Submit LLM-only mission
MISSION_ID=$(curl -s -X POST "$STAGING_URL/v1/tasks" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Generate staging smoke summary","params":{"complexity":"simple"}}' | jq -r '.id')

# 3d. Poll status & result
curl -s "$STAGING_URL/v1/tasks/$MISSION_ID" -H "Authorization: Bearer $API_KEY" | jq .
```

---

## 2. Production Cutover & Post-Deploy Smoke Checks

Production release is driven by `.github/workflows/deploy-cf.yml`. It applies additive D1 migrations, then promotes the API, Dashboard, and site in sequence. Each target must pass staging smoke checks and a separate 30-minute production observation window before the next target is promoted. Do not run manual `wrangler deploy` commands for this release path.

Before the production baseline job can pass, configure the GitHub `production` environment secret `SECURITY_ALERT_URL`. It must answer `GET` with HTTP 200 and JSON `{"active":false}` when no alert is active. The monitor stops and triggers rollback on an active, invalid, unreachable, or non-200 alert feed. If the endpoint requires bearer authentication, set `SECURITY_ALERT_TOKEN` as a second secret.

The staging smoke flow exercises invite-only onboarding and an LLM-only mission using staging credentials and data. Payment checks stay in provider sandbox mode; production smoke checks are read-only health and synthetic Dashboard/site probes.

---

## 3. 30-Minute Post-Cutover Monitoring & Rollback Triggers

The release workflow polls each production endpoint and the configured security alert feed for **30 minutes after each target deployment**. It records two synthetic probes per target per minute and evaluates each service's rolling 10-minute error rate separately.

### Mandatory Rollback Triggers

Trigger an immediate rollback (`./ci/helpers/rollback.sh api production` and/or `./ci/helpers/rollback.sh dashboard production`) if **any** of the following occur during the 30-minute observation window:

1. **Error Rate > 5%** across HTTP requests or queue consumer batches.
2. **Latency > 2× Baseline** (p95 response latency exceeds twice the pre-deploy baseline).
3. **Any Security Alert** (unauthorized tenant creation without invite code, cross-tenant access attempt, non-LLM step bypass, or secret exposure).

---

## 4. Queue, Outbox, and Credit Diagnostics

```bash
# Inspect mission outbox statuses
npx wrangler d1 execute mekong-db --command \
  "SELECT status, COUNT(*) AS count FROM mission_outbox GROUP BY status;"

# Inspect idempotent mission credit events (debit / refund)
npx wrangler d1 execute mekong-db --command \
  "SELECT mission_id, event_type, amount, created_at FROM mission_credit_events ORDER BY created_at DESC LIMIT 20;"

# Inspect pilot invite usage (capped at 5 non-revoked invites)
npx wrangler d1 execute mekong-db --command \
  "SELECT id, partner_name, status, redeemed_by_tenant_id, created_at, redeemed_at FROM pilot_invites;"
```
