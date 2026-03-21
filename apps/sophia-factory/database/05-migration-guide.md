# Migration Guide: Supabase → Cloudflare D1

**Date:** 2026-03-20  
**Status:** Ready to execute

---

## Architecture Change

### Before (Supabase for everything)
```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Supabase   │ ← Auth + Database + Storage
└─────────────┘
```

### After (Hybrid)
```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
       ├──────────────┐
       ▼              ▼
┌─────────────┐ ┌─────────────┐
│  Supabase   │ │  Cloudflare │
│  (Auth)     │ │  D1 (DB)    │
└─────────────┘ └─────────────┘
```

---

## What Changed

| Feature | Before | After |
|---------|--------|-------|
| Auth | Supabase | Supabase (unchanged) |
| Database | Supabase PostgreSQL | Cloudflare D1 (SQLite) |
| Vectors | pgvector | JSON arrays (cosine similarity in app) |
| RLS | Supabase RLS | App-level auth checks |
| Edge | HTTP latency | Native edge (Workers) |

---

## Migration Steps

### Step 1: Create D1 Database

```bash
cd apps/sophia-factory
wrangler d1 create sophia-factory-db
```

Copy the `database_id` from output and update `wrangler.toml`.

### Step 2: Apply Schema

```bash
wrangler d1 execute sophia-factory-db --file=database/04-d1-schema.sql
```

### Step 3: Update Environment Variables

```bash
# Copy .env.local
cp .env.local.example .env.local

# Edit with your values:
# - SUPABASE_URL (for Auth)
# - SUPABASE_ANON_KEY (for Auth)
# - OPENAI_API_KEY
```

### Step 4: Update Code

**Files changed:**
- `src/lib/supabase.ts` — Now Auth only (user management via hooks)
- `src/lib/d1.ts` — New D1 client (all data operations)
- `src/index.ts` — API routes using D1

### Step 5: Test Locally

```bash
# Start dev server
pnpm dev

# Or use Wrangler for local D1
wrangler dev
```

### Step 6: Deploy to Cloudflare

```bash
wrangler deploy
```

---

## Code Migration

### Supabase → D1 Mapping

| Supabase | D1 Equivalent |
|----------|---------------|
| `uuid_generate_v4()` | `crypto.randomUUID()` |
| `JSONB` | `TEXT` (JSON string) |
| `vector(1536)` | `TEXT` (JSON array) |
| `NOW()` | `CURRENT_TIMESTAMP` |
| `RLS policies` | App-level checks |
| `pgvector cosine` | Manual calculation |

### Example Query Migration

**Supabase (PostgreSQL):**
```sql
SELECT * FROM proposals 
WHERE org_id = $1 
ORDER BY created_at DESC
```

**D1 (SQLite):**
```typescript
const { results } = await db
  .prepare('SELECT * FROM proposals WHERE org_id = ? ORDER BY created_at DESC')
  .bind(orgId)
  .all()
```

---

## Vector Search Migration

### Before (pgvector)
```sql
SELECT * FROM training_documents
WHERE org_id = $1
ORDER BY embedding <=> $2::vector
LIMIT 5
```

### After (SQLite + cosine similarity)
```typescript
// See d1.ts → searchSimilarDocuments()
// Cosine similarity calculated in SQL or app layer
```

**Note:** For production, consider using Cloudflare AI embeddings + app-side similarity calculation for better performance.

---

## Rollback Plan

If D1 migration fails:

1. Keep Supabase project active (Auth only)
2. Export D1 data: `wrangler d1 export sophia-factory-db --output=data.sql`
3. Re-import to Supabase if needed

---

## Post-Migration Checklist

- [ ] D1 database created
- [ ] Schema applied successfully
- [ ] .env.local configured
- [ ] Local dev works
- [ ] Deploy to Cloudflare successful
- [ ] Auth flow tested (Supabase → D1 user linking)
- [ ] All API endpoints working
- [ ] Vector search tested

---

## Support

**Issues:** Create GitHub issue with error logs  
**Docs:** See `README.md` and `SETUP_GUIDE.md`
