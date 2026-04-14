# Sophia Supabase Setup Report

**Date:** 2026-03-20
**Status:** Complete
**Project:** Sophia AI Factory

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `database/03-rls-policies.sql` | Row Level Security policies for all tables |
| `scripts/setup-supabase.sh` | Interactive setup wizard |
| `scripts/test-supabase-connection.js` | Connection verification script |
| `package.json` | Added `db:setup`, `db:check`, `db:seed` scripts |

---

## Quick Start Commands

```bash
# Option A: Interactive setup wizard (recommended for first-time)
npm run db:setup

# Option B: Manual setup (see steps below)

# After setup, verify connection
npm run db:check
```

---

## Manual Setup Steps

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click **"New Project"**
3. Fill in:
   - **Name:** `sophia-factory`
   - **Database Password:** (save in password manager)
   - **Region:** Choose nearest to your users
4. Wait ~2 minutes for provisioning

### 2. Apply Database Schema

**Option A: Via Supabase CLI**
```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
psql "$(supabase db url)" -f database/schema.sql
psql "$(supabase db url)" -f database/03-rls-policies.sql
```

**Option B: Via Dashboard**
1. Open [SQL Editor](https://supabase.com/dashboard/project/XXX/sql/new)
2. Copy content from `database/schema.sql`
3. Paste and click **Run**
4. Copy content from `database/03-rls-policies.sql`
5. Paste and click **Run**

### 3. Configure Environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your credentials from **Settings → API**:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=sk-...your-openai-key
```

### 4. Verify Connection

```bash
npm run db:check
```

Expected output:
```
✅ Found N organization(s)
✅ Found N user(s)
✅ pgvector extension working correctly
✅ ALL TESTS PASSED - Supabase is ready!
```

---

## Database Schema Summary

| Table | Description | RLS Policy |
|-------|-------------|------------|
| `organizations` | Agencies/companies | Users see own org |
| `users` | User accounts | Users see/insert own profile |
| `brand_voices` | AI brand models | Org members CRUD |
| `proposals` | Generated proposals | Org members CRUD |
| `templates` | Proposal templates | Public read, auth write |
| `training_documents` | Brand training files | Org members CRUD |

### Extensions Enabled

- `vector` (pgvector) - For AI embedding similarity search

### Custom Functions

- `match_training_documents()` - Semantic search for training docs
- `match_brand_voices()` - Brand voice similarity search

---

## Seed Data (Optional)

To add demo data for testing:

```sql
-- Run in Supabase SQL Editor or via:
psql "$(supabase db url)" -f database/02-seed-data.sql
```

This creates:
- 1 demo organization (`Demo Agency`)
- 1 demo user (`admin@demo.agency`)
- 3 demo proposals
- 4 demo templates
- 2 demo training documents

---

## Troubleshooting

### Connection Failed

```
❌ Connection test failed: Invalid API key
```

**Fix:** Verify your `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env.local` matches the value in Supabase Dashboard → Settings → API.

### Table Does Not Exist

```
❌ relation "organizations" does not exist
```

**Fix:** Run `database/schema.sql` in the SQL Editor first.

### pgvector Not Working

```
⚠️  pgvector function not found
```

**Fix:** Ensure `CREATE EXTENSION IF NOT EXISTS vector;` was run (included in schema.sql).

### RLS Blocking Queries

```
❌ new row violates row-level security policy
```

**Fix:** Make sure you're authenticated via Supabase Auth, or temporarily disable RLS for testing:
```sql
ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
```

---

## Next Steps

1. ✅ **Complete** - Supabase project created
2. ✅ **Complete** - Database schema applied
3. ✅ **Complete** - RLS policies configured
4. 🔄 **In Progress** - Environment variables configured
5. ⏳ **Pending** - Connection verified
6. ⏳ **Pending** - Start development server (`npm run dev`)

---

## Security Notes

- **NEVER** commit `.env.local` to git
- **NEVER** share your `service_role` key publicly
- The `anon` key is safe for client-side use (RLS protects data)
- Use `service_role` key only in server-side code (Edge Functions, API routes)

---

## Unresolved Questions

- None at this time

---

**Report saved to:** `/Users/macbook/mekong-cli/plans/reports/sophia-supabase-setup-260320.md`
