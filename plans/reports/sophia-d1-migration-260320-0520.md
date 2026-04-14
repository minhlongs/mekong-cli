# Sophia AI Factory — D1 Migration Report

**Date:** 2026-03-20  
**Migration:** Supabase → Cloudflare D1 (Auth remains on Supabase)  
**Status:** ✅ READY

---

## Architecture Decision

**Supabase:** Auth ONLY (users, sessions, magic links)  
**Cloudflare D1:** All data (organizations, proposals, brand voices, training docs)

### Why D1?

| Benefit | Impact |
|---------|--------|
| Edge-native | <50ms p95 latency |
| Serverless | No connection pooling needed |
| Cost | Free tier generous |
| Integration | Native Workers binding |
| Scale | Auto-scaling |

---

## Files Created

| File | Purpose |
|------|---------|
| `database/04-d1-schema.sql` | SQLite schema (6 tables) |
| `database/05-migration-guide.md` | Step-by-step migration |
| `wrangler.toml` | Cloudflare config |
| `src/lib/d1.ts` | D1 client library |
| `src/index.ts` | API routes |
| `src/types/error.ts` | Error types |
| `.env.local` | Environment template |

---

## Schema Comparison

### Tables (6 total)

| Table | Purpose | D1 Type Changes |
|-------|---------|-----------------|
| organizations | Agency accounts | UUID → TEXT |
| users | Linked to Supabase Auth | JSONB → TEXT |
| brand_voices | AI brand profiles | vector → TEXT |
| proposals | Generated proposals | JSONB → TEXT |
| templates | Proposal templates | JSONB → TEXT |
| training_documents | Brand training data | vector → TEXT |

### Vector Handling

**Before:** pgvector `vector(1536)`  
**After:** JSON array stored as TEXT, cosine similarity in app

---

## Next Steps (User Manual)

```bash
cd apps/sophia-factory

# 1. Create D1 database
wrangler d1 create sophia-factory-db

# 2. Update wrangler.toml with database_id

# 3. Apply schema
wrangler d1 execute sophia-factory-db --file=database/04-d1-schema.sql

# 4. Configure .env.local

# 5. Test locally
wrangler dev

# 6. Deploy
wrangler deploy
```

---

## Auth Flow (Supabase → D1)

1. User signs up via Supabase Auth
2. Supabase triggers webhook
3. Webhook creates user in D1
4. App uses D1 for all data queries

---

**Migration Ready!** Awaiting user execution.
