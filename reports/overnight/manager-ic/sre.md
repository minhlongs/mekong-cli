# SRE Report — Mekong CLI
*Role: Site Reliability Engineer | Date: 2026-03-11*

---

## Reliability Philosophy

Mekong CLI runs on Cloudflare's global edge network — inheriting CF's 99.99% uptime
SLA at the infrastructure layer. Our reliability obligations are:
1. CF Workers stay within memory/CPU limits
2. D1 queries stay fast (< 50ms p99)
3. LLM provider failures degrade gracefully (fallback chain)
4. Tôm Hùm daemon processes missions without queue starvation

**Error budget:** 99.9% uptime target = 8.7 hours downtime/year allowed.
Most downtime risk comes from LLM provider outages, not CF infrastructure.

---

## Service Level Objectives (SLOs)

| Service | SLO | Measurement |
|---------|-----|-------------|
| raas-gateway API | 99.9% success rate on non-402 requests | CF Analytics |
| D1 query latency | p99 < 50ms | CF Analytics |
| Mission success rate | > 85% of submitted missions complete | App metric |
| LLM response time | p95 < 10s per call | Custom logging |
| CF Pages (landing) | 99.99% availability | CF inherits |
| Tôm Hùm queue drain | < 5 min queue depth under normal load | CF Queues metrics |

---

## Incident Response Playbook

### P0 — Production Down (raas-gateway returning 5xx to all users)

```
Detection: UptimeRobot alert → #sre-alerts Slack
Response time: < 15 minutes

Steps:
1. Check CF Workers dashboard → error rate graph
2. Check CF status page: cloudflarestatus.com
3. If CF issue: wait for CF resolution (not our problem)
4. If our code: wrangler rollback --env production
5. Verify: curl -sI https://agencyos.network/v1/health | head -3
6. Post-mortem within 24 hours
```

### P1 — Elevated Error Rate (> 1% 5xx, not total outage)

```
Detection: CF Analytics alert → #eng-alerts Slack
Response time: < 1 hour

Steps:
1. Identify which Worker is failing (raas-gateway vs openclaw-worker)
2. Check Sentry for exception details
3. Check recent deploys: git log --oneline -10
4. If recent deploy caused it: wrangler rollback
5. If LLM provider issue: check provider status page
6. If D1 issue: check query performance in CF dashboard
```

### P2 — Mission Success Rate Drop (< 85%)

```
Detection: D1 query alert → #product-alerts Slack
Response time: < 4 hours

Steps:
1. Query D1 for mission failure breakdown by error type
2. Check if specific LLM provider failing (route traffic to backup)
3. Check if specific command type failing (disable command if needed)
4. Notify users if ETA > 2 hours via Discord
```

---

## Monitoring Stack

### Current State: Mostly Unmonitored
This is the highest SRE risk. Required setup:

| Tool | Purpose | Cost | Priority |
|------|---------|------|----------|
| Cloudflare Analytics | Worker errors, latency, requests | $0 | Available now |
| Sentry (free tier) | Exception tracking with stack traces | $0 | P0 — set up immediately |
| UptimeRobot | HTTP uptime checks every 5 min | $0 | P0 — set up immediately |
| PostHog | Product analytics, funnel | $0 (self-hosted) | P1 |
| CF Queues metrics | Tôm Hùm queue depth | $0 | P1 |

### Sentry Setup (CF Workers)

```typescript
// apps/raas-gateway/index.js
import * as Sentry from "@sentry/cloudflare";

export default Sentry.withSentry(
  (env) => ({
    dsn: env.SENTRY_DSN,
    tracesSampleRate: 0.1,  // 10% sampling to stay in free tier
  }),
  {
    async fetch(request, env, ctx) {
      // existing handler
    }
  }
);
```

### Alerting Rules (CF Workers + Slack webhook)

```typescript
// Cron worker: runs every 5 minutes
async function healthCheck(env: Env) {
  const metrics = await getMetrics(env);

  if (metrics.errorRate > 0.01) {
    await notify(env.SLACK_WEBHOOK, `P1: Error rate ${metrics.errorRate * 100}%`);
  }
  if (metrics.queueDepth > 100) {
    await notify(env.SLACK_WEBHOOK, `P2: Queue depth ${metrics.queueDepth} messages`);
  }
  if (metrics.missionSuccessRate < 0.85) {
    await notify(env.SLACK_WEBHOOK, `P2: Mission success ${metrics.missionSuccessRate * 100}%`);
  }
}
```

---

## Capacity Planning

### CF Workers Limits (Free tier)

| Resource | Free Limit | Current Usage | Risk |
|----------|-----------|---------------|------|
| Requests/day | 100,000 | Unknown | Low at current scale |
| CPU time/request | 10ms | ~2ms (simple auth) | Low |
| Memory/request | 128MB | ~10MB | Low |
| D1 reads/day | 5,000,000 | Unknown | Low |
| D1 writes/day | 100,000 | Unknown | Low |
| KV reads/day | 100,000 | Unknown | Low |
| Queues messages/day | 100,000 | Unknown | Monitor at scale |

Upgrade trigger: any resource hitting 80% of free tier limit → move to $5/mo Workers Paid.

### LLM Provider Capacity

No rate limit issues expected at current scale. Monitor when:
- > 100 concurrent users
- > 1,000 `mekong cook` calls/day

Mitigation: CF KV prompt cache reduces duplicate LLM calls.

---

## Disaster Recovery

| Scenario | Detection | Recovery | RTO | RPO |
|----------|-----------|---------|-----|-----|
| Bad Worker deploy | Sentry spike + UptimeRobot | `wrangler rollback` | 5 min | 0 |
| D1 data corruption | App errors + D1 query fails | CF point-in-time restore | 4 hr | 24 hr |
| LLM provider down | Mission success rate drop | Auto-fallback to next provider | <1 min | 0 |
| Polar.sh outage | New signups fail (402 on valid users) | Manual credit grant via D1 | 30 min | 0 |
| GitHub down | CI/CD blocked | Manual `wrangler deploy` from local | 15 min | 0 |

---

## Runbooks (To Be Written)

- [ ] `runbook-worker-rollback.md` — step-by-step wrangler rollback
- [ ] `runbook-d1-restore.md` — CF D1 point-in-time recovery
- [ ] `runbook-llm-provider-switch.md` — manually force LLM provider
- [ ] `runbook-credit-grant.md` — manually add MCU credits via D1 SQL
- [ ] `runbook-queue-drain.md` — clear stuck Tôm Hùm queue messages

---

## Q2 SRE Actions

- [ ] Set up Sentry on `raas-gateway` and `openclaw-worker` (P0)
- [ ] Set up UptimeRobot for `agencyos.network` health endpoint (P0)
- [ ] Add `/v1/health` endpoint to raas-gateway returning 200 + version (P0)
- [ ] Write `wrangler rollback` runbook in `docs/deployment-guide.md` (P1)
- [ ] Configure CF Analytics alerts for error rate > 1% (P1)
- [ ] Add D1 → R2 daily backup export cron job (P1)
- [ ] Document SLOs formally in `docs/system-architecture.md` (P2)
