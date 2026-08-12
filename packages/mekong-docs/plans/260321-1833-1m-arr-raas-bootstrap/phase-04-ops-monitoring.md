# Phase 04: Ops & Monitoring

## Priority: P1
## Status: pending

## Tasks

### 4.1 Health Check Enhancement
- GET /health → include DB latency, KV status, AI status
- Add /health/deep for detailed check
- Response time tracking

### 4.2 Admin Revenue Dashboard
- GET /admin/revenue/daily — daily revenue chart data
- GET /admin/revenue/mrr — current MRR calculation
- GET /admin/churn — churned tenants this month

### 4.3 Automated Weekly Digest Email
- Cron trigger: every Monday 9am UTC
- Send usage summary to all active tenants
- Use existing /tenants/digest data + Resend API

### 4.4 Error Tracking
- Structured error logging with request ID
- GET /admin/errors — recent error log (last 100)
- Error rate monitoring

### 4.5 Rate Limit Dashboard
- GET /v1/tenants/rate-limit-status — current usage vs limit
- Include reset time, remaining requests

### 4.6 API Latency Tracking
- Add X-Response-Time header to all responses
- Store p50/p95/p99 in KV for admin dashboard

## Files to Create/Modify
- apps/raas-gateway/src/routes/health.ts (deep health)
- apps/raas-gateway/src/routes/admin.ts (revenue, errors)
- apps/raas-gateway/src/middleware/logger.ts (latency tracking)
- apps/raas-gateway/src/services/email-service.ts (digest cron)

## Success Criteria
- Deep health check returns DB/KV/AI status
- Admin can view daily revenue + MRR
- Weekly digest emails sent automatically
- Response time headers on all requests
