# Research Report: Edge Backend Migration + SEA F&B Market
Date: 2026-02-27 | Researcher: 02

---

## Topic 1: Edge Computing Backend Migration (Cloudflare Workers)

### Architecture: Hono.js as Fastify Replacement

**Why Hono, not Fastify-on-edge:**
- Fastify is Node.js-only; edge needs polyfills + adapters → adds latency, not removes it
- Hono is built on Web Standards (Fetch API), runs natively on Workers, Deno, Bun, Node.js
- Same Hono codebase deploys to Workers AND Node.js → zero lock-in
- Cloudflare internally uses Hono for D1's Web API and Workers Logs (migrated from Baselime)
- Benchmark: Hono ~1M req/s on Bun vs Fastify ~60K req/s on Node.js (different runtimes, indicative only)

**Migration path Fastify → Hono:**
```
Fastify Route:         fastify.get('/users', handler)
Hono Equivalent:       app.get('/users', handler)
Middleware:            app.use(middleware)  [nearly identical API]
Plugins → Middleware:  manual port, ~80% patterns map directly
```

**Node.js compatibility (2025 update):** Cloudflare added support for `node:crypto`, `node:stream`, `node:buffer`, `node:path` — covers ~90% of Fastify dependencies. Express/Koa now run on Workers; Fastify support in progress.

---

### D1 vs Hyperdrive: Decision Matrix

| Factor | D1 (SQLite at Edge) | Hyperdrive (Proxy to Postgres) |
|--------|--------------------|---------------------------------|
| Latency | <10ms (read replicas near user) | 17-25x faster than direct Postgres (cached), 6-8x uncached |
| Data model | SQLite semantics | Full PostgreSQL |
| AgencyOS fit | Bad — Hub uses Postgres, BullMQ deps | **Good — keeps existing Postgres + BullMQ** |
| Migration effort | HIGH (schema rewrite, SQLite quirks) | LOW (change connection string) |
| Cost | Scales by row reads/writes; can spike | Included in Workers Paid plan (~$5/mo) |
| Writes | Single-region write bottleneck | Writes still go to Postgres primary |
| Max DB size | 10GB (Workers plan) | Unlimited (your Postgres) |
| When to use | Greenfield, low-write, global reads | Existing Postgres, complex queries, BullMQ |

**Verdict for AgencyOS: Hyperdrive wins.** AgencyOS Hub is Fastify + PostgreSQL + BullMQ. Hyperdrive = connection string swap + instant edge acceleration. D1 would require full schema migration and loss of BullMQ patterns.

---

### Durable Objects: When to Use

- Stateful per-entity compute: one DO per restaurant, per agent session, per WebSocket connection
- Use case for AgencyOS: real-time agent task coordination, live order streaming, per-tenant rate limiting
- NOT for: general API routing, batch jobs (BullMQ still wins for that)
- Cost: $0.15/million DO requests + $0.20/GB-month storage

---

### Cost: VPS vs Edge-First

| Setup | Monthly Cost | Latency (global) | Scaling |
|-------|-------------|-------------------|---------|
| 2x VPS (SG + US) | ~$80-120 | 150-300ms cross-region | Manual |
| Cloudflare Workers (Paid) | $5 + usage | 10-50ms globally | Auto |
| Workers + Hyperdrive | $5 + Postgres cost | 20-60ms | Auto |
| Workers + D1 (high traffic) | Can exceed $200 | <10ms | Auto |

**Edge wins on latency and ops cost; D1 cost can surprise at scale.**

---

### Real-World Migration Pattern (Recommended for AgencyOS)

```
Phase 1: Cloudflare Gateway (TODAY) — already done
Phase 2: Migrate Fastify routes → Hono on Workers
  - Start with read-heavy, stateless endpoints (/health, /templates, /catalog)
  - Keep BullMQ Hub on VPS behind Workers (Hyperdrive proxy)
Phase 3: Durable Objects for real-time features (agent sessions, WebSocket)
Phase 4: Evaluate D1 only for new greenfield features (audit logs, analytics)
```

---

## Topic 2: SEA F&B Market Analysis

### Market Size

- SEA F&B total market: **$667B (2023)** → projected **$900B by 2028** (CAGR ~6.99%)
- SEA Foodservice segment: **$192B (2024)** → **$349B by 2029** (CAGR 12.65%)
- Vietnam F&B: **$23.6B**; Thailand: **$34B**; Indonesia: largest SEA economy
- Vietnam: 323,000 active F&B establishments (2024); 30,000 closures H1 2024 → high churn = SaaS opportunity

### POS/Ordering Dominant Players

| Player | Country | Segment | Weakness |
|--------|---------|---------|---------|
| KiotViet | Vietnam | SME retail + F&B | Basic AI, no agent features |
| Sapo | Vietnam | SME F&B + retail | Complex onboarding |
| MISA CukCuk | Vietnam | F&B focused | Expensive for micro-SMEs |
| Lightspeed / Toast | Global | Enterprise | No SEA localization |
| Wongnai / LINE MAN | Thailand | Ordering/delivery | Not full POS |
| GoBiz (Gojek) | Indonesia | Merchant tools | Fragmented |

