# Phase 03: Edge Backend Migration — Hono.js + Hyperdrive < 50ms

## Context Links

- Research: [Edge Backend + SEA Market](./research/researcher-02-edge-backend-sea-market.md)
- Existing Gateway: `apps/raas-gateway/` (Cloudflare Workers, da co)
- Hub Backend: Fastify + PostgreSQL + BullMQ (hien tai tren VPS)
- Supabase: Singapore region

## Overview

- **Priority:** P2
- **Status:** pending
- **Effort:** 1 week
- **Description:** Migrate stateless API routes tu Fastify sang Hono.js tren Cloudflare Workers. Dung Hyperdrive proxy Postgres (thay vi D1). Giu BullMQ tren VPS cho job queue. Target: < 50ms latency globally.

## Key Insights

- Hono built on Web Standards (Fetch API) — chay native tren Workers, KHONG can polyfill
- Hyperdrive: 17-25x nhanh hon direct Postgres (cached), 6-8x uncached — chi doi connection string
- D1 KHONG phu hop: AgencyOS dung Postgres + BullMQ, D1 la SQLite → migration effort qua lon
- Fastify → Hono API surface gan giong nhau: `fastify.get()` → `app.get()`, 80% patterns map truc tiep
- Workers Paid plan: ~$5/mo vs VPS $80-120/mo
- BullMQ can persistent TCP (Redis) → KHONG chay tren Workers → giu tren VPS

## Requirements

### Functional
- [ ] Migrate read-heavy routes sang Hono Workers (health, templates, catalog, pricing)
- [ ] Hyperdrive connection to Supabase Postgres (Singapore)
- [ ] Giu BullMQ Hub tren VPS, Workers proxy requests den Hub
- [ ] Durable Objects cho per-tenant sessions (future: real-time agent coordination)
- [ ] Maintain backward compatibility — existing clients khong bi anh huong

### Non-Functional
- [ ] Latency < 50ms cho read endpoints (global)
- [ ] Latency < 100ms cho write endpoints (proxy to Hub)
- [ ] Zero downtime migration (gradual route-by-route)
- [ ] Cost < $10/mo (Workers + Hyperdrive)
- [ ] Rollback mechanism: switch DNS back to VPS trong < 5min

## Architecture

### Current State

```
Client → Cloudflare Workers (Gateway/proxy) → VPS (Fastify Hub)
                                                ├── PostgreSQL (Supabase SG)
                                                └── BullMQ (Redis)
```

### Target State

```
Client → Cloudflare Workers (Hono.js)
           ├── Stateless routes → Hyperdrive → Supabase Postgres
           │   (health, templates, catalog, pricing, auth verify)
           ├── Job dispatch → Workers fetch() → VPS Hub
           │   (task creation, BullMQ enqueue)
           └── Durable Objects (future)
               (per-tenant sessions, WebSocket, rate limiting)

VPS Hub (giu lai):
  ├── BullMQ Workers (job processing)
  ├── Redis (job queue)
  └── Long-running tasks (AI agent execution, file processing)
```

### Route Migration Matrix

| Route Category | Current | Target | Latency Impact |
|---------------|---------|--------|----------------|
| `/health`, `/status` | Fastify VPS | Hono Workers | 150ms → 10ms |
| `/api/templates` | Fastify VPS | Hono + Hyperdrive | 200ms → 30ms |
| `/api/catalog` | Fastify VPS | Hono + Hyperdrive | 200ms → 30ms |
| `/api/pricing` | Fastify VPS | Hono + Hyperdrive | 150ms → 20ms |
| `/api/auth/verify` | Fastify VPS | Hono + Supabase Auth | 180ms → 40ms |
| `/api/tasks` (create) | Fastify VPS | Hono → proxy to VPS | 200ms → 100ms |
| `/api/tasks` (process) | BullMQ Workers | GIU TREN VPS | unchanged |
| `/api/agents/*` | Fastify VPS | GIU TREN VPS (long-running) | unchanged |

## Related Code Files

### Files to Modify
- `apps/raas-gateway/` — Hien tai la simple proxy, se thanh full Hono app
- `apps/raas-gateway/wrangler.toml` — Add Hyperdrive binding
- `apps/raas-gateway/package.json` — Add hono dependencies

### Files to Create
- `apps/raas-gateway/src/index.ts` — Hono app entry point
- `apps/raas-gateway/src/routes/health.ts` — Health check
- `apps/raas-gateway/src/routes/templates.ts` — Template CRUD
- `apps/raas-gateway/src/routes/catalog.ts` — Catalog queries
- `apps/raas-gateway/src/routes/pricing.ts` — Pricing endpoints
- `apps/raas-gateway/src/routes/auth.ts` — Auth verification
- `apps/raas-gateway/src/routes/proxy.ts` — Proxy to VPS Hub
- `apps/raas-gateway/src/middleware/cors.ts` — CORS config
- `apps/raas-gateway/src/middleware/auth.ts` — JWT verification
- `apps/raas-gateway/src/db.ts` — Hyperdrive Postgres client

## Implementation Steps

### Step 1: Setup Hono Project (Day 1)
1. Install Hono: `pnpm add hono @hono/zod-validator`
2. Restructure `apps/raas-gateway/` thanh Hono app
3. Tao `src/index.ts` voi Hono app instance
4. Configure `wrangler.toml`: Workers config, routes, bindings
5. Setup local dev: `wrangler dev`

