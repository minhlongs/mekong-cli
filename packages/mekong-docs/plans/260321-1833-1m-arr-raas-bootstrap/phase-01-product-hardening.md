# Phase 01: Product Hardening

## Priority: P0
## Status: pending

## Tasks

### 1.1 Mission Templates Library
- Create 20+ pre-built mission templates in DB seed
- Categories: content, code, research, marketing, sales, support
- Each template: title, description, default complexity, estimated credits
- API: GET /v1/missions/templates (already exists, need more templates)

### 1.2 Mission History Search/Filter
- Add query params to GET /v1/missions: ?status=, ?from=, ?to=, ?q= (goal search)
- Add pagination metadata (total, hasMore)

### 1.3 Webhook Reliability
- Dead-letter queue table for failed webhook deliveries
- GET /v1/webhooks/failures endpoint (list failed deliveries)
- POST /v1/webhooks/retry/:id (manual retry)

### 1.4 Tenant Settings Endpoint
- PUT /v1/tenants/settings — update webhook_url, notification prefs
- Store in tenants table (add columns if needed)

### 1.5 Mission Tags/Labels
- Add tags column to missions table
- Filter by tag: GET /v1/missions?tag=marketing

### 1.6 API Versioning Header
- Add X-API-Version: 2026-03-21 response header
- Document in OpenAPI spec

## Files to Modify
- apps/raas-gateway/src/routes/missions.ts
- apps/raas-gateway/src/routes/tenants.ts
- apps/raas-gateway/src/services/mission-executor.ts
- apps/raas-gateway/migrations/ (new migration files)

## Success Criteria
- 20+ templates seeded
- Mission search working with filters
- Webhook retry mechanism functional
- All existing tests still pass