**Gap:** No dominant player offers AI-agent-powered automation (inventory, staffing, menu optimization) for SEA SMEs.

### Pain Points AI Agents Can Solve

1. **Demand forecasting** — 68% of small F&B close within 3 years due to inventory waste; AI can cut waste 20-30%
2. **Staff scheduling** — manual, WhatsApp-based; AI scheduler saves 3-5 hrs/owner/week
3. **Menu pricing optimization** — owners price by gut feel; dynamic pricing AI can lift margins 8-15%
4. **Delivery platform management** — juggling GrabFood + ShopeeFood + Baemin = duplicated effort; unified AI hub
5. **Onboarding friction** — tech anxiety is #1 barrier; conversational AI setup (vs. 50-screen configuration) = key differentiator

### Digital Transformation Drivers

- Vietnam: 88M internet users, urbanization >40%, QR payment adoption accelerating
- Indonesia: QRIS universal QR standard mandated by BI → payment rail ready for SaaS layer
- Thailand: LINE ecosystem + LINE MAN dominance → integration opportunity
- Mobile-first ordering grew 35%+ post-COVID; delivery GMV SEA: $16.3B (2024) → $23B (2026) per Statista

### AgencyOS Template Opportunity

| Template Vertical | Target | Pricing Benchmark | TAM Signal |
|-------------------|--------|-------------------|------------|
| F&B Agent Suite (menu + inventory + delivery hub) | Vietnam/Indonesia SME restaurants | $30-80/mo | 323K VN establishments |
| Quick Service Restaurant (QSR) Pack | Bubble tea, fast food chains | $80-150/mo | Franchise model scales fast |
| Ghost Kitchen Ops | Delivery-only kitchens | $50-100/mo | 40% YoY growth segment |

---

## Summary Recommendations

**Topic 1 (Edge Migration):**
- Replace Fastify with Hono — low effort, immediate win, same DX
- Use Hyperdrive NOT D1 for AgencyOS (preserves Postgres + BullMQ investment)
- Add Durable Objects only for real-time agent coordination features
- Expected latency improvement: 150ms → 30-50ms for global users

**Topic 2 (SEA F&B Market):**
- Vietnam is highest-signal market: large active base, high tech anxiety = low current saturation, price-sensitive but proven SaaS willingness (KiotViet at $15-30/mo has millions of users)
- AI agent differentiation is wide open — no incumbent owns it
- Lead with conversational onboarding (solve tech anxiety) + WhatsApp-native workflow

---

## Unresolved Questions

1. Hyperdrive latency with Supabase (Singapore region) to Workers — need real benchmark from AgencyOS infra
2. BullMQ on Workers: Workers do not support persistent TCP connections natively; need to confirm `cloudflare:sockets` API covers BullMQ Redis protocol
3. KiotViet/Sapo API partnership feasibility — do they have open webhooks for integration?
4. Vietnam B2B SaaS payment: Polar.sh supports VND? Or need local gateway (VNPay)?

---

## Sources

- [Cloudflare Node.js Workers 2025](https://blog.cloudflare.com/nodejs-workers-2025/)
- [Cloudflare Durable Objects docs](https://developers.cloudflare.com/durable-objects/concepts/what-are-durable-objects/)
- [Hyperdrive: making databases feel global](https://blog.cloudflare.com/hyperdrive-making-regional-databases-feel-distributed/)
- [Mats' blog: Migrating D1 to Hyperdrive](https://mats.coffee/blog/d1-to-hyperdrive)
- [Hono on Cloudflare Workers](https://hono.dev/docs/getting-started/cloudflare-workers)
- [Hono vs Fastify - Better Stack](https://betterstack.com/community/guides/scaling-nodejs/hono-vs-fastify/)
- [D1: SQLite at the Edge - Architecting on Cloudflare](https://architectingoncloudflare.com/chapter-12/)
- [SEA F&B Industry 2024-2025](https://www.sourceofasia.com/fb-industry-in-southeast-asia-2024-2025/)
- [Vietnam F&B Tech SME adoption gaps](https://b-company.jp/technology-adoption-in-vietnams-fb-smes-current-gaps-challenges-and-strategic-solutions/)
- [Mordor Intelligence SEA Foodservice Market](https://www.mordorintelligence.com/industry-reports/southeast-asia-foodservice-market)
- [Vietnam Smart POS SaaS Market - Ken Research](https://www.kenresearch.com/vietnam-smart-retail-and-pos-saas-market)
- [F&B Trends 2026 SEA - HelloNimbly](https://hellonimbly.com/fb-trend-in-2026-what-southeast-asia-needs-and-how-to-deliver/)
