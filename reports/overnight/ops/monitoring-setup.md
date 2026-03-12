# Monitoring & Observability — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** monitoring, platform-monitoring-setup

---

## Current Monitoring State

### What Exists

| Component | Location | Status |
|-----------|----------|--------|
| Rate-limit metrics | `src/telemetry/rate_limit_metrics.py` | ACTIVE |
| Telemetry collector | `src/core/telemetry_collector.py` | ACTIVE |
| Telemetry uploader | `src/core/telemetry_uploader.py` | ACTIVE (consent-gated) |
| Telemetry consent | `src/core/telemetry_consent.py` | ACTIVE |
| Telemetry hooks | `src/core/telemetry_hooks.py` | ACTIVE |
| Telemetry models | `src/core/telemetry_models.py` | ACTIVE |
| Telemetry reporter | `src/core/telemetry_reporter.py` | ACTIVE |
| License monitor | `src/core/license_monitor.py` | ACTIVE |
| RaaS audit logger | `src/core/raas_audit_logger.py` | ACTIVE |
| Anomaly detector | `src/core/anomaly_detector.py` | ACTIVE |
| Log files | `logs/api.log`, `logs/api.error.log`, `logs/audit/` | ACTIVE |
| Nightly reconciliation | `scripts/nightly-reconciliation.sh` | SCHEDULED (cron) |
| Daily repo status | `.github/workflows/daily-repo-status.md` | ACTIVE (GH Actions) |
| Langfuse | `test_langfuse.py` exists | TEST-ONLY, not confirmed in prod |
| Sentry | Not found in `src/` | MISSING |
| Datadog/NewRelic | Not found | MISSING |

---

## Telemetry Architecture

```
User action (mekong cook/plan/...)
         │
         ▼
TelemetryHooks → TelemetryCollector (in-memory buffer)
                         │
                         ▼
               ConsentManager.has_consent()?
                    YES │         NO → discard
                        ▼
              TelemetryUploader.upload_batch()
                        │
                        ▼
              POST /api/v1/telemetry/events
              → https://api.mekong.dev
```

- Batch size: 100 events per upload
- Backend URL: `TELEMETRY_BACKEND_URL` env var (defaults to `https://api.mekong.dev/...`)
- Anonymous ID: `X-Anonymous-ID` header — no PII
- Consent-gated: opt-in model (plan: `plans/260307-1602-telemetry-consent-opt-in/`)

---

## Rate Limit Metrics

`src/telemetry/rate_limit_metrics.py` — `RateLimitMetricsEmitter` class:

Events emitted:
- `override_applied` — rate limit override used
- `request_allowed` — request within quota
- `rate_limited` — request blocked

Data captured per event:
- `tenant_id`, `tier`, `endpoint`, `preset`
- `quota_limit`, `quota_remaining`, `quota_utilization_pct`
- `client_ip`, `method`, `path`, `user_agent`
- `response_status`, `retry_after`

Persisted to: `rate_limit_events` table (migration `006_create_rate_limit_events.sql`)

---

## Logging Infrastructure

### Current Log Files (`logs/`)
```
api.log                    — API access log
api.error.log              — API error log
audit/                     — security/billing audit trail
autopilot.log              — daemon activity
macook-guardian.log        — M1 cooling guardian
dna-transformer*.log       — DNA transformer jobs
power-source-sync*.log     — power sync jobs
```

### Log Format
- Standard Python `logging` module throughout `src/`
- `logger = logging.getLogger(__name__)` pattern
- Log levels: DEBUG/INFO/WARNING/ERROR used
- Not structured JSON — plain text

### Gap: No Centralized Aggregation
Logs are local files only. No shipping to ELK, Loki, CloudWatch, or similar.

---

## Nightly Reconciliation

`scripts/nightly-reconciliation.sh` + `.github/workflows/nightly-reconciliation.yml`:
- Runs at **2 AM UTC daily**
- Reconciles billing between local DB and Stripe
- Writes timestamped log: `/var/log/mekong/reconciliation-YYYY-MM-DD.log`
- Optional: Telegram + webhook alerts on failure
- Requires: `MEKONG_DATABASE_URL`, `MEKONG_STRIPE_SECRET_KEY`

---

## Health Monitoring Tests

Tests that verify runtime health monitoring:
- `tests/test_health_monitoring.py` — 95 passed (verified locally)
- `tests/test_subsystem_health.py` — included in above run
- `tests/test_health_watchdog.py` — watchdog behavior

---

## Gaps & Recommendations

### Critical Gaps

| Gap | Impact | Fix |
|-----|--------|-----|
| No Sentry / error tracking | Exceptions silently lost in production | Add `sentry-sdk` to `requirements.txt`, init in `src/main.py` |
| Logs not structured JSON | Hard to query/alert on | Replace `logging.basicConfig` with `structlog` or JSON formatter |
| No uptime monitoring | No alerting if app goes down | Add UptimeRobot or CF Health Check on `/health` endpoint |
| Langfuse not confirmed in prod | LLM call tracing missing | Configure `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` in Fly secrets |
| No APM | No latency percentiles | Add CF Analytics / Fly metrics dashboard |

### Recommended Setup

```bash
# 1. Sentry (error tracking)
pip install sentry-sdk
# src/main.py:
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=0.1)

# 2. Structured logging
pip install structlog
# Replace logging.getLogger() with structlog.get_logger()

# 3. Fly metrics
fly metrics dashboard -a agencyos-gateway

# 4. Uptime monitoring
# Add Cloudflare Health Check or UptimeRobot for /health endpoint

# 5. Langfuse (LLM tracing)
# Set in Fly secrets:
fly secrets set LANGFUSE_PUBLIC_KEY=pk-... LANGFUSE_SECRET_KEY=sk-...
```

---

## Alerting Channels Available

- `src/core/telegram_bot.py` — Telegram notifications (configured via `TELEGRAM_API_TOKEN`)
- Nightly reconciliation supports webhook alerts (`MEKONG_WEBHOOK_URL`)
- GitHub Actions notifications via workflow status emails

---

## Monitoring Score: 5/10

Good internal telemetry pipeline and rate-limit metrics. Missing production error tracking (Sentry), structured logging, and uptime monitoring. LLM tracing via Langfuse exists in tests but not confirmed in production.