### Step 2: Hyperdrive Configuration (Day 1)
1. Tao Hyperdrive config tren Cloudflare dashboard
   ```bash
   npx wrangler hyperdrive create agencyos-db \
     --connection-string="postgresql://user:pass@db.supabase.co:5432/postgres"
   ```
2. Add binding vao `wrangler.toml`:
   ```toml
   [[hyperdrive]]
   binding = "HYPERDRIVE"
   id = "<hyperdrive-config-id>"
   ```
3. Tao `src/db.ts`: Postgres client qua Hyperdrive
4. Test connection: SELECT 1

### Step 3: Migrate Stateless Routes (Day 2-3)
1. `/health` + `/status` — simplest, test pipeline
2. `/api/templates` — read-only, Hyperdrive query
3. `/api/catalog` — read-only, Hyperdrive query
4. `/api/pricing` — read-only, cached
5. `/api/auth/verify` — JWT verify + Supabase check
6. Moi route: test local → deploy preview → benchmark latency

### Step 4: VPS Proxy Layer (Day 3)
1. Tao `src/routes/proxy.ts` — forward requests den VPS Hub
2. Routes can proxy: `/api/tasks` (create), `/api/agents/*`
3. Add timeout: 30s cho proxy requests
4. Error handling: 502 Bad Gateway khi VPS khong response
5. Health check: Workers ping VPS moi 30s

### Step 5: Middleware (Day 4)
1. CORS middleware: allow agencyos-landing + agencyos-web origins
2. Auth middleware: JWT verify tu Supabase
3. Rate limiting: per-IP, per-tenant
4. Request logging: structured JSON
5. Error handler: consistent error response format

### Step 6: Gradual Rollout (Day 4-5)
1. Deploy Hono Workers cung voi existing gateway
2. Route 10% traffic → Hono (Cloudflare traffic splitting)
3. Monitor: latency, error rate, Postgres connection pool
4. Tang len 50% → 100% neu stable
5. Giu VPS Hub running cho BullMQ + long-running tasks

### Step 7: Benchmark + Optimize (Day 5)
1. Benchmark tu nhieu regions: `curl -w "%{time_total}" https://api.agencyos.network/health`
2. Target: < 50ms tu Vietnam, < 80ms tu US/EU
3. Optimize: cache frequently-read data tai Workers (KV hoac Cache API)
4. Monitor Hyperdrive connection pool usage
5. Setup alerting: latency > 100ms → alert

## Todo List

- [ ] Install + setup Hono project
- [ ] Configure wrangler.toml
- [ ] Setup Hyperdrive connection
- [ ] Test Hyperdrive → Supabase Postgres
- [ ] Migrate `/health` route
- [ ] Migrate `/api/templates` route
- [ ] Migrate `/api/catalog` route
- [ ] Migrate `/api/pricing` route
- [ ] Migrate `/api/auth/verify` route
- [ ] Implement VPS proxy layer
- [ ] Add CORS middleware
- [ ] Add auth middleware
- [ ] Add rate limiting
- [ ] Gradual rollout (10% → 50% → 100%)
- [ ] Benchmark latency tu nhieu regions
- [ ] Setup monitoring + alerting
- [ ] Document rollback procedure

## Success Criteria

- Read endpoints < 50ms latency (from Vietnam)
- Write endpoints < 100ms (proxy to VPS)
- Zero downtime during migration
- All existing clients KHONG bi anh huong
- Cost < $10/mo (Workers + Hyperdrive)
- Rollback possible trong < 5min (DNS switch)
- BullMQ jobs van chay binh thuong tren VPS

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hyperdrive connection pool exhaustion | 503 errors | Monitor pool usage, config max connections |
| Node.js API khong tuong thich Workers | Route fail | Test tung route rieng, giu VPS fallback |
| Supabase Auth SDK khong chay tren Workers | Auth broken | Dung raw JWT verify thay vi SDK |
| VPS proxy timeout | Task creation fail | Retry logic + queue offline |
| Gradual rollout gap | Some users get old, some new | Sticky sessions via cookie |

## Security Considerations

- Hyperdrive connection string: stored in Cloudflare secrets, KHONG trong code
- JWT verification: validate signature + expiry + audience
- VPS proxy: authenticated voi shared secret header
- Rate limiting: chong DDoS tai edge layer
- CORS: strict origin whitelist
- No raw SQL trong route handlers — dung parameterized queries

## Next Steps

- Durable Objects cho real-time agent coordination (Phase 3.5)
- Evaluate D1 cho greenfield features (audit logs, analytics)
- WebSocket support qua Durable Objects (live order streaming)
- Multi-region Postgres (Supabase Read Replicas) neu latency van > 50ms tu US/EU

## Unresolved Questions

1. Hyperdrive free tier gioi han bao nhieu connections?
2. Supabase Auth SDK co chay tren Workers runtime khong? Hay can raw JWT verify?
3. BullMQ Redis: `cloudflare:sockets` da support Redis protocol chua? (xac nhan KHONG dung tren Workers)
4. VPS Hub hien tai dung Fastify version nao? Co deprecated APIs khong?
5. Cloudflare traffic splitting: co can Enterprise plan khong hay Workers Paid du?
6. Existing raas-gateway code structure — can review truoc khi overwrite?
